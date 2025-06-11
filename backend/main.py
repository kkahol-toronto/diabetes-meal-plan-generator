from fastapi import FastAPI, HTTPException, Depends, status, Request, Body, File, UploadFile, Form
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
)
import uuid
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
import re
import traceback
import sys
from fastapi import Request as FastAPIRequest
from PIL import Image
import base64
from fastapi import APIRouter

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

class UserInDB(User):
    hashed_password: str

class Patient(BaseModel):
    name: str = Field(..., min_length=1, description="Patient's full name")
    phone: str = Field(..., min_length=10, description="Patient's phone number")
    condition: str = Field(..., min_length=1, description="Patient's medical condition")
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
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
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
        "name": patient_name
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

def generate_meal_plan_prompt(user_profile: UserProfile) -> str:
    """Legacy function - now redirects to comprehensive profile handling"""
    # This function is deprecated - the main endpoint now uses comprehensive profiling
    return "This function has been replaced with comprehensive profile analysis"

def generate_recipe_prompt(meal_name: str, user_profile: UserProfile) -> str:
    """Legacy function - now redirects to comprehensive profile handling"""
    # This function is deprecated - the main endpoint now uses comprehensive profiling
    return "This function has been replaced with comprehensive profile analysis"

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

        # Define a simpler JSON structure based on selected days
        example_meals = {
            "breakfast": ["Oatmeal with berries", "Whole grain toast with eggs"],
            "lunch": ["Grilled chicken salad", "Quinoa bowl"],
            "dinner": ["Baked salmon", "Steamed vegetables"],
            "snacks": ["Apple with almonds", "Greek yogurt"]
        }
        
        # Adjust example structure based on number of days
        json_structure_meals = {}
        for meal_type, examples in example_meals.items():
            if days <= 2:
                json_structure_meals[meal_type] = examples[:days]
            else:
                # For more than 2 days, provide appropriate number of examples
                json_structure_meals[meal_type] = examples + [f"Day {i+3} {meal_type}" for i in range(max(0, days - 2))]
        
        json_structure = f"""
{{
    "breakfast": {json_structure_meals["breakfast"]},
    "lunch": {json_structure_meals["lunch"]},
    "dinner": {json_structure_meals["dinner"]},
    "snacks": {json_structure_meals["snacks"]},
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
- Consider medical conditions for ingredient selection
- Match calorie target and dietary features
- Keep meal names concise but descriptive
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
- Consider medical conditions for ingredient selection
- Match calorie target and dietary features
- Keep meal names concise but descriptive
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
            "image_url": img_str
        }
        
        print(f"[analyze_and_record_food] Prepared consumption data: {consumption_data}")
        
        # Save to consumption history
        print(f"[analyze_and_record_food] Attempting to save consumption record for user {current_user['id']}")
        consumption_record = await save_consumption_record(current_user["id"], consumption_data)
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
                current_user["id"],
                summary_message,
                is_user=False,
                session_id=session_id
            )
            print("[analyze_and_record_food] Successfully saved chat messages")
        
        return {
            "success": True,
            "consumption_record_id": consumption_record["id"],
            "analysis": analysis_data
        }
        
    except Exception as e:
        print(f"[analyze_and_record_food] Error: {str(e)}")
        print(f"[analyze_and_record_food] Full error details:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/consumption/history")
async def get_consumption_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get user's consumption history"""
    try:
        print(f"[get_consumption_history] Starting request for user {current_user['id']}")
        print(f"[get_consumption_history] User data: {current_user}")
        
        history = await get_user_consumption_history(current_user["id"], limit)
        print(f"[get_consumption_history] Retrieved {len(history)} records")
        print(f"[get_consumption_history] First record (if any): {history[0] if history else 'No records'}")
        
        return history  # Return the records directly
    except Exception as e:
        print(f"[get_consumption_history] Error: {str(e)}")
        print(f"[get_consumption_history] Full error details:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/consumption/analytics")
