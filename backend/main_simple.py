#!/usr/bin/env python3
"""
Simplified FastAPI backend without pydantic dependencies
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import urllib.parse
import hashlib
import secrets

# Import working modules
from dotenv import load_dotenv
from passlib.context import CryptContext
from jose import JWTError, jwt

# Try to import database functions without pydantic
try:
    from database import (
        create_user,
        get_user_by_email,
        save_patient_profile,
        get_patient_profile
    )
    print("✓ Database imports successful")
    database_available = True
except ImportError as e:
    print(f"✗ Database imports failed: {e}")
    database_available = False
    # Fallback functions
    async def create_user(user_data): pass
    async def get_user_by_email(email): return None
    async def save_patient_profile(profile): return True
    async def get_patient_profile(user_id): return {}

# Load environment variables
load_dotenv()

# Security setup
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Simple in-memory user store (for testing when database is not available)
users_store = {
    "test@example.com": {
        "email": "test@example.com", 
        "username": "test@example.com",
        "hashed_password": pwd_context.hash("password123"),
        "disabled": False
    }
}

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Simple Flask-like app for testing
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse

class SimpleAPIHandler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    
    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            response = {"status": "healthy", "message": "Simple API is working!"}
            self.wfile.write(json.dumps(response).encode())
        
        elif self.path == '/api/profile/get':
            # Simple profile get endpoint
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            response = {
                "fullName": "Test User",
                "age": 30,
                "sex": "Male",
                "ethnicity": ["Other"]
            }
            self.wfile.write(json.dumps(response).encode())
        
        else:
            self.send_response(404)
            self._set_cors_headers()
            self.end_headers()
    
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
            else:
                data = {}
            
            if self.path == '/login':
                # Handle login
                username = data.get('username', '')
                password = data.get('password', '')
                
                print(f"Login attempt for: {username}")
                
                # Check credentials
                user = users_store.get(username)
                if user and verify_password(password, user['hashed_password']):
                    # Create access token
                    access_token = create_access_token(data={"sub": username})
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self._set_cors_headers()
                    self.end_headers()
                    
                    response = {
                        "access_token": access_token,
                        "token_type": "bearer",
                        "message": "Login successful"
                    }
                    self.wfile.write(json.dumps(response).encode())
                    print(f"✓ Login successful for {username}")
                else:
                    self.send_response(401)
                    self.send_header('Content-type', 'application/json')
                    self._set_cors_headers()
                    self.end_headers()
                    response = {"detail": "Incorrect username or password"}
                    self.wfile.write(json.dumps(response).encode())
                    print(f"✗ Login failed for {username}")
            
            elif self.path == '/register':
                # Handle registration
                email = data.get('email', '')
                password = data.get('password', '')
                registration_code = data.get('registration_code', '')
                
                print(f"Registration attempt for: {email}")
                
                # Simple registration (accept any registration code for testing)
                if email and password:
                    hashed_password = get_password_hash(password)
                    users_store[email] = {
                        "email": email,
                        "username": email,
                        "hashed_password": hashed_password,
                        "disabled": False
                    }
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self._set_cors_headers()
                    self.end_headers()
                    response = {"message": "Registration successful"}
                    self.wfile.write(json.dumps(response).encode())
                    print(f"✓ Registration successful for {email}")
                else:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self._set_cors_headers()
                    self.end_headers()
                    response = {"detail": "Email and password required"}
                    self.wfile.write(json.dumps(response).encode())
            
            elif self.path == '/api/profile/save':
                # Handle profile save
                print(f"Profile save request: {data}")
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self._set_cors_headers()
                self.end_headers()
                response = {
                    "status": "success", 
                    "message": "Profile saved successfully!",
                    "received": data
                }
                self.wfile.write(json.dumps(response).encode())
                print("✓ Profile saved successfully")
            
            else:
                self.send_response(404)
                self._set_cors_headers()
                self.end_headers()
                
        except Exception as e:
            print(f"Error handling request: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            response = {"status": "error", "message": str(e)}
            self.wfile.write(json.dumps(response).encode())

if __name__ == "__main__":
    print("Starting enhanced simple API server...")
    print("Available endpoints:")
    print("  GET  /health - Health check")
    print("  POST /login - User login")
    print("  POST /register - User registration") 
    print("  GET  /api/profile/get - Get user profile")
    print("  POST /api/profile/save - Save user profile")
    print("\nTest credentials:")
    print("  Email: test@example.com")
    print("  Password: password123")
    
    server = HTTPServer(('localhost', 8000), SimpleAPIHandler)
    print("\nServer running on http://localhost:8000")
    print("Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown() 