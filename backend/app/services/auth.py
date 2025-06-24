from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Optional, Dict, Any
from datetime import datetime
import os

# Import User model
from ..models.user import User

# Setup OAuth2 with the same token URL as in main.py
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Get JWT settings from environment
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Validate the JWT token and return the current user.
    This is a dependency that can be used in FastAPI route functions.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
            
        # Get user from database
        from database import get_user_by_email
        user = await get_user_by_email(username)
        if user is None:
            raise credentials_exception
            
        return user
        
    except JWTError:
        raise credentials_exception
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error authenticating user: {str(e)}") 