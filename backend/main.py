from fastapi import FastAPI, Depends, HTTPException, status, Request, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, EmailStr, Field, ValidationError
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
from twilio.rest import Client
from openai import AzureOpenAI
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from logging.handlers import RotatingFileHandler
import os
import json
import openai
import asyncio
import re
import io
import base64
import uuid
import pytz
import traceback
import logging
import sys
import random
import string

# Import database functions
from database import (
    create_user,
    get_user_by_email,
    get_patient_by_registration_code,
    create_patient,
    get_all_patients,
    save_meal_plan,
    get_patient_profile,
    save_patient_profile,
    get_user_recipes,
    save_chat_message,
    get_user_meal_plans,
    get_user_shopping_lists,
    save_shopping_list,
    save_recipes,
    get_recent_chat_history,
    get_user_sessions,
    clear_chat_history,
    delete_meal_plan_by_id,
    delete_all_user_meal_plans,
    interactions_container,
    get_user_email_by_patient_id
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            'app.log',
            maxBytes=10000000,
            backupCount=5
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(title="Diabetes Diet Manager API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Add trusted hosts middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Replace with your domain in production
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
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 30

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

class UserInDB(User):
    hashed_password: str

class Patient(BaseModel):
    name: str = Field(..., min_length=1, description="Patient's full name")
    phone: str = Field(..., min_length=10, description="Patient's phone number")
    condition: str = Field(..., min_length=1, description="Patient's medical condition")
    registration_code: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "phone": "1234567890",
                "condition": "Type 2 Diabetes"
            }
        }

class UserProfile(BaseModel):
    age: int
    gender: str
    medical_conditions: List[str]
    height: float
    weight: float
    waist_circumference: float
    systolic_bp: int
    diastolic_bp: int
    heart_rate: int
    ethnicity: str
    diet_type: str
    calories_target: int
    diet_features: List[str]
    weight_loss_goal: bool

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

