from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Optional
import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

# Re-use database connection & models from the primary backend
from backend import database as db
from backend.app.models.user import User
from backend.app.services.auth import SECRET_KEY, ALGORITHM

ADMIN_PORTAL_TITLE = "Diabetes Diet Manager – Admin Portal"
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

app = FastAPI(title=ADMIN_PORTAL_TITLE, docs_url="/docs", redoc_url="/redoc")

# Mount static assets (CSS / JS)
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# Session management
from starlette.middleware.sessions import SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_admin_user(request: Request):
    """Get current admin user from session token."""
    token = request.session.get("token")
    if not token:
        return None
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        
        # Get user from database
        user = await db.get_user_by_email(username)
        
        if not user or not user.get("is_admin", False):
            return None
            
        return user
    except JWTError:
        return None

@app.get("/")
async def root(request: Request):
    """Root endpoint that redirects to admin panel if authenticated, login if not."""
    user = await get_current_admin_user(request)
    if user:
        return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render the login page."""
    # If already logged in, redirect to admin panel
    user = await get_current_admin_user(request)
    if user:
        return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("login.html", {"request": request, "title": ADMIN_PORTAL_TITLE})

@app.post("/token")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """Handle admin login."""
    user = await db.get_user_by_email(form_data.username)
    if not user or not user.get("is_admin") or not pwd_context.verify(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user["email"], "is_admin": True},
        expires_delta=access_token_expires
    )
    
    # Store token in session
    request.session["token"] = access_token
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/logout")
async def logout(request: Request):
    """Handle logout."""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    """Render the main admin panel table with all registered users."""
    user = await get_current_admin_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        
    # Get all patients from the database
    users = await db.get_all_patients()
    
    return templates.TemplateResponse(
        "admin_panel.html", 
        {
            "request": request, 
            "users": users, 
            "title": ADMIN_PORTAL_TITLE,
            "current_user": user
        }
    )

@app.get("/users/{user_id}", response_class=HTMLResponse)
async def user_profile(user_id: str, request: Request):
    """Display and edit the comprehensive health profile for a single user."""
    user = await get_current_admin_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        
    profile = await db.get_patient_by_id(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")

    return templates.TemplateResponse(
        "profile.html", 
        {
            "request": request, 
            "user": profile, 
            "title": ADMIN_PORTAL_TITLE,
            "current_user": user
        }
    )

@app.post("/users/{user_id}/update", response_class=HTMLResponse)
async def update_user_profile(user_id: str, request: Request):
    """Update a user's profile."""
    user = await get_current_admin_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        
    form_data = await request.form()
    user_data = dict(form_data)
    
    try:
        # First check if patient exists
        patient = await db.get_patient_by_id(user_id)
        if not patient:
            raise HTTPException(status_code=404, detail="User not found")
            
        # Update the patient data
        await db.update_user(user_id, user_data)
        return RedirectResponse(
            url=f"/users/{user_id}", 
            status_code=status.HTTP_302_FOUND
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 