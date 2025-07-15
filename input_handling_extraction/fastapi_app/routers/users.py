import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from ..models.users import UserRegistration
from ..services.user_service import UserService

load_dotenv()

router = APIRouter(prefix="/users", tags=["users"])

# initialize user service
user_service = UserService()

@router.post("/register")
def register_user(user_data: UserRegistration):
    """register a new user"""
    success = user_service.register_user(user_data.username, user_data.email)
    if success:
        return {"message": "User registered successfully", "username": user_data.username}
    else:
        raise HTTPException(status_code=400, detail="Username already exists")

@router.post("/login")
def login_user(username: str):
    """authenticate a user"""
    if user_service.authenticate_user(username):
        return {"message": "Login successful", "username": username}
    else:
        raise HTTPException(status_code=401, detail="Invalid username")

@router.get("/")
def list_users():
    """list all registered users"""
    return {"users": user_service.get_users_list()}

@router.get("/table")
def get_users_table():
    """get users data as a table with all details"""
    return {"users_table": user_service.get_users_table()} 