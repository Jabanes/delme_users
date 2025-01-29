import sqlite3
from typing import List
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from fastapi.middleware.cors import CORSMiddleware  # Import CORSMiddleware


# Database setup
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

# Model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic model for User creation
class UserCreate(BaseModel):
    name: str
    email: str

# FastAPI app

origins = [
   "https://delme-users-1.onrender.com",
   "https://jade-sunburst-3dc4a3.netlify.app/",
   "http://127.0.0.1:5500",  # Add the port to specify where the frontend is hosted during development
   "http://localhost:5500"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # List of origins to allow
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)
# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}

# Routes

# Create a new user
@app.post("/users/", response_model=dict)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(name=user.name, email=user.email)
    
    # Add the user to the database session
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Return the created user's data
    return {"id": db_user.id, "name": db_user.name, "email": db_user.email}

# Get a user by ID
@app.get("/users/{user_id}", response_model=dict)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "name": user.name, "email": user.email}

@app.get("/users", response_model=List[dict])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()  # Fetch all users
    if not users:  # If no users are found
        raise HTTPException(status_code=404, detail="Users not found")
    
    # Return a list of users' data
    return [{"id": user.id, "name": user.name, "email": user.email} for user in users]
# Update a user by ID
@app.put("/users/{user_id}", response_model=dict)
def update_user(user_id: int, user: UserCreate, db: Session = Depends(get_db)):
    user_in_db = db.query(User).filter(User.id == user_id).first()
    if user_in_db is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_in_db.name = user.name
    user_in_db.email = user.email
    db.commit()
    
    return {"id": user_in_db.id, "name": user_in_db.name, "email": user_in_db.email}

# Delete a user by ID
@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

# Run the application (for development purposes, use uvicorn to run it)
# If running directly, you can use: `uvicorn filename:app --reload`