class PatientProfile(BaseModel):
    # Date of Intake
    intakeDate: Optional[str] = None
    intakeDateUpdatedBy: Optional[str] = None  # 'admin' or 'user'

    # Patient Demographics
    fullName: Optional[str] = None
    fullNameUpdatedBy: Optional[str] = None
    dateOfBirth: Optional[str] = None
    dateOfBirthUpdatedBy: Optional[str] = None
    age: Optional[int] = None
    ageUpdatedBy: Optional[str] = None
    sex: Optional[str] = None
    sexUpdatedBy: Optional[str] = None
    ethnicity: Optional[List[str]] = None
    ethnicityUpdatedBy: Optional[str] = None
    ethnicityOther: Optional[str] = None
    ethnicityOtherUpdatedBy: Optional[str] = None

    # Medical History
    medicalHistory: Optional[List[str]] = None
    medicalHistoryUpdatedBy: Optional[str] = None
    medicalHistoryOther: Optional[str] = None
    medicalHistoryOtherUpdatedBy: Optional[str] = None

    # Current Medications
    medications: Optional[List[str]] = None
    medicationsUpdatedBy: Optional[str] = None
    medicationsOther: Optional[str] = None
    medicationsOtherUpdatedBy: Optional[str] = None

    # Most Recent Lab Values
    labValues: Optional[Dict[str, Optional[float]]] = None
    labValuesUpdatedBy: Optional[str] = None

    # Vital Signs
    vitalSigns: Optional[Dict[str, Optional[float]]] = None
    vitalSignsUpdatedBy: Optional[str] = None

    # Dietary Information
    dietaryInfo: Optional[Dict[str, Any]] = None
    dietaryInfoUpdatedBy: Optional[str] = None

    # Physical Activity Profile
    physicalActivity: Optional[Dict[str, Any]] = None
    physicalActivityUpdatedBy: Optional[str] = None

    # Lifestyle & Preferences
    lifestyle: Optional[Dict[str, Any]] = None
    lifestyleUpdatedBy: Optional[str] = None

    # Goals & Readiness to Change
    goals: Optional[List[str]] = None
    goalsUpdatedBy: Optional[str] = None
    goalsOther: Optional[str] = None
    goalsOtherUpdatedBy: Optional[str] = None
    readiness: Optional[str] = None
    readinessUpdatedBy: Optional[str] = None

    # Meal Plan Targeting
    mealPlanTargeting: Optional[Dict[str, Any]] = None
    mealPlanTargetingUpdatedBy: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "intakeDate": "2024-03-20",
                "intakeDateUpdatedBy": "admin",
                "fullName": "John Doe",
                "fullNameUpdatedBy": "user",
                "dateOfBirth": "1980-01-01",
                "dateOfBirthUpdatedBy": "admin",
                "age": 44,
                "ageUpdatedBy": "admin",
                "sex": "Male",
                "sexUpdatedBy": "admin",
                "ethnicity": ["Caucasian"],
                "ethnicityUpdatedBy": "admin",
                "medicalHistory": ["Type 2 Diabetes"],
                "medicalHistoryUpdatedBy": "admin",
                "medications": ["Metformin"],
                "medicationsUpdatedBy": "admin",
                "labValues": {
                    "a1c": 7.2,
                    "fastingGlucose": 6.5
                },
                "labValuesUpdatedBy": "admin",
                "vitalSigns": {
                    "heightCm": 175,
                    "weightKg": 80,
                    "bmi": 26.1
                },
                "vitalSignsUpdatedBy": "admin"
            }
        }

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
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

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
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        user = await get_user_by_email(form_data.username)
        if not user or not verify_password(form_data.password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is admin and include in token
        token_data = {"sub": user["email"]}
        if user.get("is_admin"):
            token_data["is_admin"] = True
            
        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data=token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login"
        )

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
    user_data = {
        "username": data.email,
        "email": data.email,
        "hashed_password": hashed_password,
        "disabled": False,
        "patient_id": patient["id"]
    }
    
    await create_user(user_data)
    return {"message": "Registration successful"}

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
        
        # Enrich patients with email information
        enriched_patients = []
        for patient in patients:
            patient_data = dict(patient)  # Convert to regular dict
            # Try to get the associated user email
            try:
                user_email = await get_user_email_by_patient_id(patient['id'])
                if user_email:
                    patient_data['email'] = user_email
                else:
                    patient_data['email'] = 'Not registered'
            except Exception:
                patient_data['email'] = 'Error fetching email'
            
            enriched_patients.append(patient_data)
        
        return enriched_patients
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

def generate_meal_plan_prompt(user_profile: UserProfile) -> str:
    return f"""Generate a detailed meal plan for a person with the following profile:
Age: {user_profile.age}
Gender: {user_profile.gender}
Medical Conditions: {', '.join(user_profile.medical_conditions)}
Height: {user_profile.height} cm
Weight: {user_profile.weight} kg
Waist Circumference: {user_profile.waist_circumference} cm
Blood Pressure: {user_profile.systolic_bp}/{user_profile.diastolic_bp}
Heart Rate: {user_profile.heart_rate} bpm
Ethnicity: {user_profile.ethnicity}
Diet Type: {user_profile.diet_type}
Calories Target: {user_profile.calories_target} kcal
Diet Features: {', '.join(user_profile.diet_features)}
Weight Loss Goal: {'Yes' if user_profile.weight_loss_goal else 'No'}

Please provide:
1. Daily calorie and macronutrient breakdown
2. Detailed meal plan for each day of the week
3. Include saturated fat, unsaturated fat, omega-3, and omega-6 breakdown
4. Ensure the plan is suitable for the specified medical conditions
5. Consider cultural preferences based on ethnicity
6. Follow the specified diet type and features

Format the response as a JSON object with the following structure:
{{
    "dailyCalories": number,
    "macronutrients": {{
        "protein": number,
        "carbs": number,
        "fats": number,
        "saturatedFat": number,
        "unsaturatedFat": number,
        "omega3": number,
        "omega6": number
    }},
    "meals": {{
        "breakfast": [
            {{
                "name": string,
                "calories": number,
                "macronutrients": {{
                    "protein": number,
                    "carbs": number,
                    "fats": number
                }}
            }}
        ],
        "lunch": [...],
        "dinner": [...],
        "snacks": [...]
    }}
}}"""