async def get_consumption_analytics_endpoint(
    days: int = 7,
    current_user: User = Depends(get_current_user)
):
    """Get consumption analytics for specified period"""
    try:
        analytics = await get_consumption_analytics(current_user["id"], days)
        return analytics
    except Exception as e:
        print(f"Error getting consumption analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
                        yield content
            except Exception as e:
                print(f"Error in streaming response: {str(e)}")
                if full_message:
                    yield full_message
            
            # Save the complete assistant message after streaming
            if full_message:
                await save_chat_message(
                    current_user["id"],
                    full_message,
                    is_user=False,
                    session_id=user_message["session_id"],
                    image_url=img_str
                )
        
        return StreamingResponse(generate(), media_type="text/plain")
        
    except Exception as e:
        print(f"Error in image analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper for intent detection
def has_logging_intent(message: str) -> bool:
    logging_intents = [
        "log this", "add this to my history", "record this", "save this",
        "log it", "add this meal", "add this food", "log meal", "log food"
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
    current_user: User = Depends(get_current_user)
):
    """
    Accepts a chat message with optional image.
    If logging intent is detected, logs the meal after image analysis.
    """
    image_url = None
    img_str = None
    analysis_data = None

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

    # If there's an image, analyze it (reuse logic from /consumption/analyze-and-record)
    if img_str:
        # Generate structured analysis using OpenAI (copied from /consumption/analyze-and-record)
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
        analysis_text = response.choices[0].message.content
        try:
            import json
            start_idx = analysis_text.find('{')
            end_idx = analysis_text.rfind('}') + 1
            json_str = analysis_text[start_idx:end_idx]
            analysis_data = json.loads(json_str)
        except Exception:
            analysis_data = None

    # Nutrition question intent detection
    nutrition_fields = extract_nutrition_question(message)

    # Detect logging intent in the message
    if has_logging_intent(message) and analysis_data:
        # Prepare consumption data (copied from /consumption/analyze-and-record)
        consumption_data = {
            "food_name": analysis_data.get("food_name"),
            "estimated_portion": analysis_data.get("estimated_portion"),
            "nutritional_info": analysis_data.get("nutritional_info", {}),
            "medical_rating": analysis_data.get("medical_rating", {}),
            "image_analysis": analysis_data.get("analysis_notes"),
            "image_url": img_str
        }
        await save_consumption_record(current_user["id"], consumption_data)
        # Optionally, save a chat message confirming the log
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
            current_user["id"],
            summary_message,
            is_user=False,
            session_id=session_id
        )

    # Generate assistant response
    assistant_message = None
    if img_str and analysis_data:
        if nutrition_fields:
            # Focused answer for specific nutrition question(s)
            nutri = analysis_data.get('nutritional_info', {})
            food_name = analysis_data.get('food_name', 'this food')
            portion = analysis_data.get('estimated_portion', '')
            responses = []
            for field in nutrition_fields:
                value = nutri.get(field, None)
                if value is not None:
                    # Friendly field name
                    field_label = field.capitalize()
                    unit = 'mg' if field == 'sodium' else 'g' if field in ['protein', 'carbohydrates', 'fat', 'fiber', 'sugar'] else 'kcal' if field == 'calories' else ''
                    responses.append(f"{field_label} in {food_name} ({portion}): {value} {unit}".strip())
            if responses:
                assistant_message = '\n'.join(responses)
            else:
                assistant_message = "Sorry, I couldn't find that nutrition info for this food."
        else:
            # Full analysis as before
            assistant_message = f"Here's the analysis for your image:\n\n{analysis_data}"
    else:
        assistant_message = "Message received."

    await save_chat_message(
        current_user["id"],
        assistant_message,
        is_user=False,
        session_id=session_id
    )

    return {"success": True}

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
    meal_plans = await get_user_meal_plans(current_user["id"])
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
        f"AND c.user_id = '{current_user['id']}' "
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
    weekly = await get_consumption_analytics(current_user["id"], days=7)
    monthly = await get_consumption_analytics(current_user["id"], days=30)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 