from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict, Any
from datetime import datetime, timedelta
from jose import jwt
import os
from ..models.user import User
from ..services.auth import get_current_user
from ..database.user_db import get_user_by_email
from ..utils.logger import logger

router = APIRouter()

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Dict:
    """Authenticate user and return access token."""
    try:
        # Get user from database
        user = await get_user_by_email(form_data.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # TODO: Verify password hash here
        # For now, accept any password for demo purposes
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["email"]}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/register")
async def register(user_data: Dict[str, Any]) -> Dict:
    """Register a new user."""
    try:
        # TODO: Implement user registration logic
        # For now, return success for demo purposes
        
        return {
            "message": "User registered successfully",
            "user_id": "mock-user-id"
        }
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")

@router.get("/user/profile")
async def get_user_profile(current_user: User = Depends(get_current_user)) -> Dict:
    """Get current user's profile."""
    try:
        return {
            "success": True,
            "user": {
                "email": current_user["email"],
                "name": current_user.get("name", ""),
                "id": current_user["id"],
                "dietary_restrictions": current_user.get("dietary_restrictions", []),
                "health_conditions": current_user.get("health_conditions", []),
                "preferences": current_user.get("preferences", {}),
                "goals": current_user.get("goals", {})
            }
        }
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user profile") 