def generate_recipe_prompt(meal_name: str, user_profile: UserProfile) -> str:
    return f"""Generate a detailed recipe for {meal_name} that is suitable for a person with the following profile:
Medical Conditions: {', '.join(user_profile.medical_conditions)}
Diet Type: {user_profile.diet_type}
Diet Features: {', '.join(user_profile.diet_features)}

Please provide:
1. List of ingredients with amounts and preparation instructions
2. Step-by-step cooking instructions
3. Nutritional information
4. Ensure the recipe is suitable for the specified medical conditions
5. Follow the specified diet type and features

Format the response as a JSON object with the following structure:
{{
    "name": string,
    "ingredients": [
        {{
            "name": string,
            "amount": string,
            "preparation": string
        }}
    ],
    "instructions": [string],
    "nutritionalInfo": {{
        "calories": number,
        "protein": number,
        "carbs": number,
        "fats": number
    }}
}}"""

@app.post("/generate-meal-plan")
async def generate_meal_plan(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    try:
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

        data = await request.json()
        user_profile = data.get('user_profile', {})

        print('user_profile received:', user_profile)
        print("/generate-meal-plan endpoint called")
        print(f"Current user: {current_user}")
        print(f"User profile received: {user_profile}")
        print("Model:", os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"))
        print("Endpoint:", os.getenv("AZURE_OPENAI_ENDPOINT"))
        print("API Version:", os.getenv("AZURE_OPENAI_API_VERSION"))

        # Define a simpler JSON structure
        json_structure = """
{
    "breakfast": ["Oatmeal with berries", "Whole grain toast with eggs"],
    "lunch": ["Grilled chicken salad", "Quinoa bowl"],
    "dinner": ["Baked salmon", "Steamed vegetables"],
    "snacks": ["Apple with almonds", "Greek yogurt"],
    "dailyCalories": 2000,
    "macronutrients": {
        "protein": 100,
        "carbs": 250,
        "fats": 70
    }
}"""

        # Construct the prompt dynamically, including lab values if available
        prompt_parts = [
            "Create a diabetes-friendly meal plan based on this profile:",
            f"Name: {user_profile.get('fullName', 'Not provided')}",
            f"Age: {user_profile.get('age', 'Not provided')}",
            f"Sex: {user_profile.get('sex', 'Not provided')}",
            f"Weight: {user_profile.get('vitalSigns', {}).get('weightKg', 'Not provided')} kg",
            f"Height: {user_profile.get('vitalSigns', {}).get('heightCm', 'Not provided')} cm",
            f"Ethnicity: {', '.join(user_profile.get('ethnicity', []) or ['Not provided'])}",
            f"Medical History: {', '.join(user_profile.get('medicalHistory', []) or ['None'])}",
            f"Medications: {', '.join(user_profile.get('medications', []) or ['None'])}",
            f"Diet Type: {user_profile.get('dietaryInfo', {}).get('dietType', 'Not provided')}",
            f"Diet Features: {', '.join(user_profile.get('dietaryInfo', {}).get('dietFeatures', []) or ['None'])}",
            f"Allergies: {user_profile.get('dietaryInfo', {}).get('allergies', 'None')}",
            f"Food Dislikes: {user_profile.get('dietaryInfo', {}).get('dislikes', 'None')}",
            f"Physical Activity Level: {user_profile.get('physicalActivity', {}).get('workActivityLevel', 'Not provided')}",
            f"Exercise Frequency: {user_profile.get('physicalActivity', {}).get('exerciseFrequency', 'Not provided')}",
            f"Exercise Types: {', '.join(user_profile.get('physicalActivity', {}).get('exerciseTypes', []) or ['None'])}",
            f"Mobility Issues: {user_profile.get('physicalActivity', {}).get('mobilityIssues', 'Not provided')}",
            f"Meal Prep Method: {user_profile.get('lifestyle', {}).get('mealPrepMethod', 'Not provided')}",
            f"Available Appliances: {', '.join(user_profile.get('lifestyle', {}).get('availableAppliances', []) or ['None'])}",
            f"Eating Schedule: {user_profile.get('lifestyle', {}).get('eatingSchedule', 'Not provided')}",
            f"Goals: {', '.join(user_profile.get('goals', []) or ['None'])}",
            f"Readiness to Change: {user_profile.get('readiness', 'Not provided')}",
            f"Wants Weight Loss: {user_profile.get('mealPlanTargeting', {}).get('wantsWeightLoss', 'Not provided')}",
            f"Calorie Target: {user_profile.get('mealPlanTargeting', {}).get('calorieTarget', 'Not provided')}",
        ]

        # Add lab values only if the labValues dictionary exists and is not empty
        lab_values = user_profile.get('labValues', {})
        if lab_values:
            lab_value_strings = []
            if lab_values.get('a1c') is not None:
                 lab_value_strings.append(f"A1C: {lab_values['a1c']}%")
            if lab_values.get('fastingGlucose') is not None:
                 lab_value_strings.append(f"Fasting Glucose: {lab_values['fastingGlucose']} mg/dL")
            if lab_values.get('ldlC') is not None:
                 lab_value_strings.append(f"LDL-C: {lab_values['ldlC']} mg/dL")
            if lab_values.get('hdlC') is not None:
                 lab_value_strings.append(f"HDL-C: {lab_values['hdlC']} mg/dL")
            if lab_values.get('triglycerides') is not None:
                 lab_value_strings.append(f"Triglycerides: {lab_values['triglycerides']} mg/dL")
            if lab_values.get('totalCholesterol') is not None:
                 lab_value_strings.append(f"Total Cholesterol: {lab_values['totalCholesterol']} mg/dL")
            if lab_values.get('egfr') is not None:
                 lab_value_strings.append(f"eGFR: {lab_values['egfr']} mL/min/1.73 m²")
            if lab_values.get('creatinine') is not None:
                 lab_value_strings.append(f"Creatinine: {lab_values['creatinine']} mg/dL")
            if lab_values.get('potassium') is not None:
                 lab_value_strings.append(f"Potassium: {lab_values['potassium']} mEq/L")
            if lab_values.get('uacr') is not None:
                 lab_value_strings.append(f"UACR: {lab_values['uacr']} mg/g")
            if lab_values.get('alt') is not None:
                 lab_value_strings.append(f"ALT: {lab_values['alt']} U/L")
            if lab_values.get('ast') is not None:
                 lab_value_strings.append(f"AST: {lab_values['ast']} U/L")
            if lab_values.get('vitaminD') is not None:
                 lab_value_strings.append(f"Vitamin D: {lab_values['vitaminD']} nmol/L")
            if lab_values.get('vitaminB12') is not None:
                 lab_value_strings.append(f"Vitamin B12: {lab_values['vitaminB12']} pmol/L")

            if lab_value_strings: # Only add the Lab Values section if there are any non-null values
                prompt_parts.append("\nMost Recent Lab Values:")
                prompt_parts.extend(lab_value_strings)


        prompt_parts.append(f"\nReturn a JSON object with exactly this structure (replace the example values with appropriate ones):\n{json_structure}")

        prompt_parts.append("""
Important:
1. Ensure all meal arrays have exactly 7 items (one for each day of the week)
2. Keep meal names concise
3. Ensure calorie and macronutrient values are numbers, not strings
4. Do not include any explanations or markdown, just the JSON object""")

        prompt = "\n".join(prompt_parts) # Join with newline characters

        print("Prompt for OpenAI:")
        print(prompt)

        try:
            response = client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                messages=[
                    {
                        "role": "system",
                        "content": "You are a meal planning assistant. Always respond with valid JSON matching the exact structure requested. No explanations or markdown."
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

                # Ensure arrays have 7 items
                for meal_type in ['breakfast', 'lunch', 'dinner', 'snacks']:
                    if not isinstance(meal_plan.get(meal_type), list): # Use .get for safety
                        meal_plan[meal_type] = ["Not specified"] * 7
                    while len(meal_plan[meal_type]) < 7:
                        meal_plan[meal_type].append("Not specified")
                    meal_plan[meal_type] = meal_plan[meal_type][:7]  # Trim if too long

                # Ensure macronutrients are numbers
                macro_keys = ['protein', 'carbs', 'fats']
                if isinstance(meal_plan.get('macronutrients'), dict): # Check if macronutrients is a dict
                    for key in macro_keys:
                        if not isinstance(meal_plan['macronutrients'].get(key), (int, float)):
                            meal_plan['macronutrients'][key] = 0
                else: # If macronutrients is not a dict, initialize it
                     meal_plan['macronutrients'] = {"protein": 0, "carbs": 0, "fats": 0}


                if not isinstance(meal_plan.get('dailyCalories'), (int, float)):
                    meal_plan['dailyCalories'] = 2000

                await save_meal_plan(
                    user_id=current_user["email"],
                    meal_plan_data=meal_plan
                )
                print("Meal plan saved to database")

                # Explicitly convert the returned meal_plan to a plain dictionary
                try:
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
    request: Request,
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
    request: Request,
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
                    If an amount seems unrealistic, recompute or cap it to a reasonable upper bound and add a "_note" field explaining the adjustment.

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
    request: Request,
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
    
    # Format user profile information for the system prompt
    profile = current_user.get("profile", {})
    system_prompt = f"""You are a helpful diet assistant for diabetes patients. The user has the following profile:
- Name: {profile.get('name', 'Not specified')}
- Age: {profile.get('age', 'Not specified')}
- Gender: {profile.get('gender', 'Not specified')}
- Weight: {profile.get('weight', 'Not specified')} kg
- Height: {profile.get('height', 'Not specified')} cm
- Waist Circumference: {profile.get('waistCircumference', 'Not specified')} cm
- Blood Pressure: {profile.get('systolicBP', 'Not specified')}/{profile.get('diastolicBP', 'Not specified')} mmHg
- Heart Rate: {profile.get('heartRate', 'Not specified')} bpm
- Ethnicity: {profile.get('ethnicity', 'Not specified')}
- Diet Type: {profile.get('dietType', 'Not specified')}
- Calorie Target: {profile.get('calorieTarget', 'Not specified')} calories
- Diet Features: {', '.join(profile.get('dietFeatures', []))}
- Medical Conditions: {', '.join(profile.get('medicalConditions', []))}
- Allergies: {', '.join(profile.get('allergies', []))}
- Dietary Restrictions: {', '.join(profile.get('dietaryRestrictions', []))}
- Food Preferences: {', '.join(profile.get('foodPreferences', []))}

Provide clear, concise, and accurate information about diet management, meal planning, and general diabetes care, taking into account the user's specific profile and preferences. Focus on recipe, nutrition and exercise queries only. When asking for a recipe ensure you always give a calorie count and nutritional information for the recipe."""
    
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
        max_tokens=800,
        temperature=1.0,
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
                    yield content
        except Exception as e:
            print(f"Error in streaming response: {str(e)}")
            if full_message:
                yield full_message
    
    # Create a streaming response
    streaming_response = StreamingResponse(generate(), media_type="text/plain")
    
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
        "name": patient_name
    }

@app.post("/user/profile")
async def save_user_profile(
    request: Request,
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
    request: Request,
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
        prompt = f"""Generate a detailed recipe for the following meal: {meal_name}\n\nUser profile context: {json.dumps(user_profile, indent=2)}\n\nPlease provide:\n1. A list of ingredients with quantities\n2. Step-by-step preparation instructions\n3. Nutritional information (calories, protein, carbs, fat)\n\nFor all nutritional values, return them as strings with units (e.g., '3g', '115 kcal').\n\nFormat the response as a JSON object with the following structure:\n{{\n    \"name\": \"Recipe Name\",\n    \"ingredients\": [\"ingredient1\", \"ingredient2\", ...],\n    \"instructions\": [\"step1\", \"step2\", ...],\n    \"nutritional_info\": {{\n        \"calories\": \"number with unit, e.g. '115 kcal'\",\n        \"protein\": \"number with unit, e.g. '3g'\",\n        \"carbs\": \"number with unit, e.g. '16g'\",\n        \"fat\": \"number with unit, e.g. '4g'\"\n    }}\n}}"""
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
        raw_content = response.choices[0].message.content
        print("Raw OpenAI response:")
        print(raw_content)
        # Remove Markdown code block if present
        if raw_content.strip().startswith('```'):
            raw_content = re.sub(r'^```[a-zA-Z]*\s*|```$', '', raw_content.strip(), flags=re.MULTILINE).strip()
        try:
            recipe = json.loads(raw_content)
            print("Parsed recipe JSON:")
            print(recipe)
        except Exception as parse_err:
            print("Error parsing OpenAI response as JSON:")
            print(parse_err)
            raise HTTPException(status_code=500, detail=f"OpenAI response not valid JSON: {parse_err}\nRaw response: {raw_content}")
        return recipe
    except Exception as e:
        print(f"Error in /generate-recipe: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
async def save_user_shopping_list(
    request: Request,
    current_user: User = Depends(get_current_user)
):
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
async def save_user_recipes(
    request: Request,
    current_user: User = Depends(get_current_user)
):
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

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.error(f"Validation error: {str(exc)}")
    logger.error(f"Validation error details: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
            "body": exc.model.__name__ if hasattr(exc, 'model') else "Unknown"
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception
):
    logger.error(f"Global error handler caught: {str(exc)}")
    logger.error(traceback.format_exc())
    
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

@app.post("/test-echo")
async def test_echo(current_user: User = Depends(get_current_user)):
    print(">>>> Entered /test-echo endpoint")
    return {"ok": True}

@app.post("/debug/profile")
async def debug_profile_data(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Debug endpoint to log profile data being sent"""
    print(f"[DEBUG] Current user: {current_user.get('email')}")
    print(f"[DEBUG] Is admin: {current_user.get('is_admin')}")
    
    try:
        raw_body = await request.body()
        print(f"[DEBUG] Raw request body length: {len(raw_body)}")
        
        json_data = await request.json()
        print(f"[DEBUG] JSON data keys: {list(json_data.keys())}")
        print(f"[DEBUG] JSON data sample: {str(json_data)[:500]}...")
        
        # Try to parse as PatientProfile
        try:
            profile = PatientProfile(**json_data)
            print(f"[DEBUG] Successfully parsed as PatientProfile")
            return {"status": "success", "message": "Data is valid PatientProfile"}
        except ValidationError as e:
            print(f"[DEBUG] Validation error: {e.errors()}")
            return {
                "status": "validation_error", 
                "errors": e.errors(),
                "received_keys": list(json_data.keys())
            }
        except Exception as e:
            print(f"[DEBUG] Other error: {str(e)}")
            return {"status": "error", "message": str(e)}
            
    except Exception as e:
        print(f"[DEBUG] Failed to parse request: {str(e)}")
        return {"status": "request_error", "message": str(e)}

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
        query = f"SELECT * FROM c WHERE c.type = 'meal_plan' AND c.id = '{plan_id}' AND c.user_id = '{current_user['email']}'"
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

@app.delete("/meal_plans/{plan_id}")
async def delete_meal_plan(
    plan_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Deletes a specific meal plan by ID for the current user."""
    try:
        # Use "email" consistently with how save_meal_plan uses it
        user_id = current_user.get("email")
        if not user_id:
             raise HTTPException(status_code=400, detail="User ID not found in token.")
             
        deleted = await delete_meal_plan_by_id(plan_id, user_id)
        
        if not deleted:
             # Return 404 if the plan wasn't found for *this* user
             raise HTTPException(status_code=404, detail="Meal plan not found or does not belong to user.")
             
        return {"message": f"Meal plan '{plan_id}' deleted successfully"}
        
    except Exception as e:
        print(f"Error in DELETE /meal_plans/{{plan_id}}: {e}")
        # Log the full traceback for better debugging
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

@app.delete("/meal_plans/all") # Use DELETE with a specific path for clarity
async def delete_all_meal_plans_endpoint(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Deletes all meal plans for the current user."""
    try:
        # Use "email" consistently with how save_meal_plan uses it
        user_id = current_user.get("email")
        if not user_id:
             raise HTTPException(status_code=400, detail="User ID not found in token.")

        deleted_count = await delete_all_user_meal_plans(user_id)

        return {"message": f"Successfully deleted all {deleted_count} meal plans for user {user_id}"}

    except Exception as e:
        print(f"Error in DELETE /meal_plans/all: {e}")
        # Log the full traceback for better debugging
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to delete all meal plans: {str(e)}")

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

@app.post("/save-full-meal-plan")
async def save_full_meal_plan_endpoint(
    full_meal_plan_data: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Saves the full meal plan data including recipes and shopping list."""
    try:
        user_id = current_user.get("email") # Or use "id" depending on how you identify users
        if not user_id:
             raise HTTPException(status_code=400, detail="User ID not found in token.")
             
        # The save_meal_plan function in database.py is designed to accept
        # the meal_plan dictionary and use **meal_plan, so we can pass the
        # full_meal_plan_data directly if it contains the required base fields
        # (breakfast, lunch, etc.) plus recipes and shopping_list.
        
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

@app.post("/api/profile/save")
async def save_profile(
    profile: PatientProfile,
    current_user: User = Depends(get_current_user)
):
    """Save or update a patient's profile."""
    try:
        # Convert Pydantic model to dict
        profile_data = profile.dict(exclude_none=True)
        
        # Add updated_by information for each field
        is_admin = current_user.get("is_admin", False)
        updated_by = "admin" if is_admin else "user"
        
        # Get existing profile to merge with
        existing_profile = await get_patient_profile(current_user["email"])
        
        # Update the updated_by fields for changed values
        for key, value in profile_data.items():
            if not key.endswith("UpdatedBy") and value is not None:
                updated_by_key = f"{key}UpdatedBy"
                profile_data[updated_by_key] = updated_by
        
        # Merge with existing profile
        if existing_profile:
            merged_data = {**existing_profile, **profile_data}
        else:
            merged_data = profile_data
        
        # Save to database
        saved_profile = await save_patient_profile(current_user["email"], merged_data)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Profile saved successfully", "profile": saved_profile}
        )
    except Exception as e:
        print(f"[ADMIN SAVE] Error saving profile: {str(e)}")
        print(f"[ADMIN SAVE] Error type: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save profile: {str(e)}"
        )

@app.get("/api/profile/get")
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get a patient's profile."""
    try:
        profile = await get_patient_profile(current_user["email"])
        if not profile:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": "Profile not found"}
            )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"profile": profile}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile: {str(e)}"
        )

@app.get("/api/admin/profile/{user_id}")
async def get_user_profile(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Admin endpoint to get a specific user's profile by patient ID (registration code)."""
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access user profiles"
        )
    
    try:
        # Resolve patient ID (registration code) to user email
        user_email = await get_user_email_by_patient_id(user_id)
        if not user_email:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": "User not found for this patient ID"}
            )
        
        profile = await get_patient_profile(user_email)
        if not profile:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": "Profile not found"}
            )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"profile": profile}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile: {str(e)}"
        )

