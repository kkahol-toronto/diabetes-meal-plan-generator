from fastapi import FastAPI, HTTPException, Depends, status, Request, Body, File, UploadFile, Form
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
import json
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from twilio.rest import Client
import random
import string
from database import (
    create_user, get_user_by_email, create_patient,
    get_patient_by_registration_code, get_all_patients,
    save_meal_plan, get_user_meal_plans, get_meal_plan_by_id,
    save_shopping_list, get_user_shopping_lists,
    save_chat_message, save_recipes, get_user_recipes,
    get_recent_chat_history,
    format_chat_history_for_prompt,
    clear_chat_history,
    get_user_sessions,
    get_patient_by_id,
    user_container,
    get_context_history,
    generate_session_id,
    interactions_container,
    view_meal_plans,
    delete_meal_plan_by_id,
    delete_all_user_meal_plans,
    save_consumption_record,
    get_user_consumption_history,
    get_consumption_analytics,
    get_user_meal_history,
    log_meal_suggestion,
    get_ai_suggestion,
    update_consumption_meal_type,
)

# Use interactions_container as consumption_collection for consistency
consumption_collection = interactions_container
import uuid
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import re
import traceback
import sys
from fastapi import Request as FastAPIRequest
from PIL import Image
import base64
from fastapi import APIRouter
import logging
from collections import defaultdict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(title="Diabetes Diet Manager API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure OpenAI
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

# Configure Twilio
twilio_client = Client(os.getenv("SMS_API_SID"), os.getenv("SMS_KEY"))

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Update password context to use newer bcrypt settings
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Explicitly set rounds for bcrypt
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: EmailStr
    disabled: Optional[bool] = None
    # Privacy & Consent Fields
    consent_given: Optional[bool] = None
    consent_timestamp: Optional[str] = None
    policy_version: Optional[str] = None
    data_retention_preference: Optional[str] = "standard"  # "minimal", "standard", "extended"
    marketing_consent: Optional[bool] = False
    analytics_consent: Optional[bool] = True
    last_consent_update: Optional[str] = None

class UserInDB(User):
    hashed_password: str

class Patient(BaseModel):
    name: str = Field(..., min_length=1, description="Patient's full name")
    phone: str = Field(..., min_length=10, description="Patient's phone number")
    condition: str = Field(..., min_length=1, description="Primary medical condition")
    medical_conditions: Optional[List[str]] = Field(default=[], description="All medical conditions")
    medications: Optional[List[str]] = Field(default=[], description="Current medications")
    allergies: Optional[List[str]] = Field(default=[], description="Food allergies")
    dietary_restrictions: Optional[List[str]] = Field(default=[], description="Dietary restrictions")
    registration_code: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        schema_extra = {
            "example": {
                "name": "John Doe",
                "phone": "1234567890",
                "condition": "Type 2 Diabetes"
            }
        }

class UserProfile(BaseModel):
    # Patient Demographics
    name: Optional[str] = None
    dateOfBirth: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    ethnicity: Optional[List[str]] = []
    
    # Medical History
    medical_conditions: Optional[List[str]] = []
    medicalConditions: Optional[List[str]] = []  # For backward compatibility
    
    # Current Medications
    currentMedications: Optional[List[str]] = []
    
    # Lab Values (Optional)
    labValues: Optional[Dict[str, Optional[str]]] = {}
    
    # Vital Signs
    height: Optional[float] = None
    weight: Optional[float] = None
    bmi: Optional[float] = None
    waistCircumference: Optional[float] = None
    waist_circumference: Optional[float] = None  # For backward compatibility
    systolicBP: Optional[int] = None
    systolic_bp: Optional[int] = None  # For backward compatibility
    diastolicBP: Optional[int] = None
    diastolic_bp: Optional[int] = None  # For backward compatibility
    heartRate: Optional[int] = None
    heart_rate: Optional[int] = None  # For backward compatibility
    
    # Dietary Information
    dietType: Optional[List[str]] = []
    diet_type: Optional[str] = None  # For backward compatibility
    dietaryFeatures: Optional[List[str]] = []
    diet_features: Optional[List[str]] = []  # For backward compatibility
    dietaryRestrictions: Optional[List[str]] = []
    foodPreferences: Optional[List[str]] = []
    allergies: Optional[List[str]] = []
    strongDislikes: Optional[List[str]] = []
    
    # Physical Activity
    workActivityLevel: Optional[str] = None
    exerciseFrequency: Optional[str] = None
    exerciseTypes: Optional[List[str]] = []
    mobilityIssues: Optional[bool] = False
    
    # Lifestyle & Preferences
    mealPrepCapability: Optional[str] = None
    availableAppliances: Optional[List[str]] = []
    eatingSchedule: Optional[str] = None
    
    # Goals & Readiness
    primaryGoals: Optional[List[str]] = []
    readinessToChange: Optional[str] = None
    
    # Meal Plan Targeting
    wantsWeightLoss: Optional[bool] = False
    weight_loss_goal: Optional[bool] = False  # For backward compatibility
    calorieTarget: Optional[str] = None
    calories_target: Optional[int] = None  # For backward compatibility

class MealPlanRequest(BaseModel):
    user_profile: UserProfile
    family_members: Optional[List[UserProfile]] = None
    additional_requirements: Optional[str] = None

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class RegistrationData(BaseModel):
    registration_code: str
    email: EmailStr
    password: str
    consent_given: bool
    consent_timestamp: str
    policy_version: str
    data_retention_preference: Optional[str] = "standard"
    marketing_consent: Optional[bool] = False
    analytics_consent: Optional[bool] = True

class ImageAnalysisRequest(BaseModel):
    prompt: str

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    print("get_current_user called")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        print("Decoding JWT token...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        print(f"Decoded username: {username}")
        if username is None:
            print("Username is None in token payload")
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError as e:
        print(f"JWTError while decoding token: {e}")
        raise credentials_exception
    except Exception as e:
        print(f"Unexpected error while decoding token: {e}")
        raise credentials_exception
    try:
        print(f"Fetching user by email: {token_data.username}")
        user = await get_user_by_email(token_data.username)
        print(f"User fetched: {user}")
        if user is None:
            print("User not found in database")
            raise credentials_exception
        print("Returning user from get_current_user")
        return user
    except Exception as e:
        print(f"Error fetching user from database: {e}")
        raise credentials_exception

def generate_registration_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def send_registration_code(phone: str, code: str):
    """Send registration code via SMS using Twilio"""
    try:
        message = twilio_client.messages.create(
            body=f"Your registration code for Diabetes Diet Manager is: {code}",
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            to=phone
        )
        print(f"Twilio message sent successfully: {message.sid}")
        return message.sid
    except Exception as e:
        print(f"Failed to send SMS: {str(e)}")
        return None

@app.post("/login", response_model=Token)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    print(f"Login attempt for user: {form_data.username}")
    
    user = await get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        print(f"Login failed for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print(f"User found: {user}")
    
    # Get form data directly from the request
    form = await request.form()
    consent_given = form.get('consent_given', 'false').lower() == 'true'
    consent_timestamp = form.get('consent_timestamp')
    policy_version = form.get('policy_version')
    
    if not consent_given:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consent is required to login"
        )
    
    # Update user's consent information
    try:
        # Build a new dictionary with only the fields we want to update
        update_dict = {
            "id": user["id"],  # Required for upsert
            "type": "user",    # Required for querying
            "consent_given": consent_given,
            "consent_timestamp": consent_timestamp,
            "policy_version": policy_version,
            # Preserve other critical fields
            "email": user["email"],
            "username": user["username"],
            "hashed_password": user["hashed_password"],
            "disabled": user.get("disabled", False),
            "is_admin": user.get("is_admin", False),  # CRITICAL: Preserve admin status
            "patient_id": user.get("patient_id"),
            "registration_code": user.get("registration_code"),  # Preserve registration code
            "profile": user.get("profile", {}),
            "data_retention_preference": user.get("data_retention_preference", "standard"),
            "marketing_consent": user.get("marketing_consent", False),
            "analytics_consent": user.get("analytics_consent", True),
            "last_consent_update": user.get("last_consent_update"),
            "created_at": user.get("created_at"),
            "updated_at": datetime.utcnow().isoformat(),
            "updated_by": "system"
        }
        
        # Perform the upsert
        user_container.upsert_item(body=update_dict)
    except Exception as e:
        print(f"Error during user update: {e}")
        # If update fails, continue with login since consent info is not critical
    
    # Get patient info if available
    patient_name = None
    if user.get("patient_id"):
        try:
            print(f"Fetching patient info for patient_id: {user['patient_id']}")
            patient = await get_patient_by_id(user["patient_id"])
            if patient:
                patient_name = patient.get("name")
                print(f"Found patient name: {patient_name}")
            else:
                print("No patient found with the given ID")
        except Exception as e:
            print(f"Error fetching patient info: {str(e)}")
    else:
        print("No patient_id found in user data")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "sub": user["email"],
        "is_admin": user.get("is_admin", False),
        "name": patient_name,
        "consent_given": user.get("consent_given", False),
        "consent_timestamp": user.get("consent_timestamp"),
        "policy_version": user.get("policy_version")
    }
    print(f"Creating token with data: {token_data}")
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register")
async def register(data: RegistrationData):
    # Find patient with registration code
    patient = await get_patient_by_registration_code(data.registration_code)
    if not patient:
        raise HTTPException(status_code=400, detail="Invalid registration code")
    
    existing_user = await get_user_by_email(data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(data.password)
    
    # Check if admin has already created a profile for this patient
    admin_profile = None
    try:
        profile_query = f"SELECT * FROM c WHERE c.type = 'user_profile' AND c.registration_code = '{data.registration_code}'"
        profiles = list(user_container.query_items(query=profile_query, enable_cross_partition_query=True))
        if profiles:
            admin_profile = profiles[0].get('profile', {})
    except Exception as e:
        print(f"Error checking for admin profile: {e}")
    
    # Create comprehensive user profile from patient data
    initial_profile = {
        "name": patient.get("name", ""),
        "medicalConditions": patient.get("medical_conditions", [patient.get("condition", "")]),
        "currentMedications": patient.get("medications", []),
        "allergies": patient.get("allergies", []),
        "dietaryRestrictions": patient.get("dietary_restrictions", []),
        "calorieTarget": "2000",  # Default, will be customized based on conditions
        "primaryGoals": ["Manage health conditions", "Maintain balanced nutrition"]
    }
    
    # If admin has created a profile, merge it with patient data (admin profile takes precedence)
    if admin_profile:
        # Merge profiles, giving priority to admin-entered data
        for key, value in admin_profile.items():
            if value and value != []:  # Only override if admin actually entered data
                initial_profile[key] = value
    
    user_data = {
        "username": data.email,
        "email": data.email,
        "hashed_password": hashed_password,
        "disabled": False,
        "patient_id": patient["id"],
        "registration_code": data.registration_code,  # Store registration code
        "profile": initial_profile,  # Include merged profile
        "consent_given": data.consent_given,
        "consent_timestamp": data.consent_timestamp,
        "policy_version": data.policy_version,
        "data_retention_preference": data.data_retention_preference,
        "marketing_consent": data.marketing_consent,
        "analytics_consent": data.analytics_consent,
        "last_consent_update": data.consent_timestamp
    }
    
    await create_user(user_data)
    
    # Create a proper user profile record in the database
    profile_record = {
        "id": f"profile_{data.email}",
        "type": "user_profile",
        "user_id": data.email,
        "registration_code": data.registration_code,
        "profile": initial_profile,
        "created_by": "patient_registration",
        "admin_prefilled": bool(admin_profile),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # Save the profile
    try:
        user_container.upsert_item(body=profile_record)
    except Exception as e:
        print(f"Error saving user profile record: {e}")
    
    return {
        "message": "Registration successful", 
        "profile_initialized": True,
        "admin_prefilled": bool(admin_profile),
        "health_conditions": initial_profile["medicalConditions"]
    }

@app.post("/admin/create-patient")
async def create_patient_endpoint(
    patient: Patient,
    current_user: User = Depends(get_current_user)
):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        registration_code = generate_registration_code()
        patient_data = {
            "name": patient.name,
            "phone": patient.phone,
            "condition": patient.condition,
            "medical_conditions": patient.medical_conditions or [patient.condition],
            "medications": patient.medications or [],
            "allergies": patient.allergies or [],
            "dietary_restrictions": patient.dietary_restrictions or [],
            "registration_code": registration_code,
            "created_at": datetime.utcnow().isoformat()
        }
        
        await create_patient(patient_data)
        
        # Try to send registration code via SMS
        sms_result = send_registration_code(patient.phone, registration_code)
        
        if sms_result:
            return {
                "message": "Patient created and registration code sent via SMS",
                "registration_code": registration_code
            }
        else:
            return {
                "message": "Patient created successfully. Please note down the registration code as SMS could not be sent.",
                "registration_code": registration_code
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/patients")
async def get_patients(current_user: User = Depends(get_current_user)):
    # Check if user is admin using the token data
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        patients = await get_all_patients()
        return patients
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/login", response_model=Token)
async def admin_login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await get_user_by_email(form_data.username)
    if not user or not user.get("is_admin") or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"], "is_admin": True},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/admin/patient/{registration_code}")
async def get_patient_by_code(
    registration_code: str,
    current_user: User = Depends(get_current_user)
):
    # Check if user is admin
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        patient = await get_patient_by_registration_code(registration_code)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        return patient
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/patient-profile/{registration_code}")
async def get_patient_profile(
    registration_code: str,
    current_user: User = Depends(get_current_user)
):
    # Check if user is admin
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # First verify the patient exists
        patient = await get_patient_by_registration_code(registration_code)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Try to find if the patient has registered and has a profile
        # Look for user with registration code
        query = f"SELECT * FROM c WHERE c.type = 'user' AND c.registration_code = '{registration_code}'"
        users = list(user_container.query_items(query=query, enable_cross_partition_query=True))
        
        if not users:
            # Check if admin has created a profile
            profile_query = f"SELECT * FROM c WHERE c.type = 'user_profile' AND c.registration_code = '{registration_code}'"
            profiles = list(user_container.query_items(query=profile_query, enable_cross_partition_query=True))
            
            if not profiles:
                raise HTTPException(status_code=404, detail="Patient profile not found")
            
            return {"profile": profiles[0].get('profile', {})}
        
        user = users[0]
        
        # Get the user's profile
        profile_query = f"SELECT * FROM c WHERE c.type = 'user_profile' AND c.user_id = '{user['email']}'"
        profiles = list(user_container.query_items(query=profile_query, enable_cross_partition_query=True))
        
        if not profiles:
            raise HTTPException(status_code=404, detail="Patient profile not found")
        
        return {"profile": profiles[0].get('profile', {})}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching patient profile: {str(e)}")

@app.post("/admin/patient-profile/{registration_code}")
async def save_patient_profile(
    registration_code: str,
    request: dict,
    current_user: User = Depends(get_current_user)
):
    # Check if user is admin
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # First verify the patient exists
        patient = await get_patient_by_registration_code(registration_code)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        profile_data = request.get('profile', {})
        
        # Try to find if patient has registered
        query = f"SELECT * FROM c WHERE c.type = 'user' AND c.registration_code = '{registration_code}'"
        users = list(user_container.query_items(query=query, enable_cross_partition_query=True))
        
        if users:
            # Patient has registered - update their existing profile
            user = users[0]
            user_email = user['email']
        else:
            # Patient hasn't registered yet - create a placeholder profile linked to registration code
            user_email = f"pending_{registration_code}@placeholder.com"
        
        # Create or update profile record
        profile_record = {
            "id": f"profile_{user_email}",
            "type": "user_profile",
            "user_id": user_email,
            "registration_code": registration_code,
            "profile": profile_data,
            "created_by": "admin",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Save to database
        user_container.upsert_item(body=profile_record)
        
        return {
            "message": "Patient profile saved successfully",
            "status": "saved_by_admin",
            "patient_registered": bool(users)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving patient profile: {str(e)}")

@app.post("/admin/resend-code/{patient_id}")
async def resend_registration_code(
    patient_id: str,
    current_user: User = Depends(get_current_user)
):
    # Check if user is admin
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Get patient by ID
        patient = await get_patient_by_id(patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Send registration code via SMS
        registration_code = patient.get("registration_code")
        phone = patient.get("phone")
        
        if not registration_code or not phone:
            raise HTTPException(status_code=400, detail="Patient missing registration code or phone number")
        
        sms_result = send_registration_code(phone, registration_code)
        
        if sms_result:
            return {"message": "Registration code resent successfully via SMS"}
        else:
            return {"message": "Failed to send SMS. Please check the phone number."}
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resending registration code: {str(e)}")

def generate_meal_plan_prompt(user_profile: UserProfile) -> str:
    """Legacy function - now redirects to comprehensive profile handling"""
    # This function is deprecated - the main endpoint now uses comprehensive profiling
    return "This function has been replaced with comprehensive profile analysis"

def generate_recipe_prompt(meal_name: str, user_profile: UserProfile) -> str:
    """Legacy function - now redirects to comprehensive profile handling"""
    # This function is deprecated - the main endpoint now uses comprehensive profiling
    return "This function has been replaced with comprehensive profile analysis"

# ============================================================================
# COMPREHENSIVE AI HEALTH COACH SYSTEM
# ============================================================================

async def get_comprehensive_user_context(user_email: str):
    """
    Get complete user context including profile, consumption history, meal plans, and health conditions.
    This creates a unified view of the user for the AI health coach.
    """
    try:
        # Get user profile with all health conditions
        user_data = await get_user_by_email(user_email)
        user_profile = user_data.get("profile", {})
        
        # Get consumption history (last 30 days)
        consumption_history = await get_user_consumption_history(user_email, limit=100)
        
        # Get meal plan history
        meal_plans = await get_user_meal_plans(user_email)
        latest_meal_plan = meal_plans[0] if meal_plans else None
        
        # Extract health conditions and medications
        medical_conditions = user_profile.get("medicalConditions", []) or user_profile.get("medical_conditions", [])
        current_medications = user_profile.get("currentMedications", [])
        
        # Get dietary restrictions and preferences
        dietary_restrictions = user_profile.get("dietaryRestrictions", [])
        food_preferences = user_profile.get("foodPreferences", [])
        allergies = user_profile.get("allergies", [])
        strong_dislikes = user_profile.get("strongDislikes", [])
        
        # Get physical metrics
        age = user_profile.get("age")
        weight = user_profile.get("weight")
        height = user_profile.get("height")
        bmi = user_profile.get("bmi")
        
        # Get vital signs
        systolic_bp = user_profile.get("systolicBP") or user_profile.get("systolic_bp")
        diastolic_bp = user_profile.get("diastolicBP") or user_profile.get("diastolic_bp")
        
        # Get goals and targets
        calorie_target = user_profile.get("calorieTarget", "2000")
        primary_goals = user_profile.get("primaryGoals", [])
        wants_weight_loss = user_profile.get("wantsWeightLoss", False) or user_profile.get("weight_loss_goal", False)
        
        # Analyze recent consumption patterns
        recent_consumption = []
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        total_calories = 0
        condition_adherence = {"total_meals": 0, "condition_friendly": 0}
        favorite_foods = {}
        
        for entry in consumption_history:
            try:
                entry_date = datetime.fromisoformat(entry.get("timestamp", "").replace("Z", "+00:00"))
                if entry_date >= thirty_days_ago:
                    recent_consumption.append(entry)
                    
                    # Track nutrition
                    nutrition = entry.get("nutritional_info", {})
                    total_calories += nutrition.get("calories", 0)
                    
                    # Track food frequency
                    food_name = entry.get("food_name", "").lower()
                    favorite_foods[food_name] = favorite_foods.get(food_name, 0) + 1
                    
                    # Track condition-specific adherence
                    condition_adherence["total_meals"] += 1
                    medical_rating = entry.get("medical_rating", {})
                    
                    # Check suitability for user's specific conditions
                    is_suitable = True
                    for condition in medical_conditions:
                        condition_key = f"{condition.lower()}_suitability"
                        if condition_key in medical_rating:
                            suitability = medical_rating[condition_key].lower()
                            if suitability not in ["high", "good", "suitable"]:
                                is_suitable = False
                                break
                    
                    if is_suitable:
                        condition_adherence["condition_friendly"] += 1
                        
            except:
                continue
        
        # Calculate adherence rate
        adherence_rate = 0
        if condition_adherence["total_meals"] > 0:
            adherence_rate = (condition_adherence["condition_friendly"] / condition_adherence["total_meals"]) * 100
        
        # Get top favorite foods
        top_favorites = sorted(favorite_foods.items(), key=lambda x: x[1], reverse=True)[:10]
        favorite_foods_list = [food for food, count in top_favorites]
        
        # Calculate average daily calories
        avg_daily_calories = (total_calories / 30) if total_calories > 0 else 2000
        
        return {
            "user_profile": {
                "medical_conditions": medical_conditions,
                "current_medications": current_medications,
                "dietary_restrictions": dietary_restrictions,
                "food_preferences": food_preferences,
                "allergies": allergies,
                "strong_dislikes": strong_dislikes,
                "age": age,
                "weight": weight,
                "height": height,
                "bmi": bmi,
                "systolic_bp": systolic_bp,
                "diastolic_bp": diastolic_bp,
                "calorie_target": calorie_target,
                "primary_goals": primary_goals,
                "wants_weight_loss": wants_weight_loss
            },
            "consumption_analysis": {
                "total_recent_meals": len(recent_consumption),
                "avg_daily_calories": avg_daily_calories,
                "adherence_rate": adherence_rate,
                "favorite_foods": favorite_foods_list,
                "recent_consumption": recent_consumption[-10:]  # Last 10 meals for context
            },
            "meal_plan_context": {
                "has_active_plan": latest_meal_plan is not None,
                "latest_plan": latest_meal_plan,
                "total_plans_created": len(meal_plans)
            }
        }
        
    except Exception as e:
        print(f"Error getting comprehensive user context: {str(e)}")
        return None

async def get_ai_health_coach_response(user_context: dict, query_type: str, specific_data: dict = None):
    """
    Unified AI Health Coach that provides personalized responses for ALL health conditions.
    Supports: Diabetes, Hypertension, Heart Disease, Kidney Disease, PCOS, Thyroid, etc.
    
    Args:
        user_context: Complete user context from get_comprehensive_user_context()
        query_type: Type of query (meal_suggestion, food_analysis, adaptive_plan, general_coaching)
        specific_data: Any specific data for the query (e.g., food analysis results)
    """
    try:
        profile = user_context["user_profile"]
        consumption = user_context["consumption_analysis"]
        meal_plan = user_context["meal_plan_context"]
        
        # Build comprehensive health profile for AI
        health_conditions = profile["medical_conditions"]
        medications = profile["current_medications"]
        
        # Create comprehensive condition-specific coaching context
        condition_context = ""
        if health_conditions:
            condition_context = f"PATIENT'S HEALTH CONDITIONS: {', '.join(health_conditions)}\n"
            condition_context += f"CURRENT MEDICATIONS: {', '.join(medications) if medications else 'None listed'}\n"
            
            # Add condition-specific dietary guidelines
            condition_guidelines = []
            for condition in health_conditions:
                condition_lower = condition.lower()
                if "diabetes" in condition_lower:
                    condition_guidelines.append("- Diabetes: Low glycemic index foods, controlled carbohydrates, high fiber")
                elif "hypertension" in condition_lower or "blood pressure" in condition_lower:
                    condition_guidelines.append("- Hypertension: Low sodium (<2300mg/day), DASH diet, potassium-rich foods")
                elif "heart" in condition_lower or "cardiac" in condition_lower:
                    condition_guidelines.append("- Heart Disease: Low saturated fat, omega-3 fatty acids, whole grains")
                elif "kidney" in condition_lower or "renal" in condition_lower:
                    condition_guidelines.append("- Kidney Disease: Controlled protein, phosphorus, and potassium")
                elif "pcos" in condition_lower:
                    condition_guidelines.append("- PCOS: Low glycemic index, anti-inflammatory foods, balanced macros")
                elif "thyroid" in condition_lower:
                    condition_guidelines.append("- Thyroid: Iodine-rich foods, selenium, avoid goitrogens")
                elif "cholesterol" in condition_lower:
                    condition_guidelines.append("- High Cholesterol: Low saturated fat, high fiber, plant sterols")
                elif "obesity" in condition_lower or "weight" in condition_lower:
                    condition_guidelines.append("- Weight Management: Calorie control, portion sizes, nutrient density")
            
            if condition_guidelines:
                condition_context += f"CONDITION-SPECIFIC GUIDELINES:\n" + "\n".join(condition_guidelines) + "\n"
        
        # Build dietary context
        dietary_context = f"""DIETARY PROFILE:
- Restrictions: {', '.join(profile['dietary_restrictions']) if profile['dietary_restrictions'] else 'None'}
- Preferences: {', '.join(profile['food_preferences']) if profile['food_preferences'] else 'None'}
- Allergies: {', '.join(profile['allergies']) if profile['allergies'] else 'None'}
- Dislikes: {', '.join(profile['strong_dislikes']) if profile['strong_dislikes'] else 'None'}"""
        
        # Build health metrics context
        metrics_context = f"""HEALTH METRICS:
- Age: {profile['age'] or 'Not provided'}
- Weight: {profile['weight'] or 'Not provided'} lbs
- BMI: {profile['bmi'] or 'Not provided'}
- Blood Pressure: {profile['systolic_bp'] or 'N/A'}/{profile['diastolic_bp'] or 'N/A'} mmHg
- Calorie Target: {profile['calorie_target']}
- Goals: {', '.join(profile['primary_goals']) if profile['primary_goals'] else 'General health'}"""
        
        # Build consumption context
        consumption_context = f"""EATING PATTERNS (Last 30 days):
- Total meals logged: {consumption['total_recent_meals']}
- Average daily calories: {consumption['avg_daily_calories']:.0f}
- Health adherence rate: {consumption['adherence_rate']:.1f}%
- Favorite foods: {', '.join(consumption['favorite_foods'][:5]) if consumption['favorite_foods'] else 'None identified'}"""
        
        # Build meal plan context
        plan_context = f"""MEAL PLAN STATUS:
- Has active meal plan: {'Yes' if meal_plan['has_active_plan'] else 'No'}
- Total plans created: {meal_plan['total_plans_created']}"""
        
        # Create query-specific prompts
        if query_type == "food_analysis":
            food_data = specific_data or {}
            prompt = f"""You are a comprehensive health coach AI specializing in personalized nutrition for multiple health conditions.

{condition_context}
{dietary_context}
{metrics_context}
{consumption_context}
{plan_context}

CURRENT FOOD ANALYSIS:
Food: {food_data.get('food_name', 'Unknown')}
Calories: {food_data.get('nutritional_info', {}).get('calories', 'N/A')}
Carbs: {food_data.get('nutritional_info', {}).get('carbohydrates', 'N/A')}g
Protein: {food_data.get('nutritional_info', {}).get('protein', 'N/A')}g
Fat: {food_data.get('nutritional_info', {}).get('fat', 'N/A')}g

Provide personalized coaching that:
1. Evaluates this food choice for ALL the user's health conditions
2. Compares to their meal plan (if they have one)
3. Considers their eating patterns and adherence rate
4. Gives specific next meal suggestions based on remaining calories
5. Provides condition-specific guidance (not just diabetes)
6. Suggests meal plan adaptations if needed

Be encouraging, specific, and focus on their particular health conditions."""

        elif query_type == "meal_suggestion":
            remaining_calories = specific_data.get("remaining_calories", 500)
            meal_type = specific_data.get("meal_type", "lunch")
            
            prompt = f"""You are a comprehensive health coach AI providing meal suggestions for multiple health conditions.

{condition_context}
{dietary_context}
{metrics_context}
{consumption_context}
{plan_context}

CURRENT REQUEST:
- Meal type: {meal_type}
- Remaining calories: {remaining_calories}
- Time context: {specific_data.get('time_context', 'Current meal')}

Provide 3-5 specific meal suggestions that:
1. Fit within the calorie budget
2. Are appropriate for ALL their health conditions
3. Respect dietary restrictions and preferences
4. Consider their favorite foods when appropriate
5. Include specific portions and preparation methods
6. Explain why each suggestion is good for their conditions

Focus on their specific health conditions, not just general advice."""

        elif query_type == "adaptive_plan":
            prompt = f"""You are a comprehensive health coach AI creating adaptive meal plans for multiple health conditions.

{condition_context}
{dietary_context}
{metrics_context}
{consumption_context}
{plan_context}

Create a personalized 7-day meal plan that:
1. Addresses ALL the user's health conditions specifically
2. Incorporates their favorite foods when condition-appropriate
3. Respects all dietary restrictions and allergies
4. Targets their calorie and macro goals
5. Adapts based on their eating patterns and adherence rate
6. Provides condition-specific meal timing and combinations
7. Includes medication timing considerations if relevant

Provide a JSON response with the exact structure:
{{
    "plan_name": "Personalized Health Plan - {datetime.now().strftime('%Y-%m-%d')}",
    "duration_days": 7,
    "dailyCalories": {profile['calorie_target']},
    "health_focus": [list of their health conditions],
    "breakfast": ["Day 1: [specific meal]", ...],
    "lunch": ["Day 1: [specific meal]", ...],
    "dinner": ["Day 1: [specific meal]", ...],
    "snacks": ["Day 1: [specific snack]", ...],
    "adaptations": ["Condition-specific adaptations based on their profile"],
    "coaching_notes": "Personalized notes for their health conditions and patterns"
}}"""

        else:  # general_coaching
            prompt = f"""You are a comprehensive health coach AI providing general health coaching.

{condition_context}
{dietary_context}
{metrics_context}
{consumption_context}
{plan_context}

Provide personalized health coaching that addresses their specific conditions and current status."""

        # Get AI response
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {
                    "role": "system",
                    "content": "You are a comprehensive health coach AI that specializes in personalized nutrition and lifestyle guidance for multiple health conditions. You provide specific, actionable advice based on complete user profiles."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"Error getting AI health coach response: {str(e)}")
        return None

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    return {"message": "Welcome to Diabetes Diet Manager API"}

@app.post("/generate-meal-plan")
async def generate_meal_plan(
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        data = await request.json()
        user_profile = data.get("user_profile")
        previous_meal_plan = data.get("previous_meal_plan")
        days = data.get("days", 7)  # Default to 7 days if not provided

        if not user_profile:
            raise HTTPException(status_code=400, detail="User profile is required")
        
        # Validate days parameter
        if not isinstance(days, int) or days < 1 or days > 7:
            raise HTTPException(status_code=400, detail="Days must be an integer between 1 and 7")

        # Get the user's document
        user_doc = await get_user_by_email(current_user["email"])
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")

        # Update the user's profile with the calorie and macro goals
        if "profile" not in user_doc:
            user_doc["profile"] = {}
        
        # Update the profile with the goals from the meal plan
        user_doc["profile"]["calorieTarget"] = user_profile.get("calorieTarget", "2000")
        user_doc["profile"]["macroGoals"] = {
            "protein": user_profile.get("macroGoals", {}).get("protein", 100),
            "carbs": user_profile.get("macroGoals", {}).get("carbs", 250),
            "fat": user_profile.get("macroGoals", {}).get("fat", 66)
        }

        # Save the updated profile
        user_container.replace_item(item=user_doc["id"], body=user_doc)

        # Continue with meal plan generation...

        # Check required environment variables
        required_env_vars = [
            "AZURE_OPENAI_KEY",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_API_VERSION",
            "AZURE_OPENAI_DEPLOYMENT_NAME"
        ]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            raise HTTPException(
                status_code=500,
                detail=f"Missing required environment variables: {', '.join(missing_vars)}"
            )

        print('user_profile received:', user_profile)
        print("/generate-meal-plan endpoint called")
        print(f"Current user: {current_user}")
        print(f"User profile received: {user_profile}")
        print("Model:", os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"))
        print("Endpoint:", os.getenv("AZURE_OPENAI_ENDPOINT"))
        print("API Version:", os.getenv("AZURE_OPENAI_API_VERSION"))

        # If previous_meal_plan is provided, use it for 70/30 overlap
        def get_overlap_meals(prev_meals, new_meals):
            import re
            if not prev_meals or not isinstance(prev_meals, list):
                return new_meals
            overlap_count = int(0.7 * len(new_meals))
            new_count = len(new_meals) - overlap_count
            prev_sample = random.sample(prev_meals, min(overlap_count, len(prev_meals)))
            # Remove any duplicates from new_meals
            remaining_new = [m for m in new_meals if m not in prev_sample]

            # Helper: extract keywords from meal name
            def extract_keywords(meal):
                return set(re.findall(r"\\w+", meal.lower()))

            prev_keywords = set()
            for meal in prev_sample:
                prev_keywords.update(extract_keywords(meal))

            # Find new meals that share a keyword with any previous meal
            related_new = []
            unrelated_new = []
            for meal in remaining_new:
                if extract_keywords(meal) & prev_keywords:
                    related_new.append(meal)
                else:
                    unrelated_new.append(meal)

            # Prefer related new meals for the 30% new
            new_sample = []
            if len(related_new) >= new_count:
                new_sample = random.sample(related_new, new_count)
            else:
                new_sample = related_new + random.sample(unrelated_new, min(new_count - len(related_new), len(unrelated_new)))

            return prev_sample + new_sample

        # Define a robust JSON structure based on selected days
        example_meals = {
            "breakfast": ["Oatmeal with berries", "Whole grain toast with eggs", "Greek yogurt with granola", "Scrambled eggs with spinach", "Smoothie bowl", "Avocado toast", "Pancakes with fruit"],
            "lunch": ["Grilled chicken salad", "Quinoa bowl", "Turkey sandwich", "Vegetable soup", "Pasta salad", "Chicken wrap", "Buddha bowl"],
            "dinner": ["Baked salmon with vegetables", "Grilled chicken with rice", "Beef stir-fry", "Vegetable curry", "Baked cod with quinoa", "Turkey meatballs", "Roasted vegetables with protein"],
            "snacks": ["Apple with almonds", "Greek yogurt", "Carrot sticks with hummus", "Mixed nuts", "Cheese and crackers", "Berries with cottage cheese", "Protein smoothie"]
        }
        
        # Create exactly the right number of meals for each type based on days
        json_structure_meals = {}
        for meal_type, examples in example_meals.items():
            # Take exactly 'days' number of meals, cycling through examples if needed
            selected_meals = []
            for i in range(days):
                selected_meals.append(examples[i % len(examples)])
            json_structure_meals[meal_type] = selected_meals
        
        json_structure = f"""
{{
    "breakfast": {json.dumps(json_structure_meals["breakfast"])},
    "lunch": {json.dumps(json_structure_meals["lunch"])},
    "dinner": {json.dumps(json_structure_meals["dinner"])},
    "snacks": {json.dumps(json_structure_meals["snacks"])},
    "dailyCalories": 2000,
    "macronutrients": {{
        "protein": 100,
        "carbs": 250,
        "fats": 70
    }}
}}"""

        # Helper function to get profile value with fallbacks
        def get_profile_value(profile, new_key, old_key=None, default='Not provided'):
            value = profile.get(new_key)
            if not value and old_key:
                value = profile.get(old_key)
            if isinstance(value, list) and value:
                return ', '.join(value)
            elif isinstance(value, list):
                return default
            return value or default

        # Create comprehensive profile summary
        profile_summary = f"""
PATIENT DEMOGRAPHICS:
Name: {get_profile_value(user_profile, 'name')}
Age: {get_profile_value(user_profile, 'age')}
Gender: {get_profile_value(user_profile, 'gender')}
Ethnicity: {get_profile_value(user_profile, 'ethnicity', default='Not specified')}

VITAL SIGNS & MEASUREMENTS:
Height: {get_profile_value(user_profile, 'height')} cm
Weight: {get_profile_value(user_profile, 'weight')} kg
BMI: {get_profile_value(user_profile, 'bmi', default='Not calculated')}
Waist Circumference: {get_profile_value(user_profile, 'waistCircumference', 'waist_circumference')} cm
Blood Pressure: {get_profile_value(user_profile, 'systolicBP', 'systolic_bp')}/{get_profile_value(user_profile, 'diastolicBP', 'diastolic_bp')} mmHg
Heart Rate: {get_profile_value(user_profile, 'heartRate', 'heart_rate')} bpm

MEDICAL CONDITIONS:
Medical Conditions: {get_profile_value(user_profile, 'medicalConditions', 'medical_conditions', 'None specified')}
Current Medications: {get_profile_value(user_profile, 'currentMedications', default='None specified')}

LAB VALUES (if available):
{json.dumps(user_profile.get('labValues', {}), indent=2) if user_profile.get('labValues') else 'Not provided'}

DIETARY INFORMATION:
**PREFERRED CUISINE TYPE: {get_profile_value(user_profile, 'dietType', 'diet_type', 'Not specified')}** ⭐ MUST FOLLOW THIS CUISINE STYLE ⭐
Dietary Features: {get_profile_value(user_profile, 'dietaryFeatures', 'diet_features', 'None specified')}
Dietary Restrictions: {get_profile_value(user_profile, 'dietaryRestrictions', default='None specified')}
Food Preferences: {get_profile_value(user_profile, 'foodPreferences', default='None specified')}
Food Allergies: {get_profile_value(user_profile, 'allergies', default='None specified')}
Strong Dislikes: {get_profile_value(user_profile, 'strongDislikes', default='None specified')}

PHYSICAL ACTIVITY:
Work Activity Level: {get_profile_value(user_profile, 'workActivityLevel', default='Not specified')}
Exercise Frequency: {get_profile_value(user_profile, 'exerciseFrequency', default='Not specified')}
Exercise Types: {get_profile_value(user_profile, 'exerciseTypes', default='Not specified')}
Mobility Issues: {'Yes' if user_profile.get('mobilityIssues') else 'No'}

LIFESTYLE & PREFERENCES:
Meal Prep Capability: {get_profile_value(user_profile, 'mealPrepCapability', default='Not specified')}
Available Appliances: {get_profile_value(user_profile, 'availableAppliances', default='Standard kitchen')}
Eating Schedule: {get_profile_value(user_profile, 'eatingSchedule', default='Standard 3 meals')}

GOALS & TARGET:
Primary Health Goals: {get_profile_value(user_profile, 'primaryGoals', default='General wellness')}
Readiness to Change: {get_profile_value(user_profile, 'readinessToChange', default='Not specified')}
Weight Loss Goal: {'Yes' if user_profile.get('wantsWeightLoss') or user_profile.get('weight_loss_goal') else 'No'}
Calorie Target: {get_profile_value(user_profile, 'calorieTarget', 'calories_target', '2000')} kcal/day
        """

        # Format the prompt with proper error handling for optional fields
        if previous_meal_plan:
            # Add previous meal plan to the prompt and instruct the model for 70/30 overlap
            prev_meal_plan_str = json.dumps({k: previous_meal_plan.get(k, []) for k in ['breakfast', 'lunch', 'dinner', 'snacks']}, indent=2)
            prompt = f"""Create a comprehensive, medically-appropriate meal plan based on this detailed patient profile:

{profile_summary}

Here is the previous week's meal plan (for each meal type, 7 days):
{prev_meal_plan_str}

CRITICAL INSTRUCTIONS:
1. MEDICAL SAFETY: Carefully consider all medical conditions, medications, and lab values. Ensure meals are appropriate for diabetes management and any other health conditions.
2. DIETARY COMPLIANCE: Strictly follow dietary restrictions, allergies, and food preferences.
3. DIET TYPE ADHERENCE: **CRITICALLY IMPORTANT** - Follow the specified Diet Type exactly:
   - If "Western" or "European": MUST include traditional European/Western dishes such as:
     * BREAKFAST: Scrambled eggs with toast, pancakes, French toast, English breakfast, cereal with milk, bagels with cream cheese
     * LUNCH: Sandwiches (turkey, ham, BLT), burgers, pizza slices, pasta salads, chicken Caesar salad, club sandwiches  
     * DINNER: Spaghetti with meatballs, grilled chicken with mashed potatoes, beef steak with vegetables, baked fish with rice, pizza, lasagna, roast beef
     * SNACKS: Cheese and crackers, nuts, yogurt, fruit, granola bars
   - If "Mediterranean": Focus on Mediterranean cuisine with olive oil, fish, vegetables, legumes, etc.
   - If "South Asian": Include curries, rice dishes, lentils, chapati, etc.
   - If "East Asian": Include stir-fries, rice, noodles, steamed dishes, etc.
   - If "Caribbean": Include rice and beans, plantains, jerk seasonings, etc.
   - DO NOT substitute with health food alternatives unless specifically requested - give authentic traditional dishes
4. CULTURAL CONSIDERATIONS: Incorporate ethnicity and cultural food preferences where specified.
5. ACTIVITY ALIGNMENT: Consider physical activity level for calorie and macronutrient targets.
6. MEAL CONTINUITY: For each meal type (breakfast, lunch, dinner, snacks), reuse about 70% of meals from the previous plan and create 30% new similar meals.
7. APPLIANCE CONSTRAINTS: Only suggest meals that can be prepared with available appliances.

Return a JSON object with exactly this structure:
{json_structure}

REQUIREMENTS:
- Each meal array must have exactly {days} items (one for each day of the {days}-day meal plan)
- breakfast array: exactly {days} different breakfast meals
- lunch array: exactly {days} different lunch meals  
- dinner array: exactly {days} different dinner meals
- snacks array: exactly {days} different snack options
- Consider medical conditions for ingredient selection
- Match calorie target and dietary features
- Keep meal names concise but descriptive (e.g., "Grilled Chicken Salad", not "Day 1 Lunch")
- Ensure all values are numbers, not strings
- No explanations or markdown, just the JSON object"""
        else:
            prompt = f"""Create a comprehensive, medically-appropriate meal plan based on this detailed patient profile:

{profile_summary}

CRITICAL INSTRUCTIONS:
1. MEDICAL SAFETY: Carefully consider all medical conditions, medications, and lab values. Ensure meals are appropriate for diabetes management and any other health conditions.
2. DIETARY COMPLIANCE: Strictly follow dietary restrictions, allergies, and food preferences.
3. DIET TYPE ADHERENCE: **CRITICALLY IMPORTANT** - Follow the specified Diet Type exactly:
   - If "Western" or "European": MUST include traditional European/Western dishes such as:
     * BREAKFAST: Scrambled eggs with toast, pancakes, French toast, English breakfast, cereal with milk, bagels with cream cheese
     * LUNCH: Sandwiches (turkey, ham, BLT), burgers, pizza slices, pasta salads, chicken Caesar salad, club sandwiches  
     * DINNER: Spaghetti with meatballs, grilled chicken with mashed potatoes, beef steak with vegetables, baked fish with rice, pizza, lasagna, roast beef
     * SNACKS: Cheese and crackers, nuts, yogurt, fruit, granola bars
   - If "Mediterranean": Focus on Mediterranean cuisine with olive oil, fish, vegetables, legumes, etc.
   - If "South Asian": Include curries, rice dishes, lentils, chapati, etc.
   - If "East Asian": Include stir-fries, rice, noodles, steamed dishes, etc.
   - If "Caribbean": Include rice and beans, plantains, jerk seasonings, etc.
   - DO NOT substitute with health food alternatives unless specifically requested - give authentic traditional dishes
4. CULTURAL CONSIDERATIONS: Incorporate ethnicity and cultural food preferences where specified.
5. ACTIVITY ALIGNMENT: Consider physical activity level for calorie and macronutrient targets.
6. APPLIANCE CONSTRAINTS: Only suggest meals that can be prepared with available appliances.
7. PERSONALIZATION: Use lifestyle preferences and eating schedule to optimize meal timing and preparation.

Return a JSON object with exactly this structure:
{json_structure}

REQUIREMENTS:
- Each meal array must have exactly {days} items (one for each day of the {days}-day meal plan)
- breakfast array: exactly {days} different breakfast meals
- lunch array: exactly {days} different lunch meals  
- dinner array: exactly {days} different dinner meals
- snacks array: exactly {days} different snack options
- Consider medical conditions for ingredient selection
- Match calorie target and dietary features
- Keep meal names concise but descriptive (e.g., "Grilled Chicken Salad", not "Day 1 Lunch")
- Ensure all values are numbers, not strings
- No explanations or markdown, just the JSON object"""

        print("Prompt for OpenAI:")
        print(prompt)

        try:
            response = client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                messages=[
                    {
                        "role": "system",
                        "content": "You are a meal planning assistant specializing in culturally authentic cuisine. When a user specifies 'Western' or 'European' diet type, you MUST provide traditional Western/European dishes like pizza (regular crust), pasta (wheat-based), sandwiches, burgers, steaks, etc. AVOID health substitutions like gluten-free, quinoa, cauliflower crust, zucchini noodles unless specifically requested. Include 5 healthy traditional meals and 2 indulgent traditional meals per week for balance. Always respond with valid JSON matching the exact structure requested. No explanations or markdown."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            print("OpenAI response received")
            
            if not response.choices or not response.choices[0].message:
                raise HTTPException(
                    status_code=500,
                    detail="No response received from OpenAI"
                )

            raw_content = response.choices[0].message.content.strip()
            print("Raw OpenAI response:")
            print(raw_content)

            try:
                meal_plan = json.loads(raw_content)
                print("Meal plan parsed successfully:")
                print(json.dumps(meal_plan, indent=2))
                
                # Validate meal plan structure
                required_keys = ['breakfast', 'lunch', 'dinner', 'snacks', 'dailyCalories', 'macronutrients']
                missing_keys = [key for key in required_keys if key not in meal_plan]
                if missing_keys:
                    print(f"Missing required keys in meal plan: {missing_keys}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Invalid meal plan format. Missing keys: {', '.join(missing_keys)}"
                    )

                # Ensure arrays have the correct number of items based on selected days
                for meal_type in ['breakfast', 'lunch', 'dinner', 'snacks']:
                    if not isinstance(meal_plan[meal_type], list):
                        meal_plan[meal_type] = ["Not specified"] * days
                    while len(meal_plan[meal_type]) < days:
                        meal_plan[meal_type].append("Not specified")
                    meal_plan[meal_type] = meal_plan[meal_type][:days]  # Trim if too long

                # Ensure macronutrients are numbers
                macro_keys = ['protein', 'carbs', 'fats']
                for key in macro_keys:
                    if not isinstance(meal_plan['macronutrients'].get(key), (int, float)):
                        meal_plan['macronutrients'][key] = 0

                if not isinstance(meal_plan.get('dailyCalories'), (int, float)):
                    meal_plan['dailyCalories'] = 2000

                # If previous_meal_plan is provided, use it for 70/30 overlap
                if previous_meal_plan:
                    for meal_type in ['breakfast', 'lunch', 'dinner', 'snacks']:
                        prev_meals = previous_meal_plan.get(meal_type, [])
                        new_meals = meal_plan.get(meal_type, [])
                        if isinstance(prev_meals, list) and isinstance(new_meals, list) and len(new_meals) == days:
                            meal_plan[meal_type] = get_overlap_meals(prev_meals, new_meals)

                # Explicitly convert the returned meal_plan to a plain dictionary
                try:
                    # import json # Removed local import
                    plain_meal_plan = json.loads(json.dumps(meal_plan))
                    print("[/generate-meal-plan] Converted returned meal_plan to plain dict")
                    return plain_meal_plan
                except Exception as e:
                    print(f"[/generate-meal-plan] Failed to convert returned meal_plan to plain dict: {e}")
                    # Return the original meal_plan if conversion fails, error might occur again
                    return meal_plan

            except json.JSONDecodeError as e:
                print("Failed to parse OpenAI response as JSON:")
                print(f"Error message: {str(e)}")
                print(f"Error location: line {e.lineno}, column {e.colno}")
                print(f"Error context: {e.doc[max(0, e.pos-50):e.pos+50]}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to parse meal plan response: {str(e)}"
                )

        except Exception as openai_error:
            print("OpenAI API error:", str(openai_error))
            print("Full error details:", openai_error.__dict__)
            raise HTTPException(
                status_code=500,
                detail=f"OpenAI API error: {str(openai_error)}"
            )

    except HTTPException as he:
        print(f"HTTP Exception in /generate-meal-plan: {str(he.detail)}")
        raise he
    except Exception as e:
        print(f"Unexpected error in /generate-meal-plan: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@app.post("/generate-recipes")
async def generate_recipes(
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        data = await request.json()
        meal_plan = data.get('meal_plan', {})
        print("/generate-recipes endpoint called")
        print("Received meal_plan:", meal_plan)
        # Format the prompt for recipe generation
        prompt = f"""Generate detailed recipes for the following meal plan:\n{json.dumps(meal_plan, indent=2)}\n\nFor each meal, provide:\n1. A list of ingredients with quantities\n2. Step-by-step preparation instructions\n3. Nutritional information (calories, protein, carbs, fat)\n\nFormat the response as a JSON array of recipe objects with the following structure:\n[\n    {{\n        \"name\": \"Recipe Name\",\n        \"ingredients\": [\"ingredient1\", \"ingredient2\", ...],\n        \"instructions\": [\"step1\", \"step2\", ...],\n        \"nutritional_info\": {{\n            \"calories\": number,\n            \"protein\": number,\n            \"carbs\": number,\n            \"fat\": number\n        }}\n    }},\n    ...\n]"""
        print("Prompt for OpenAI:")
        print(prompt)
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {"role": "system", "content": "You are a diabetes diet planning assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000,
        )
        print("OpenAI response received")
        recipes = json.loads(response.choices[0].message.content)
        print("Recipes parsed:")
        print(recipes)
        await save_recipes(current_user["email"], recipes)
        return recipes
    except Exception as e:
        print(f"Error in /generate-recipes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-shopping-list")
async def generate_shopping_list(
    request: FastAPIRequest,
    recipes: List[dict],
    current_user: User = Depends(get_current_user)
):
    try:
        print("/generate-shopping-list endpoint called")
        print("Received recipes:")
        print(recipes)
        prompt = f"""Generate a shopping list based on the following recipes:
                    {json.dumps(recipes, indent=2)}

                    Group items by category (e.g., Produce, Dairy, Meat, etc.) and combine quantities for the same items.

                    ––––– UNIT RULES –––––
                    • Express quantities in units a Canadian grocery shopper can actually buy ("purchasable quantity").
                    – **Fresh herbs** (cilantro/coriander, parsley, mint, dill, etc.): use whole bunches.  
                        *Assume 1 bunch ≈ 30 g; round ⭡ to the nearest whole bunch.*
                    – **Loose fruit & veg** commonly weighed at checkout (apples, oranges, onions, potatoes, carrots, etc.): use pounds (lb).  
                        *Round ⭡ to the nearest 1 lb, minimum 1 lb.*
                    – **Packaged produce** (bags of spinach, baby carrots, etc.): round ⭡ to the nearest 250 g (≈ ½ lb) or to the nearest package size you specify in the item name (e.g., "1 × 250 g bag baby spinach").
                    – **Liquids**: keep ml/l, but round ⭡ to the nearest 100 ml (or common bottle size) if <1 l; use whole litres if ≥1 l.
                    – **Dry pantry staples** (rice, flour, sugar, pasta, beans, nuts, etc.): use grams/kilograms, rounded ⭡ to the nearest 100 g for ≤1 kg or to the nearest 0.5 kg for >1 kg.
                    – If an item is only sold by count (e.g., eggs, garlic bulbs, lemons), use "pieces".
                    – Avoid descriptors like "large" or "medium"; only use count-based units when weight/volume makes no sense.

                    ––––– SANITY CHECK –––––
                    After calculating totals, scan the list for obviously implausible amounts (e.g., >2 bunches of coriander for ≤8 servings, >5 lb of garlic, etc.).  
                    If an amount seems unrealistic, recompute or cap it to a reasonable upper bound and add a "note" field explaining the adjustment.

                    ––––– ROUNDING GRID (CANADIAN GROCERY) –––––
                    When you finish aggregating all recipes, convert each total to the **next-larger** purchasable size:

                    • Loose produce sold by weight (onions, apples, tomatoes, carrots, potatoes, peppers, etc.):
                    – Express in **pounds (lb)** and round **up** to the nearest 1 lb.
                        *Example 1 → 2.82 lb ⇒ 3 lb  (≈ 1.36 kg)*

                    • Mid-volume produce often pre-bagged (spinach, baby carrots, kale, salad mix, frozen peas, frozen beans):
                    – Use the next-larger multiple of **454 g = 1 lb** (or mention the closest bag size if that's clearer).
                        *Example 510 g ⇒ 908 g (2 × 454 g bags).*

                    • Bulky vegetables normally sold by unit (cauliflower, cabbage, squash, bottle gourd, cucumber, eggplant):
                    – Convert to **whole pieces/heads** and give an *≈ weight* in parentheses if helpful.
                        *Example 1.43 lb cauliflower ⇒ "1 head (≈1.5 lb)".*

                    • Herbs with stems (cilantro/coriander, parsley, dill, mint, etc.):
                    – Use **bunches**. 1 bunch ≈ 30 g.  
                        Round up to the nearest whole bunch **but also sanity-cap at 3 bunches unless recipe count clearly justifies more**.

                    • Ginger, garlic bulbs, green chilli, curry leaves:
                    – Sell by weight or count in small amounts.  
                        ➜ Round ginger/garlic/chilli up to **0.25 lb** increments.  
                        ➜ For garlic bulbs or curry leaves sold by unit, keep **pieces** but sanity-cap at 1 bulb per 2 cloves required (e.g., 38 cloves ⇒ 19 bulbs max, but prefer 4 bulbs and note the assumption).

                    • Liquids (milk, oil, stock, etc.):
                    – Round up to the next **100 ml** below 1 l or whole **lite**rs if ≥ 1 l.

                    • Dry pantry staples (flour, rice, sugar, lentils, pasta, etc.):
                    – Round up to the next **100 g** below 1 kg, else the next **0.5 kg**.

                    After rounding, perform a **sanity sweep**.  
                    Flag anything that still looks extreme (e.g., >3 lb chilli, >3 bunches cilantro for ≤8 servings) and reduce to a realistic maximum, adding `"note"` to explain.

                    ––––– OUTPUT FORMAT –––––
                    Return **only** a JSON array with each element:
                    {{
                    "name": "Item Name",
                    "amount": "Quantity with Purchasable Unit",
                    "category": "Category Name",
                    "note": "Optional brief note about rounding or sanity adjustment"
                    }}
                    Omit the "note" key if no comment is needed.
                    """
        print("Prompt for OpenAI:")
        print(prompt)
        # Call Azure OpenAI (synchronous call)
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {"role": "system", "content": "You are a diabetes diet planning assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=20000
        )
        print("OpenAI response received")
        raw_content = response.choices[0].message.content
        print("Raw OpenAI response:")
        print(raw_content)
        # Remove Markdown code block if present
        if raw_content.strip().startswith('```'):
            raw_content = re.sub(r'^```[a-zA-Z]*\s*|```$', '', raw_content.strip(), flags=re.MULTILINE).strip()
        # Extract the first JSON array from the response
        match = re.search(r'\[.*?\]', raw_content, re.DOTALL)
        if match:
            json_str = match.group(0)
        else:
            json_str = raw_content  # fallback, may still error
        try:
            shopping_list = json.loads(json_str)
            print("Parsed shopping list:")
            print(shopping_list)
        except Exception as parse_err:
            print("Error parsing OpenAI response as JSON:")
            print(parse_err)
            raise HTTPException(status_code=500, detail=f"OpenAI response not valid JSON: {parse_err}\nRaw response: {raw_content}")
        await save_shopping_list(
            user_id=current_user["email"],
            shopping_list={"items": shopping_list}
        )
        return shopping_list
    except Exception as e:
        print(f"Error in /generate-shopping-list: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/export/consolidated-meal-plan")
async def export_consolidated_meal_plan(current_user: User = Depends(get_current_user)):
    try:
        print(">>>> Entered /export/consolidated-meal-plan endpoint")
        # Fetch meal plans
        meal_plans = await get_user_meal_plans(current_user["email"])
        if not meal_plans:
            print("No meal plan found")
            raise HTTPException(status_code=404, detail="No meal plan found")
        latest_meal_plan = meal_plans[-1]
        print("meal_plan:", latest_meal_plan)
        # Fetch latest recipes and shopping list for the user
        all_recipes = await get_user_recipes(current_user["email"])
        recipes = all_recipes[-1]["recipes"] if all_recipes else []
        all_shopping_lists = await get_user_shopping_lists(current_user["email"])
        shopping_list = all_shopping_lists[-1]["items"] if all_shopping_lists else []
        print("recipes:", recipes)
        print("shopping_list:", shopping_list)
        # Generate PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
        elements = []
        styles = getSampleStyleSheet()
        # Add cover page
        try:
            cover_path = os.path.join("assets", "coverpage.png")
            elements.append(RLImage(cover_path, width=10*inch, height=6*inch))
            elements.append(Spacer(1, 48))
        except Exception as cover_err:
            print(f"Could not add cover page: {cover_err}")
        # Title
        elements.append(Paragraph("Consolidated Meal Plan", styles['Title']))
        elements.append(Spacer(1, 12))
        # Meal Plan Section
        elements.append(Paragraph("Meal Plan", styles['Heading1']))
        elements.append(Spacer(1, 12))
        data = [["Day", "Breakfast", "Lunch", "Dinner", "Snacks"]]
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for i, day in enumerate(days):
            data.append([
                day,
                latest_meal_plan["breakfast"][i] if i < len(latest_meal_plan["breakfast"]) else "",
                latest_meal_plan["lunch"][i] if i < len(latest_meal_plan["lunch"]) else "",
                latest_meal_plan["dinner"][i] if i < len(latest_meal_plan["dinner"]) else "",
                latest_meal_plan["snacks"][i] if i < len(latest_meal_plan["snacks"]) else "",
            ])
        col_widths = [0.8*inch, 2.5*inch, 2.5*inch, 2.5*inch, 2.5*inch]
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        for row in range(1, len(data)):
            for col in range(1, 5):
                table._cellvalues[row][col] = Paragraph(str(table._cellvalues[row][col]), styles['BodyText'])
        elements.append(table)
        elements.append(Spacer(1, 24))
        # Recipes Section (new page)
        elements.append(PageBreak())
        elements.append(Paragraph("Recipes", styles['Heading1']))
        elements.append(Spacer(1, 12))
        for recipe in recipes:
            elements.append(Paragraph(recipe["name"], styles['Heading2']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("Nutritional Information", styles['Heading3']))
            elements.append(Paragraph(f"Calories: {recipe['nutritional_info']['calories']}", styles['Normal']))
            elements.append(Paragraph(f"Protein: {recipe['nutritional_info']['protein']}", styles['Normal']))
            elements.append(Paragraph(f"Carbs: {recipe['nutritional_info']['carbs']}", styles['Normal']))
            elements.append(Paragraph(f"Fat: {recipe['nutritional_info']['fat']}", styles['Normal']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("Ingredients", styles['Heading3']))
            for ingredient in recipe["ingredients"]:
                elements.append(Paragraph(f"• {ingredient}", styles['Normal']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("Instructions", styles['Heading3']))
            for i, instruction in enumerate(recipe["instructions"], 1):
                elements.append(Paragraph(f"{i}. {instruction}", styles['Normal']))
            elements.append(Spacer(1, 24))
        # Shopping List Section (new page)
        elements.append(PageBreak())
        elements.append(Paragraph("Shopping List", styles['Heading1']))
        elements.append(Spacer(1, 12))
        categories = {}
        for item in shopping_list:
            if item["category"] not in categories:
                categories[item["category"]] = []
            categories[item["category"]].append(item)
        for category, items in categories.items():
            elements.append(Paragraph(category, styles['Heading2']))
            elements.append(Spacer(1, 12))
            for item in items:
                elements.append(Paragraph(f"• {item['name']} - {item['amount']}", styles['Normal']))
            elements.append(Spacer(1, 24))
        doc.build(elements)
        buffer.seek(0)
        username = current_user["email"].split("@")[0]
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"{username}_{date_str}_consolidated_meal_plan.pdf"
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        print("Error in /export/consolidated-meal-plan:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/export/{type}")
async def export_document(
    type: str,
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        data = await request.json()
        
        if type == "meal-plan":
            content = data["meal_plan"]
            title = "Meal Plan"
        elif type == "recipes":
            content = data["recipes"]
            title = "Recipe Collection"
        elif type == "shopping-list":
            content = data["shopping_list"]
            title = "Shopping List"
        else:
            raise HTTPException(status_code=400, detail="Invalid export type")

        # Generate PDF using reportlab
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
        elements = []

        # Add title
        styles = getSampleStyleSheet()
        elements.append(Paragraph(title, styles['Title']))
        elements.append(Spacer(1, 12))

        # Add content based on type
        if type == "meal-plan":
            # Create table for meal plan
            data = [["Day", "Breakfast", "Lunch", "Dinner", "Snacks"]]
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            for i, day in enumerate(days):
                data.append([
                    day,
                    content["breakfast"][i] if i < len(content["breakfast"]) else "",
                    content["lunch"][i] if i < len(content["lunch"]) else "",
                    content["dinner"][i] if i < len(content["dinner"]) else "",
                    content["snacks"][i] if i < len(content["snacks"]) else "",
                ])
            # Set column widths
            col_widths = [0.8*inch, 2.5*inch, 2.5*inch, 2.5*inch, 2.5*inch]
            table = Table(data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            # Enable word wrap for all cells except header
            for row in range(1, len(data)):
                for col in range(1, 5):
                    table._cellvalues[row][col] = Paragraph(str(table._cellvalues[row][col]), styles['BodyText'])
            elements.append(table)

        elif type == "recipes":
            # Add each recipe
            for recipe in content:
                elements.append(Paragraph(recipe["name"], styles['Heading1']))
                elements.append(Spacer(1, 12))

                # Nutritional info
                elements.append(Paragraph("Nutritional Information", styles['Heading2']))
                elements.append(Paragraph(f"Calories: {recipe['nutritional_info']['calories']}", styles['Normal']))
                elements.append(Paragraph(f"Protein: {recipe['nutritional_info']['protein']}", styles['Normal']))
                elements.append(Paragraph(f"Carbs: {recipe['nutritional_info']['carbs']}", styles['Normal']))
                elements.append(Paragraph(f"Fat: {recipe['nutritional_info']['fat']}", styles['Normal']))
                elements.append(Spacer(1, 12))

                # Ingredients
                elements.append(Paragraph("Ingredients", styles['Heading2']))
                for ingredient in recipe["ingredients"]:
                    elements.append(Paragraph(f"• {ingredient}", styles['Normal']))
                elements.append(Spacer(1, 12))

                # Instructions
                elements.append(Paragraph("Instructions", styles['Heading2']))
                for i, instruction in enumerate(recipe["instructions"], 1):
                    elements.append(Paragraph(f"{i}. {instruction}", styles['Normal']))
                elements.append(Spacer(1, 24))

        elif type == "shopping-list":
            # Group items by category
            categories = {}
            for item in content:
                if item["category"] not in categories:
                    categories[item["category"]] = []
                categories[item["category"]].append(item)

            # Add each category
            for category, items in categories.items():
                elements.append(Paragraph(category, styles['Heading1']))
                elements.append(Spacer(1, 12))
                for item in items:
                    elements.append(Paragraph(f"• {item['name']} - {item['amount']}", styles['Normal']))
                elements.append(Spacer(1, 24))

        # Build PDF
        doc.build(elements)
        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={type}-{datetime.now().strftime('%Y%m%d')}.pdf"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/message")
async def send_chat_message(
    message: ChatMessage,
    current_user: User = Depends(get_current_user)
):
    # Save user message
    user_message = await save_chat_message(
        current_user["id"],
        message.message,
        is_user=True,
        session_id=message.session_id
    )
    
    # Get chat history for context
    chat_history = await format_chat_history_for_prompt(
        current_user["id"],
        message.session_id or user_message["session_id"]
    )
    
    # 🧠 ENHANCED AI COACH CONTEXT - Get comprehensive user data
    profile = current_user.get("profile", {})
    
    # Get recent meal plans (last 3 for context)
    try:
        recent_meal_plans = await get_user_meal_plans(current_user["id"])
        recent_meal_plans = recent_meal_plans[:3]  # Last 3 meal plans
    except Exception as e:
        print(f"Error fetching meal plans for chat context: {e}")
        recent_meal_plans = []
    
    # Get recent consumption history (last 7 days)
    try:
        recent_consumption = await get_user_consumption_history(current_user["id"], limit=20)
        # Filter to last 7 days
        from datetime import datetime, timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_consumption = [
            record for record in recent_consumption 
            if datetime.fromisoformat(record.get("timestamp", "").replace("Z", "+00:00")) > seven_days_ago
        ]
    except Exception as e:
        print(f"Error fetching consumption history for chat context: {e}")
        recent_consumption = []
    
    # Get today's consumption for daily tracking
    try:
        today = datetime.utcnow().date()
        tomorrow = today + timedelta(days=1)
        today_consumption = [
            record for record in recent_consumption
            if today <= datetime.fromisoformat(record.get("timestamp", "").replace("Z", "+00:00")).date() < tomorrow
        ]
    except Exception as e:
        print(f"Error filtering today's consumption: {e}")
        today_consumption = []
    
    # Calculate today's nutritional totals
    today_totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
    for record in today_consumption:
        nutritional_info = record.get("nutritional_info", {})
        today_totals["calories"] += nutritional_info.get("calories", 0)
        today_totals["protein"] += nutritional_info.get("protein", 0)
        today_totals["carbs"] += nutritional_info.get("carbohydrates", 0)
        today_totals["fat"] += nutritional_info.get("fat", 0)
    
    # Get user's goals from profile or latest meal plan
    calorie_goal = 2000  # Default
    macro_goals = {"protein": 100, "carbs": 250, "fat": 70}  # Defaults
    
    if profile.get("calorieTarget"):
        try:
            calorie_goal = int(profile["calorieTarget"])
        except:
            pass
    elif recent_meal_plans and recent_meal_plans[0].get("dailyCalories"):
        calorie_goal = recent_meal_plans[0]["dailyCalories"]
    
    if profile.get("macroGoals"):
        macro_goals.update(profile["macroGoals"])
    elif recent_meal_plans and recent_meal_plans[0].get("macronutrients"):
        macros = recent_meal_plans[0]["macronutrients"]
        macro_goals = {
            "protein": macros.get("protein", 100),
            "carbs": macros.get("carbs", 250),
            "fat": macros.get("fats", 70)
        }
    
    # Calculate adherence and progress
    calorie_adherence = (today_totals["calories"] / calorie_goal * 100) if calorie_goal > 0 else 0
    protein_adherence = (today_totals["protein"] / macro_goals["protein"] * 100) if macro_goals["protein"] > 0 else 0
    carb_adherence = (today_totals["carbs"] / macro_goals["carbs"] * 100) if macro_goals["carbs"] > 0 else 0
    fat_adherence = (today_totals["fat"] / macro_goals["fat"] * 100) if macro_goals["fat"] > 0 else 0
    
    # Analyze recent consumption patterns
    diabetes_suitable_count = 0
    total_recent_records = len(recent_consumption)
    for record in recent_consumption:
        medical_rating = record.get("medical_rating", {})
        diabetes_suitability = medical_rating.get("diabetes_suitability", "").lower()
        if diabetes_suitability in ["high", "good", "suitable"]:
            diabetes_suitable_count += 1
    
    diabetes_adherence = (diabetes_suitable_count / total_recent_records * 100) if total_recent_records > 0 else 0
    
    # Create comprehensive AI Coach system prompt
    system_prompt = f"""You are an advanced AI Diet Coach and Diabetes Management Specialist. You are the central intelligence of a comprehensive diabetes meal planning and tracking system.

🎯 **YOUR ROLE**: You are not just a chatbot - you are the user's personal diet coach, meal planner, and diabetes management companion. You have full access to their meal plans, consumption history, and progress data.

👤 **USER PROFILE**:
- Name: {profile.get('name', 'Not specified')}
- Age: {profile.get('age', 'Not specified')}
- Gender: {profile.get('gender', 'Not specified')}
- Weight: {profile.get('weight', 'Not specified')} kg
- Height: {profile.get('height', 'Not specified')} cm
- BMI: {profile.get('bmi', 'Not calculated')}
- Blood Pressure: {profile.get('systolicBP', 'Not specified')}/{profile.get('diastolicBP', 'Not specified')} mmHg
- Medical Conditions: {', '.join(profile.get('medicalConditions', []))}
- Allergies: {', '.join(profile.get('allergies', []))}
- Diet Type: {', '.join(profile.get('dietType', []))}
- Dietary Restrictions: {', '.join(profile.get('dietaryRestrictions', []))}

🎯 **DAILY GOALS & PROGRESS**:
- Calorie Goal: {calorie_goal} kcal
- Protein Goal: {macro_goals['protein']}g
- Carb Goal: {macro_goals['carbs']}g  
- Fat Goal: {macro_goals['fat']}g

📊 **TODAY'S PROGRESS** ({datetime.utcnow().strftime('%B %d, %Y')}):
- Calories: {today_totals['calories']:.0f}/{calorie_goal} ({calorie_adherence:.1f}%)
- Protein: {today_totals['protein']:.1f}/{macro_goals['protein']}g ({protein_adherence:.1f}%)
- Carbs: {today_totals['carbs']:.1f}/{macro_goals['carbs']}g ({carb_adherence:.1f}%)
- Fat: {today_totals['fat']:.1f}/{macro_goals['fat']}g ({fat_adherence:.1f}%)
- Meals logged today: {len(today_consumption)}

📈 **RECENT PERFORMANCE** (Last 7 days):
- Total meals logged: {total_recent_records}
- Diabetes-suitable meals: {diabetes_suitable_count} ({diabetes_adherence:.1f}%)
- Recent meal plans available: {len(recent_meal_plans)}

🍽️ **RECENT MEAL PLANS**:
{chr(10).join([f"- Plan {i+1} (Created: {plan.get('created_at', 'Unknown')[:10]}): {plan.get('dailyCalories', 'N/A')} kcal/day" for i, plan in enumerate(recent_meal_plans[:2])]) if recent_meal_plans else "- No recent meal plans found"}

🥗 **TODAY'S CONSUMPTION**:
{chr(10).join([f"- {record.get('food_name', 'Unknown food')} ({record.get('estimated_portion', 'Unknown portion')}) - {record.get('nutritional_info', {}).get('calories', 'N/A')} kcal" for record in today_consumption[-3:]]) if today_consumption else "- No meals logged today yet"}

🧠 **YOUR COACHING INTELLIGENCE**:
1. **Adaptive Recommendations**: Based on today's intake, suggest meal adjustments
2. **Progress Recognition**: Celebrate achievements and provide encouragement
3. **Smart Balancing**: If user exceeded calories/carbs, suggest lighter options for remaining meals
4. **Reward System**: If user has been compliant, occasionally suggest enjoyable treats within limits
5. **Meal Plan Integration**: Reference their actual meal plans and suggest modifications
6. **Real-time Guidance**: Provide immediate feedback on food choices and portions

🎯 **COACHING PRIORITIES**:
1. **Diabetes Management**: Always prioritize blood sugar stability
2. **Adherence Support**: Help user stick to their meal plans while being flexible
3. **Behavioral Coaching**: Encourage positive habits and address challenges
4. **Nutritional Education**: Explain the 'why' behind recommendations
5. **Motivation**: Keep user engaged and motivated in their health journey

💡 **RESPONSE STYLE**:
- Be encouraging, supportive, and knowledgeable
- Use specific data from their actual consumption and meal plans
- Provide actionable, personalized advice
- Acknowledge their progress and efforts
- Be conversational but professional
- Use emojis appropriately to make interactions engaging

Remember: You have access to their complete meal planning and consumption history. Use this data to provide highly personalized, contextual advice that feels like it comes from someone who truly knows their journey."""
    
    # Ensure chat history is a list of message objects
    formatted_chat_history = []
    for msg in chat_history:
        if isinstance(msg, tuple) and len(msg) == 2:
            content, is_user = msg
            formatted_chat_history.append(
                {"role": "user", "content": content} if is_user else {"role": "assistant", "content": content}
            )
    
    # Generate response using OpenAI
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        messages=[
            {"role": "system", "content": system_prompt},
            *formatted_chat_history,
            {"role": "user", "content": message.message}
        ],
        max_tokens=1000,  # Increased for more comprehensive responses
        temperature=0.8,  # Slightly more creative for engaging coaching
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        stream=True
    )
    
    # Stream the response and collect the full message
    full_message = ""
    async def generate():
        nonlocal full_message
        try:
            for chunk in response:
                if not chunk.choices:
                    continue
                if not chunk.choices[0].delta:
                    continue
                content = chunk.choices[0].delta.content
                if content:
                    full_message += content
                    # Yield as SSE JSON event
                    yield f"data: {json.dumps({'content': content})}\n\n"
        except Exception as e:
            print(f"Error in streaming response: {str(e)}")
            if full_message:
                # Send whatever was accumulated as final SSE event
                yield f"data: {json.dumps({'content': full_message})}\n\n"
    
    # Create a streaming response
    streaming_response = StreamingResponse(generate(), media_type="text/event-stream")
    
    # Save the complete assistant message after streaming is done
    async def save_message():
        if full_message:
            await save_chat_message(
                current_user["id"],
                full_message,
                is_user=False,
                session_id=user_message["session_id"]
            )
    
    # Add a callback to save the message after streaming
    streaming_response.background = save_message
    
    return streaming_response

@app.get("/chat/history")
async def get_chat_history(
    session_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    messages = await get_recent_chat_history(current_user["id"], session_id)
    return messages

@app.get("/chat/sessions")
async def get_chat_sessions(current_user: User = Depends(get_current_user)):
    sessions = await get_user_sessions(current_user["id"])
    return sessions

@app.delete("/chat/history")
async def delete_chat_history(
    session_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    await clear_chat_history(current_user["id"], session_id)
    return {"message": "Chat history cleared successfully"}

@app.get("/users/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    print("Current user data:", current_user)  # Add logging
    
    # Get patient info if available
    patient_name = None
    if current_user.get("patient_id"):
        try:
            patient = await get_patient_by_id(current_user["patient_id"])
            if patient:
                patient_name = patient.get("name")
        except Exception as e:
            print(f"Error fetching patient info: {str(e)}")
    
    return {
        "email": current_user["email"],
        "username": current_user["username"],
        "is_admin": current_user.get("is_admin", False),
        "name": patient_name,
        "consent_given": current_user.get("consent_given", False),
        "consent_timestamp": current_user.get("consent_timestamp", None),
        "policy_version": current_user.get("policy_version", None)
    }

@app.post("/user/profile")
async def save_user_profile(
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user)
):
    data = await request.json()
    profile = data.get("profile")
    if not profile:
        raise HTTPException(status_code=400, detail="No profile data provided")
    user_doc = await get_user_by_email(current_user["email"])
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    user_doc["profile"] = profile
    user_container.replace_item(item=user_doc["id"], body=user_doc)
    return {"message": "Profile saved"}

@app.get("/user/profile")
async def get_user_profile(current_user: User = Depends(get_current_user)):
    user_doc = await get_user_by_email(current_user["email"])
    if not user_doc or "profile" not in user_doc:
        return {}
    return user_doc["profile"]

@app.post("/generate-recipe")
async def generate_recipe(
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        data = await request.json()
        meal_name = data.get('meal_name')
        user_profile = data.get('user_profile', {})
        print("/generate-recipe endpoint called")
        print("Meal name:", meal_name)
        print("User profile:", user_profile)
        
        if not meal_name:
            raise HTTPException(status_code=400, detail="No meal name provided")
        
        # Check if OpenAI client is properly configured
        if not client:
            print("ERROR: OpenAI client is not initialized")
            raise HTTPException(status_code=500, detail="OpenAI client not configured")
        
        # Check environment variables
        openai_key = os.getenv("AZURE_OPENAI_KEY")
        openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        
        print(f"OpenAI Key exists: {bool(openai_key)}")
        print(f"OpenAI Endpoint: {openai_endpoint}")
        print(f"Deployment Name: {deployment_name}")
        
        if not openai_key or not openai_endpoint or not deployment_name:
            missing = []
            if not openai_key: missing.append("AZURE_OPENAI_KEY")
            if not openai_endpoint: missing.append("AZURE_OPENAI_ENDPOINT")
            if not deployment_name: missing.append("AZURE_OPENAI_DEPLOYMENT_NAME")
            error_msg = f"Missing environment variables: {', '.join(missing)}"
            print(f"ERROR: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Create profile summary for recipe generation
        def get_profile_value(profile, new_key, old_key=None, default='Not specified'):
            value = profile.get(new_key)
            if not value and old_key:
                value = profile.get(old_key)
            if isinstance(value, list) and value:
                return ', '.join(value)
            elif isinstance(value, list):
                return default
            return value or default

        medical_summary = f"""
MEDICAL CONDITIONS: {get_profile_value(user_profile, 'medicalConditions', 'medical_conditions', 'None')}
CURRENT MEDICATIONS: {get_profile_value(user_profile, 'currentMedications', default='None')}
DIETARY RESTRICTIONS: {get_profile_value(user_profile, 'dietaryRestrictions', default='None')}
FOOD ALLERGIES: {get_profile_value(user_profile, 'allergies', default='None')}
FOOD DISLIKES: {get_profile_value(user_profile, 'strongDislikes', default='None')}
**PREFERRED CUISINE TYPE: {get_profile_value(user_profile, 'dietType', 'diet_type', 'Standard')}** ⭐ MUST FOLLOW THIS CUISINE STYLE ⭐
DIETARY FEATURES: {get_profile_value(user_profile, 'dietaryFeatures', 'diet_features', 'None')}
AVAILABLE APPLIANCES: {get_profile_value(user_profile, 'availableAppliances', default='Standard kitchen equipment')}
MEAL PREP CAPABILITY: {get_profile_value(user_profile, 'mealPrepCapability', default='Self-prepared')}
        """

        prompt = f"""Generate a detailed, medically-appropriate recipe for: {meal_name}

PATIENT MEDICAL & DIETARY CONTEXT:
{medical_summary}

CRITICAL REQUIREMENTS:
1. MEDICAL SAFETY: Ensure recipe is safe for all listed medical conditions
2. MEDICATION INTERACTIONS: Avoid ingredients that may interact with medications
3. DIETARY COMPLIANCE: Strictly adhere to dietary restrictions and allergies
4. CUISINE TYPE ADHERENCE: **CRITICALLY IMPORTANT** - Follow the specified cuisine type exactly:
   - If "Western" or "European": Use Western/European cooking methods, ingredients, and flavors
   - If "Mediterranean": Use Mediterranean ingredients like olive oil, herbs, fish, vegetables
   - If "South Asian": Use appropriate spices, cooking methods, and traditional ingredients
   - If "East Asian": Use Asian cooking techniques, sauces, and ingredients
   - If "Caribbean": Use Caribbean spices, cooking methods, and traditional ingredients
5. EQUIPMENT CONSTRAINTS: Only use available appliances and match meal prep capability
6. DIABETES-FRIENDLY: Ensure appropriate carbohydrate content and glycemic index

Please provide:
1. A list of ingredients with precise quantities
2. Step-by-step preparation instructions
3. Cooking tips for the specified medical conditions
4. Nutritional information per serving

Format the response as a JSON object with the following structure:
{{
    "name": "Recipe Name",
    "ingredients": ["ingredient1 with quantity", "ingredient2 with quantity", ...],
    "instructions": ["step1", "step2", ...],
    "nutritional_info": {{
        "calories": "number with unit, e.g. '115 kcal'",
        "protein": "number with unit, e.g. '3g'",
        "carbs": "number with unit, e.g. '16g'",
        "fat": "number with unit, e.g. '4g'"
    }}
}}"""
        
        print("Prompt for OpenAI:")
        print(prompt[:200] + "..." if len(prompt) > 200 else prompt)
        
        try:
            print("Calling OpenAI API...")
            response = client.chat.completions.create(
                model=deployment_name,
                messages=[
                    {"role": "system", "content": "You are a diabetes diet planning assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
            )
            print("OpenAI response received successfully")
        except Exception as openai_error:
            print(f"OpenAI API Error: {type(openai_error).__name__}: {str(openai_error)}")
            # Check for common OpenAI errors
            if "rate_limit" in str(openai_error).lower():
                raise HTTPException(status_code=429, detail="OpenAI rate limit exceeded. Please try again later.")
            elif "quota" in str(openai_error).lower():
                raise HTTPException(status_code=503, detail="OpenAI quota exceeded. Please check your API limits.")
            elif "authentication" in str(openai_error).lower() or "401" in str(openai_error):
                raise HTTPException(status_code=500, detail="OpenAI authentication failed. Please check API credentials.")
            elif "network" in str(openai_error).lower() or "connection" in str(openai_error).lower():
                raise HTTPException(status_code=502, detail="Network error connecting to OpenAI. Please try again.")
            else:
                raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(openai_error)}")
        
        raw_content = response.choices[0].message.content
        print("Raw OpenAI response received")
        print(f"Response length: {len(raw_content) if raw_content else 0}")
        
        if not raw_content:
            raise HTTPException(status_code=500, detail="Empty response from OpenAI")
        
        # Remove Markdown code block if present
        if raw_content.strip().startswith('```'):
            raw_content = re.sub(r'^```[a-zA-Z]*\s*|```$', '', raw_content.strip(), flags=re.MULTILINE).strip()
        
        try:
            recipe = json.loads(raw_content)
            print("Successfully parsed recipe JSON")
            print(f"Recipe name: {recipe.get('name', 'Unknown')}")
        except json.JSONDecodeError as parse_err:
            print(f"JSON parsing error: {str(parse_err)}")
            print(f"Raw content (first 500 chars): {raw_content[:500]}")
            raise HTTPException(status_code=500, detail=f"Invalid JSON response from OpenAI: {str(parse_err)}")
        except Exception as parse_err:
            print(f"Unexpected parsing error: {str(parse_err)}")
            raise HTTPException(status_code=500, detail=f"Error parsing OpenAI response: {str(parse_err)}")
        
        return recipe
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"Unexpected error in /generate-recipe: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/user/shopping-list")
async def get_user_shopping_list(current_user: User = Depends(get_current_user)):
    """Get the most recent shopping list for the current user"""
    try:
        shopping_lists = await get_user_shopping_lists(current_user["email"])
        if not shopping_lists:
            return {"items": []}
        # Return the most recent shopping list (assuming sorted by creation time or session_id)
        # If not sorted, sort by session_id or add a timestamp in the future
        return shopping_lists[-1]
    except Exception as e:
        print(f"Error fetching shopping list: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/user/shopping-list")
async def save_user_shopping_list(request: FastAPIRequest, current_user: User = Depends(get_current_user)):
    data = await request.json()
    items = data.get("items")
    if not items or not isinstance(items, list):
        raise HTTPException(status_code=400, detail="No items provided or invalid format")
    try:
        await save_shopping_list(current_user["email"], {"items": items})
        return {"message": "Shopping list saved successfully"}
    except Exception as e:
        print(f"Error saving shopping list: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user/recipes")
async def get_user_recipes_endpoint(current_user: User = Depends(get_current_user)):
    """Get the most recent recipes for the current user"""
    try:
        recipes_list = await get_user_recipes(current_user["email"])
        if not recipes_list:
            return {"recipes": []}
        return recipes_list[-1]
    except Exception as e:
        print(f"Error fetching recipes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/user/recipes")
async def save_user_recipes(request: FastAPIRequest, current_user: User = Depends(get_current_user)):
    data = await request.json()
    recipes = data.get("recipes")
    if not recipes or not isinstance(recipes, list):
        raise HTTPException(status_code=400, detail="No recipes provided or invalid format")
    try:
        await save_recipes(current_user["email"], recipes)
        return {"message": "Recipes saved"}
    except Exception as e:
        print(f"Error saving recipes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.exception_handler(Exception)
async def global_exception_handler(request: FastAPIRequest, exc: Exception):
    print(f"Global exception handler: {exc}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )

@app.post("/test-echo")
async def test_echo(current_user: User = Depends(get_current_user)):
    print(">>>> Entered /test-echo endpoint")
    return {"ok": True}

@app.post("/export/test-minimal")
async def export_test_minimal():
    print(">>>> Entered /export/test-minimal endpoint")
    return {"ok": True}

@app.post("/generate_plan")
async def generate_plan(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Save a generated meal plan to history"""
    try:
        data = await request.json()
        
        # Validate required fields
        required_fields = ["user_profile", "recipes", "shopping_list"]
        for field in required_fields:
            if field not in data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Save the meal plan using Cosmos DB
        meal_plan = await save_meal_plan(current_user["email"], data)
        
        return {
            "status": "success",
            "message": "Meal plan saved successfully",
            "meal_plan": meal_plan
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/meal_plans")
async def get_meal_plans(
    current_user: User = Depends(get_current_user)
):
    """Get all meal plans for the current user"""
    try:
        meal_plans = await get_user_meal_plans(current_user["email"])
        return {"meal_plans": meal_plans}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve meal plans: {str(e)}"
        )

@app.get("/meal_plans/{plan_id}")
async def get_meal_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific meal plan by ID"""
    try:
        # Query Cosmos DB for the specific meal plan
        query = f"SELECT * FROM c WHERE c.type = 'meal_plan' AND c.id = '{plan_id}' AND c.user_id = '{current_user['id']}'"
        items = list(interactions_container.query_items(query=query, enable_cross_partition_query=True))
        
        if not items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meal plan not found"
            )
            
        return {"meal_plan": items[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve meal plan: {str(e)}"
        )

@app.delete("/meal_plans/all") # Use DELETE with a specific path for clarity
async def delete_all_meal_plans_endpoint(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Deletes all meal plans for the current user."""
    try:
        user_id = current_user.get("email")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in token. Please log in again.")

        deleted_count = await delete_all_user_meal_plans(user_id)

        if deleted_count == 0:
            return {"message": "No meal plans were found to delete. Your history is already empty."}
        else:
            return {"message": f"Successfully deleted all {deleted_count} meal plan(s) for user {user_id}."}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in DELETE /meal_plans/all: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to delete all meal plans: {str(e)}")

@app.delete("/meal_plans/{plan_id}")
async def delete_meal_plan(
    plan_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Deletes a specific meal plan by ID for the current user."""
    try:
        user_id = current_user.get("email")
        if not user_id:
             raise HTTPException(status_code=400, detail="User ID not found in token.")
        deleted = await delete_meal_plan_by_id(plan_id, user_id)
        if not deleted:
             raise HTTPException(status_code=404, detail="Meal plan not found or does not belong to user.")
        return {"message": f"Meal plan '{plan_id}' deleted successfully"}
    except Exception as e:
        print(f"Error in DELETE /meal_plans/{{plan_id}}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to delete meal plan: {str(e)}")

@app.post("/meal_plans/bulk_delete")
async def bulk_delete_meal_plans(
    plan_ids: List[str] = Body(..., embed=True),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Deletes a list of specific meal plans by ID for the current user."""
    if not plan_ids:
        raise HTTPException(status_code=400, detail="No meal plan IDs provided for deletion.")
        
    user_id = current_user.get("email")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found in token.")

    deleted_count = 0
    failed_deletions = []
    corrupted_plans = []
    
    for plan_id in plan_ids:
        try:
            if not plan_id:
                failed_deletions.append("Empty ID provided")
                continue

            # Ensure plan_id has the correct prefix
            if not plan_id.startswith('meal_plan_'):
                plan_id = f'meal_plan_{plan_id}'

            deleted = await delete_meal_plan_by_id(plan_id, user_id)
            
            if deleted:
                deleted_count += 1
            else:
                # Check if the plan exists but is corrupted
                query = f"SELECT c.id, c.created_at, c.dailyCalories, c.macronutrients FROM c WHERE c.type = 'meal_plan' AND c.id = '{plan_id}' AND c.user_id = '{user_id}'"
                items = list(interactions_container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                ))
                
                if items:
                    # Plan exists but might be corrupted
                    plan = items[0]
                    required_fields = ['created_at', 'dailyCalories', 'macronutrients']
                    missing_fields = [field for field in required_fields if field not in plan]
                    if missing_fields:
                        corrupted_plans.append(f"{plan_id} (missing: {', '.join(missing_fields)})")
                    else:
                        failed_deletions.append(f"{plan_id} (not found or access denied)")
                else:
                    failed_deletions.append(f"{plan_id} (not found or access denied)")

        except Exception as e:
            print(f"Error deleting meal plan {plan_id} during bulk delete: {e}")
            failed_deletions.append(f"{plan_id} (error: {str(e)})")

    if deleted_count == 0 and not failed_deletions and not corrupted_plans:
        raise HTTPException(status_code=404, detail="No meal plans were found to delete.")
    
    response = {
        "message": f"Successfully deleted {deleted_count} meal plan(s).",
        "deleted_count": deleted_count
    }
    
    if failed_deletions:
        response["failed_deletions"] = failed_deletions
    
    if corrupted_plans:
        response["corrupted_plans"] = corrupted_plans
    
    return response

@app.get("/view-meal-plans")
async def view_meal_plans_endpoint(current_user: Dict[str, Any] = Depends(get_current_user)):
    """View all meal plans for the current user"""
    try:
        meal_plans = await view_meal_plans(current_user["email"])
        return {"meal_plans": meal_plans}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/save-consolidated-pdf")
async def save_consolidated_pdf_endpoint(
    request: FastAPIRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Generates and saves a consolidated PDF, returns PDF info for storage reference."""
    try:
        data = await request.json()
        meal_plan = data.get('meal_plan', {})
        recipes = data.get('recipes', [])
        shopping_list = data.get('shopping_list', [])
        
        print("Generating consolidated PDF for saving...")
        
        # Generate PDF using the same logic as the download endpoint
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
        elements = []
        styles = getSampleStyleSheet()
        
        # Add cover page
        try:
            cover_path = os.path.join("assets", "coverpage.png")
            elements.append(RLImage(cover_path, width=10*inch, height=6*inch))
            elements.append(Spacer(1, 48))
        except Exception as cover_err:
            print(f"Could not add cover page: {cover_err}")
        
        # Title
        elements.append(Paragraph("Consolidated Meal Plan", styles['Title']))
        elements.append(Spacer(1, 12))
        
        # Meal Plan Section
        elements.append(Paragraph("Meal Plan", styles['Heading1']))
        elements.append(Spacer(1, 12))
        data_table = [["Day", "Breakfast", "Lunch", "Dinner", "Snacks"]]
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for i, day in enumerate(days):
            data_table.append([
                day,
                meal_plan["breakfast"][i] if i < len(meal_plan["breakfast"]) else "",
                meal_plan["lunch"][i] if i < len(meal_plan["lunch"]) else "",
                meal_plan["dinner"][i] if i < len(meal_plan["dinner"]) else "",
                meal_plan["snacks"][i] if i < len(meal_plan["snacks"]) else "",
            ])
        col_widths = [0.8*inch, 2.5*inch, 2.5*inch, 2.5*inch, 2.5*inch]
        table = Table(data_table, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        for row in range(1, len(data_table)):
            for col in range(1, 5):
                table._cellvalues[row][col] = Paragraph(str(table._cellvalues[row][col]), styles['BodyText'])
        elements.append(table)
        elements.append(Spacer(1, 24))
        
        # Recipes Section (new page)
        elements.append(PageBreak())
        elements.append(Paragraph("Recipes", styles['Heading1']))
        elements.append(Spacer(1, 12))
        for recipe in recipes:
            elements.append(Paragraph(recipe["name"], styles['Heading2']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("Nutritional Information", styles['Heading3']))
            elements.append(Paragraph(f"Calories: {recipe['nutritional_info']['calories']}", styles['Normal']))
            elements.append(Paragraph(f"Protein: {recipe['nutritional_info']['protein']}", styles['Normal']))
            elements.append(Paragraph(f"Carbs: {recipe['nutritional_info']['carbs']}", styles['Normal']))
            elements.append(Paragraph(f"Fat: {recipe['nutritional_info']['fat']}", styles['Normal']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("Ingredients", styles['Heading3']))
            for ingredient in recipe["ingredients"]:
                elements.append(Paragraph(f"• {ingredient}", styles['Normal']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("Instructions", styles['Heading3']))
            for i, instruction in enumerate(recipe["instructions"], 1):
                elements.append(Paragraph(f"{i}. {instruction}", styles['Normal']))
            elements.append(Spacer(1, 24))
        
        # Shopping List Section (new page)
        elements.append(PageBreak())
        elements.append(Paragraph("Shopping List", styles['Heading1']))
        elements.append(Spacer(1, 12))
        categories = {}
        for item in shopping_list:
            if item["category"] not in categories:
                categories[item["category"]] = []
            categories[item["category"]].append(item)
        for category, items in categories.items():
            elements.append(Paragraph(category, styles['Heading2']))
            elements.append(Spacer(1, 12))
            for item in items:
                elements.append(Paragraph(f"• {item['name']} - {item['amount']}", styles['Normal']))
            elements.append(Spacer(1, 24))
        
        doc.build(elements)
        buffer.seek(0)
        
        # Create filename
        username = current_user["email"].split("@")[0]
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{username}_{date_str}_consolidated_meal_plan.pdf"
        
        # Save PDF to a storage directory (create directory if it doesn't exist)
        storage_dir = os.path.join("storage", "pdfs")
        os.makedirs(storage_dir, exist_ok=True)
        file_path = os.path.join(storage_dir, filename)
        
        with open(file_path, 'wb') as f:
            f.write(buffer.getvalue())
        
        # Return PDF info for storage in meal plan
        pdf_info = {
            "filename": filename,
            "file_path": file_path,
            "generated_at": datetime.now().isoformat(),
            "file_size": len(buffer.getvalue())
        }
        
        print(f"Consolidated PDF saved to: {file_path}")
        return {"pdf_info": pdf_info}
        
    except Exception as e:
        print("Error in /save-consolidated-pdf:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download-saved-pdf/{filename}")
async def download_saved_pdf(
    filename: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Download a previously saved consolidated PDF"""
    try:
        # Security check: ensure filename is safe and belongs to user
        username = current_user["email"].split("@")[0]
        if not filename.startswith(username) or ".." in filename or "/" in filename:
            raise HTTPException(status_code=403, detail="Access denied")
        
        file_path = os.path.join("storage", "pdfs", filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        return FileResponse(
            file_path,
            media_type="application/pdf",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error downloading saved PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save-full-meal-plan")
async def save_full_meal_plan_endpoint(
    full_meal_plan_data: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Saves the full meal plan data including recipes, shopping list, and PDF reference."""
    try:
        user_id = current_user.get("email") # Or use "id" depending on how you identify users
        if not user_id:
             raise HTTPException(status_code=400, detail="User ID not found in token.")
             
        # The save_meal_plan function in database.py is designed to accept
        # the meal_plan dictionary and use **meal_plan, so we can pass the
        # full_meal_plan_data directly if it contains the required base fields
        # (breakfast, lunch, etc.) plus recipes, shopping_list, and consolidated_pdf.
        
        # It might be a good idea to add validation here or in save_meal_plan
        # to ensure the basic meal plan fields are present.

        saved_plan = await save_meal_plan(user_id, full_meal_plan_data)
        
        # You might want to return the saved_plan data or just a success message
        return {"message": "Meal plan saved successfully", "plan_id": saved_plan.get("id")}
        
    except ValueError as e:
        # Handle validation errors from save_meal_plan
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Handle other potential errors during saving
        print(f"Error saving full meal plan: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="An error occurred while saving the meal plan.")

@app.get("/debug/meal_plans")
async def debug_meal_plans(current_user: User = Depends(get_current_user)):
    """Return all meal plans for the current user, including IDs and partition keys, for debugging."""
    try:
        user_id = current_user.get("email")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in token.")
        query = f"SELECT * FROM c WHERE c.type = 'meal_plan' AND c.user_id = '{user_id}'"
        print(f"[DEBUG] Querying all meal plans for user_id: {user_id}")
        items = list(interactions_container.query_items(query=query, enable_cross_partition_query=True))
        print(f"[DEBUG] Found {len(items)} meal plans for user_id: {user_id}")
        return {"meal_plans": items}
    except Exception as e:
        print(f"[DEBUG] Error in /debug/meal_plans: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/consumption/analyze-and-record")
async def analyze_and_record_food(
    image: UploadFile = File(...),
    session_id: str = Form(None),
    meal_type: str = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Analyze food image and optionally record to consumption history"""
    try:
        print(f"[analyze_and_record_food] Starting analysis for user {current_user['id']}")
        
        # Read and validate image
        contents = await image.read()
        
        # Validate file type and size
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        if len(contents) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB")
        
        # Check file extension
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        file_extension = image.filename.lower().split('.')[-1] if image.filename else ''
        if not file_extension or f'.{file_extension}' not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Unsupported file format. Allowed formats: {', '.join(allowed_extensions)}")
        
        try:
            # Try to open and validate the image
            img = Image.open(BytesIO(contents))
            
            # Convert to RGB if necessary (handles RGBA, P modes, etc.)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if too large (max 1024x1024 for processing efficiency)
            max_size = 1024
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Convert image to base64
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=85, optimize=True)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            print("[analyze_and_record_food] Image processed and converted to base64")
            
        except Exception as img_error:
            print(f"[analyze_and_record_food] Image processing error: {str(img_error)}")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid or corrupted image file. Please upload a valid image in one of these formats: {', '.join(allowed_extensions)}"
            )
        
        # Generate structured analysis using OpenAI
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {
                    "role": "system",
                    "content": """You are a nutrition analysis expert for diabetes patients. 
                    Analyze the food image and return a structured JSON response with the following format:
                    {
                        "food_name": "descriptive name of the food",
                        "estimated_portion": "portion size estimate",
                        "nutritional_info": {
                            "calories": number,
                            "carbohydrates": number (in grams),
                            "protein": number (in grams),
                            "fat": number (in grams),
                            "fiber": number (in grams),
                            "sugar": number (in grams),
                            "sodium": number (in mg)
                        },
                        "medical_rating": {
                            "diabetes_suitability": "high/medium/low",
                            "glycemic_impact": "low/medium/high",
                            "recommended_frequency": "daily/weekly/occasional/avoid",
                            "portion_recommendation": "recommended portion size for diabetes patients"
                        },
                        "analysis_notes": "detailed explanation of nutritional analysis and diabetes considerations"
                    }
                    Provide realistic estimates based on visual analysis. Be conservative with diabetes suitability ratings."""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this food image and provide detailed nutritional information and diabetes suitability rating."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_str}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=800,
            temperature=0.3
        )
        
        print("[analyze_and_record_food] Received analysis from OpenAI")
        
        # Get the response content
        analysis_text = response.choices[0].message.content
        
        # Try to parse JSON from the response
        try:
            import json
            # Extract JSON from response (in case there's additional text)
            start_idx = analysis_text.find('{')
            end_idx = analysis_text.rfind('}') + 1
            json_str = analysis_text[start_idx:end_idx]
            analysis_data = json.loads(json_str)
            print(f"[analyze_and_record_food] Successfully parsed analysis data: {analysis_data}")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[analyze_and_record_food] Error parsing analysis data: {str(e)}")
            # If JSON parsing fails, create a structured response from the text
            analysis_data = {
                "food_name": "Unknown food item",
                "estimated_portion": "Unable to determine",
                "nutritional_info": {
                    "calories": 0,
                    "carbohydrates": 0,
                    "protein": 0,
                    "fat": 0,
                    "fiber": 0,
                    "sugar": 0,
                    "sodium": 0
                },
                "medical_rating": {
                    "diabetes_suitability": "unknown",
                    "glycemic_impact": "unknown",
                    "recommended_frequency": "consult nutritionist",
                    "portion_recommendation": "consult nutritionist"
                },
                "analysis_notes": analysis_text
            }
        
        # Prepare consumption data
        consumption_data = {
            "food_name": analysis_data.get("food_name"),
            "estimated_portion": analysis_data.get("estimated_portion"),
            "nutritional_info": analysis_data.get("nutritional_info", {}),
            "medical_rating": analysis_data.get("medical_rating", {}),
            "image_analysis": analysis_data.get("analysis_notes"),
            "image_url": img_str,
            "meal_type": (meal_type or "").lower()
        }
        
        print(f"[analyze_and_record_food] Prepared consumption data: {consumption_data}")
        
        # Save to consumption history
        print(f"[analyze_and_record_food] Attempting to save consumption record for user {current_user['id']}")
        consumption_record = await save_consumption_record(current_user["email"], consumption_data, meal_type=meal_type or "")
        print(f"[analyze_and_record_food] Successfully saved consumption record with ID: {consumption_record['id']}")
        
        # Also save to chat if session_id is provided
        if session_id:
            print(f"[analyze_and_record_food] Saving to chat with session_id: {session_id}")
            # Save user message with image
            await save_chat_message(
                current_user["id"],
                "Recorded food consumption",
                is_user=True,
                session_id=session_id,
                image_url=img_str
            )
            
            # Save assistant response
            summary_message = f"**Food Recorded: {analysis_data.get('food_name')}**\n\n"
            summary_message += f"📊 **Nutritional Info (per {analysis_data.get('estimated_portion')}):**\n"
            summary_message += f"- Calories: {analysis_data.get('nutritional_info', {}).get('calories', 'N/A')}\n"
            summary_message += f"- Carbs: {analysis_data.get('nutritional_info', {}).get('carbohydrates', 'N/A')}g\n"
            summary_message += f"- Protein: {analysis_data.get('nutritional_info', {}).get('protein', 'N/A')}g\n"
            summary_message += f"- Fat: {analysis_data.get('nutritional_info', {}).get('fat', 'N/A')}g\n\n"
            summary_message += f"🩺 **Diabetes Suitability:** {analysis_data.get('medical_rating', {}).get('diabetes_suitability', 'N/A').title()}\n"
            summary_message += f"📈 **Glycemic Impact:** {analysis_data.get('medical_rating', {}).get('glycemic_impact', 'N/A').title()}\n\n"
            summary_message += f"💡 **Notes:** {analysis_data.get('analysis_notes', '')}"
            
            await save_chat_message(
                current_user["email"],
                summary_message,
                is_user=False,
                session_id=session_id
            )
            print("[analyze_and_record_food] Successfully saved chat messages")
        
        return {"consumption_record_id": consumption_record["id"], "analysis": analysis_data}
        
    except Exception as e:
        print(f"[analyze_and_record_food] Error: {str(e)}")
        print(f"[analyze_and_record_food] Full error details:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/consumption/history")
async def get_consumption_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get consumption history - USING ORIGINAL FUNCTION with better error handling"""
    try:
        print(f"[get_consumption_history] Getting history for user {current_user['id']}")
        
        # Use the original database function
        history = await get_user_consumption_history(current_user["email"], limit)
        print(f"[get_consumption_history] Retrieved {len(history)} records")
        
        return history
        
    except Exception as e:
        print(f"[get_consumption_history] Error: {str(e)}")
        print(f"[get_consumption_history] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get consumption history: {str(e)}")

@app.get("/consumption/analytics")
async def get_consumption_analytics_endpoint(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get consumption analytics - USING ORIGINAL FUNCTION with better error handling"""
    try:
        print(f"[get_consumption_analytics] Getting analytics for user {current_user['id']} for {days} days")
        
        # Use the original database function
        analytics = await get_consumption_analytics(current_user["email"], days)
        print(f"[get_consumption_analytics] Generated analytics successfully")
        
        return analytics
        
    except Exception as e:
        print(f"[get_consumption_analytics] Error: {str(e)}")
        print(f"[get_consumption_analytics] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get consumption analytics: {str(e)}")

@app.post("/chat/analyze-image")
async def analyze_image(
    image: UploadFile = File(...),
    prompt: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    try:
        # Read and validate image
        contents = await image.read()
        
        # Validate file type and size
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        if len(contents) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB")
        
        # Check file extension
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        file_extension = image.filename.lower().split('.')[-1] if image.filename else ''
        if not file_extension or f'.{file_extension}' not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Unsupported file format. Allowed formats: {', '.join(allowed_extensions)}")
        
        try:
            # Try to open and validate the image
            img = Image.open(BytesIO(contents))
            
            # Convert to RGB if necessary (handles RGBA, P modes, etc.)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if too large (max 1024x1024 for processing efficiency)
            max_size = 1024
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Convert image to base64
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=85, optimize=True)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
        except Exception as img_error:
            print(f"[analyze_image] Image processing error: {str(img_error)}")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid or corrupted image file. Please upload a valid image in one of these formats: {', '.join(allowed_extensions)}"
            )
        
        # Save user message with image
        user_message = await save_chat_message(
            current_user["id"],
            "Analyzing food image...",
            is_user=True,
            session_id=None,  # You might want to handle session_id differently
            image_url=img_str
        )
        
        # Generate response using OpenAI with image
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful diet assistant for diabetes patients. Analyze the food image and provide detailed nutritional information, including estimated calories, macronutrients, and any relevant dietary considerations for diabetes patients."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_str}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500,
            temperature=0.7,
            stream=True
        )
        
        # Stream the response
        async def generate():
            full_message = ""
            try:
                for chunk in response:
                    if not chunk.choices:
                        continue
                    if not chunk.choices[0].delta:
                        continue
                    content = chunk.choices[0].delta.content
                    if content:
                        full_message += content
                        # Yield as SSE JSON event
                        yield f"data: {json.dumps({'content': content})}\n\n"
            except Exception as e:
                print(f"Error in streaming response: {str(e)}")
                if full_message:
                    # Send whatever was accumulated as final SSE event
                    yield f"data: {json.dumps({'content': full_message})}\n\n"
            
            # Save the complete assistant message after streaming
            if full_message:
                await save_chat_message(
                    current_user["id"],
                    full_message,
                    is_user=False,
                    session_id=user_message["session_id"],
                    image_url=img_str
                )
        
        return StreamingResponse(generate(), media_type="text/event-stream")
        
    except Exception as e:
        print(f"Error in image analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper for intent detection
def has_logging_intent(message: str) -> bool:
    logging_intents = [
        "log this", "add this to my history", "record this", "save this",
        "log it", "add this meal", "add this food", "log meal", "log food",
        "can you log", "please log", "log as my", "this as my", "this was my"
    ]
    return any(kw in message.lower() for kw in logging_intents)

# Add this helper near the top of the file
import re

def extract_nutrition_question(message: str):
    """
    Returns the nutrition field(s) the user is asking about, or None if not found.
    Supports: calories, protein, carbs, fat, fiber, sugar, sodium.
    """
    nutrition_keywords = {
        'calories': ['calorie', 'calories', 'kcal'],
        'protein': ['protein', 'proteins'],
        'carbohydrates': ['carb', 'carbs', 'carbohydrate', 'carbohydrates'],
        'fat': ['fat', 'fats'],
        'fiber': ['fiber', 'fibre'],
        'sugar': ['sugar', 'sugars'],
        'sodium': ['sodium', 'salt'],
    }
    found = []
    msg = message.lower()
    for field, keywords in nutrition_keywords.items():
        for kw in keywords:
            if re.search(rf'\b{re.escape(kw)}\b', msg):
                found.append(field)
                break
    return found if found else None

@app.post("/chat/message-with-image")
async def chat_message_with_image(
    message: str = Form(...),
    image: UploadFile = File(None),
    session_id: str = Form(None),
    analysis_mode: str = Form("analysis"),  # New parameter for analysis mode
    current_user: User = Depends(get_current_user)
):
    """
    Comprehensive health coach chat with full user context integration.
    Uses the unified AI system for personalized responses based on all health conditions.
    """
    image_url = None
    img_str = None
    analysis_data = None

    # --- Determine meal type from the user's message, if mentioned ---
    meal_type_match = re.search(r"\b(breakfast|lunch|dinner|snack)s?\b", message.lower())
    meal_type = meal_type_match.group(1) if meal_type_match else None

    # 🧠 GET COMPREHENSIVE USER CONTEXT - This is the key integration!
    try:
        user_context = await get_comprehensive_user_context(current_user["email"])
        print(f"✅ Retrieved comprehensive context for user: {len(user_context.get('health_conditions', []))} conditions, {len(user_context.get('consumption_history', []))} recent meals")
    except Exception as e:
        print(f"❌ Error getting comprehensive context: {str(e)}")
        user_context = {"error": "Could not retrieve user context"}

    # 🧠 CONTEXT RETRIEVAL - Get recent chat history for context
    recent_context = None
    if has_logging_intent(message) and not image:
        # User wants to log something but didn't provide an image
        # Look for recent food analysis in chat history
        try:
            recent_messages = await get_recent_chat_history(current_user["id"], session_id, limit=10)
            for msg in recent_messages:
                if not msg.get("is_user", True) and "Food Analysis:" in msg.get("message_content", ""):
                    # Found a recent food analysis - extract the analysis data
                    msg_content = msg.get("message_content", "")
                    if "Food Analysis:" in msg_content:
                        # Try to extract food name and nutritional info from the message
                        lines = msg_content.split('\n')
                        food_name = None
                        calories = None
                        carbs = None
                        protein = None
                        fat = None
                        
                        for line in lines:
                            if "Food Analysis:" in line:
                                food_name = line.split("Food Analysis:")[1].strip().replace("**", "")
                            elif "Calories:" in line:
                                try:
                                    calories = int(line.split("Calories:")[1].strip().split()[0])
                                except:
                                    pass
                            elif "Carbs:" in line:
                                try:
                                    carbs = float(line.split("Carbs:")[1].strip().replace("g", ""))
                                except:
                                    pass
                            elif "Protein:" in line:
                                try:
                                    protein = float(line.split("Protein:")[1].strip().replace("g", ""))
                                except:
                                    pass
                            elif "Fat:" in line:
                                try:
                                    fat = float(line.split("Fat:")[1].strip().replace("g", ""))
                                except:
                                    pass
                        
                        if food_name:
                            recent_context = {
                                "food_name": food_name,
                                "estimated_portion": "1 serving",
                                "nutritional_info": {
                                    "calories": calories or 0,
                                    "carbohydrates": carbs or 0,
                                    "protein": protein or 0,
                                    "fat": fat or 0,
                                    "fiber": 0,
                                    "sugar": 0,
                                    "sodium": 0
                                },
                                "medical_rating": {
                                    "diabetes_suitability": diabetes_rating or "medium",
                                    "glycemic_impact": "medium",
                                    "recommended_frequency": "weekly",
                                    "portion_recommendation": "moderate portion"
                                },
                                "analysis_notes": f"Previously analyzed {food_name}"
                            }
                            break
        except Exception as e:
            print(f"Error retrieving context: {str(e)}")

    # If image is present, process it
    if image:
        contents = await image.read()
        try:
            img = Image.open(BytesIO(contents))
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            max_size = 1024
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=85, optimize=True)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            image_url = img_str
        except Exception as img_error:
            raise HTTPException(status_code=400, detail="Invalid or corrupted image file.")

    # Save user message (with or without image)
    user_message = await save_chat_message(
        current_user["id"],
        message,
        is_user=True,
        session_id=session_id,
        image_url=image_url
    )

    # If there's an image, analyze it based on the analysis mode
    if img_str:
        # Configure analysis based on mode
        if analysis_mode == "fridge":
            # Fridge analysis - different approach
            system_prompt = """You are a culinary AI assistant specializing in fridge analysis for diabetes patients. 
            Analyze the fridge/pantry image and provide helpful cooking suggestions.
            Return a JSON response with this format:
            {
                "items_detected": ["list of food items visible"],
                "suggested_meals": ["3-4 diabetes-friendly meal suggestions using these ingredients"],
                "cooking_tips": "practical cooking advice for diabetes management",
                "missing_ingredients": ["optional ingredients that would complement these items"],
                "health_notes": "diabetes-specific guidance for using these ingredients"
            }
            Focus on diabetes-friendly combinations and portion control."""
            
            user_prompt = "Analyze my fridge/pantry contents and suggest what I can cook that's suitable for diabetes management."
            
        else:
            # Food analysis (logging, analysis, question modes)
            system_prompt = """You are a nutrition analysis expert for diabetes patients. 
            Analyze the food image and return a structured JSON response with the following format:
            {
                "food_name": "descriptive name of the food",
                "estimated_portion": "portion size estimate",
                "nutritional_info": {
                    "calories": number,
                    "carbohydrates": number (in grams),
                    "protein": number (in grams),
                    "fat": number (in grams),
                    "fiber": number (in grams),
                    "sugar": number (in grams),
                    "sodium": number (in mg)
                },
                "medical_rating": {
                    "diabetes_suitability": "high/medium/low",
                    "glycemic_impact": "low/medium/high",
                    "recommended_frequency": "daily/weekly/occasional/avoid",
                    "portion_recommendation": "recommended portion size for diabetes patients"
                },
                "analysis_notes": "detailed explanation of nutritional analysis and diabetes considerations"
            }
            Provide realistic estimates based on visual analysis. Be conservative with diabetes suitability ratings."""
            
            if analysis_mode == "question":
                user_prompt = f"Analyze this food image and then answer this specific question: {message}"
            else:
                user_prompt = "Analyze this food image and provide detailed nutritional information and diabetes suitability rating."

        # Generate structured analysis using OpenAI
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_str}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000,
            temperature=0.3
        )
        analysis_text = response.choices[0].message.content
        try:
            import json
            start_idx = analysis_text.find('{')
            end_idx = analysis_text.rfind('}') + 1
            json_str = analysis_text[start_idx:end_idx]
            analysis_data = json.loads(json_str)
        except Exception:
            analysis_data = None

    # Handle different analysis modes
    if analysis_mode == "fridge" and analysis_data:
        # Fridge analysis response
        items = analysis_data.get('items_detected', [])
        meals = analysis_data.get('suggested_meals', [])
        tips = analysis_data.get('cooking_tips', '')
        missing = analysis_data.get('missing_ingredients', [])
        health_notes = analysis_data.get('health_notes', '')
        
        assistant_message = f"""🧊 **Fridge Analysis Complete!**

📋 **Items Detected:**
{chr(10).join([f"• {item}" for item in items]) if items else "• No specific items detected"}

👩‍🍳 **Diabetes-Friendly Meal Suggestions:**
{chr(10).join([f"{i+1}. {meal}" for i, meal in enumerate(meals)]) if meals else "1. No specific suggestions available"}

💡 **Cooking Tips for Diabetes Management:**
{tips if tips else "Cook with minimal added sugars and focus on portion control."}

🛒 **Optional Ingredients to Enhance Your Meals:**
{chr(10).join([f"• {item}" for item in missing]) if missing else "• Your fridge looks well-stocked!"}

🏥 **Health Notes:**
{health_notes if health_notes else "Focus on balanced portions and regular meal timing for optimal blood sugar management."}

Would you like me to create a detailed recipe for any of these meal suggestions?"""

    elif analysis_mode == "logging" and analysis_data:
        # Food logging mode - save to consumption history
        food_data = analysis_data
        consumption_data = {
            "food_name": food_data.get("food_name"),
            "estimated_portion": food_data.get("estimated_portion"),
            "nutritional_info": food_data.get("nutritional_info", {}),
            "image_analysis": food_data.get("analysis_notes"),
            "image_url": img_str
        }
        await save_consumption_record(current_user["email"], consumption_data, meal_type=meal_type or "")

        meal_type_text = f" as your **{meal_type}**" if meal_type else ""
        
        assistant_message = f"""🍽️ **Food Logged{meal_type_text}: {food_data.get('food_name')}**

📊 **Nutritional Info** (per {food_data.get('estimated_portion')}):
• Calories: {food_data.get('nutritional_info', {}).get('calories', 'N/A')}
• Carbs: {food_data.get('nutritional_info', {}).get('carbohydrates', 'N/A')}g
• Protein: {food_data.get('nutritional_info', {}).get('protein', 'N/A')}g
• Fat: {food_data.get('nutritional_info', {}).get('fat', 'N/A')}g
• Fiber: {food_data.get('nutritional_info', {}).get('fiber', 'N/A')}g

🩺 **Diabetes Suitability:** {food_data.get('medical_rating', {}).get('diabetes_suitability', 'N/A').title()}
📈 **Glycemic Impact:** {food_data.get('medical_rating', {}).get('glycemic_impact', 'N/A').title()}

✅ **Successfully logged to your consumption history!**

💡 **Analysis Notes:** {food_data.get('analysis_notes', 'No additional notes available.')}

Your daily tracking and meal planning will be updated to reflect this logged meal."""

    elif analysis_mode == "question" and analysis_data:
        # Question mode - provide specific answer based on the user's question
        assistant_message = f"""❓ **Question about {analysis_data.get('food_name', 'your food')}:**

Based on the image analysis, here's what I can tell you:

📊 **Nutritional Breakdown** (per {analysis_data.get('estimated_portion')}):
• Calories: {analysis_data.get('nutritional_info', {}).get('calories', 'N/A')}
• Carbs: {analysis_data.get('nutritional_info', {}).get('carbohydrates', 'N/A')}g
• Protein: {analysis_data.get('nutritional_info', {}).get('protein', 'N/A')}g
• Fat: {analysis_data.get('nutritional_info', {}).get('fat', 'N/A')}g
• Fiber: {analysis_data.get('nutritional_info', {}).get('fiber', 'N/A')}g
• Sugar: {analysis_data.get('nutritional_info', {}).get('sugar', 'N/A')}g

🩺 **For Diabetes Management:**
• **Suitability:** {analysis_data.get('medical_rating', {}).get('diabetes_suitability', 'N/A').title()}
• **Glycemic Impact:** {analysis_data.get('medical_rating', {}).get('glycemic_impact', 'N/A').title()}
• **Recommended Frequency:** {analysis_data.get('medical_rating', {}).get('recommended_frequency', 'N/A')}

💡 **Additional Notes:** {analysis_data.get('analysis_notes', 'No additional analysis available.')}

Is there anything specific about this food you'd like me to explain further?"""

    elif analysis_mode == "analysis" and analysis_data:
        # Pure analysis mode - no logging
        assistant_message = f"""🔍 **Food Analysis: {analysis_data.get('food_name')}**

📊 **Nutritional Breakdown** (per {analysis_data.get('estimated_portion')}):
• Calories: {analysis_data.get('nutritional_info', {}).get('calories', 'N/A')}
• Carbs: {analysis_data.get('nutritional_info', {}).get('carbohydrates', 'N/A')}g
• Protein: {analysis_data.get('nutritional_info', {}).get('protein', 'N/A')}g
• Fat: {analysis_data.get('nutritional_info', {}).get('fat', 'N/A')}g
• Fiber: {analysis_data.get('nutritional_info', {}).get('fiber', 'N/A')}g
• Sugar: {analysis_data.get('nutritional_info', {}).get('sugar', 'N/A')}g
• Sodium: {analysis_data.get('nutritional_info', {}).get('sodium', 'N/A')}mg

🩺 **Diabetes Management Insights:**
• **Suitability:** {analysis_data.get('medical_rating', {}).get('diabetes_suitability', 'N/A').title()}
• **Glycemic Impact:** {analysis_data.get('medical_rating', {}).get('glycemic_impact', 'N/A').title()}
• **Recommended Frequency:** {analysis_data.get('medical_rating', {}).get('recommended_frequency', 'N/A')}
• **Portion Recommendation:** {analysis_data.get('medical_rating', {}).get('portion_recommendation', 'N/A')}

💡 **Analysis Notes:** {analysis_data.get('analysis_notes', 'No additional notes available.')}

Would you like me to log this to your consumption history? Just say "log this as my [breakfast/lunch/dinner/snack]"!"""

    elif has_logging_intent(message) and (analysis_data or recent_context):
        # Legacy logging support
        food_data = analysis_data or recent_context
        consumption_data = {
            "food_name": food_data.get("food_name"),
            "estimated_portion": food_data.get("estimated_portion"),
            "nutritional_info": food_data.get("nutritional_info", {}),
            "image_analysis": food_data.get("analysis_notes"),
            "image_url": img_str if analysis_data else None
        }
        await save_consumption_record(current_user["email"], consumption_data, meal_type=meal_type or "")

        context_note = " (from previous analysis)" if recent_context and not analysis_data else ""
        meal_type_text = f" as your **{meal_type}**" if meal_type else ""
        
        assistant_message = f"""🍽️ **Food Logged{meal_type_text}: {food_data.get('food_name')}{context_note}**

📊 **Nutritional Info** (per {food_data.get('estimated_portion')}):
• Calories: {food_data.get('nutritional_info', {}).get('calories', 'N/A')}
• Carbs: {food_data.get('nutritional_info', {}).get('carbohydrates', 'N/A')}g
• Protein: {food_data.get('nutritional_info', {}).get('protein', 'N/A')}g
• Fat: {food_data.get('nutritional_info', {}).get('fat', 'N/A')}g

🩺 **Diabetes Suitability:** {food_data.get('medical_rating', {}).get('diabetes_suitability', 'N/A').title()}

✅ **Successfully recorded to your consumption history with meal type: {meal_type or 'unspecified'}!**

Your meal plan will be updated to reflect this logged meal."""

    else:
        # 🚀 USE COMPREHENSIVE AI SYSTEM FOR NON-LOGGING RESPONSES
        try:
            # Determine query type
            nutrition_fields = extract_nutrition_question(message)
            
            if img_str and analysis_data and nutrition_fields:
                query_type = "nutrition_question"
                specific_data = {
                    "nutrition_fields": nutrition_fields,
                    "food_data": analysis_data,
                    "user_message": message
                }
            elif img_str and analysis_data:
                query_type = "food_analysis"
                specific_data = {
                    "food_data": analysis_data,
                    "user_message": message
                }
            elif has_logging_intent(message) and not image and not recent_context:
                query_type = "logging_help"
                specific_data = {
                    "user_message": message
                }
            else:
                query_type = "general_health_chat"
                specific_data = {
                    "user_message": message
                }

            # 🧠 GET AI RESPONSE USING COMPREHENSIVE SYSTEM
            assistant_message = await get_ai_health_coach_response(
                user_context=user_context,
                query_type=query_type,
                specific_data=specific_data
            )
            
            print(f"✅ Generated comprehensive AI response for query type: {query_type}")

        except Exception as e:
            print(f"❌ Error in comprehensive AI system: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            
            # Fallback responses
            nutrition_fields = extract_nutrition_question(message)
            
            if img_str and analysis_data and nutrition_fields:
                # Focused answer for specific nutrition questions
                nutri = analysis_data.get('nutritional_info', {})
                food_name = analysis_data.get('food_name', 'this food')
                portion = analysis_data.get('estimated_portion', '')
                responses = []
                for field in nutrition_fields:
                    value = nutri.get(field, None)
                    if value is not None:
                        field_label = field.capitalize()
                        unit = 'mg' if field == 'sodium' else 'g' if field in ['protein', 'carbohydrates', 'fat', 'fiber', 'sugar'] else 'kcal' if field == 'calories' else ''
                        responses.append(f"{field_label} in {food_name} ({portion}): {value} {unit}".strip())
                
                if responses:
                    assistant_message = f"📊 **Nutrition Info:**\n\n" + '\n'.join(responses)
                    assistant_message += f"\n\n⚠️ **Note:** Using fallback response - comprehensive AI system temporarily unavailable."
                else:
                    assistant_message = "Sorry, I couldn't find that specific nutrition information for this food."
                    
            elif img_str and analysis_data:
                # General food analysis without logging
                assistant_message = f"""🔍 **Food Analysis: {analysis_data.get('food_name')}**

📊 **Nutritional Breakdown** (per {analysis_data.get('estimated_portion')}):
• Calories: {analysis_data.get('nutritional_info', {}).get('calories', 'N/A')}
• Carbs: {analysis_data.get('nutritional_info', {}).get('carbohydrates', 'N/A')}g
• Protein: {analysis_data.get('nutritional_info', {}).get('protein', 'N/A')}g
• Fat: {analysis_data.get('nutritional_info', {}).get('fat', 'N/A')}g

💡 **Notes:** {analysis_data.get('analysis_notes', 'No additional notes available.')}

Would you like me to record this to your consumption history? Just say "log this as my [breakfast/lunch/dinner/snack]"!

⚠️ **Note:** Using fallback response - comprehensive AI system temporarily unavailable."""
            elif has_logging_intent(message) and not image and not recent_context:
                # User wants to log something but we have no context
                assistant_message = """🤔 **I'd love to help you log your food!**

However, I don't see any recent food analysis in our conversation. To log food, you can:

1. **Share a photo** of your food with a message like "this is my snack"
2. **Or first share a photo** for analysis, then say "log this as my [meal type]"

I'm here to help track your nutrition and provide personalized health guidance! 📸🍽️

⚠️ **Note:** Using fallback response - comprehensive AI system temporarily unavailable."""
            else:
                assistant_message = """Hello! I'm your comprehensive health coach. I can help you with:

🍽️ **Food Analysis & Logging** - Upload food images for nutritional analysis
🏥 **Multi-Condition Health Management** - Personalized advice for all your health conditions  
📊 **Meal Planning & Tracking** - Smart recommendations based on your health profile
💊 **Medication & Treatment Integration** - Holistic health management

How can I help you today?

⚠️ **Note:** Using fallback response - comprehensive AI system temporarily unavailable."""

    # Save assistant response
    await save_chat_message(
        current_user["email"],
        assistant_message,
        is_user=False,
        session_id=session_id
    )

    # --- Stream response back so the frontend can progressively render ---
    import json as _json

    def _event_stream():
        chunk = _json.dumps({"content": assistant_message})
        yield f"data: {chunk}\n\n"

    return StreamingResponse(_event_stream(), media_type="text/event-stream")

@app.get("/consumption/progress")
async def get_consumption_progress(current_user: User = Depends(get_current_user)):
    """
    Returns user's daily calorie/macro goals, today's progress, and weekly/monthly averages.
    Always returns a valid set of goals, using smart defaults if needed.
    """
    # 1. Get user profile (for goals)
    user_doc = await get_user_by_email(current_user["email"])
    if not user_doc or "profile" not in user_doc:
        raise HTTPException(status_code=404, detail="User profile not found")
    profile = user_doc["profile"]

    # --- Try to get most recent meal plan for fallback ---
    recent_meal_plan = None
    meal_plans = await get_user_meal_plans(current_user["email"])
    if meal_plans and isinstance(meal_plans, list):
        # Assume sorted by created_at DESC
        recent_meal_plan = meal_plans[0] if meal_plans else None

    # Smart defaults
    smart_defaults = {
        "calories": 2000,
        "macronutrients": {
            "carbohydrates": 250,
            "protein": 100,
            "fat": 66
        }
    }

    def parse_int(val, default):
        try:
            return int(val)
        except Exception:
            return default

    # 1. Try to get calorie goal from profile, then meal plan, then default
    calorie_goal = None
    if profile.get("calorieTarget"):
        calorie_goal = parse_int(profile.get("calorieTarget"), smart_defaults["calories"])
    elif profile.get("calories_target"):
        calorie_goal = parse_int(profile.get("calories_target"), smart_defaults["calories"])
    elif recent_meal_plan and recent_meal_plan.get("dailyCalories"):
        calorie_goal = parse_int(recent_meal_plan.get("dailyCalories"), smart_defaults["calories"])
    else:
        calorie_goal = smart_defaults["calories"]

    # 2. Try to get macro goals from profile, then meal plan, then default
    macro_goals = profile.get("macroGoals")
    macro_from_meal_plan = recent_meal_plan.get("macronutrients") if recent_meal_plan else None
    macro_goal = None
    if macro_goals and isinstance(macro_goals, dict) and all(k in macro_goals for k in ["protein", "carbs", "fat"]):
        macro_goal = {
            "protein": parse_int(macro_goals.get("protein"), smart_defaults["macronutrients"]["protein"]),
            "carbs": parse_int(macro_goals.get("carbs"), smart_defaults["macronutrients"]["carbohydrates"]),
            "fat": parse_int(macro_goals.get("fat"), smart_defaults["macronutrients"]["fat"])
        }
    elif macro_from_meal_plan and all(k in macro_from_meal_plan for k in ["protein", "carbs", "fats"]):
        macro_goal = {
            "protein": parse_int(macro_from_meal_plan.get("protein"), smart_defaults["macronutrients"]["protein"]),
            "carbs": parse_int(macro_from_meal_plan.get("carbs"), smart_defaults["macronutrients"]["carbohydrates"]),
            "fat": parse_int(macro_from_meal_plan.get("fats"), smart_defaults["macronutrients"]["fat"])
        }
    else:
        macro_goal = {
            "protein": smart_defaults["macronutrients"]["protein"],
            "carbs": smart_defaults["macronutrients"]["carbohydrates"],
            "fat": smart_defaults["macronutrients"]["fat"]
        }

    # 3. (Future extensibility) Consider dietary info and physical activity for smarter defaults
    # For now, just use the above logic

    # 4. Get today's consumption records
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)
    query = (
        "SELECT c.nutritional_info FROM c WHERE c.type = 'consumption_record' "
        f"AND c.user_id = '{current_user['email']}' "
        f"AND c.timestamp >= '{today.isoformat()}' AND c.timestamp < '{tomorrow.isoformat()}'"
    )
    records = list(interactions_container.query_items(query=query, enable_cross_partition_query=True))
    today_totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
    for rec in records:
        ni = rec.get("nutritional_info", {})
        today_totals["calories"] += ni.get("calories", 0)
        today_totals["protein"] += ni.get("protein", 0)
        today_totals["carbs"] += ni.get("carbohydrates", 0)
        today_totals["fat"] += ni.get("fat", 0)

    # 5. Weekly and monthly averages (reuse analytics logic)
    weekly = await get_consumption_analytics(current_user["email"], days=7)
    monthly = await get_consumption_analytics(current_user["email"], days=30)

    def macro_avg(analytics):
        days = analytics.get("period_days", 1)
        return {
            "calories": round(analytics.get("total_calories", 0) / days, 1),
            "protein": round(analytics.get("total_macronutrients", {}).get("protein", 0) / days, 1),
            "carbs": round(analytics.get("total_macronutrients", {}).get("carbohydrates", 0) / days, 1),
            "fat": round(analytics.get("total_macronutrients", {}).get("fat", 0) / days, 1),
        }

    return {
        "goals": {
            "calories": calorie_goal,
            "protein": macro_goal["protein"],
            "carbs": macro_goal["carbs"],
            "fat": macro_goal["fat"]
        },
        "today": today_totals,
        "weekly_avg": macro_avg(weekly),
        "monthly_avg": macro_avg(monthly)
    }

def calculate_consistency_streak(consumption_history: list) -> int:
    """Calculate consistency streak based on daily logging patterns"""
    if not consumption_history:
        return 0
    
    from datetime import datetime, timedelta
    
    # Group consumption by date
    daily_logs = {}
    for record in consumption_history:
        try:
            record_date = datetime.fromisoformat(record.get("timestamp", "").replace("Z", "+00:00")).date()
            if record_date not in daily_logs:
                daily_logs[record_date] = 0
            daily_logs[record_date] += 1
        except:
            continue
    
    # Calculate streak from today backwards
    today = datetime.utcnow().date()
    streak = 0
    current_date = today
    
    # Check each day backwards
    for i in range(30):  # Check last 30 days max
        if current_date in daily_logs and daily_logs[current_date] >= 2:  # At least 2 meals logged
            streak += 1
        else:
            break  # Streak broken
        current_date -= timedelta(days=1)
    
    return streak

@app.get("/coach/daily-insights")
async def get_daily_coaching_insights(current_user: User = Depends(get_current_user)):
    """Get daily insights - USING ORIGINAL LOGIC with better integration"""
    try:
        print(f"[get_daily_insights] Getting insights for user {current_user['email']}")
        
        # Get user profile
        profile = current_user.get("profile", {})
        
        # Get recent meal plans
        try:
            recent_meal_plans = await get_user_meal_plans(current_user["email"])
            recent_meal_plans = recent_meal_plans[:3]
        except Exception as e:
            print(f"Error fetching meal plans for coaching insights: {e}")
            recent_meal_plans = []
        
        # Get recent consumption history (last 7 days) - USING ORIGINAL FUNCTION
        try:
            recent_consumption = await get_user_consumption_history(current_user["email"], limit=30)
            from datetime import datetime, timedelta
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            recent_consumption = [
                record for record in recent_consumption 
                if datetime.fromisoformat(record.get("timestamp", "").replace("Z", "+00:00")) > seven_days_ago
            ]
        except Exception as e:
            print(f"Error fetching consumption history for coaching insights: {e}")
            recent_consumption = []
        
        # Get today's consumption
        today = datetime.utcnow().date()
        tomorrow = today + timedelta(days=1)
        today_consumption = [
            record for record in recent_consumption
            if today <= datetime.fromisoformat(record.get("timestamp", "").replace("Z", "+00:00")).date() < tomorrow
        ]
        
        # Calculate today's totals - USING CONSISTENT FIELD NAMES
        today_totals = {"calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0, "fiber": 0, "sugar": 0, "sodium": 0}
        for record in today_consumption:
            nutritional_info = record.get("nutritional_info", {})
            today_totals["calories"] += nutritional_info.get("calories", 0)
            today_totals["protein"] += nutritional_info.get("protein", 0)
            today_totals["carbohydrates"] += nutritional_info.get("carbohydrates", nutritional_info.get("carbs", 0))  # Handle both field names
            today_totals["fat"] += nutritional_info.get("fat", 0)
            today_totals["fiber"] += nutritional_info.get("fiber", 0)
            today_totals["sugar"] += nutritional_info.get("sugar", 0)
            today_totals["sodium"] += nutritional_info.get("sodium", 0)
        
        # Get goals
        calorie_goal = 2000
        macro_goals = {"protein": 100, "carbohydrates": 250, "fat": 70}
        
        if profile.get("calorieTarget"):
            try:
                calorie_goal = int(profile["calorieTarget"])
            except:
                pass
        elif recent_meal_plans and recent_meal_plans[0].get("dailyCalories"):
            calorie_goal = recent_meal_plans[0]["dailyCalories"]
        
        if profile.get("macroGoals"):
            macro_goals.update(profile["macroGoals"])
        elif recent_meal_plans and recent_meal_plans[0].get("macronutrients"):
            macros = recent_meal_plans[0]["macronutrients"]
            macro_goals = {
                "protein": macros.get("protein", 100),
                "carbohydrates": macros.get("carbs", 250),
                "fat": macros.get("fats", 70)
            }
        
        # Calculate adherence percentages
        adherence = {
            "calories": min(100, (today_totals["calories"] / calorie_goal * 100)) if calorie_goal > 0 else 0,
            "protein": min(100, (today_totals["protein"] / macro_goals["protein"] * 100)) if macro_goals["protein"] > 0 else 0,
            "carbohydrates": min(100, (today_totals["carbohydrates"] / macro_goals["carbohydrates"] * 100)) if macro_goals["carbohydrates"] > 0 else 0,
            "fat": min(100, (today_totals["fat"] / macro_goals["fat"] * 100)) if macro_goals["fat"] > 0 else 0
        }
        
        # Enhanced diabetes score calculation based on multiple factors
        condition_suitable_count = 0
        total_recent_records = len(recent_consumption)
        weekly_calories = 0
        
        # Get user's health conditions
        user_conditions = profile.get("medicalConditions", []) or profile.get("medical_conditions", [])
        
        # Enhanced scoring factors
        diabetes_score_factors = {
            "high_suitability": 0,
            "medium_suitability": 0,
            "low_suitability": 0,
            "high_carb_meals": 0,
            "high_sugar_meals": 0,
            "processed_foods": 0,
            "healthy_choices": 0
        }
        
        for record in recent_consumption:
            # Access nutritional info properly
            nutritional_info = record.get("nutritional_info", {})
            weekly_calories += nutritional_info.get("calories", 0)
            
            # Get nutritional values
            carbs = nutritional_info.get("carbohydrates", 0)
            sugar = nutritional_info.get("sugar", 0)
            fiber = nutritional_info.get("fiber", 0)
            sodium = nutritional_info.get("sodium", 0)
            
            # Check medical rating
            medical_rating = record.get("medical_rating", {})
            diabetes_suitability = medical_rating.get("diabetes_suitability", "medium").lower()
            glycemic_impact = medical_rating.get("glycemic_impact", "medium").lower()
            
            # Score based on diabetes suitability
            if diabetes_suitability == "high":
                diabetes_score_factors["high_suitability"] += 1
                condition_suitable_count += 1
            elif diabetes_suitability == "medium":
                diabetes_score_factors["medium_suitability"] += 1
                condition_suitable_count += 0.7  # Partial credit
            else:
                diabetes_score_factors["low_suitability"] += 1
            
            # Penalize high carb meals (>45g carbs per meal)
            if carbs > 45:
                diabetes_score_factors["high_carb_meals"] += 1
            
            # Penalize high sugar meals (>15g sugar per meal)
            if sugar > 15:
                diabetes_score_factors["high_sugar_meals"] += 1
            
            # Penalize high sodium (>800mg per meal)
            if sodium > 800:
                diabetes_score_factors["processed_foods"] += 1
            
            # Reward healthy choices (high fiber, low glycemic)
            if fiber >= 5 and glycemic_impact == "low":
                diabetes_score_factors["healthy_choices"] += 1
        
        # Calculate enhanced diabetes score
        if total_recent_records > 0:
            base_score = (condition_suitable_count / total_recent_records * 100)
            
            # Apply penalties and bonuses
            carb_penalty = (diabetes_score_factors["high_carb_meals"] / total_recent_records) * 15
            sugar_penalty = (diabetes_score_factors["high_sugar_meals"] / total_recent_records) * 20
            processed_penalty = (diabetes_score_factors["processed_foods"] / total_recent_records) * 10
            healthy_bonus = (diabetes_score_factors["healthy_choices"] / total_recent_records) * 10
            
            health_adherence = max(0, min(100, base_score - carb_penalty - sugar_penalty - processed_penalty + healthy_bonus))
        else:
            # Default score for new users - show 0 until they have data
            health_adherence = 0
        
        # Generate coaching recommendations
        recommendations = []
        
        # Calorie recommendations
        if adherence["calories"] < 70:
            remaining_calories = calorie_goal - today_totals["calories"]
            recommendations.append({
                "type": "calorie_low",
                "priority": "medium",
                "message": f"You're {remaining_calories:.0f} calories below your goal. Consider adding a healthy snack or slightly larger portions.",
                "action": "increase_intake"
            })
        elif adherence["calories"] > 110:
            excess_calories = today_totals["calories"] - calorie_goal
            recommendations.append({
                "type": "calorie_high",
                "priority": "medium",
                "message": f"You're {excess_calories:.0f} calories over your goal. Consider lighter options for remaining meals.",
                "action": "reduce_intake"
            })
        else:
            recommendations.append({
                "type": "calorie_good",
                "priority": "low",
                "message": "Great job staying within your calorie target! 🎯",
                "action": "maintain"
            })
        
        # Protein recommendations
        if adherence["protein"] < 80:
            protein_needed = macro_goals["protein"] - today_totals["protein"]
            recommendations.append({
                "type": "protein_low",
                "priority": "medium",
                "message": f"You need {protein_needed:.0f}g more protein today. Try adding lean meats, eggs, or Greek yogurt.",
                "action": "add_protein"
            })
        
        # Carb recommendations
        if adherence["carbohydrates"] > 120:
            recommendations.append({
                "type": "carb_high",
                "priority": "high",
                "message": "Your carb intake is high today. Focus on low-carb options for remaining meals to help manage blood sugar.",
                "action": "reduce_carbs"
            })
        
        # Weekly performance feedback
        if health_adherence >= 80:
            recommendations.append({
                "type": "weekly_excellent",
                "priority": "low",
                "message": f"Excellent! {health_adherence:.0f}% of your recent meals were health-suitable for your conditions. You've earned a small treat! 🌟",
                "action": "reward"
            })
        elif health_adherence >= 60:
            recommendations.append({
                "type": "weekly_good",
                "priority": "low",
                "message": f"Good progress! {health_adherence:.0f}% health-suitable meals. Let's aim for 80%+ this week.",
                "action": "improve"
            })
        else:
            recommendations.append({
                "type": "weekly_needs_improvement",
                "priority": "high",
                "message": f"Only {health_adherence:.0f}% of recent meals were health-suitable for your conditions. Let's focus on better choices.",
                "action": "focus_improvement"
            })
        
        # Meal timing recommendations
        current_hour = datetime.utcnow().hour
        if current_hour < 10 and len([r for r in today_consumption if "breakfast" in r.get("food_name", "").lower()]) == 0:
            recommendations.append({
                "type": "breakfast_reminder",
                "priority": "medium",
                "message": "Don't forget breakfast! It's important for blood sugar stability throughout the day.",
                "action": "eat_breakfast"
            })
        
        insights = {
            "date": today.isoformat(),
            "goals": {
                "calories": calorie_goal,
                "protein": macro_goals["protein"],
                "carbohydrates": macro_goals["carbohydrates"],
                "fat": macro_goals["fat"]
            },
            "today_totals": today_totals,
            "adherence": adherence,
            "diabetes_adherence": health_adherence,  # Now represents overall health adherence
            "health_adherence": health_adherence,  # Add explicit health adherence field
            "health_conditions": user_conditions,  # Add user's health conditions
            "consistency_streak": calculate_consistency_streak(recent_consumption),
            "meals_logged_today": len(today_consumption),
            "weekly_stats": {
                "total_meals": total_recent_records,
                "diabetes_suitable_percentage": health_adherence,  # Now represents overall health adherence
                "health_suitable_percentage": health_adherence,
                "average_daily_calories": weekly_calories / 7 if weekly_calories > 0 else 0
            },
            "recommendations": recommendations,
            "has_meal_plan": len(recent_meal_plans) > 0,
            "latest_meal_plan_date": recent_meal_plans[0].get("created_at") if recent_meal_plans else None,
            # Add insights for the frontend
            "insights": [
                {
                    "category": "Daily Progress",
                    "message": f"You've logged {len(today_consumption)} meals today with {health_adherence:.0f}% health-suitable choices for your conditions: {', '.join(user_conditions[:2])}{'...' if len(user_conditions) > 2 else ''}.",
                    "action": "View Details"
                },
                {
                    "category": "Weekly Trend", 
                    "message": f"This week you've maintained {total_recent_records} meal logs with consistent tracking for your health management.",
                    "action": "Keep Going"
                },
                {
                    "category": "Health Focus",
                    "message": f"Your meal choices are {health_adherence:.0f}% aligned with recommendations for {', '.join(user_conditions[:2])}.",
                    "action": "Get Recommendations"
                }
            ] if len(today_consumption) > 0 else [
                {
                    "category": "Getting Started",
                    "message": f"Start logging your meals to get personalized AI insights for your health conditions: {', '.join(user_conditions)}!",
                    "action": "Log First Meal"
                }
            ]
        }
        
        print(f"[get_daily_insights] Generated insights successfully")
        
        return insights
        
    except Exception as e:
        print(f"[get_daily_insights] Error: {str(e)}")
        print(f"[get_daily_insights] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get daily insights: {str(e)}")

@app.post("/coach/quick-log")
async def quick_log_food(
    food_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Quick log food - USING ORIGINAL SAVE FUNCTION with better AI analysis"""
    try:
        print(f"[quick_log_food] Starting quick log for user {current_user['id']}")
        print(f"[quick_log_food] Food data received: {food_data}")
        
        food_name = food_data.get("food_name", "").strip()
        portion = food_data.get("portion", "medium portion").strip()
        
        if not food_name:
            raise HTTPException(status_code=400, detail="Food name is required")
        
        # Use AI to estimate nutritional values with comprehensive analysis
        prompt = f"""
        Analyze the food item: {food_name} ({portion})
        
        Provide a comprehensive JSON response with this exact structure:
        {{
            "food_name": "{food_name}",
            "estimated_portion": "{portion}",
            "nutritional_info": {{
                "calories": <number>,
                "carbohydrates": <number>,
                "protein": <number>,
                "fat": <number>,
                "fiber": <number>,
                "sugar": <number>,
                "sodium": <number>
            }},
            "medical_rating": {{
                "diabetes_suitability": "high/medium/low",
                "glycemic_impact": "low/medium/high",
                "recommended_frequency": "daily/weekly/occasional/avoid",
                "portion_recommendation": "appropriate/reduce/increase"
            }},
            "analysis_notes": "Brief explanation of nutritional value and diabetes considerations"
        }}
        
        Base estimates on standard nutritional databases. Be accurate and conservative with diabetes ratings.
        Only return valid JSON, no other text.
        """
        
        # Initialize fallback data
        fallback_data = {
            "food_name": food_name,
            "estimated_portion": portion,
            "nutritional_info": {
                "calories": 200,
                "carbohydrates": 25,
                "protein": 10,
                "fat": 8,
                "fiber": 3,
                "sugar": 5,
                "sodium": 300
            },
            "medical_rating": {
                "diabetes_suitability": "medium",
                "glycemic_impact": "medium",
                "recommended_frequency": "weekly",
                "portion_recommendation": "appropriate"
            },
            "analysis_notes": f"Nutritional estimate for {food_name}. Consult with healthcare provider for personalized advice."
        }
        
        try:
            print("[quick_log_food] Calling OpenAI for nutritional analysis")
            response = client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                messages=[
                    {
                        "role": "system",
                        "content": "You are a nutrition analysis expert specializing in diabetes management. Provide accurate nutritional estimates and diabetes-appropriate recommendations."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            # Parse AI response
            analysis_text = response.choices[0].message.content
            print(f"[quick_log_food] OpenAI response: {analysis_text}")
            
            try:
                # Extract JSON from response
                start_idx = analysis_text.find('{')
                end_idx = analysis_text.rfind('}') + 1
                json_str = analysis_text[start_idx:end_idx]
                analysis_data = json.loads(json_str)
                print(f"[quick_log_food] Successfully parsed AI analysis: {analysis_data}")
            except (json.JSONDecodeError, ValueError) as parse_error:
                print(f"[quick_log_food] JSON parsing error: {str(parse_error)}")
                analysis_data = fallback_data
                
        except Exception as openai_error:
            print(f"[quick_log_food] OpenAI API error: {str(openai_error)}. Using fallback estimation.")
            analysis_data = fallback_data
        
        # Prepare consumption data in the same format as the image analysis system
        consumption_data = {
            "food_name": analysis_data.get("food_name", food_name),
            "estimated_portion": analysis_data.get("estimated_portion", portion),
            "nutritional_info": analysis_data.get("nutritional_info", fallback_data["nutritional_info"]),
            "medical_rating": analysis_data.get("medical_rating", fallback_data["medical_rating"]),
            "image_analysis": analysis_data.get("analysis_notes", f"Quick log entry for {food_name}"),
            "image_url": None,  # No image for quick log
            "meal_type": (food_data.get("meal_type") or "snack").lower()
        }
        
        print(f"[quick_log_food] Prepared consumption data: {consumption_data}")
        
        # Save to consumption history using the ORIGINAL save function
        print(f"[quick_log_food] Saving consumption record for user {current_user['email']}")
        consumption_record = await save_consumption_record(current_user["email"], consumption_data, meal_type=food_data.get("meal_type", "snack"))
        print(f"[quick_log_food] Successfully saved consumption record with ID: {consumption_record['id']}")
        
        # ------------------------------
        # FORCE COMPLETE MEAL PLAN REGENERATION AFTER EVERY LOG
        # ------------------------------
        try:
            print("[quick_log_food] Triggering complete meal plan regeneration after food log...")
            
            # Get today's consumption including the new log
            today = datetime.utcnow().date()
            consumption_data_full = await get_user_consumption_history(current_user["email"], limit=100)
            today_consumption = [
                r for r in consumption_data_full
                if datetime.fromisoformat(r.get("timestamp", "").replace("Z", "+00:00")).date() == today
            ]
            
            # Calculate calories consumed so far
            calories_consumed = sum(r.get("nutritional_info", {}).get("calories", 0) for r in today_consumption)
            
            # Get user profile for dietary restrictions
            profile = current_user.get("profile", {})
            dietary_restrictions = profile.get('dietaryRestrictions', [])
            allergies = profile.get('allergies', [])
            diet_type = profile.get('dietType', [])
            target_calories = int(profile.get('calorieTarget', '2000'))
            remaining_calories = max(0, target_calories - calories_consumed)
            
            # Build explicit restriction warnings for AI
            restriction_warnings = []
            if 'vegetarian' in [r.lower() for r in dietary_restrictions] or 'vegetarian' in [d.lower() for d in diet_type]:
                restriction_warnings.append("STRICTLY VEGETARIAN - NO MEAT, POULTRY, FISH, OR SEAFOOD")
            if any('egg' in r.lower() for r in dietary_restrictions) or any('egg' in a.lower() for a in allergies):
                restriction_warnings.append("NO EGGS - Avoid all egg-based dishes and ingredients")
            if any('nut' in a.lower() for a in allergies):
                restriction_warnings.append("NUT ALLERGY - Avoid all nuts and nut-based products")
            
            restriction_text = "\n".join([f"⚠️ {warning}" for warning in restriction_warnings])
            
            # Generate completely new meal plan calibrated to consumption
            prompt = f"""You are a registered dietitian AI. The user just logged a meal. Generate a COMPLETE new meal plan for the REST OF TODAY based on their consumption and dietary profile.

USER PROFILE:
Diet Type: {', '.join(diet_type) or 'Standard'}
Dietary Restrictions: {', '.join(dietary_restrictions) or 'None'}
Allergies: {', '.join(allergies) or 'None'}
Target Daily Calories: {target_calories}
Calories Already Consumed Today: {calories_consumed}
Remaining Calories for Today: {remaining_calories}

{restriction_text if restriction_warnings else ""}

CRITICAL REQUIREMENTS:
- ALL dishes must be diabetes-friendly (low glycemic index)
- ALL dishes must be completely vegetarian and egg-free
- Adjust portion sizes based on remaining calories
- Provide SPECIFIC dish names, not generic descriptions
- Consider the time of day and what's realistic to eat

Generate a complete meal plan for the rest of today:

{{
  "meals": {{
    "breakfast": "<specific vegetarian dish without eggs>",
    "lunch": "<specific vegetarian dish without eggs>", 
    "dinner": "<specific vegetarian dish without eggs>",
    "snack": "<specific vegetarian snack without eggs>"
  }},
  "calibration_notes": "Adjusted based on {calories_consumed} calories already consumed today"
}}

Examples of appropriate dishes:
- Breakfast: "Steel-cut oats with almond milk, cinnamon, and fresh blueberries"
- Lunch: "Mediterranean quinoa salad with chickpeas, cucumber, and olive oil"
- Dinner: "Black bean and sweet potato curry with brown rice"
- Snack: "Apple slices with almond butter and a sprinkle of cinnamon"

Ensure ALL dishes are completely vegetarian and egg-free."""

            ai_resp = client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=600
            )

            import json as _json
            try:
                # Parse AI response
                ai_content = ai_resp.choices[0].message.content
                start_idx = ai_content.find('{')
                end_idx = ai_content.rfind('}') + 1
                ai_json = _json.loads(ai_content[start_idx:end_idx])
                
                # Create new calibrated meal plan
                new_plan = {
                    "id": f"calibrated_{current_user['email']}_{today.isoformat()}_{int(datetime.utcnow().timestamp())}",
                    "date": today.isoformat(),
                    "type": "ai_calibrated_post_log",
                    "meals": ai_json.get("meals", {}),
                    "dailyCalories": target_calories,
                    "calories_consumed": calories_consumed,
                    "calories_remaining": remaining_calories,
                    "created_at": datetime.utcnow().isoformat(),
                    "notes": f"Regenerated after food log. {ai_json.get('calibration_notes', '')}"
                }
                
                # Post-process to ensure dietary compliance (safety filter)
                def sanitize_meal(meal_text: str) -> str:
                    """Ensure meal is vegetarian and egg-free"""
                    meal_lower = meal_text.lower()
                    
                    # Check for non-vegetarian ingredients
                    non_veg_keywords = ['chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'turkey', 'lamb', 'meat', 'seafood', 'shrimp']
                    egg_keywords = ['egg', 'eggs', 'omelet', 'omelette', 'scrambled', 'poached', 'fried egg']
                    
                    if any(keyword in meal_lower for keyword in non_veg_keywords):
                        return "Vegetarian lentil and vegetable curry with quinoa"
                    if any(keyword in meal_lower for keyword in egg_keywords):
                        return "Overnight oats with almond milk, chia seeds, and fresh berries"
                    
                    return meal_text
                
                # Apply safety filter to all meals
                for meal_type in new_plan["meals"]:
                    new_plan["meals"][meal_type] = sanitize_meal(new_plan["meals"][meal_type])
                
                # Save the new calibrated plan
                await save_meal_plan(current_user["email"], new_plan)
                print(f"[quick_log_food] Generated and saved new calibrated meal plan. Remaining calories: {remaining_calories}")
                
            except Exception as parse_err:
                print(f"[quick_log_food] Failed to parse AI meal plan JSON: {parse_err}")
                # Fallback: just trigger the normal get_todays_meal_plan
                await get_todays_meal_plan(current_user)
                
        except Exception as plan_err:
            print(f"[quick_log_food] Failed to regenerate meal plan: {plan_err}")
            import traceback
            print(traceback.format_exc())
        
        # Return success response in the SAME FORMAT as before
        return {
            "success": True,
            "message": f"Successfully logged {analysis_data.get('food_name', food_name)}",
            "consumption_record_id": consumption_record["id"],
            "analysis": analysis_data,
            "food_name": analysis_data.get("food_name", food_name),
            "nutritional_summary": {
                "calories": analysis_data.get("nutritional_info", {}).get("calories", 0),
                "carbohydrates": analysis_data.get("nutritional_info", {}).get("carbohydrates", 0),
                "protein": analysis_data.get("nutritional_info", {}).get("protein", 0),
                "fat": analysis_data.get("nutritional_info", {}).get("fat", 0)
            },
            "diabetes_rating": analysis_data.get("medical_rating", {}).get("diabetes_suitability", "medium")
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"[quick_log_food] Unexpected error: {str(e)}")
        print(f"[quick_log_food] Full error details:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to log food item: {str(e)}")

@app.get("/coach/todays-meal-plan")
async def get_todays_meal_plan(current_user: User = Depends(get_current_user)):
    """
    Get today's adaptive meal plan based on recent consumption and health conditions.
    Returns the most recent meal plan or creates a new one if needed.
    """
    try:
        print(f"[get_todays_meal_plan] Getting today's meal plan for user {current_user['email']}")
        
        # Fetch user's meal plan history
        meal_plans = await get_user_meal_plans(current_user["email"])
        
        # Today's date helper
        today = datetime.utcnow().date()
        
        # Start with no plan selected
        todays_plan = None

        # Try to find a plan explicitly dated today
        for plan in meal_plans:
            plan_date = plan.get("date")
            if plan_date:
                try:
                    if datetime.fromisoformat(plan_date).date() == today:
                        todays_plan = plan
                        break
                except Exception:
                    continue
        
        # If still none, derive today's meals from the most recent saved plan
        if not todays_plan and meal_plans:
            # Choose the most recent plan that actually contains array-style meals
            latest_plan = None
            for p in meal_plans:
                if isinstance(p.get("breakfast"), list) and isinstance(p.get("lunch"), list):
                    latest_plan = p
                    break
            if latest_plan is None:
                latest_plan = meal_plans[0]
            
            # Helper to safely pull meal array/string for index
            def _pick(meal_key: str):
                val = latest_plan.get(meal_key)
                if isinstance(val, list):
                    return val[today.weekday()] if today.weekday() < len(val) else (val[0] if val else "")
                return val or ""

            derived_meals = {
                "breakfast": _pick("breakfast"),
                "lunch": _pick("lunch"),
                "dinner": _pick("dinner"),
                "snack": _pick("snacks") or _pick("snack")
            }

            todays_plan = {
                "id": f"derived_{latest_plan.get('id', 'plan')}_{today.isoformat()}",
                "date": today.isoformat(),
                "type": "derived_from_latest",
                "health_conditions": latest_plan.get("health_conditions", []),
                "meals": derived_meals,
                "dailyCalories": latest_plan.get("dailyCalories"),
                "macronutrients": latest_plan.get("macronutrients", {}),
                "created_at": datetime.utcnow().isoformat(),
                "notes": "Pulled from your most recent saved meal plan."
            }

        # Final safety: if after all previous steps todays_plan is still None, create minimal fallback
        if not todays_plan:
            todays_plan = {
                "id": f"fallback_{current_user['email']}_{today.isoformat()}",
            "date": today.isoformat(),
                "type": "fallback_basic",
                "meals": {
                    "breakfast": "Oatmeal with berries",
                    "lunch": "Mixed green salad with chickpeas",
                    "dinner": "Grilled vegetables with quinoa",
                    "snack": "Apple slices with peanut butter"
                },
                "created_at": datetime.utcnow().isoformat(),
                "notes": "Generic fallback meal plan."
            }

        # --------------
        # NORMALIZE MEAL-PLAN SHAPE FOR FRONTEND
        # --------------
        
        # Ensure function defined before use remains unchanged
        
        def _ensure_meals_dict(plan: dict, today_idx: int):
            """Convert legacy meal-plan keys (breakfast, lunch, dinner, snacks arrays) into
            the new shape { 'meals': { breakfast: str, lunch: str, dinner: str, snack: str } } expected by the dashboard."""
            if not plan:
                return plan
            if "meals" in plan and isinstance(plan["meals"], dict):
                return plan  # already in new format

            meals_dict = {}

            # Helper to pull either string or array element
            def _extract(meal_key_plural: str):
                val = plan.get(meal_key_plural)
                if isinstance(val, list):
                    return val[today_idx] if today_idx < len(val) else (val[0] if val else "")
                return val or ""

            meals_dict["breakfast"] = _extract("breakfast")
            meals_dict["lunch"] = _extract("lunch")
            meals_dict["dinner"] = _extract("dinner")
            snack_val = _extract("snacks") or _extract("snack")

            # If snack still empty, create a quick smart fallback based on dietary restrictions
            if not snack_val:
                # Basic smart logic: pick a diabetes-friendly, vegetarian-friendly default
                snack_val = "Apple slices with almond butter (fiber + protein)"

                # Further tweak if user has nut allergy noted in plan/profile
                allergies_list = current_user.get("profile", {}).get("allergies", [])
                if any("nut" in a.lower() for a in allergies_list):
                    snack_val = "Greek yogurt with fresh berries (low GI)"

            meals_dict["snack"] = snack_val

            plan["meals"] = meals_dict
            return plan

        todays_plan = _ensure_meals_dict(todays_plan, today.weekday())

        # Check if any meals are placeholders and generate concrete ones if needed
        if todays_plan and todays_plan.get("meals"):
            def _looks_placeholder(text: str) -> bool:
                return any(keyword in text.lower() for keyword in ["healthy", "balanced", "nutritious", "option", "_"]) # Added _ to catch empty strings

            needs_generation = any(
                _looks_placeholder(meal)
                for meal in todays_plan["meals"].values()
            )
            
            if needs_generation:
                print(f"[get_todays_meal_plan] Placeholder meals detected in today's plan – generating concrete recipes via OpenAI…")

                profile = current_user.get("profile", {})
                
                # Use existing meals as a base for generation, fill in missing with generic prompts
                current_meals = todays_plan["meals"]
                breakfast_prompt = current_meals.get("breakfast", "a healthy breakfast option")
                lunch_prompt = current_meals.get("lunch", "a balanced lunch option")
                dinner_prompt = current_meals.get("dinner", "a nutritious dinner option")
                snack_prompt = current_meals.get("snack", "a healthy snack option")

                # Construct a more detailed prompt for the AI with stronger dietary enforcement
                dietary_restrictions = profile.get('dietaryRestrictions', [])
                allergies = profile.get('allergies', [])
                diet_type = profile.get('dietType', [])
                
                # Build explicit restriction warnings
                restriction_warnings = []
                if 'vegetarian' in [r.lower() for r in dietary_restrictions] or 'vegetarian' in [d.lower() for d in diet_type]:
                    restriction_warnings.append("STRICTLY VEGETARIAN - NO MEAT, POULTRY, FISH, OR SEAFOOD")
                if any('egg' in r.lower() for r in dietary_restrictions) or any('egg' in a.lower() for a in allergies):
                    restriction_warnings.append("NO EGGS - Avoid all egg-based dishes and ingredients")
                if any('nut' in a.lower() for a in allergies):
                    restriction_warnings.append("NUT ALLERGY - Avoid all nuts and nut-based products")
                
                restriction_text = "\n".join([f"⚠️ {warning}" for warning in restriction_warnings])
                
                prompt = f"""You are a registered dietitian AI. Generate specific, concrete dish names for each meal (breakfast, lunch, dinner, snack) for TODAY, given the user's profile and dietary needs.

USER PROFILE:
Diet Type: {', '.join(diet_type) or 'Standard'}
Dietary Restrictions: {', '.join(dietary_restrictions) or 'None'}
Allergies: {', '.join(allergies) or 'None'}
Health Conditions: {', '.join(profile.get('medical_conditions', [])) or 'None'}

{restriction_text if restriction_warnings else ""}

CRITICAL REQUIREMENTS:
- ALL dishes must be diabetes-friendly (low glycemic index)
- ALL dishes must strictly adhere to dietary restrictions and allergies
- Provide SPECIFIC dish names, not generic descriptions
- Each meal should be balanced and nutritious

Existing Plan (replace placeholders with specific dishes):
Breakfast: {breakfast_prompt}
Lunch: {lunch_prompt}
Dinner: {dinner_prompt}
Snack: {snack_prompt}

Provide JSON exactly in this format, with specific dish names only:
{{
  "meals": {{
    "breakfast": "<specific vegetarian dish name without eggs>",
    "lunch": "<specific vegetarian dish name without eggs>",
    "dinner": "<specific vegetarian dish name without eggs>",
    "snack": "<specific vegetarian snack without eggs>"
  }}
}}

Examples of appropriate dishes:
- Breakfast: "Overnight oats with almond milk, chia seeds, and fresh berries"
- Lunch: "Quinoa Buddha bowl with roasted vegetables and tahini dressing"
- Dinner: "Lentil curry with brown rice and steamed broccoli"
- Snack: "Hummus with cucumber slices and whole grain crackers"

Ensure ALL dishes are completely vegetarian and egg-free. Do not include any meat, poultry, fish, seafood, or egg-based ingredients."""

                try:
                    ai_resp = client.chat.completions.create(
                        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7, # Slightly higher temperature for more creativity
                        max_tokens=500
                    )

                    import json as _json
                    ai_json = _json.loads(ai_resp.choices[0].message.content)
                    
                    # Update only the meals that were placeholders or needed refinement
                    updated_meals = ai_json.get("meals", {})
                    
                    # Post-process to ensure dietary compliance (safety filter)
                    def sanitize_meal(meal_text: str) -> str:
                        """Ensure meal is vegetarian and egg-free"""
                        meal_lower = meal_text.lower()
                        
                        # Check for non-vegetarian ingredients
                        non_veg_keywords = ['chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'turkey', 'lamb', 'meat', 'seafood', 'shrimp']
                        egg_keywords = ['egg', 'eggs', 'omelet', 'omelette', 'scrambled', 'poached', 'fried egg']
                        
                        if any(keyword in meal_lower for keyword in non_veg_keywords):
                            return "Vegetarian lentil and vegetable curry with quinoa"
                        if any(keyword in meal_lower for keyword in egg_keywords):
                            return "Overnight oats with almond milk, chia seeds, and fresh berries"
                        
                        return meal_text
                    
                    for meal_type, dish_name in updated_meals.items():
                        if _looks_placeholder(current_meals.get(meal_type, "")) or dish_name != current_meals.get(meal_type, ""):
                            # Apply safety filter before saving
                            todays_plan["meals"][meal_type] = sanitize_meal(dish_name)

                    todays_plan["type"] = "ai_generated_concrete"
                    todays_plan["notes"] = (todays_plan.get("notes", "") + " Meals made concrete by AI with dietary compliance.").strip()

                    # Save the updated plan to history
                    await save_meal_plan(current_user["email"], todays_plan)
                    print("[get_todays_meal_plan] Saved AI-generated concrete meals for today.")
                except Exception as gen_err:
                    print(f"[get_todays_meal_plan] Error during concrete meal generation or parsing: {gen_err}")
                    import traceback
                    print(traceback.format_exc())

        # ------------------
        # REAL-TIME CALIBRATION (same-day)
        # ------------------
        try:
            consumption_data_full = await get_user_consumption_history(current_user["email"], limit=100)
            today_consumption_full = [
                r for r in consumption_data_full
                if datetime.fromisoformat(r.get("timestamp", "").replace("Z", "+00:00")).date() == today
            ]

            # Sum calories eaten so far
            calories_so_far = sum(r.get("nutritional_info", {}).get("calories", 0) for r in today_consumption_full)

            calorie_goal_day = todays_plan.get("dailyCalories") or 0
            if calorie_goal_day > 0:
                remaining = calorie_goal_day - calories_so_far

                # If the user already exceeded the daily goal, lighten upcoming meals
                if remaining < -100:
                    if "lunch" in todays_plan.get("meals", {}):
                        todays_plan["meals"]["lunch"] += " (lighter portion recommended)"
                    if "dinner" in todays_plan.get("meals", {}):
                        todays_plan["meals"]["dinner"] += " (lighter portion recommended)"
                    if "snack" in todays_plan.get("meals", {}):
                        todays_plan["meals"]["snack"] += " (optional if still hungry)"

                    note = "Adjusted lunch/dinner due to higher calories consumed earlier today."
                    todays_plan["notes"] = f"{todays_plan.get('notes', '')} {note}".strip()

                # Positive reinforcement when following plan (within ±10% at mealtime)
                elif 0 <= remaining <= calorie_goal_day * 0.1:
                    note = "Great job sticking close to the plan so far! Keep it up."
                    todays_plan["notes"] = f"{todays_plan.get('notes', '')} {note}".strip()

                # If user is significantly below target, suggest a slightly larger upcoming meal or an extra snack
                elif remaining > calorie_goal_day * 0.2:
                    if "snack" in todays_plan.get("meals", {}):
                        if "optional" in todays_plan["meals"]["snack"].lower(): # Remove optional note if previously added
                             todays_plan["meals"]["snack"] = todays_plan["meals"]["snack"].replace(" (optional if still hungry)", "").strip()

                        todays_plan["meals"]["snack"] += " (recommended)"
                    elif "dinner" in todays_plan.get("meals", {}):
                        todays_plan["meals"]["dinner"] += " (slightly larger portion recommended)"
                    
                    note = "Consider a slightly larger portion or an extra snack to meet your calorie goals."
                    todays_plan["notes"] = f"{todays_plan.get('notes', '')} {note}".strip()

            # If plan has a 'type' of 'ai_generated_today' or 'ai_generated_concrete', it means it was just generated or refined
            # In this case, we don't need to explicitly save it again here if it was already saved during generation.
            # But if it was a derived/fallback plan that just got calibrated, save it.
            if todays_plan.get("type") not in ["ai_generated_today", "ai_generated_concrete"] and calories_so_far > 0: # Only save if consumption has happened and it's not a fresh AI gen
                 # Generate a unique ID for this calibrated plan if it's not already saved
                if "id" not in todays_plan or todays_plan["id"].startswith("derived_") or todays_plan["id"].startswith("fallback_"):
                    todays_plan["id"] = f"calibrated_{current_user['email']}_{today.isoformat()}_{int(datetime.utcnow().timestamp())}"
                    todays_plan["created_at"] = datetime.utcnow().isoformat()
                
                todays_plan["type"] = "calibrated_daily"
                await save_meal_plan(current_user["email"], todays_plan)
                print("[get_todays_meal_plan] Saved calibrated meal plan for today.")

        except Exception as e:
            print(f"[get_todays_meal_plan] Calibration error: {e}")

        # FORCE VEGETARIAN MEAL GENERATION - Don't use old plans that may contain non-vegetarian dishes
        profile = current_user.get("profile", {})
        dietary_restrictions = profile.get('dietaryRestrictions', [])
        allergies = profile.get('allergies', [])
        diet_type = profile.get('dietType', [])
        
        # Check if user is vegetarian or has egg restrictions
        is_vegetarian = 'vegetarian' in [r.lower() for r in dietary_restrictions] or 'vegetarian' in [d.lower() for d in diet_type]
        no_eggs = any('egg' in r.lower() for r in dietary_restrictions) or any('egg' in a.lower() for a in allergies)
        
        # Always generate fresh vegetarian meals for users with dietary restrictions
        if is_vegetarian or no_eggs:
            print(f"[get_todays_meal_plan] User has dietary restrictions - generating fresh vegetarian meal plan")
            
            # Generate completely fresh vegetarian meal plan
            restriction_warnings = []
            if is_vegetarian:
                restriction_warnings.append("STRICTLY VEGETARIAN - NO MEAT, POULTRY, FISH, OR SEAFOOD")
            if no_eggs:
                restriction_warnings.append("NO EGGS - Avoid all egg-based dishes and ingredients")
            if any('nut' in a.lower() for a in allergies):
                restriction_warnings.append("NUT ALLERGY - Avoid all nuts and nut-based products")
            
            restriction_text = "\n".join([f"⚠️ {warning}" for warning in restriction_warnings])
            
            prompt = f"""You are a registered dietitian AI. Generate a complete daily meal plan for TODAY that is diabetes-friendly and strictly adheres to dietary restrictions.

USER PROFILE:
Diet Type: {', '.join(diet_type) or 'Standard'}
Dietary Restrictions: {', '.join(dietary_restrictions) or 'None'}
Allergies: {', '.join(allergies) or 'None'}

{restriction_text if restriction_warnings else ""}

CRITICAL REQUIREMENTS:
- ALL dishes must be diabetes-friendly (low glycemic index)
- ALL dishes must be completely vegetarian and egg-free
- Provide SPECIFIC dish names, not generic descriptions
- Each meal should be balanced and nutritious

Generate a complete meal plan for today:

{{
  "meals": {{
    "breakfast": "<specific vegetarian dish without eggs>",
    "lunch": "<specific vegetarian dish without eggs>",
    "dinner": "<specific vegetarian dish without eggs>",
    "snack": "<specific vegetarian snack without eggs>"
  }}
}}

Examples of appropriate dishes:
- Breakfast: "Steel-cut oats with almond milk, cinnamon, and fresh blueberries"
- Lunch: "Mediterranean quinoa salad with chickpeas, cucumber, and olive oil"
- Dinner: "Black bean and sweet potato curry with brown rice"
- Snack: "Apple slices with almond butter"

Ensure ALL dishes are completely vegetarian and egg-free."""

            try:
                ai_resp = client.chat.completions.create(
                    model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=500
                )

                import json as _json
                ai_content = ai_resp.choices[0].message.content
                start_idx = ai_content.find('{')
                end_idx = ai_content.rfind('}') + 1
                ai_json = _json.loads(ai_content[start_idx:end_idx])
                
                # Apply safety filter to ensure compliance
                def sanitize_meal(meal_text: str) -> str:
                    """Ensure meal is vegetarian and egg-free"""
                    meal_lower = meal_text.lower()
                    
                    # Check for non-vegetarian ingredients
                    non_veg_keywords = ['chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'turkey', 'lamb', 'meat', 'seafood', 'shrimp']
                    egg_keywords = ['egg', 'eggs', 'omelet', 'omelette', 'scrambled', 'poached', 'fried egg']
                    
                    if any(keyword in meal_lower for keyword in non_veg_keywords):
                        return "Vegetarian lentil and vegetable curry with quinoa"
                    if any(keyword in meal_lower for keyword in egg_keywords):
                        return "Overnight oats with almond milk, chia seeds, and fresh berries"
                    
                    return meal_text
                
                # Apply safety filter to all meals
                safe_meals = {}
                for meal_type, dish in ai_json.get("meals", {}).items():
                    safe_meals[meal_type] = sanitize_meal(dish)
                
                # Clean up any repetitive notes in meal names
                for meal_type in safe_meals:
                    meal_text = safe_meals[meal_type]
                    # Remove repetitive "(recommended)" text
                    meal_text = meal_text.replace(" (recommended) (recommended)", " (recommended)")
                    meal_text = meal_text.replace(" (recommended) (recommended) (recommended)", " (recommended)")
                    meal_text = meal_text.replace(" (recommended) (recommended) (recommended) (recommended)", " (recommended)")
                    safe_meals[meal_type] = meal_text
                
                todays_plan = {
                    "id": f"fresh_vegetarian_{current_user['email']}_{today.isoformat()}",
                    "date": today.isoformat(),
                    "type": "fresh_vegetarian_generated",
                    "meals": safe_meals,
                    "dailyCalories": int(profile.get('calorieTarget', '2000')),
                    "created_at": datetime.utcnow().isoformat(),
                    "notes": ""  # Clean notes - no repetitive text
                }
                
                print(f"[get_todays_meal_plan] Generated fresh vegetarian meal plan: {safe_meals}")
                
            except Exception as gen_err:
                print(f"[get_todays_meal_plan] Error generating fresh vegetarian plan: {gen_err}")
                # Fallback to safe vegetarian meals
                todays_plan = {
                    "id": f"fallback_vegetarian_{current_user['email']}_{today.isoformat()}",
                    "date": today.isoformat(),
                    "type": "fallback_vegetarian",
                    "meals": {
                        "breakfast": "Steel-cut oats with almond milk and fresh berries",
                        "lunch": "Quinoa Buddha bowl with roasted vegetables and tahini",
                        "dinner": "Lentil curry with brown rice and steamed broccoli",
                        "snack": "Apple slices with almond butter"
                    },
                    "dailyCalories": int(profile.get('calorieTarget', '2000')),
                    "created_at": datetime.utcnow().isoformat(),
                    "notes": ""  # Clean notes
                }
        
        # If no plan generated yet, use fallback
        if not todays_plan:
            todays_plan = {
                "id": f"fallback_{current_user['email']}_{today.isoformat()}",
                "date": today.isoformat(),
                "type": "fallback_basic",
                "meals": {
                    "breakfast": "Steel-cut oats with almond milk and fresh berries",
                    "lunch": "Quinoa Buddha bowl with roasted vegetables and tahini",
                    "dinner": "Lentil curry with brown rice and steamed broccoli",
                    "snack": "Apple slices with almond butter"
                },
                "dailyCalories": 2000,
                "created_at": datetime.utcnow().isoformat(),
                "notes": ""
            }

        # Clean up any duplicate "(recommended)" tags that may have accumulated
        for _meal_key, _meal_text in todays_plan.get("meals", {}).items():
            while " (recommended) (recommended)" in _meal_text:
                _meal_text = _meal_text.replace(" (recommended) (recommended)", " (recommended)")
            todays_plan["meals"][_meal_key] = _meal_text

        return todays_plan
    except HTTPException:
        raise
    except Exception as e:
        print(f"[get_todays_meal_plan] Unexpected error: {str(e)}")
        print(f"[get_todays_meal_plan] Full error details:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to retrieve or generate meal plan: {str(e)}")


@app.post("/coach/adaptive-meal-plan")
async def create_adaptive_meal_plan(
    payload: dict = Body(None),
    current_user: User = Depends(get_current_user)
):
    """
    Create an adaptive meal plan based on user's consumption history and preferences.
    Uses existing database functions instead of direct MongoDB queries.
    """
    try:
        # Parse quick-action options sent from the client (may be null)
        req_days = int(payload.get("days", 7)) if payload else 7
        req_cuisine = payload.get("cuisine_type", "") if payload else ""

        # Get user's consumption history using existing function
        consumption_history = await get_user_consumption_history(current_user["email"], limit=100)
        
        # Get user's meal plan history using existing function
        meal_plan_history = await get_user_meal_plans(current_user["email"])
        
        # Get user profile for preferences
        user_profile = current_user.get("profile", {})
        
        # Analyze consumption patterns
        favorite_foods = {}
        total_meals = len(consumption_history)
        diabetes_friendly_count = 0
        total_calories = 0
        total_carbs = 0
        total_protein = 0
        
        # Filter to last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_consumption = []
        
        for entry in consumption_history:
            try:
                entry_date = datetime.fromisoformat(entry.get("timestamp", "").replace("Z", "+00:00"))
                if entry_date >= thirty_days_ago:
                    recent_consumption.append(entry)
            except:
                continue
        
        for entry in recent_consumption:
            food_name = entry.get("food_name", "").lower()
            favorite_foods[food_name] = favorite_foods.get(food_name, 0) + 1
            
            # Get nutritional info
            nutrition = entry.get("nutritional_info", {})
            total_calories += nutrition.get("calories", 0)
            total_carbs += nutrition.get("carbohydrates", 0)
            total_protein += nutrition.get("protein", 0)
            
            # Check diabetes suitability
            medical_rating = entry.get("medical_rating", {})
            diabetes_suitability = medical_rating.get("diabetes_suitability", "").lower()
            if diabetes_suitability in ["high", "good", "suitable"]:
                diabetes_friendly_count += 1
        
        # Calculate metrics
        total_recent_meals = len(recent_consumption)
        adherence_rate = (diabetes_friendly_count / total_recent_meals * 100) if total_recent_meals > 0 else 0
        avg_daily_calories = (total_calories / 30) if total_calories > 0 else 2000
        
        # Get top favorite foods
        top_favorites = sorted(favorite_foods.items(), key=lambda x: x[1], reverse=True)[:10]
        favorite_foods_list = [food for food, count in top_favorites]
        
        # Get user preferences
        dietary_restrictions = user_profile.get("dietaryRestrictions", [])
        food_preferences = user_profile.get("foodPreferences", [])
        allergies = user_profile.get("allergies", [])
        calorie_target = user_profile.get("calorieTarget", "2000")
        
        try:
            target_calories = int(calorie_target)
        except:
            target_calories = int(avg_daily_calories) if avg_daily_calories > 1200 else 2000
        
        # Create adaptive meal plan prompt
        prompt = f"""Create a personalized {req_days}-day diabetes-friendly meal plan based on this user's analysis:
        
USER ANALYSIS:
- Total recent meals logged: {total_recent_meals}
        - Diabetes adherence rate: {adherence_rate:.1f}%
- Average daily calories: {avg_daily_calories:.0f}
- Target daily calories: {target_calories}
        - Favorite foods: {', '.join(favorite_foods_list[:5]) if favorite_foods_list else 'None identified'}
        
USER PREFERENCES:
- Dietary restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}
- Food preferences: {', '.join(food_preferences) if food_preferences else 'None'}
- Allergies: {', '.join(allergies) if allergies else 'None'}

REQUIREMENTS:
1. Create a diabetes-friendly meal plan with {target_calories} calories per day
2. Incorporate user's favorite foods where diabetes-appropriate
3. Respect all dietary restrictions and allergies
4. Focus on low glycemic index foods
5. Balance macronutrients appropriately for diabetes
6. Include variety and meal prep efficiency
7. Provide specific adaptations based on user's eating patterns

Provide a JSON response with this exact structure:
{{
    "plan_name": "Adaptive Diabetes Plan - {datetime.now().strftime('%Y-%m-%d')}",
            "duration_days": {req_days},
    "dailyCalories": {target_calories},
    "macronutrients": {{"protein": {int(target_calories * 0.2 / 4)}, "carbs": {int(target_calories * 0.45 / 4)}, "fats": {int(target_calories * 0.35 / 9)}}},
    "breakfast": ["Day 1: [specific breakfast with portions]", "Day 2: [specific breakfast with portions]", "Day 3: [specific breakfast with portions]", "Day 4: [specific breakfast with portions]", "Day 5: [specific breakfast with portions]", "Day 6: [specific breakfast with portions]", "Day 7: [specific breakfast with portions]"],
    "lunch": ["Day 1: [specific lunch with portions]", "Day 2: [specific lunch with portions]", "Day 3: [specific lunch with portions]", "Day 4: [specific lunch with portions]", "Day 5: [specific lunch with portions]", "Day 6: [specific lunch with portions]", "Day 7: [specific lunch with portions]"],
    "dinner": ["Day 1: [specific dinner with portions]", "Day 2: [specific dinner with portions]", "Day 3: [specific dinner with portions]", "Day 4: [specific dinner with portions]", "Day 5: [specific dinner with portions]", "Day 6: [specific dinner with portions]", "Day 7: [specific dinner with portions]"],
    "snacks": ["Day 1: [specific snack]", "Day 2: [specific snack]", "Day 3: [specific snack]", "Day 4: [specific snack]", "Day 5: [specific snack]", "Day 6: [specific snack]", "Day 7: [specific snack]"],
    "adaptations": ["Based on your {adherence_rate:.0f}% diabetes adherence rate, this plan focuses on [specific adaptations]", "Incorporated your favorite foods: {', '.join(favorite_foods_list[:3]) if favorite_foods_list else 'general healthy options'}", "Adjusted calories from your average {avg_daily_calories:.0f} to target {target_calories}"],
    "coaching_notes": "This adaptive plan is personalized based on your eating patterns over the last 30 days. [Add specific coaching based on adherence rate and patterns]"
}}

Make each meal specific with exact portions and cooking methods. Ensure all 7 days are included for each meal type."""
        
        try:
            response = client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                messages=[
                    {
                        "role": "system",
                        "content": "You are a diabetes nutrition specialist. Create practical, specific meal plans that are diabetes-friendly and personalized to the user's history."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            # Parse AI response
            ai_content = response.choices[0].message.content
            # Extract JSON from response
            start_idx = ai_content.find('{')
            end_idx = ai_content.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                json_str = ai_content[start_idx:end_idx]
                meal_plan_data = json.loads(json_str)
            else:
                raise json.JSONDecodeError("No JSON found", ai_content, 0)
                
        except Exception as ai_error:
            print(f"AI generation error: {str(ai_error)}. Using fallback meal plan.")
            # Comprehensive fallback meal plan
            meal_plan_data = {
                "plan_name": f"Adaptive Diabetes Plan - {datetime.now().strftime('%Y-%m-%d')}",
                "duration_days": {req_days},
                "dailyCalories": target_calories,
                "macronutrients": {"protein": int(target_calories * 0.2 / 4), "carbs": int(target_calories * 0.45 / 4), "fats": int(target_calories * 0.35 / 9)},
                "breakfast": [
                    "Day 1: Greek yogurt (1 cup) with berries (1/2 cup) and almonds (1 oz)",
                    "Day 2: Oatmeal (1/2 cup dry) with cinnamon and walnuts (1 tbsp)",
                    "Day 3: Scrambled eggs (2) with spinach and whole grain toast (1 slice)",
                    "Day 4: Smoothie with protein powder, spinach, and berries",
                    "Day 5: Cottage cheese (1 cup) with cucumber and tomatoes",
                    "Day 6: Avocado toast (1 slice) with poached egg",
                    "Day 7: Chia pudding with unsweetened almond milk and berries"
                ],
                "lunch": [
                    "Day 1: Grilled chicken salad (4 oz) with mixed greens and olive oil dressing",
                    "Day 2: Lentil soup (1 cup) with side salad",
                    "Day 3: Turkey and avocado wrap in whole grain tortilla",
                    "Day 4: Quinoa bowl with roasted vegetables and chickpeas",
                    "Day 5: Salmon (4 oz) with steamed broccoli and brown rice (1/3 cup)",
                    "Day 6: Vegetable stir-fry with tofu and cauliflower rice",
                    "Day 7: Bean and vegetable soup with whole grain roll"
                ],
                "dinner": [
                    "Day 1: Baked cod (5 oz) with roasted Brussels sprouts and sweet potato",
                    "Day 2: Lean beef stir-fry with bell peppers and brown rice",
                    "Day 3: Grilled chicken breast with asparagus and quinoa",
                    "Day 4: Baked salmon with roasted vegetables",
                    "Day 5: Turkey meatballs with zucchini noodles and marinara",
                    "Day 6: Pork tenderloin with roasted cauliflower and green beans",
                    "Day 7: Vegetarian chili with side of mixed greens"
                ],
                "snacks": [
                    "Day 1: Apple slices with almond butter (1 tbsp)",
                    "Day 2: Handful of mixed nuts (1 oz)",
                    "Day 3: Celery sticks with hummus (2 tbsp)",
                    "Day 4: Greek yogurt (1/2 cup) with cinnamon",
                    "Day 5: Hard-boiled egg with cucumber slices",
                    "Day 6: Berries (1/2 cup) with cottage cheese",
                    "Day 7: Vegetable sticks with guacamole"
                ],
                "adaptations": [
                    f"Based on your {adherence_rate:.0f}% diabetes adherence rate, this plan emphasizes low-glycemic foods",
                    f"Incorporated your eating patterns from {total_recent_meals} recent meals",
                    f"Adjusted from your average {avg_daily_calories:.0f} calories to target {target_calories} calories"
                ],
                "coaching_notes": f"This adaptive plan is based on your consumption history. Your {adherence_rate:.0f}% diabetes adherence rate shows {'excellent' if adherence_rate >= 80 else 'good' if adherence_rate >= 60 else 'room for improvement'} progress. Focus on consistent meal timing and portion control."
            }
        
        # Save to database using existing function
        meal_plan_data.update({
            "user_id": current_user["email"],  # Use email as user_id for consistency
            "created_at": datetime.utcnow().isoformat(),
            "plan_type": "adaptive",
            "user_adherence_rate": adherence_rate,
            "based_on_meals": total_recent_meals,
            "favorite_foods_incorporated": favorite_foods_list[:5]
        })
        
        # Save using existing database function
        saved_plan = await save_meal_plan(current_user["email"], meal_plan_data)
        
        return {
            "success": True,
            "meal_plan": meal_plan_data,
            "analysis": {
                "total_meals_analyzed": total_recent_meals,
                "adherence_rate": round(adherence_rate, 1),
                "favorite_foods": favorite_foods_list[:5],
                "adaptations_made": len(meal_plan_data.get("adaptations", [])),
                "avg_daily_calories": round(avg_daily_calories, 0),
                "target_calories": target_calories
            },
            "message": "Adaptive meal plan created successfully based on your consumption history!"
        }
        
    except Exception as e:
        print(f"Error creating adaptive meal plan: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to create adaptive meal plan: {str(e)}")

    # --- Post-filter to enforce vegetarian / egg-free etc. (extra safety) ---
    banned_keywords = []
    restrictions_lower = [r.lower() for r in dietary_restrictions]
    if "vegetarian" in restrictions_lower or "ovo-vegetarian" not in restrictions_lower:
        banned_keywords += ["chicken", "beef", "pork", "fish", "salmon", "tuna", "shrimp", "cod", "turkey", "lamb", "steak"]
    if any(keyword in restrictions_lower for keyword in ["no eggs", "egg-free", "no egg", "vegetarian"]):
        banned_keywords += ["egg", "eggs", "omelet", "omelette", "scrambled eggs", "poached egg"]

    def sanitize(meal: str) -> str:
        lower = meal.lower()
        if any(bk in lower for bk in banned_keywords):
            return "Vegetarian alternative meal"
        return meal

    for mt in ["breakfast", "lunch", "dinner", "snacks"]:
        if isinstance(meal_plan_data.get(mt), list):
            meal_plan_data[mt] = [sanitize(m) for m in meal_plan_data[mt]]

@app.get("/coach/consumption-insights")
async def get_consumption_insights(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    try:
        # Get consumption data using existing function
        consumption_data = await get_user_consumption_history(current_user["email"], limit=200)
        
        # Filter to specified period
        start_date = datetime.utcnow() - timedelta(days=days)
        filtered_data = []
        for entry in consumption_data:
            try:
                entry_date = datetime.fromisoformat(entry.get("timestamp", "").replace("Z", "+00:00"))
                if entry_date >= start_date:
                    filtered_data.append(entry)
            except:
                continue
        
        consumption_data = filtered_data
        
        if not consumption_data:
            return {
                "message": "No consumption data found for the specified period",
                "insights": {}
            }
        
        # Analyze patterns
        daily_calories = {}
        meal_times = {"breakfast": [], "lunch": [], "dinner": [], "snack": []}
        food_frequency = {}
        weekly_adherence = {}
        
        for entry in consumption_data:
            try:
                entry_date = datetime.fromisoformat(entry.get("timestamp", "").replace("Z", "+00:00"))
                date_key = entry_date.strftime("%Y-%m-%d")
                meal_type = entry.get("meal_type", "snack")
                food_name = entry.get("food_name", "").lower()
                
                # Get nutritional info
                nutrition = entry.get("nutritional_info", {})
                calories = nutrition.get("calories", 0)
                
                # Daily calories
                daily_calories[date_key] = daily_calories.get(date_key, 0) + calories
                
                # Meal timing
                hour = entry_date.hour
                meal_times[meal_type].append(hour)
                
                # Food frequency
                food_frequency[food_name] = food_frequency.get(food_name, 0) + 1
                
                # Weekly adherence using medical rating
                week_key = entry_date.strftime("%Y-W%U")
                if week_key not in weekly_adherence:
                    weekly_adherence[week_key] = {"total": 0, "diabetes_friendly": 0}
                
                weekly_adherence[week_key]["total"] += 1
                medical_rating = entry.get("medical_rating", {})
                diabetes_suitability = medical_rating.get("diabetes_suitability", "").lower()
                if diabetes_suitability in ["high", "good", "suitable"]:
                    weekly_adherence[week_key]["diabetes_friendly"] += 1
            except:
                continue
        
        # Calculate insights
        avg_daily_calories = sum(daily_calories.values()) / len(daily_calories) if daily_calories else 0
        
        # Most common meal times
        common_meal_times = {}
        for meal_type, times in meal_times.items():
            if times:
                common_meal_times[meal_type] = sum(times) / len(times)
        
        # Top foods
        top_foods = sorted(food_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Weekly adherence rates
        adherence_by_week = {}
        for week, data in weekly_adherence.items():
            rate = (data["diabetes_friendly"] / data["total"] * 100) if data["total"] > 0 else 0
            adherence_by_week[week] = round(rate, 1)
        
        return {
            "period_days": days,
            "total_meals_logged": len(consumption_data),
            "insights": {
                "average_daily_calories": round(avg_daily_calories, 1),
                "common_meal_times": common_meal_times,
                "top_foods": [{"food": food, "frequency": freq} for food, freq in top_foods],
                "weekly_adherence_rates": adherence_by_week,
                "daily_calorie_trend": daily_calories
            },
            "recommendations": [
                f"Your average daily intake is {avg_daily_calories:.0f} calories",
                f"You've logged {len(consumption_data)} meals in the last {days} days",
                "Consider maintaining consistent meal times for better blood sugar control" if len(set(common_meal_times.values())) > 2 else "Good job maintaining consistent meal times!"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting consumption insights: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get consumption insights")

@app.get("/coach/notifications")
async def get_notifications(
    current_user: User = Depends(get_current_user)
):
    """Get intelligent notifications based on actual user data - NO FAKE NOTIFICATIONS"""
    try:
        print(f"[get_notifications] Getting notifications for user {current_user['email']}")
        
        # Get user's recent consumption data
        consumption_data = await get_user_consumption_history(current_user["email"], limit=20)
        
        if not consumption_data:
            print("[get_notifications] No consumption data found")
            return []  # Return empty array if no data
        
        # Filter today's consumption
        today = datetime.utcnow().date()
        today_consumption = []
        
        for entry in consumption_data:
            try:
                entry_date = datetime.fromisoformat(entry.get("timestamp", "").replace("Z", "+00:00")).date()
                if entry_date == today:
                    today_consumption.append(entry)
            except:
                continue
        
        notifications = []
        
        # Only show meaningful notifications based on actual data
        if len(today_consumption) == 0:
            # Only show this once per day and only if it's past breakfast time
            current_hour = datetime.utcnow().hour
            if current_hour > 9:
                notifications.append({
                    "type": "info",
                    "message": "Start logging your meals to get personalized AI coaching!",
                    "priority": "medium",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": "Track your first meal to begin receiving intelligent recommendations."
                })
        else:
            # Calculate today's totals from actual nutritional_info
            today_totals = {"calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0}
            diabetes_suitable_count = 0
            
            for entry in today_consumption:
                nutritional_info = entry.get("nutritional_info", {})
                today_totals["calories"] += nutritional_info.get("calories", 0)
                today_totals["protein"] += nutritional_info.get("protein", 0)
                today_totals["carbohydrates"] += nutritional_info.get("carbohydrates", 0)
                today_totals["fat"] += nutritional_info.get("fat", 0)
                
                # Check diabetes suitability from medical_rating
                medical_rating = entry.get("medical_rating", {})
                diabetes_suitability = medical_rating.get("diabetes_suitability", "").lower()
                if diabetes_suitability in ["high", "good", "suitable"]:
                    diabetes_suitable_count += 1
            
            # Only show achievement notifications for real accomplishments
            if len(today_consumption) >= 3:  # At least 3 meals logged
                adherence_rate = (diabetes_suitable_count / len(today_consumption)) * 100
                if adherence_rate >= 80:
                    notifications.append({
                        "type": "success",
                        "message": f"Excellent! {adherence_rate:.0f}% of your meals today are diabetes-suitable.",
                        "priority": "low",
                        "timestamp": datetime.utcnow().isoformat(),
                        "details": "Keep up the great work with your healthy choices!"
                    })
        
        print(f"[get_notifications] Generated {len(notifications)} notifications")
        return notifications
        
    except Exception as e:
        print(f"[get_notifications] Error: {str(e)}")
        return []  # Return empty array on error instead of raising exception

@app.post("/test/create-sample-data")
async def create_sample_data():
    """Create sample consumption data for testing"""
    try:
        # Sample consumption records for the last 7 days
        sample_foods = [
            {
                "food_name": "Grilled Chicken Breast with Vegetables",
                "nutritional_info": {
                    "calories": 350,
                    "protein": 45,
                    "carbohydrates": 15,
                    "fat": 12,
                    "fiber": 5,
                    "sugar": 8,
                    "sodium": 450
                },
                "medical_rating": {
                    "diabetes_suitability": "high",
                    "hypertension_suitability": "high",
                    "heart_disease_suitability": "high",
                    "cholesterol_suitability": "high",
                    "overall_health_score": 85
                }
            },
            {
                "food_name": "Greek Yogurt with Berries",
                "nutritional_info": {
                    "calories": 180,
                    "protein": 15,
                    "carbohydrates": 20,
                    "fat": 5,
                    "fiber": 3,
                    "sugar": 15,
                    "sodium": 80
                },
                "medical_rating": {
                    "diabetes_suitability": "good",
                    "hypertension_suitability": "good",
                    "heart_disease_suitability": "good",
                    "cholesterol_suitability": "excellent",
                    "overall_health_score": 78
                }
            },
            {
                "food_name": "Quinoa Salad with Avocado",
                "nutritional_info": {
                    "calories": 420,
                    "protein": 12,
                    "carbohydrates": 45,
                    "fat": 18,
                    "fiber": 8,
                    "sugar": 6,
                    "sodium": 320
                },
                "medical_rating": {
                    "diabetes_suitability": "high",
                    "hypertension_suitability": "excellent",
                    "heart_disease_suitability": "high",
                    "cholesterol_suitability": "high",
                    "overall_health_score": 88
                }
            },
            {
                "food_name": "Salmon with Sweet Potato",
                "nutritional_info": {
                    "calories": 480,
                    "protein": 35,
                    "carbohydrates": 35,
                    "fat": 22,
                    "fiber": 6,
                    "sugar": 12,
                    "sodium": 380
                },
                "medical_rating": {
                    "diabetes_suitability": "high",
                    "hypertension_suitability": "high",
                    "heart_disease_suitability": "excellent",
                    "cholesterol_suitability": "excellent",
                    "overall_health_score": 90
                }
            },
            {
                "food_name": "Oatmeal with Nuts",
                "nutritional_info": {
                    "calories": 320,
                    "protein": 12,
                    "carbohydrates": 45,
                    "fat": 12,
                    "fiber": 8,
                    "sugar": 8,
                    "sodium": 150
                },
                "medical_rating": {
                    "diabetes_suitability": "good",
                    "hypertension_suitability": "good",
                    "heart_disease_suitability": "good",
                    "cholesterol_suitability": "good",
                    "overall_health_score": 82
                }
            }
        ]
        
        # Create records for the last 7 days
        created_records = []
        for day_offset in range(7):
            record_date = datetime.utcnow() - timedelta(days=day_offset)
            
            # Create 2-3 meals per day
            meals_per_day = 2 if day_offset > 3 else 3
            for meal_index in range(meals_per_day):
                food = sample_foods[meal_index % len(sample_foods)]
                
                # Adjust timestamp for different meal times
                if meal_index == 0:  # Breakfast
                    meal_time = record_date.replace(hour=8, minute=30)
                elif meal_index == 1:  # Lunch
                    meal_time = record_date.replace(hour=12, minute=45)
                else:  # Dinner
                    meal_time = record_date.replace(hour=18, minute=30)
                
                consumption_record = {
                    "id": f"sample_{day_offset}_{meal_index}_{int(meal_time.timestamp())}",
                    "type": "consumption_record",
                    "user_id": "test@example.com",
                    "food_name": food["food_name"],
                    "nutritional_info": food["nutritional_info"],
                    "medical_rating": food["medical_rating"],
                    "timestamp": meal_time.isoformat() + "Z",
                    "session_id": f"sample_session_{day_offset}",
                    "created_at": meal_time.isoformat()
                }
                
                # Save to database
                interactions_container.create_item(body=consumption_record)
                created_records.append(consumption_record)
        
        return {
            "message": f"Created {len(created_records)} sample consumption records",
            "records_created": len(created_records),
            "date_range": f"{(datetime.utcnow() - timedelta(days=6)).date()} to {datetime.utcnow().date()}"
        }
        
    except Exception as e:
        print(f"Error creating sample data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create sample data: {str(e)}")

@app.post("/test/create-user")
async def create_test_user():
    """Create a test user for development purposes"""
    try:
        # Create a test patient first with comprehensive health conditions
        patient_data = {
            "id": "TEST123",  # Use registration code as ID for consistency
            "name": "Test Patient",
            "phone": "1234567890",
            "condition": "Type 2 Diabetes",
            "medical_conditions": ["Type 2 Diabetes", "Hypertension", "High Cholesterol", "PCOS"],
            "medications": ["Metformin", "Lisinopril", "Atorvastatin", "Spironolactone"],
            "allergies": ["Shellfish", "Tree Nuts"],
            "dietary_restrictions": ["Low Sodium", "Low Glycemic Index"],
            "registration_code": "TEST123",
            "type": "patient",  # Add type field
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Save patient to database
        user_container.create_item(body=patient_data)
        
        # Create test user
        hashed_password = get_password_hash("test123")
        print(f"[create_test_user] Hashed password: {hashed_password}")
        user_data = {
            "id": "test@example.com",  # Use email as ID for consistency
            "username": "test@example.com",
            "email": "test@example.com",
            "hashed_password": hashed_password,
            "disabled": False,
            "patient_id": "TEST123",
            "type": "user",  # Add type field
            "profile": {
                "name": "Test Patient",
                "age": 45,
                "gender": "Female",
                "height": 165.0,
                "weight": 75.0,
                "bmi": 27.5,
                "systolicBP": 140,
                "diastolicBP": 90,
                "medicalConditions": ["Type 2 Diabetes", "Hypertension", "High Cholesterol", "PCOS"],
                "currentMedications": ["Metformin", "Lisinopril", "Atorvastatin", "Spironolactone"],
                "allergies": ["Shellfish", "Tree Nuts"],
                "dietaryRestrictions": ["Low Sodium", "Low Glycemic Index"],
                "foodPreferences": ["Mediterranean", "Plant-based proteins"],
                "calorieTarget": "1800",
                "primaryGoals": ["Manage diabetes", "Lower blood pressure", "Reduce cholesterol", "Manage PCOS symptoms", "Lose weight"],
                "macroGoals": {
                    "protein": 90,
                    "carbs": 180,
                    "fat": 60
                }
            }
        }
        
        # Save user to database
        user_container.create_item(body=user_data)
        
        return {"message": "Test user created successfully", "email": "test@example.com", "password": "test123"}
        
    except Exception as e:
        # If user already exists, just return success
        if "Conflict" in str(e):
            return {"message": "Test user already exists", "email": "test@example.com", "password": "test123"}
        raise HTTPException(status_code=500, detail=f"Failed to create test user: {str(e)}")

@app.post("/test/quick-log")
async def test_quick_log_food(food_data: dict):
    """Test quick log food without authentication"""
    try:
        print(f"[test_quick_log_food] Starting test quick log")
        print(f"[test_quick_log_food] Food data received: {food_data}")
        
        food_name = food_data.get("food_name", "").strip()
        portion = food_data.get("portion", "medium portion").strip()
        
        if not food_name:
            raise HTTPException(status_code=400, detail="Food name is required")
        
        # Use AI to estimate nutritional values with comprehensive analysis
        prompt = f"""
        Analyze the food item: {food_name} ({portion})
        
        Provide a comprehensive JSON response with this exact structure:
        {{
            "food_name": "{food_name}",
            "estimated_portion": "{portion}",
            "nutritional_info": {{
                "calories": <number>,
                "carbohydrates": <number>,
                "protein": <number>,
                "fat": <number>,
                "fiber": <number>,
                "sugar": <number>,
                "sodium": <number>
            }},
            "medical_rating": {{
                "diabetes_suitability": "high/medium/low",
                "glycemic_impact": "low/medium/high",
                "recommended_frequency": "daily/weekly/occasional/avoid",
                "portion_recommendation": "appropriate/reduce/increase"
            }},
            "analysis_notes": "Brief explanation of nutritional value and diabetes considerations"
        }}
        
        Base estimates on standard nutritional databases. Be accurate and conservative with diabetes ratings.
        Only return valid JSON, no other text.
        """
        
        # Initialize fallback data
        fallback_data = {
            "food_name": food_name,
            "estimated_portion": portion,
            "nutritional_info": {
                "calories": 200,
                "carbohydrates": 25,
                "protein": 10,
                "fat": 8,
                "fiber": 3,
                "sugar": 5,
                "sodium": 300
            },
            "medical_rating": {
                "diabetes_suitability": "medium",
                "glycemic_impact": "medium",
                "recommended_frequency": "weekly",
                "portion_recommendation": "appropriate"
            },
            "analysis_notes": f"Nutritional estimate for {food_name}. Consult with healthcare provider for personalized advice."
        }
        
        try:
            print("[test_quick_log_food] Calling OpenAI for nutritional analysis")
            response = client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                messages=[
                    {
                        "role": "system",
                        "content": "You are a nutrition analysis expert specializing in diabetes management. Provide accurate nutritional estimates and diabetes-appropriate recommendations."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            # Parse AI response
            analysis_text = response.choices[0].message.content
            print(f"[test_quick_log_food] OpenAI response: {analysis_text}")
            
            try:
                # Extract JSON from response
                start_idx = analysis_text.find('{')
                end_idx = analysis_text.rfind('}') + 1
                json_str = analysis_text[start_idx:end_idx]
                analysis_data = json.loads(json_str)
                print(f"[test_quick_log_food] Successfully parsed AI analysis: {analysis_data}")
            except (json.JSONDecodeError, ValueError) as parse_error:
                print(f"[test_quick_log_food] JSON parsing error: {str(parse_error)}")
                analysis_data = fallback_data
                
        except Exception as openai_error:
            print(f"[test_quick_log_food] OpenAI API error: {str(openai_error)}. Using fallback estimation.")
            analysis_data = fallback_data
        
        # Prepare consumption data in the same format as the image analysis system
        consumption_data = {
            "food_name": analysis_data.get("food_name", food_name),
            "estimated_portion": analysis_data.get("estimated_portion", portion),
            "nutritional_info": analysis_data.get("nutritional_info", fallback_data["nutritional_info"]),
            "medical_rating": analysis_data.get("medical_rating", fallback_data["medical_rating"]),
            "image_analysis": analysis_data.get("analysis_notes", f"Quick log entry for {food_name}"),
            "image_url": None,  # No image for quick log
            "meal_type": (food_data.get("meal_type") or "snack").lower()
        }
        
        print(f"[test_quick_log_food] Prepared consumption data: {consumption_data}")
        
        # Save to consumption history using the test user
        print(f"[test_quick_log_food] Saving consumption record for test user")
        consumption_record = await save_consumption_record("test@example.com", consumption_data)
        print(f"[test_quick_log_food] Successfully saved consumption record with ID: {consumption_record['id']}")
        
        # Return success response in the SAME FORMAT as before
        return {
            "success": True,
            "message": f"Successfully logged {analysis_data.get('food_name', food_name)}",
            "consumption_record_id": consumption_record["id"],
            "analysis": analysis_data,
            "food_name": analysis_data.get("food_name", food_name),
            "nutritional_summary": {
                "calories": analysis_data.get("nutritional_info", {}).get("calories", 0),
                "carbohydrates": analysis_data.get("nutritional_info", {}).get("carbohydrates", 0),
                "protein": analysis_data.get("nutritional_info", {}).get("protein", 0),
                "fat": analysis_data.get("nutritional_info", {}).get("fat", 0)
            },
            "diabetes_rating": analysis_data.get("medical_rating", {}).get("diabetes_suitability", "medium")
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"[test_quick_log_food] Unexpected error: {str(e)}")
        print(f"[test_quick_log_food] Full error details:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to log food item: {str(e)}")

@app.get("/test/consumption/history")
async def test_get_consumption_history(limit: int = 50):
    """Test consumption history without authentication"""
    try:
        print(f"[test_get_consumption_history] Getting history for test user, limit: {limit}")
        
        # Get consumption history for test user
        consumption_data = await get_user_consumption_history("test@example.com", limit)
        print(f"[test_get_consumption_history] Found {len(consumption_data)} records")
        
        return consumption_data
        
    except Exception as e:
        print(f"[test_get_consumption_history] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get consumption history: {str(e)}")

@app.get("/test/consumption/analytics")
async def test_get_consumption_analytics(days: int = 7):
    """Test consumption analytics without authentication"""
    try:
        print(f"[test_get_consumption_analytics] Getting analytics for test user, days: {days}")
        
        # Get analytics for test user
        analytics_data = await get_consumption_analytics("test@example.com", days)
        print(f"[test_get_consumption_analytics] Analytics data generated successfully")
        
        return analytics_data
        
    except Exception as e:
        print(f"[test_get_consumption_analytics] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get consumption analytics: {str(e)}")

@app.get("/test/coach/daily-insights")
async def test_get_daily_insights():
    """Test daily insights without authentication"""
    try:
        print(f"[test_get_daily_insights] Getting daily insights for test user")
        
        # Get consumption analytics for today
        today_analytics = await get_consumption_analytics("test@example.com", 1)
        weekly_analytics = await get_consumption_analytics("test@example.com", 7)
        
        # Test user's comprehensive health conditions
        health_conditions = ["Type 2 Diabetes", "Hypertension", "High Cholesterol", "PCOS"]
        
        # Calculate comprehensive health adherence
        health_adherence = weekly_analytics.get("adherence_stats", {}).get("diabetes_suitable_percentage", 85)
        total_meals = today_analytics.get("total_meals", 0)
        
        insights_data = {
            "date": datetime.utcnow().date().isoformat(),
            "goals": {
                "calories": 1800,  # Adjusted for weight management
                "protein": 90,
                "carbohydrates": 180,
                "fat": 60
            },
            "today_totals": today_analytics.get("daily_averages", {
                "calories": 0,
                "protein": 0,
                "carbohydrates": 0,
                "fat": 0,
                "fiber": 0,
                "sugar": 0,
                "sodium": 0
            }),
            "adherence": {
                "calories": 75,
                "protein": 80,
                "carbohydrates": 70,
                "fat": 65
            },
            "diabetes_adherence": health_adherence,  # Now represents overall health adherence
            "health_adherence": health_adherence,
            "health_conditions": health_conditions,
            "consistency_streak": max(0, weekly_analytics.get("total_meals", 0) // 2),
            "meals_logged_today": total_meals,
            "weekly_stats": {
                "total_meals": weekly_analytics.get("total_meals", 0),
                "diabetes_suitable_percentage": health_adherence,
                "health_suitable_percentage": health_adherence,
                "average_daily_calories": weekly_analytics.get("daily_averages", {}).get("calories", 0)
            },
            "recommendations": [
                {
                    "type": "nutrition",
                    "priority": "high",
                    "message": "Focus on low-sodium foods to help manage your hypertension",
                    "action": "view_low_sodium_foods"
                },
                {
                    "type": "diabetes",
                    "priority": "high", 
                    "message": "Choose low glycemic index foods to maintain stable blood sugar",
                    "action": "view_low_gi_foods"
                },
                {
                    "type": "cholesterol",
                    "priority": "medium",
                    "message": "Include omega-3 rich foods like salmon to help lower cholesterol",
                    "action": "view_heart_healthy_foods"
                },
                {
                    "type": "pcos",
                    "priority": "medium",
                    "message": "Anti-inflammatory foods can help manage PCOS symptoms",
                    "action": "view_anti_inflammatory_foods"
                }
            ],
            "has_meal_plan": False,
            "latest_meal_plan_date": None,
            # Add comprehensive insights for the frontend
            "insights": [
                {
                    "category": "Daily Progress",
                    "message": f"You've logged {total_meals} meals today with {health_adherence:.0f}% health-suitable choices for your conditions: {', '.join(health_conditions[:2])}{'...' if len(health_conditions) > 2 else ''}.",
                    "action": "View Details"
                },
                {
                    "category": "Weekly Trend", 
                    "message": f"This week you've maintained {weekly_analytics.get('total_meals', 0)} meal logs with consistent tracking for your health management.",
                    "action": "Keep Going"
                },
                {
                    "category": "Health Focus",
                    "message": f"Your meal choices are {health_adherence:.0f}% aligned with recommendations for {', '.join(health_conditions[:2])}.",
                    "action": "Get Recommendations"
                },
                {
                    "category": "Multi-Condition Management",
                    "message": f"Managing {len(health_conditions)} conditions requires balanced nutrition - you're doing great!",
                    "action": "View Comprehensive Plan"
                }
            ] if total_meals > 0 else [
                {
                    "category": "Getting Started",
                    "message": f"Start logging your meals to get personalized AI insights for your health conditions: {', '.join(health_conditions)}!",
                    "action": "Log First Meal"
                }
            ]
        }
        
        print(f"[test_get_daily_insights] Daily insights generated successfully")
        
        return insights_data
        
    except Exception as e:
        print(f"[test_get_daily_insights] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get daily insights: {str(e)}")

@app.get("/test/coach/notifications")
async def test_get_notifications():
    """Test notifications without authentication"""
    try:
        print(f"[test_get_notifications] Getting notifications for test user")
        
        # Create a mock user for testing
        mock_user = {
            "email": "test@example.com",
            "id": "test@example.com",
            "profile": {
                "calorieTarget": "2000",
                "medicalConditions": ["Type 2 Diabetes"]
            }
        }
        
        return await get_notifications(mock_user)
        
    except Exception as e:
        print(f"[test_get_notifications] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get notifications: {str(e)}")

@app.get("/test/coach/todays-meal-plan")
async def test_get_todays_meal_plan():
    """Test today's meal plan without authentication"""
    try:
        print(f"[test_get_todays_meal_plan] Getting today's meal plan for test user")
        
        # Create a mock user for testing
        mock_user = {
            "email": "test@example.com",
            "id": "test@example.com"
        }
        
        return await get_todays_meal_plan(mock_user)
        
    except Exception as e:
        print(f"[test_get_todays_meal_plan] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get today's meal plan: {str(e)}")

async def adapt_meal_plan_based_on_consumption(user_email: str, today_consumption: list, latest_meal_plan: dict = None):
    """
    Intelligently adapt tomorrow's meal plan based on today's consumption patterns.
    This function analyzes what the user ate today vs. their plan and suggests adjustments.
    """
    try:
        if not latest_meal_plan:
            return None
            
        # Calculate today's totals
        today_calories = sum(record.get("nutritional_info", {}).get("calories", 0) for record in today_consumption)
        today_carbs = sum(record.get("nutritional_info", {}).get("carbohydrates", 0) for record in today_consumption)
        today_protein = sum(record.get("nutritional_info", {}).get("protein", 0) for record in today_consumption)
        today_fat = sum(record.get("nutritional_info", {}).get("fat", 0) for record in today_consumption)
        
        # Get user's goals
        calorie_goal = latest_meal_plan.get("dailyCalories", 2000)
        macros = latest_meal_plan.get("macronutrients", {})
        carb_goal = macros.get("carbs", 250)
        protein_goal = macros.get("protein", 100)
        fat_goal = macros.get("fats", 70)
        
        # Calculate deviations
        calorie_deviation = today_calories - calorie_goal
        carb_deviation = today_carbs - carb_goal
        protein_deviation = today_protein - protein_goal
        fat_deviation = today_fat - fat_goal
        
        # Generate adaptive suggestions
        adaptations = []
        
        # Calorie adjustments
        if calorie_deviation > 300:  # Exceeded by more than 300 calories
            adaptations.append({
                "type": "calorie_reduction",
                "message": f"Since you exceeded your calorie goal by {calorie_deviation:.0f} calories today, tomorrow's portions will be slightly smaller to help balance your weekly intake.",
                "adjustment": -200  # Reduce tomorrow by 200 calories
            })
        elif calorie_deviation < -300:  # Under by more than 300 calories
            adaptations.append({
                "type": "calorie_increase",
                "message": f"You were {abs(calorie_deviation):.0f} calories under your goal today. Tomorrow's plan includes slightly larger portions to ensure adequate nutrition.",
                "adjustment": 200  # Increase tomorrow by 200 calories
            })
        
        # Carb adjustments
        if carb_deviation > 50:  # Too many carbs
            adaptations.append({
                "type": "carb_reduction",
                "message": "Tomorrow's plan emphasizes more protein and vegetables to balance today's higher carb intake.",
                "adjustment": "more_protein_vegetables"
            })
        elif carb_deviation < -30:  # Too few carbs
            adaptations.append({
                "type": "carb_increase",
                "message": "Tomorrow includes healthy complex carbs to ensure you have enough energy.",
                "adjustment": "add_complex_carbs"
            })
        
        # Protein adjustments
        if protein_deviation < -20:  # Too little protein
            adaptations.append({
                "type": "protein_increase",
                "message": "Tomorrow's meals will include extra lean protein to meet your daily needs.",
                "adjustment": "add_lean_protein"
            })
        
        # Create tomorrow's adapted meal plan
        tomorrow = datetime.utcnow().date() + timedelta(days=1)
        tomorrow_day_index = tomorrow.weekday()
        
        # Get base meals for tomorrow from the current plan
        adapted_plan = {
            "id": f"adapted_{user_email}_{int(datetime.utcnow().timestamp())}",
            "user_id": user_email,
            "created_at": datetime.utcnow().isoformat(),
            "type": "adaptive_meal_plan",
            "date": tomorrow.isoformat(),
            "adaptations": adaptations,
            "based_on_consumption": {
                "date": datetime.utcnow().date().isoformat(),
                "calories": today_calories,
                "deviations": {
                    "calories": calorie_deviation,
                    "carbs": carb_deviation,
                    "protein": protein_deviation,
                    "fat": fat_deviation
                }
            }
        }
        
        # Copy base meal structure and apply adaptations
        if tomorrow_day_index < 7:  # Valid day of week
            base_breakfast = latest_meal_plan.get("breakfast", [])[tomorrow_day_index] if tomorrow_day_index < len(latest_meal_plan.get("breakfast", [])) else "Healthy breakfast option"
            base_lunch = latest_meal_plan.get("lunch", [])[tomorrow_day_index] if tomorrow_day_index < len(latest_meal_plan.get("lunch", [])) else "Balanced lunch option"
            base_dinner = latest_meal_plan.get("dinner", [])[tomorrow_day_index] if tomorrow_day_index < len(latest_meal_plan.get("dinner", [])) else "Nutritious dinner option"
            
            # Apply adaptations to meals
            adapted_breakfast = base_breakfast
            adapted_lunch = base_lunch
            adapted_dinner = base_dinner
            
            for adaptation in adaptations:
                if adaptation["type"] == "carb_reduction":
                    adapted_lunch += " (with extra vegetables instead of rice/bread)"
                    adapted_dinner += " (with cauliflower rice or extra greens)"
                elif adaptation["type"] == "protein_increase":
                    adapted_breakfast += " + Greek yogurt"
                    adapted_lunch += " + extra lean protein"
                elif adaptation["type"] == "calorie_reduction":
                    adapted_breakfast += " (smaller portion)"
                    adapted_lunch += " (lighter version)"
                    adapted_dinner += " (reduced portion)"
            
            adapted_plan.update({
                "breakfast": [adapted_breakfast],
                "lunch": [adapted_lunch],
                "dinner": [adapted_dinner],
                "dailyCalories": max(1200, calorie_goal + sum(a.get("adjustment", 0) for a in adaptations if isinstance(a.get("adjustment"), int))),
                "macronutrients": latest_meal_plan.get("macronutrients", {})
            })
        
        # Save the adapted plan to database
        await save_meal_plan(user_email, adapted_plan)
        
        return adapted_plan
        
    except Exception as e:
        print(f"Error in adaptive meal planning: {str(e)}")
        return None

@app.post("/coach/meal-suggestion")
async def get_meal_suggestion(
    request: dict,
    current_user: User = Depends(get_current_user)
):
    """
    🧠 COMPREHENSIVE AI COACH - Central intelligence with full access to user data
    Provides intelligent responses based on consumption history, meal plans, progress, and health data
    """
    try:
        print(f"[AI_COACH] Processing query for user: {current_user['email']}")
        
        # Handle both simple query format and detailed format
        query = request.get("query", "").strip()
        if not query:
            return {
                "success": False,
                "error": "Please provide a question or query"
            }
        
        # 🔍 COMPREHENSIVE DATA GATHERING - Get ALL user context
        print("[AI_COACH] Gathering comprehensive user data...")
        
        # 1. Get user profile with all health information
        try:
            user_profile_query = f"SELECT * FROM c WHERE c.type = 'user' AND c.id = '{current_user['email']}'"
            user_profiles = list(user_container.query_items(query=user_profile_query, enable_cross_partition_query=True))
            user_profile = user_profiles[0].get("profile", {}) if user_profiles else {}
        except Exception as e:
            print(f"[AI_COACH] Error fetching user profile: {e}")
            user_profile = {}
        
        # 2. Get comprehensive consumption history (last 30 days)
        try:
            consumption_history = await get_user_consumption_history(current_user["email"], limit=100)
            # Filter to last 30 days for comprehensive analysis
            from datetime import datetime, timedelta
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_consumption = [
                record for record in consumption_history 
                if datetime.fromisoformat(record.get("timestamp", "").replace("Z", "+00:00")) > thirty_days_ago
            ]
        except Exception as e:
            print(f"[AI_COACH] Error fetching consumption history: {e}")
            recent_consumption = []
        
        # 3. Get today's consumption for daily analysis
        try:
            today = datetime.utcnow().date()
            tomorrow = today + timedelta(days=1)
            today_consumption = [
                record for record in recent_consumption
                if today <= datetime.fromisoformat(record.get("timestamp", "").replace("Z", "+00:00")).date() < tomorrow
            ]
        except Exception as e:
            print(f"[AI_COACH] Error filtering today's consumption: {e}")
            today_consumption = []
        
        # 4. Get meal plans history
        try:
            meal_plans = await get_user_meal_plans(current_user["email"])
            latest_meal_plan = meal_plans[0] if meal_plans else None
        except Exception as e:
            print(f"[AI_COACH] Error fetching meal plans: {e}")
            meal_plans = []
            latest_meal_plan = None
        
        # 5. Get consumption analytics for trends
        try:
            weekly_analytics = await get_consumption_analytics(current_user["email"], 7)
            monthly_analytics = await get_consumption_analytics(current_user["email"], 30)
        except Exception as e:
            print(f"[AI_COACH] Error fetching analytics: {e}")
            weekly_analytics = {}
            monthly_analytics = {}
        
        # 6. Get progress data
        try:
            progress_data = await get_consumption_progress(current_user)
        except Exception as e:
            print(f"[AI_COACH] Error fetching progress data: {e}")
            progress_data = {}
        
        # 📊 COMPREHENSIVE DATA ANALYSIS
        print("[AI_COACH] Analyzing comprehensive user data...")
        
        # Calculate today's nutritional totals
        today_totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0, "sugar": 0, "sodium": 0}
        for record in today_consumption:
            nutritional_info = record.get("nutritional_info", {})
            today_totals["calories"] += nutritional_info.get("calories", 0)
            today_totals["protein"] += nutritional_info.get("protein", 0)
            today_totals["carbs"] += nutritional_info.get("carbohydrates", 0)
            today_totals["fat"] += nutritional_info.get("fat", 0)
            today_totals["fiber"] += nutritional_info.get("fiber", 0)
            today_totals["sugar"] += nutritional_info.get("sugar", 0)
            today_totals["sodium"] += nutritional_info.get("sodium", 0)
        
        # Calculate weekly averages
        weekly_totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "meals": 0}
        for record in recent_consumption[-21:]:  # Last 3 weeks for better average
            nutritional_info = record.get("nutritional_info", {})
            weekly_totals["calories"] += nutritional_info.get("calories", 0)
            weekly_totals["protein"] += nutritional_info.get("protein", 0)
            weekly_totals["carbs"] += nutritional_info.get("carbohydrates", 0)
            weekly_totals["fat"] += nutritional_info.get("fat", 0)
            weekly_totals["meals"] += 1
        
        weekly_averages = {}
        if weekly_totals["meals"] > 0:
            days_logged = max(1, weekly_totals["meals"] / 3)  # Estimate days
            weekly_averages = {
                "calories": weekly_totals["calories"] / days_logged,
                "protein": weekly_totals["protein"] / days_logged,
                "carbs": weekly_totals["carbs"] / days_logged,
                "fat": weekly_totals["fat"] / days_logged
            }
        
        # Get user's goals and health info
        calorie_goal = 2000  # Default
        macro_goals = {"protein": 100, "carbs": 250, "fat": 70}
        
        if user_profile.get("calorieTarget"):
            try:
                calorie_goal = int(user_profile["calorieTarget"])
            except:
                pass
        elif latest_meal_plan and latest_meal_plan.get("dailyCalories"):
            calorie_goal = latest_meal_plan["dailyCalories"]
        
        # Health conditions and dietary info
        health_conditions = user_profile.get("medicalConditions", []) or user_profile.get("medical_conditions", [])
        dietary_restrictions = user_profile.get("dietaryRestrictions", []) or user_profile.get("dietary_restrictions", [])
        allergies = user_profile.get("allergies", [])
        medications = user_profile.get("currentMedications", [])
        
        # Calculate diabetes adherence and health metrics
        diabetes_suitable_count = 0
        high_carb_meals = 0
        high_sugar_meals = 0
        high_sodium_meals = 0
        
        for record in recent_consumption:
            medical_rating = record.get("medical_rating", {})
            nutritional_info = record.get("nutritional_info", {})
            
            # Diabetes suitability
            diabetes_suitability = medical_rating.get("diabetes_suitability", "").lower()
            if diabetes_suitability in ["high", "good", "suitable"]:
                diabetes_suitable_count += 1
            
            # Track concerning patterns
            if nutritional_info.get("carbohydrates", 0) > 45:
                high_carb_meals += 1
            if nutritional_info.get("sugar", 0) > 15:
                high_sugar_meals += 1
            if nutritional_info.get("sodium", 0) > 800:
                high_sodium_meals += 1
        
        total_recent_meals = len(recent_consumption)
        diabetes_adherence = (diabetes_suitable_count / total_recent_meals * 100) if total_recent_meals > 0 else 0
        
        # Calculate consistency streak
        consistency_streak = calculate_consistency_streak(recent_consumption)
        
        # Analyze meal timing patterns
        meal_times = {}
        for record in recent_consumption:
            meal_type = record.get("meal_type", "unknown")
            timestamp = record.get("timestamp", "")
            try:
                hour = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).hour
                if meal_type not in meal_times:
                    meal_times[meal_type] = []
                meal_times[meal_type].append(hour)
            except:
                pass
        
        # Get recent meal names for pattern analysis
        recent_meals = [record.get("food_name", "Unknown") for record in recent_consumption[:10]]
        today_meals = [record.get("food_name", "Unknown") for record in today_consumption]
        
        # 🤖 BUILD COMPREHENSIVE AI COACH SYSTEM PROMPT
        print("[AI_COACH] Building comprehensive AI response...")
        
        system_prompt = f"""You are an advanced AI Diet Coach and Diabetes Management Specialist with FULL ACCESS to the user's comprehensive health data. You are their personal nutrition expert, meal planner, and health companion.

🎯 **YOUR ROLE**: You are the central intelligence of their diabetes management system with complete visibility into their eating patterns, progress, and health journey.

👤 **USER PROFILE**:
- Name: {user_profile.get('name', 'Not specified')}
- Age: {user_profile.get('age', 'Not specified')} | Gender: {user_profile.get('gender', 'Not specified')}
- Weight: {user_profile.get('weight', 'Not specified')} kg | Height: {user_profile.get('height', 'Not specified')} cm
- BMI: {user_profile.get('bmi', 'Not calculated')}
- Blood Pressure: {user_profile.get('systolicBP', 'Not specified')}/{user_profile.get('diastolicBP', 'Not specified')} mmHg

🏥 **HEALTH CONDITIONS & MEDICATIONS**:
- Medical Conditions: {', '.join(health_conditions) if health_conditions else 'None specified'}
- Current Medications: {', '.join(medications) if medications else 'None specified'}
- Allergies: {', '.join(allergies) if allergies else 'None specified'}
- Dietary Restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None specified'}

🎯 **DAILY GOALS & TODAY'S PROGRESS** ({datetime.utcnow().strftime('%B %d, %Y')}):
- Calorie Goal: {calorie_goal} kcal | Today: {today_totals['calories']:.0f} kcal ({today_totals['calories']/calorie_goal*100:.1f}%)
- Protein Goal: {macro_goals['protein']}g | Today: {today_totals['protein']:.1f}g ({today_totals['protein']/macro_goals['protein']*100:.1f}%)
- Carbs: {today_totals['carbs']:.1f}g | Fat: {today_totals['fat']:.1f}g
- Fiber: {today_totals['fiber']:.1f}g | Sugar: {today_totals['sugar']:.1f}g | Sodium: {today_totals['sodium']:.0f}mg
- Meals logged today: {len(today_consumption)}

📊 **RECENT PERFORMANCE ANALYSIS** (Last 30 days):
- Total meals logged: {total_recent_meals}
- Diabetes-suitable meals: {diabetes_suitable_count}/{total_recent_meals} ({diabetes_adherence:.1f}%)
- High-carb meals (>45g): {high_carb_meals} | High-sugar meals (>15g): {high_sugar_meals}
- High-sodium meals (>800mg): {high_sodium_meals}
- Consistency streak: {consistency_streak} days
- Weekly averages: {weekly_averages.get('calories', 0):.0f} cal, {weekly_averages.get('protein', 0):.1f}g protein

🍽️ **MEAL PATTERNS & HISTORY**:
- Today's meals: {', '.join(today_meals) if today_meals else 'No meals logged today'}
- Recent meals: {', '.join(recent_meals[:5]) if recent_meals else 'No recent meals'}
- Meal timing patterns: {meal_times}

📋 **CURRENT MEAL PLAN STATUS**:
- Has active meal plan: {'Yes' if latest_meal_plan else 'No'}
- Latest meal plan date: {latest_meal_plan.get('created_at', 'None')[:10] if latest_meal_plan else 'None'}
- Total meal plans created: {len(meal_plans)}

🎯 **HEALTH INSIGHTS**:
- Diabetes adherence trend: {diabetes_adherence:.1f}% (Target: >80%)
- Carb management: {'Good' if high_carb_meals < total_recent_meals * 0.3 else 'Needs attention'}
- Sugar control: {'Good' if high_sugar_meals < total_recent_meals * 0.2 else 'Needs attention'}
- Sodium management: {'Good' if high_sodium_meals < total_recent_meals * 0.3 else 'Needs attention'}

**CRITICAL FORMATTING INSTRUCTIONS**:
1. **NO MARKDOWN**: Do not use any markdown formatting (no #, ##, ###, *, **, _, __, ---, etc.)
2. **PLAIN TEXT ONLY**: Return clean, readable plain text that displays well in a web interface
3. **USE EMOJIS**: Use emojis for visual appeal instead of markdown headers
4. **LINE BREAKS**: Use simple line breaks for structure, not markdown syntax
5. **LISTS**: Use simple bullet points (•) or numbers, not markdown list syntax
6. **EMPHASIS**: Use CAPITAL LETTERS or emojis for emphasis, not markdown bold/italic

**RESPONSE INSTRUCTIONS**:
1. **Be Comprehensive**: Use ALL the data above to provide intelligent, personalized responses
2. **Be Specific**: Reference actual numbers, patterns, and trends from their data
3. **Be Actionable**: Provide specific recommendations based on their current status
4. **Be Encouraging**: Acknowledge their progress and efforts
5. **Be Health-Focused**: Always consider their medical conditions in recommendations
6. **Be Contextual**: Consider their meal timing, recent choices, and patterns
7. **Be Readable**: Format for easy reading in a web interface without markdown

Answer their question with the full context of their health journey, current progress, and specific data patterns. Use plain text formatting that will display beautifully in a web interface."""

        user_prompt = f"""User's Question: "{query}"

Please provide a comprehensive, personalized response that:
- Uses their specific consumption data and patterns
- References their actual progress numbers
- Considers their health conditions and goals
- Provides actionable recommendations
- Acknowledges their current status and trends

Be conversational but informative, like a knowledgeable nutrition coach who knows them well."""

        # 🚀 GET AI RESPONSE FROM AZURE OPENAI
        try:
            response = client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # 🧹 CLEAN MARKDOWN FORMATTING for better frontend display
            import re
            # Remove markdown headers
            ai_response = re.sub(r'^#{1,6}\s+', '', ai_response, flags=re.MULTILINE)
            # Remove markdown bold/italic
            ai_response = re.sub(r'\*\*(.*?)\*\*', r'\1', ai_response)
            ai_response = re.sub(r'\*(.*?)\*', r'\1', ai_response)
            ai_response = re.sub(r'__(.*?)__', r'\1', ai_response)
            ai_response = re.sub(r'_(.*?)_', r'\1', ai_response)
            # Remove markdown horizontal rules
            ai_response = re.sub(r'^---+$', '', ai_response, flags=re.MULTILINE)
            # Clean up multiple line breaks
            ai_response = re.sub(r'\n{3,}', '\n\n', ai_response)
            
        except Exception as e:
            print(f"[AI_COACH] Error getting AI response: {e}")
            ai_response = f"I'm having trouble accessing my AI capabilities right now, but I can see you have {len(today_consumption)} meals logged today with {today_totals['calories']:.0f} calories. Your diabetes adherence is at {diabetes_adherence:.1f}%. Please try your question again in a moment."
        
        # 📝 LOG THE INTERACTION
        try:
            await log_meal_suggestion(
                user_id=current_user["email"],
                meal_type="ai_coach_query",
                suggestion=ai_response,
                context={
                    "query": query,
                    "today_totals": today_totals,
                    "diabetes_adherence": diabetes_adherence,
                    "meals_logged": len(today_consumption),
                    "consistency_streak": consistency_streak
                }
            )
        except Exception as e:
            print(f"[AI_COACH] Error logging interaction: {e}")
        
        print(f"[AI_COACH] Successfully generated comprehensive response for user")
        
        return {
            "success": True,
            "suggestion": ai_response,
            "response": ai_response,  # Frontend compatibility
            "context": {
                "comprehensive_analysis": True,
                "data_sources": [
                    "user_profile", "consumption_history", "meal_plans", 
                    "progress_tracking", "health_conditions", "dietary_patterns"
                ],
                "today_meals": len(today_consumption),
                "total_calories_today": today_totals["calories"],
                "diabetes_adherence": diabetes_adherence,
                "consistency_streak": consistency_streak,
                "has_meal_plan": latest_meal_plan is not None,
                "analysis_period": "30_days",
                "personalized": True,
                "health_focused": True
            }
        }
        
    except Exception as e:
        print(f"[AI_COACH] Critical error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": "I'm experiencing technical difficulties. Please try again in a moment.",
            "suggestion": "I'm currently unable to access your comprehensive health data. Please try your question again.",
            "response": "I'm currently unable to access your comprehensive health data. Please try your question again."
        }

async def get_ai_suggestion(prompt: str) -> str:
    """Get meal suggestion from Azure OpenAI"""
    try:
        # Call Azure OpenAI API
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            messages=[
                {"role": "system", "content": "You are a knowledgeable nutritionist and meal planner. Provide specific, healthy meal suggestions that consider dietary restrictions and nutritional needs."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error getting AI suggestion: {str(e)}")
        return None

async def log_meal_suggestion(user_id: str, meal_type: str, suggestion: str, context: dict):
    """Log meal suggestion for future reference"""
    try:
        suggestion_log = {
            "user_id": user_id,
            "meal_type": meal_type,
            "suggestion": suggestion,
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Save to database
        await db.meal_suggestions.insert_one(suggestion_log)
    except Exception as e:
        logger.error(f"Error logging meal suggestion: {str(e)}")
        # Non-critical error, don't raise

def build_meal_suggestion_prompt(
    meal_type: str,
    remaining_calories: int,
    meal_patterns: dict,
    dietary_restrictions: list,
    health_conditions: list,
    context: dict,
    preferences: str
) -> str:
    """
    Build a context-aware prompt for meal suggestions.
    """
    query_context = context.get("query_context", "")
    current_hour = context.get("current_hour", 0)
    is_late_meal = context.get("is_late_meal", False)
    todays_meals = context.get("todays_meals", [])
    
    prompt = f"""Based on the user's query "{query_context}", suggest a {meal_type} that:
    1. Fits within {remaining_calories} remaining calories
    2. Considers their dietary restrictions: {', '.join(dietary_restrictions)}
    3. Is appropriate for their health conditions: {', '.join(health_conditions)}
    4. Avoids repetition with today's meals: {', '.join([m['name'] for m in todays_meals])}
    5. {"Provides a lighter option since it's a late meal" if is_late_meal else "Provides a satisfying portion"}
    6. Matches their usual meal patterns for {meal_type}
    7. {preferences if preferences else ""}
    
    Include:
    - Specific ingredients and portions
    - Brief preparation instructions
    - Nutritional breakdown
    - Health benefits
    - Any relevant tips or modifications
    """
    
    return prompt

def analyze_meal_patterns(meal_history: list) -> dict:
    """
    Analyze user's meal patterns to provide more personalized suggestions.
    """
    patterns = {
        "breakfast": [],
        "lunch": [],
        "dinner": [],
        "snack": []
    }
    
    for meal in meal_history:
        if meal["meal_type"] in patterns:
            patterns[meal["meal_type"]].append({
                "name": meal["food_name"],
                "frequency": 1,  # Can be updated for repeated meals
                "calories": meal["nutritional_info"]["calories"]
            })
    
    return patterns

@ app.get("/meal_plans/history")
async def get_meal_plans_history_alias(current_user: User = Depends(get_current_user)):
    """Alias for /meal_plans to maintain frontend backward compatibility"""
    return await get_meal_plans(current_user)

# --- Update meal type for existing record ---
@app.patch("/consumption/{record_id}/meal-type")
async def update_meal_type(record_id: str, payload: dict = Body(...), current_user: User = Depends(get_current_user)):
    meal_type = payload.get("meal_type", "").lower()
    if meal_type not in ["breakfast", "lunch", "dinner", "snack"]:
        raise HTTPException(status_code=400, detail="Invalid meal_type")

    try:
        await update_consumption_meal_type(current_user["email"], record_id, meal_type)
        return {"success": True}
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not allowed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# PRIVACY & GDPR COMPLIANCE ENDPOINTS
# ============================================================================

class DataExportRequest(BaseModel):
    data_types: List[str]  # ["profile", "meal_plans", "consumption_history", "chat_history", "recipes", "shopping_lists"]
    format_type: str = "pdf"  # "pdf", "json", "docx"

class AccountDeletionRequest(BaseModel):
    deletion_type: str = "complete"  # "complete" or "anonymize"
    confirmation: str  # User must type "DELETE" to confirm

class ConsentUpdateRequest(BaseModel):
    consent_given: Optional[bool] = None
    marketing_consent: Optional[bool] = None
    analytics_consent: Optional[bool] = None
    data_retention_preference: Optional[str] = None
    policy_version: Optional[str] = None

@app.post("/privacy/export-data")
async def export_user_data(
    export_request: DataExportRequest,
    current_user: User = Depends(get_current_user)
):
    """Export user data in specified format with user-selected data types"""
    try:
        user_email = current_user["email"]
        data_types = export_request.data_types
        format_type = export_request.format_type
        
        print(f"[PRIVACY] Exporting data for user {user_email}, types: {data_types}, format: {format_type}")
        
        # Collect requested data
        export_data = {}
        
        if "profile" in data_types:
            export_data["profile"] = current_user.get("profile", {})
            export_data["user_info"] = {
                "email": current_user.get("email"),
                "username": current_user.get("username"),
                "consent_given": current_user.get("consent_given"),
                "consent_timestamp": current_user.get("consent_timestamp"),
                "policy_version": current_user.get("policy_version"),
                "data_retention_preference": current_user.get("data_retention_preference"),
                "marketing_consent": current_user.get("marketing_consent"),
                "analytics_consent": current_user.get("analytics_consent")
            }
        
        if "meal_plans" in data_types:
            export_data["meal_plans"] = await get_user_meal_plans(user_email, limit=10)
        
        if "consumption_history" in data_types:
            export_data["consumption_history"] = await get_user_consumption_history(user_email, limit=10)
        
        if "chat_history" in data_types:
            export_data["chat_history"] = await get_all_user_chat_history(user_email, limit=10)
        
        if "recipes" in data_types:
            export_data["recipes"] = await get_user_recipes(user_email, limit=10)
        
        if "shopping_lists" in data_types:
            export_data["shopping_lists"] = await get_user_shopping_lists(user_email, limit=10)
        
        # Generate document based on format
        if format_type == "pdf":
            return await generate_data_export_pdf(export_data, current_user)
        elif format_type == "json":
            # Limit data to last 10 items for consistency
            limited_export_data = {}
            for key, value in export_data.items():
                if isinstance(value, list) and len(value) > 10:
                    limited_export_data[key] = value[-10:]  # Last 10 items
                else:
                    limited_export_data[key] = value
            
            # Add comprehensive metadata
            limited_export_data["metadata"] = {
                "export_date": datetime.utcnow().isoformat(),
                "export_date_formatted": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
                "user_email": user_email,
                "patient_name": limited_export_data.get("profile", {}).get("name", "Not specified"),
                "data_types_included": data_types,
                "policy_version": current_user.get("policy_version", "1.0"),
                "consent_status": "granted" if current_user.get("consent_given") else "not_granted",
                "marketing_consent": current_user.get("marketing_consent", False),
                "analytics_consent": current_user.get("analytics_consent", False),
                "data_retention_preference": current_user.get("data_retention_preference", "standard"),
                "total_records": sum(len(v) if isinstance(v, list) else 1 for v in limited_export_data.values() if key != "metadata"),
                "export_format": "json",
                "gdpr_compliance": "Article 20 - Right to Data Portability"
            }
            
            filename = f"health_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            return JSONResponse(
                content=limited_export_data,
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        elif format_type == "docx":
            return await generate_data_export_docx(export_data, current_user)
        else:
            raise HTTPException(status_code=400, detail="Unsupported format type")
            
    except Exception as e:
        print(f"[PRIVACY] Error exporting data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Data export failed: {str(e)}")

@app.delete("/privacy/delete-account")
async def delete_user_account(
    deletion_request: AccountDeletionRequest,
    current_user: User = Depends(get_current_user)
):
    """Delete user account and all associated data"""
    try:
        # Validate confirmation
        if deletion_request.confirmation.upper() != "DELETE":
            raise HTTPException(status_code=400, detail="Invalid confirmation. Please type 'DELETE' to confirm.")
        
        user_email = current_user["email"]
        deletion_type = deletion_request.deletion_type
        
        print(f"[PRIVACY] Account deletion requested for {user_email}, type: {deletion_type}")
        
        if deletion_type == "complete":
            # Delete all user data
            await delete_all_user_data(user_email)
        else:
            # Anonymize user data
            await anonymize_user_data(user_email)
        
        # Log deletion for compliance
        await log_data_deletion(user_email, deletion_type)
        
        return {"message": "Account deletion completed successfully", "deletion_type": deletion_type}
    
    except Exception as e:
        print(f"[PRIVACY] Error deleting account: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Account deletion failed: {str(e)}")

@app.put("/privacy/update-consent")
async def update_user_consent(
    consent_data: ConsentUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """Update user consent preferences"""
    try:
        user_email = current_user["email"]
        
        # Update consent in database
        await update_user_consent_preferences(user_email, consent_data.dict(exclude_unset=True))
        
        return {"message": "Consent preferences updated successfully"}
    
    except Exception as e:
        print(f"[PRIVACY] Error updating consent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Consent update failed: {str(e)}")

# ============================================================================
# PRIVACY HELPER FUNCTIONS
# ============================================================================

async def get_all_user_chat_history(user_email: str, limit: int = None):
    """Get chat history for a user with optional limit"""
    try:
        # Build query with optional TOP clause for database-level limiting
        if limit:
            query = f"""
            SELECT TOP {limit} *
            FROM c
            WHERE c.type = 'chat_message'
            AND c.user_id = '{user_email}'
            ORDER BY c.timestamp DESC
            """
        else:
            query = f"""
            SELECT *
            FROM c
            WHERE c.type = 'chat_message'
            AND c.user_id = '{user_email}'
            ORDER BY c.timestamp ASC
            """
        
        chat_messages = list(interactions_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        return chat_messages
    except Exception as e:
        print(f"Error getting chat history: {str(e)}")
        return []

async def delete_all_user_data(user_email: str):
    """Completely delete all user data"""
    try:
        print(f"[PRIVACY] Starting complete data deletion for {user_email}")
        
        # Delete from interactions container (meal plans, consumption, chat, etc.)
        collections_to_clean = [
            "meal_plan",
            "consumption_record", 
            "chat_message",
            "shopping_list",
            "recipe"
        ]
        
        total_deleted = 0
        for doc_type in collections_to_clean:
            query = f"SELECT * FROM c WHERE c.type = '{doc_type}' AND c.user_id = '{user_email}'"
            items = list(interactions_container.query_items(query=query, enable_cross_partition_query=True))
            
            for item in items:
                try:
                    interactions_container.delete_item(
                        item=item["id"], 
                        partition_key=item.get("session_id", user_email)
                    )
                    total_deleted += 1
                except Exception as e:
                    print(f"Error deleting item {item.get('id')}: {str(e)}")
        
        # Delete user account from user container
        try:
            user_container.delete_item(item=user_email, partition_key=user_email)
            total_deleted += 1
        except Exception as e:
            print(f"Error deleting user account: {str(e)}")
        
        print(f"[PRIVACY] Deleted {total_deleted} records for user {user_email}")
        
    except Exception as e:
        print(f"[PRIVACY] Error in complete data deletion: {str(e)}")
        raise Exception(f"Failed to delete user data: {str(e)}")

async def anonymize_user_data(user_email: str):
    """Anonymize user data while preserving analytics value"""
    try:
        print(f"[PRIVACY] Starting data anonymization for {user_email}")
        
        # Generate anonymous ID
        anonymous_id = f"anon_{uuid.uuid4().hex[:8]}"
        
        # Anonymize user profile
        anonymized_profile = {
            "name": "Anonymized User",
            "age": None,
            "gender": None,
            "medicalConditions": ["Anonymized"],
            "anonymized": True,
            "anonymization_date": datetime.utcnow().isoformat()
        }
        
        # Update user record with anonymized data
        user_update = {
            "username": anonymous_id,
            "email": f"{anonymous_id}@anonymized.local",
            "profile": anonymized_profile,
            "anonymized": True,
            "original_email_hash": hash(user_email),
            "anonymization_date": datetime.utcnow().isoformat()
        }
        
        # Get current user data for anonymization
        current_user_data = await get_user_by_email(user_email)
        if not current_user_data:
            raise Exception("User not found for anonymization")
        
        # Update user in database
        user_container.upsert_item(body={**current_user_data, **user_update})
        
        print(f"[PRIVACY] User {user_email} anonymized as {anonymous_id}")
        
    except Exception as e:
        print(f"[PRIVACY] Error in anonymization: {str(e)}")
        raise Exception(f"Failed to anonymize user data: {str(e)}")

async def log_data_deletion(user_email: str, deletion_type: str):
    """Log data deletion for compliance"""
    try:
        deletion_log = {
            "type": "data_deletion_log",
            "user_email": user_email,
            "deletion_type": deletion_type,
            "timestamp": datetime.utcnow().isoformat(),
            "id": f"deletion_{uuid.uuid4().hex}",
            "session_id": "privacy_logs"
        }
        
        interactions_container.create_item(body=deletion_log)
        print(f"[PRIVACY] Logged {deletion_type} deletion for {user_email}")
        
    except Exception as e:
        print(f"[PRIVACY] Error logging deletion: {str(e)}")

async def update_user_consent_preferences(user_email: str, consent_updates: dict):
    """Update user consent preferences"""
    try:
        # Add timestamp for consent update
        consent_updates["last_consent_update"] = datetime.utcnow().isoformat()
        
        # Get current user data
        current_user_data = await get_user_by_email(user_email)
        if not current_user_data:
            raise Exception("User not found")
        
        # Update user with new consent preferences
        updated_user = {**current_user_data, **consent_updates}
        user_container.upsert_item(body=updated_user)
        
        print(f"[PRIVACY] Updated consent preferences for {user_email}")
        
    except Exception as e:
        print(f"[PRIVACY] Error updating consent: {str(e)}")
        raise Exception(f"Failed to update consent preferences: {str(e)}")

async def generate_data_export_pdf(export_data: dict, user_info: dict):
    """Generate professional PDF export of user data with logo and improved layout"""
    try:
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
        import os
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            rightMargin=72, leftMargin=72,
            topMargin=100, bottomMargin=72,
            title="Health Data Export"
        )
        
        # Custom styles
        styles = getSampleStyleSheet()
        
        # Define custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2E7D32')
        )
        
        section_title_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            spaceBefore=30,
            textColor=colors.HexColor('#1976D2'),
            borderWidth=1,
            borderColor=colors.HexColor('#1976D2'),
            borderPadding=10,
            backColor=colors.HexColor('#E3F2FD')
        )
        
        subsection_style = ParagraphStyle(
            'SubSection',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=15,
            textColor=colors.HexColor('#424242')
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            leading=12,
            alignment=TA_JUSTIFY
        )
        
        story = []
        
        # Header with logo
        def add_logo_header():
            header_content = []
            logo_path = os.path.join(os.path.dirname(__file__), "assets", "coverpage2.png")
            
            if os.path.exists(logo_path):
                try:
                    # Create header table with logo
                    logo_img = RLImage(logo_path, width=2*inch, height=1*inch)
                    header_data = [
                        ["Diabetes Meal Plan Generator", logo_img],
                        ["Personal Health Data Export", ""]
                    ]
                    header_table = Table(header_data, colWidths=[5*inch, 2*inch])
                    header_table.setStyle(TableStyle([
                        ('ALIGN', (0,0), (0,-1), 'LEFT'),
                        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
                        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                        ('FONTSIZE', (0,0), (0,0), 16),
                        ('FONTSIZE', (0,1), (0,1), 12),
                        ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor('#2E7D32')),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
                    ]))
                    header_content.append(header_table)
                except Exception as e:
                    print(f"Error adding logo: {e}")
                    # Fallback without logo
                    header_content.append(Paragraph("Diabetes Meal Plan Generator", title_style))
                    header_content.append(Paragraph("Personal Health Data Export", subsection_style))
            else:
                # Fallback without logo
                header_content.append(Paragraph("Diabetes Meal Plan Generator", title_style))
                header_content.append(Paragraph("Personal Health Data Export", subsection_style))
            
            return header_content
        
        # Add header
        story.extend(add_logo_header())
        story.append(Spacer(1, 30))
        
        # Export metadata
        story.append(Paragraph("Export Information", section_title_style))
        
        export_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        user_profile = export_data.get("profile", {})
        
        metadata_data = [
            ["Export Date:", export_date],
            ["Account Email:", user_info.get("email", "Not specified")],
            ["Patient Name:", user_profile.get("name", "Not specified")],
            ["Data Policy Version:", user_info.get("policy_version", "1.0")],
            ["Consent Status:", "✓ Granted" if user_info.get("consent_given") else "✗ Not granted"],
            ["Marketing Consent:", "✓ Yes" if user_info.get("marketing_consent") else "✗ No"],
            ["Analytics Consent:", "✓ Yes" if user_info.get("analytics_consent") else "✗ No"],
            ["Data Retention:", user_info.get("data_retention_preference", "Standard").title()],
        ]
        
        metadata_table = Table(metadata_data, colWidths=[2.5*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F5F5F5')),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
            ('ALIGN', (0,0), (0,-1), 'RIGHT'),
            ('ALIGN', (1,0), (1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#E0E0E0')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(metadata_table)
        story.append(PageBreak())
        
        # Patient Profile Section
        if "profile" in export_data and export_data["profile"]:
            story.extend(generate_profile_pdf_section(export_data["profile"], styles))
        
        # Meal Plans Section (last 10)
        if "meal_plans" in export_data and export_data["meal_plans"]:
            story.extend(generate_meal_plans_pdf_section(export_data["meal_plans"][-10:], styles))
        
        # Consumption History Section (last 10)
        if "consumption_history" in export_data and export_data["consumption_history"]:
            story.extend(generate_consumption_pdf_section(export_data["consumption_history"][-10:], styles))
        
        # AI Coach Conversations Section (last 10)
        if "chat_history" in export_data and export_data["chat_history"]:
            story.extend(generate_chat_pdf_section(export_data["chat_history"][-10:], styles))
        
        # Recipes Section (last 10)
        if "recipes" in export_data and export_data["recipes"]:
            story.extend(generate_recipes_pdf_section(export_data["recipes"][-10:], styles))
        
        # Shopping Lists Section (last 10)
        if "shopping_lists" in export_data and export_data["shopping_lists"]:
            story.extend(generate_shopping_lists_pdf_section(export_data["shopping_lists"][-10:], styles))
        
        # Privacy Notice Section
        story.append(PageBreak())
        story.append(Paragraph("Privacy & Compliance Notice", section_title_style))
        
        # Privacy Notice Section - split into multiple paragraphs to avoid ReportLab parsing issues
        export_timestamp = datetime.now().isoformat()
        
        privacy_paragraphs = [
            "<b>Data Protection Compliance:</b> This document contains your personal health data exported from the Diabetes Meal Plan Generator system in compliance with the General Data Protection Regulation (GDPR) Article 20 - Right to Data Portability.",
            
            "<b>Data Security:</b> Please store this document securely and do not share it with unauthorized parties. This data export includes sensitive health information that should be protected according to applicable privacy laws.",
            
            "<b>Data Usage:</b> You have the right to use this data for your personal health management, share it with healthcare providers, or transfer it to other compatible health management systems.",
            
            f"<b>Support:</b> For questions about your data, privacy rights, or technical support, please contact our support team at support@diabetesmealplangenerator.com",
            
            f"<b>Export Timestamp:</b> {export_timestamp}"
        ]
        
        for para_text in privacy_paragraphs:
            story.append(Paragraph(para_text, normal_style))
            story.append(Spacer(1, 12))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        filename = f"health_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return StreamingResponse(
            BytesIO(buffer.read()),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        print(f"[PRIVACY] Error generating PDF: {str(e)}")
        raise Exception(f"Failed to generate PDF export: {str(e)}")

def generate_profile_pdf_section(profile: dict, styles):
    """Generate comprehensive profile section for PDF"""
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    
    story = []
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        spaceBefore=30,
        textColor=colors.HexColor('#1976D2'),
        borderWidth=1,
        borderColor=colors.HexColor('#1976D2'),
        borderPadding=10,
        backColor=colors.HexColor('#E3F2FD')
    )
    
    subsection_style = ParagraphStyle(
        'SubSection',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=15,
        textColor=colors.HexColor('#424242')
    )
    
    story.append(Paragraph("Patient Health Profile", section_title_style))
    
    # Demographics
    story.append(Paragraph("Personal Information", subsection_style))
    demo_data = [
        ["Name:", profile.get("name", "Not specified")],
        ["Age:", str(profile.get("age", "Not specified"))],
        ["Gender:", profile.get("gender", "Not specified")],
        ["Date of Birth:", profile.get("dateOfBirth", "Not specified")],
    ]
    
    demo_table = Table(demo_data, colWidths=[2*inch, 4*inch])
    demo_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F8F9FA')),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#DEE2E6')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(demo_table)
    story.append(Spacer(1, 15))
    
    # Medical Information
    story.append(Paragraph("Medical Information", subsection_style))
    medical_conditions = profile.get("medicalConditions", profile.get("medical_conditions", []))
    medications = profile.get("currentMedications", [])
    allergies = profile.get("allergies", [])
    
    medical_data = [
        ["Medical Conditions:", ", ".join(medical_conditions) if medical_conditions else "None specified"],
        ["Current Medications:", ", ".join(medications) if medications else "None specified"],
        ["Allergies:", ", ".join(allergies) if allergies else "None specified"],
    ]
    
    medical_table = Table(medical_data, colWidths=[2*inch, 4*inch])
    medical_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#FFF3E0')),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#FFB74D')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(medical_table)
    story.append(Spacer(1, 15))
    
    # Vital Signs
    if any([profile.get("height"), profile.get("weight"), profile.get("bmi")]):
        story.append(Paragraph("Vital Signs & Measurements", subsection_style))
        vital_data = [
            ["Height:", f"{profile.get('height', 'Not recorded')} cm" if profile.get('height') else "Not recorded"],
            ["Weight:", f"{profile.get('weight', 'Not recorded')} kg" if profile.get('weight') else "Not recorded"],
            ["BMI:", f"{profile.get('bmi', 'Not calculated')}" if profile.get('bmi') else "Not calculated"],
            ["Blood Pressure:", f"{profile.get('systolicBP', 'N/A')}/{profile.get('diastolicBP', 'N/A')} mmHg" if profile.get('systolicBP') else "Not recorded"],
            ["Heart Rate:", f"{profile.get('heartRate', 'Not recorded')} bpm" if profile.get('heartRate') else "Not recorded"],
        ]
        
        vital_table = Table(vital_data, colWidths=[2*inch, 4*inch])
        vital_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#E8F5E8')),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#4CAF50')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(vital_table)
        story.append(Spacer(1, 15))
    
    story.append(PageBreak())
    return story

def generate_meal_plans_pdf_section(meal_plans: List[dict], styles):
    """Generate enhanced meal plans section for PDF"""
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    
    story = []
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        spaceBefore=30,
        textColor=colors.HexColor('#1976D2'),
        borderWidth=1,
        borderColor=colors.HexColor('#1976D2'),
        borderPadding=10,
        backColor=colors.HexColor('#E3F2FD')
    )
    
    subsection_style = ParagraphStyle(
        'SubSection',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=15,
        textColor=colors.HexColor('#424242')
    )
    
    story.append(Paragraph("Meal Plans (Last 10)", section_title_style))
    story.append(Paragraph(f"Total meal plans in system: {len(meal_plans)}", styles['Normal']))
    story.append(Spacer(1, 15))
    
    for i, plan in enumerate(meal_plans[:10], 1):  # Limit to 10
        story.append(Paragraph(f"Meal Plan #{i}", subsection_style))
        
        # Plan Overview
        created_date = plan.get("created_at", "Unknown date")
        daily_calories = plan.get("dailyCalories", "Not specified")
        macros = plan.get("macronutrients", {})
        
        overview_data = [
            ["Created:", created_date],
            ["Daily Calories:", str(daily_calories)],
            ["Carbs:", f"{macros.get('carbs', 'N/A')}%"],
            ["Protein:", f"{macros.get('protein', 'N/A')}%"],
            ["Fat:", f"{macros.get('fat', 'N/A')}%"],
        ]
        
        overview_table = Table(overview_data, colWidths=[1.5*inch, 2*inch])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#FFF8E1')),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#FFD54F')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(overview_table)
        
        # Meals breakdown
        meals = plan.get("meals", {})
        if meals:
            story.append(Spacer(1, 10))
            story.append(Paragraph("Daily Meals:", styles['Heading4']))
            
            meal_data = [["Meal Type", "Description"]]
            for meal_type, meal_list in meals.items():
                if isinstance(meal_list, list) and meal_list:
                    meal_text = "; ".join(meal_list[:3])  # First 3 meals
                    if len(meal_list) > 3:
                        meal_text += f" ... (and {len(meal_list) - 3} more)"
                elif isinstance(meal_list, str):
                    meal_text = meal_list[:100] + "..." if len(meal_list) > 100 else meal_list
                else:
                    meal_text = "Not specified"
                
                meal_data.append([meal_type.title(), meal_text])
            
            meal_table = Table(meal_data, colWidths=[1.5*inch, 4.5*inch])
            meal_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E1F5FE')),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 8),
                ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#81D4FA')),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
                ('RIGHTPADDING', (0,0), (-1,-1), 6),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ]))
            story.append(meal_table)
        
        story.append(Spacer(1, 20))
    
    story.append(PageBreak())
    return story

def generate_consumption_pdf_section(consumption_history: List[dict], styles):
    """Generate enhanced consumption history section for PDF"""
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    
    story = []
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        spaceBefore=30,
        textColor=colors.HexColor('#1976D2'),
        borderWidth=1,
        borderColor=colors.HexColor('#1976D2'),
        borderPadding=10,
        backColor=colors.HexColor('#E3F2FD')
    )
    
    subsection_style = ParagraphStyle(
        'SubSection',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=15,
        textColor=colors.HexColor('#424242')
    )
    
    story.append(Paragraph("Food Consumption History (Last 10)", section_title_style))
    
    if not consumption_history:
        story.append(Paragraph("No consumption records found.", styles['Normal']))
        story.append(PageBreak())
        return story
    
    # Analytics summary
    total_calories = sum(
        record.get("nutritional_info", {}).get("calories", 0) 
        for record in consumption_history 
        if record.get("nutritional_info", {}).get("calories")
    )
    avg_calories = total_calories / len(consumption_history) if consumption_history else 0
    
    story.append(Paragraph("Summary Statistics", subsection_style))
    summary_data = [
        ["Total Records:", str(len(consumption_history))],
        ["Total Calories Logged:", f"{total_calories:.0f} kcal"],
        ["Average Calories per Entry:", f"{avg_calories:.1f} kcal"],
    ]
    
    summary_table = Table(summary_data, colWidths=[2.5*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#E8F5E8')),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#4CAF50')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    # Detailed consumption records
    story.append(Paragraph("Recent Food Entries", subsection_style))
    
    consumption_data = [["Date", "Food", "Portion", "Calories", "Medical Rating"]]
    
    for record in consumption_history[:10]:  # Last 10
        timestamp = record.get("timestamp", "Unknown")
        try:
            from datetime import datetime
            if timestamp != "Unknown":
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_date = dt.strftime("%m/%d/%Y")
            else:
                formatted_date = "Unknown"
        except:
            formatted_date = timestamp
        
        food_name = record.get("food_name", "Unknown food")
        portion = record.get("estimated_portion", "Unknown")
        
        nutrition = record.get("nutritional_info", {})
        calories = nutrition.get("calories", "N/A")
        
        medical_rating = record.get("medical_rating", {})
        rating_score = medical_rating.get("overall_rating", "N/A")
        rating_text = f"{rating_score}/5" if rating_score != "N/A" else "N/A"
        
        consumption_data.append([
            formatted_date,
            food_name[:30] + "..." if len(food_name) > 30 else food_name,
            str(portion)[:20] + "..." if len(str(portion)) > 20 else str(portion),
            f"{calories} kcal" if calories != "N/A" else "N/A",
            rating_text
        ])
    
    consumption_table = Table(consumption_data, colWidths=[1*inch, 2*inch, 1.5*inch, 1*inch, 1*inch])
    consumption_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#FFE0B2')),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#FF9800')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(consumption_table)
    
    story.append(PageBreak())
    return story

def generate_chat_pdf_section(chat_history: List[dict], styles):
    """Generate enhanced AI coach conversations section for PDF"""
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    
    story = []
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        spaceBefore=30,
        textColor=colors.HexColor('#1976D2'),
        borderWidth=1,
        borderColor=colors.HexColor('#1976D2'),
        borderPadding=10,
        backColor=colors.HexColor('#E3F2FD')
    )
    
    subsection_style = ParagraphStyle(
        'SubSection',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=15,
        textColor=colors.HexColor('#424242')
    )
    
    story.append(Paragraph("AI Health Coach Conversations (Last 10)", section_title_style))
    
    if not chat_history:
        story.append(Paragraph("No chat history found.", styles['Normal']))
        story.append(PageBreak())
        return story
    
    story.append(Paragraph(f"Total chat messages: {len(chat_history)}", styles['Normal']))
    story.append(Spacer(1, 15))
    
    # Show conversations in a more readable format
    story.append(Paragraph("Recent Conversations", subsection_style))
    
    for i, message in enumerate(chat_history[-10:], 1):  # Last 10 messages
        role = "You" if message.get("is_user") else "AI Health Coach"
        content = message.get("message_content", "")
        timestamp = message.get("timestamp", "Unknown time")
        
        try:
            from datetime import datetime
            if timestamp != "Unknown time":
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%m/%d/%Y %I:%M %p")
            else:
                formatted_time = "Unknown time"
        except:
            formatted_time = timestamp
        
        # Create conversation entry
        role_color = colors.HexColor('#2196F3') if role == "You" else colors.HexColor('#4CAF50')
        
        conversation_data = [
            [f"{role} - {formatted_time}", ""],
            [content[:500] + "..." if len(content) > 500 else content, ""]
        ]
        
        conversation_table = Table(conversation_data, colWidths=[6*inch, 0.5*inch])
        conversation_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), role_color),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('FONTSIZE', (0,1), (-1,1), 9),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#E0E0E0')),
        ]))
        story.append(conversation_table)
        story.append(Spacer(1, 10))
    
    story.append(PageBreak())
    return story

def generate_recipes_pdf_section(recipes: List[dict], styles):
    """Generate recipes section for PDF"""
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.units import inch
    
    story = []
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        spaceBefore=30,
        textColor=colors.HexColor('#1976D2'),
        borderWidth=1,
        borderColor=colors.HexColor('#1976D2'),
        borderPadding=10,
        backColor=colors.HexColor('#E3F2FD')
    )
    
    story.append(Paragraph("Saved Recipes (Last 10)", section_title_style))
    
    if not recipes:
        story.append(Paragraph("No saved recipes found.", styles['Normal']))
        story.append(PageBreak())
        return story
    
    story.append(Paragraph(f"Total saved recipes: {len(recipes)}", styles['Normal']))
    story.append(Spacer(1, 15))
    
    for i, recipe_collection in enumerate(recipes[:10], 1):  # Last 10
        recipe_list = recipe_collection.get("recipes", [])
        created_date = recipe_collection.get("created_at", "Unknown date")
        
        story.append(Paragraph(f"Recipe Collection #{i} - {created_date}", styles['Heading3']))
        
        if recipe_list:
            for recipe in recipe_list[:5]:  # Show first 5 recipes from each collection
                recipe_name = recipe.get("name", "Unnamed Recipe")
                ingredients = recipe.get("ingredients", [])
                instructions = recipe.get("instructions", "No instructions provided")
                
                story.append(Paragraph(recipe_name, styles['Heading4']))
                story.append(Paragraph(f"<b>Ingredients:</b> {', '.join(ingredients[:10])}", styles['Normal']))
                story.append(Paragraph(f"<b>Instructions:</b> {instructions[:200]}...", styles['Normal']))
                story.append(Spacer(1, 10))
        
        story.append(Spacer(1, 15))
    
    story.append(PageBreak())
    return story

def generate_shopping_lists_pdf_section(shopping_lists: List[dict], styles):
    """Generate shopping lists section for PDF"""
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.units import inch
    
    story = []
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        spaceBefore=30,
        textColor=colors.HexColor('#1976D2'),
        borderWidth=1,
        borderColor=colors.HexColor('#1976D2'),
        borderPadding=10,
        backColor=colors.HexColor('#E3F2FD')
    )
    
    story.append(Paragraph("Shopping Lists (Last 10)", section_title_style))
    
    if not shopping_lists:
        story.append(Paragraph("No shopping lists found.", styles['Normal']))
        story.append(PageBreak())
        return story
    
    story.append(Paragraph(f"Total shopping lists: {len(shopping_lists)}", styles['Normal']))
    story.append(Spacer(1, 15))
    
    for i, shopping_list in enumerate(shopping_lists[:10], 1):  # Last 10
        created_date = shopping_list.get("created_at", "Unknown date")
        items = shopping_list.get("items", [])
        
        story.append(Paragraph(f"Shopping List #{i} - {created_date}", styles['Heading3']))
        
        if items:
            # Group items by category if available
            categorized = {}
            for item in items:
                category = item.get("category", "Miscellaneous")
                if category not in categorized:
                    categorized[category] = []
                categorized[category].append(item.get("name", "Unknown item"))
            
            for category, category_items in categorized.items():
                story.append(Paragraph(f"<b>{category}:</b>", styles['Heading4']))
                items_text = ", ".join(category_items)
                story.append(Paragraph(items_text, styles['Normal']))
                story.append(Spacer(1, 8))
        
        story.append(Spacer(1, 15))
    
    story.append(PageBreak())
    return story

async def generate_data_export_docx(export_data: dict, user_info: dict):
    """Generate simplified DOCX export using HTML format"""
    try:
        # Limit data to last 10 items for consistency
        limited_export_data = {}
        for key, value in export_data.items():
            if isinstance(value, list) and len(value) > 10:
                limited_export_data[key] = value[-10:]  # Last 10 items
            else:
                limited_export_data[key] = value
        
        # Create a comprehensive text-based export that can be saved as DOCX
        export_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        user_profile = limited_export_data.get("profile", {})
        
        content = f"""
        DIABETES MEAL PLAN GENERATOR
        Personal Health Data Export
        
        ========================================
        EXPORT INFORMATION
        ========================================
        
        Export Date: {export_date}
        Account Email: {user_info.get("email", "Not specified")}
        Patient Name: {user_profile.get("name", "Not specified")}
        Data Policy Version: {user_info.get("policy_version", "1.0")}
        Consent Status: {"✓ Granted" if user_info.get("consent_given") else "✗ Not granted"}
        Marketing Consent: {"✓ Yes" if user_info.get("marketing_consent") else "✗ No"}
        Analytics Consent: {"✓ Yes" if user_info.get("analytics_consent") else "✗ No"}
        Data Retention: {user_info.get("data_retention_preference", "Standard").title()}
        
        ========================================
        PATIENT HEALTH PROFILE
        ========================================
        
        Personal Information:
        - Name: {user_profile.get("name", "Not specified")}
        - Age: {user_profile.get("age", "Not specified")}
        - Gender: {user_profile.get("gender", "Not specified")}
        - Date of Birth: {user_profile.get("dateOfBirth", "Not specified")}
        
        Medical Information:
        - Medical Conditions: {", ".join(user_profile.get("medicalConditions", user_profile.get("medical_conditions", []))) or "None specified"}
        - Current Medications: {", ".join(user_profile.get("currentMedications", [])) or "None specified"}
        - Allergies: {", ".join(user_profile.get("allergies", [])) or "None specified"}
        
        """
        
        # Add meal plans section
        if "meal_plans" in limited_export_data and limited_export_data["meal_plans"]:
            content += "\n========================================\n"
            content += "MEAL PLANS (LAST 10)\n"
            content += "========================================\n\n"
            
            for i, plan in enumerate(limited_export_data["meal_plans"][:10], 1):
                content += f"Meal Plan #{i}\n"
                content += f"Created: {plan.get('created_at', 'Unknown date')}\n"
                content += f"Daily Calories: {plan.get('dailyCalories', 'Not specified')}\n"
                macros = plan.get("macronutrients", {})
                content += f"Macros - Carbs: {macros.get('carbs', 'N/A')}%, Protein: {macros.get('protein', 'N/A')}%, Fat: {macros.get('fat', 'N/A')}%\n\n"
        
        # Add consumption history section
        if "consumption_history" in limited_export_data and limited_export_data["consumption_history"]:
            content += "\n========================================\n"
            content += "FOOD CONSUMPTION HISTORY (LAST 10)\n"
            content += "========================================\n\n"
            
            for record in limited_export_data["consumption_history"][:10]:
                content += f"Date: {record.get('timestamp', 'Unknown')}\n"
                content += f"Food: {record.get('food_name', 'Unknown food')}\n"
                content += f"Portion: {record.get('estimated_portion', 'Unknown')}\n"
                nutrition = record.get("nutritional_info", {})
                content += f"Calories: {nutrition.get('calories', 'N/A')} kcal\n"
                medical_rating = record.get("medical_rating", {})
                rating_score = medical_rating.get("overall_rating", "N/A")
                content += f"Medical Rating: {rating_score}/5\n\n"
        
        # Add chat history section
        if "chat_history" in limited_export_data and limited_export_data["chat_history"]:
            content += "\n========================================\n"
            content += "AI HEALTH COACH CONVERSATIONS (LAST 10)\n"
            content += "========================================\n\n"
            
            for message in limited_export_data["chat_history"][-10:]:
                role = "You" if message.get("is_user") else "AI Health Coach"
                content += f"{role}: {message.get('message_content', '')}\n"
                content += f"Time: {message.get('timestamp', 'Unknown time')}\n\n"
        
        # Add privacy notice
        content += "\n========================================\n"
        content += "PRIVACY & COMPLIANCE NOTICE\n"
        content += "========================================\n\n"
        content += """Data Protection Compliance: This document contains your personal health data exported from the Diabetes Meal Plan Generator system in compliance with the General Data Protection Regulation (GDPR) Article 20 - Right to Data Portability.

Data Security: Please store this document securely and do not share it with unauthorized parties. This data export includes sensitive health information that should be protected according to applicable privacy laws.

Data Usage: You have the right to use this data for your personal health management, share it with healthcare providers, or transfer it to other compatible health management systems.

Support: For questions about your data, privacy rights, or technical support, please contact our support team at support@diabetesmealplangenerator.com

Export Timestamp: """ + datetime.now().isoformat()
        
        # Return as downloadable text file that can be opened in Word
        filename = f"health_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        print(f"[PRIVACY] Error generating DOCX: {str(e)}")
        # Fallback to JSON if DOCX generation fails
        return JSONResponse(content={
            "message": "DOCX export encountered an error, providing JSON format instead",
            "error": str(e),
            "data": limited_export_data,
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "format": "json_fallback"
            }
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 