@app.post("/api/admin/profile/{user_id}")
async def save_user_profile(
    user_id: str,
    profile: PatientProfile,
    current_user: User = Depends(get_current_user)
):
    """Admin endpoint to save a specific user's profile by patient ID (registration code)."""
    print(f"[ADMIN SAVE] Received request for user_id: {user_id}")
    print(f"[ADMIN SAVE] Current user: {current_user.get('email')}")
    print(f"[ADMIN SAVE] Profile data keys: {list(profile.dict().keys()) if profile else 'None'}")
    
    if not current_user.get("is_admin"):
        print(f"[ADMIN SAVE] Access denied - user is not admin")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify user profiles"
        )
    
    try:
        # Resolve patient ID (registration code) to user email
        user_email = await get_user_email_by_patient_id(user_id)
        if not user_email:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found for this patient ID"
            )
        
        # Convert Pydantic model to dict
        profile_data = profile.dict(exclude_none=True)
        
        # Add admin as the updater for all fields
        for key, value in profile_data.items():
            if not key.endswith("UpdatedBy") and value is not None:
                updated_by_key = f"{key}UpdatedBy"
                profile_data[updated_by_key] = "admin"
        
        # Get existing profile to merge with
        existing_profile = await get_patient_profile(user_email)
        
        # Merge with existing profile
        if existing_profile:
            merged_data = {**existing_profile, **profile_data}
        else:
            merged_data = profile_data
        
        # Save to database
        saved_profile = await save_patient_profile(user_email, merged_data)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Profile saved successfully", "profile": saved_profile}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save profile: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 