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
import asyncio
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
import pytz
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

# Robust OpenAI API wrapper with retry logic and better error handling
async def robust_openai_call(
    messages: List[Dict[str, str]], 
    max_tokens: int = 2000, 
    temperature: float = 0.7,
    response_format: Optional[Dict[str, str]] = None,
    max_retries: int = 3,
    timeout: int = 60,
    context: str = "openai_call"
) -> Dict[str, Any]:
    """
    Robust OpenAI API call with retry logic, timeout handling, and comprehensive error handling.
    
    Args:
        messages: List of message dictionaries for the chat completion
        max_tokens: Maximum tokens for the response
        temperature: Temperature for response generation
        response_format: Optional response format (e.g., {"type": "json_object"})
        max_retries: Maximum number of retry attempts
        timeout: Timeout in seconds for each API call
        context: Context string for logging purposes
        
    Returns:
        Dict containing the API response or error information
    """
    
    for attempt in range(max_retries):
        try:
            print(f"[{context}] Attempt {attempt + 1}/{max_retries} - Calling OpenAI API...")
            
            # Prepare the API call parameters
            api_params = {
                "model": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "timeout": timeout
            }
            
            # Add response format if specified
            if response_format:
                api_params["response_format"] = response_format
                
            # Make the API call
            response = client.chat.completions.create(**api_params)
            
            # Validate the response
            if not response.choices or not response.choices[0].message:
                raise ValueError("Empty response from OpenAI API")
                
            raw_content = response.choices[0].message.content
            if not raw_content or not raw_content.strip():
                raise ValueError("Empty content in OpenAI response")
                
            print(f"[{context}] API call successful on attempt {attempt + 1}")
            
            return {
                "success": True,
                "content": raw_content.strip(),
                "usage": response.usage.dict() if response.usage else None,
                "attempt": attempt + 1
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"[{context}] Attempt {attempt + 1} failed: {error_msg}")
            
            # Check if this is a rate limit error
            if "rate_limit" in error_msg.lower() or "429" in error_msg:
                wait_time = min(2 ** attempt, 60)  # Exponential backoff, max 60 seconds
                print(f"[{context}] Rate limit detected, waiting {wait_time} seconds...")
                await asyncio.sleep(wait_time)
                continue
            
            # Check if this is a timeout error
            if "timeout" in error_msg.lower():
                print(f"[{context}] Timeout detected on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(min(2 ** attempt, 60))  # Exponential backoff, max 60 seconds
                    continue
            
            # For other errors, wait a bit before retrying
            if attempt < max_retries - 1:
                wait_time = min(2 ** attempt, 60)  # Exponential backoff, max 60 seconds
                print(f"[{context}] Waiting {wait_time} seconds before retry...")
                await asyncio.sleep(wait_time)
            else:
                # Final attempt failed
                print(f"[{context}] All {max_retries} attempts failed. Last error: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "error_type": type(e).__name__,
                    "attempts": max_retries
                }
                
    # This should never be reached, but just in case
    return {
        "success": False,
        "error": "Maximum retries exceeded",
        "attempts": max_retries
    }

# Helper function to parse JSON with better error handling
def robust_json_parse(json_string: str, context: str = "json_parse") -> Dict[str, Any]:
    """
    Parse JSON string with better error handling and fallback mechanisms.
    
    Args:
        json_string: The JSON string to parse
        context: Context string for logging
        
    Returns:
        Dict containing parsed JSON or error information
    """
    try:
        # First, try to parse as-is
        return {"success": True, "data": json.loads(json_string)}
    except json.JSONDecodeError as e:
        print(f"[{context}] Initial JSON parse failed: {e}")
        
        # Try to extract JSON from the string (in case there's extra text)
        try:
            # Find the first { and last }
            start_idx = json_string.find('{')
            end_idx = json_string.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                extracted_json = json_string[start_idx:end_idx]
                return {"success": True, "data": json.loads(extracted_json)}
        except:
            pass
            
        # Try to clean up common JSON issues
        try:
            # Remove common markdown formatting
            cleaned = json_string.replace('```json', '').replace('```', '')
            cleaned = cleaned.strip()
            
            # Fix common trailing comma issues
            cleaned = re.sub(r',\s*}', '}', cleaned)
            cleaned = re.sub(r',\s*]', ']', cleaned)
            
            return {"success": True, "data": json.loads(cleaned)}
        except:
            pass
            
        # Return error if all parsing attempts failed
        return {
            "success": False,
            "error": f"JSON parsing failed: {str(e)}",
            "raw_content": json_string[:500] + "..." if len(json_string) > 500 else json_string
        }

# Fallback mechanisms for when OpenAI API fails
def generate_fallback_meal_plan(user_profile: dict, days: int = 7) -> dict:
    """
    Generate a fallback meal plan when OpenAI API fails.
    This provides a safe, diabetes-friendly meal plan based on user profile.
    """
    print("[FALLBACK] Generating fallback meal plan...")
    
    # Get dietary restrictions for safe fallback
    dietary_restrictions = user_profile.get('dietaryRestrictions', [])
    allergies = user_profile.get('allergies', [])
    diet_type = user_profile.get('dietType', [])
    
    # Check if user is vegetarian
    is_vegetarian = any('vegetarian' in str(restriction).lower() for restriction in dietary_restrictions + diet_type)
    
    # Check for allergies
    has_egg_allergy = any('egg' in str(allergy).lower() for allergy in allergies)
    has_dairy_allergy = any('dairy' in str(allergy).lower() or 'milk' in str(allergy).lower() for allergy in allergies)
    has_gluten_allergy = any('gluten' in str(allergy).lower() or 'wheat' in str(allergy).lower() for allergy in allergies)
    
    # Safe breakfast options
    breakfast_options = [
        "Oatmeal with berries and cinnamon",
        "Greek yogurt with nuts and seeds",
        "Whole grain toast with avocado",
        "Smoothie with spinach and banana",
        "Chia seed pudding with fruit",
        "Quinoa breakfast bowl with vegetables",
        "Almond butter on whole grain toast"
    ]
    
    # Safe lunch options
    lunch_options = [
        "Quinoa salad with mixed vegetables",
        "Lentil soup with whole grain bread",
        "Chickpea curry with brown rice",
        "Vegetable stir-fry with tofu",
        "Bean and vegetable wrap",
        "Hummus with vegetable sticks",
        "Stuffed bell peppers with quinoa"
    ]
    
    # Safe dinner options
    dinner_options = [
        "Baked sweet potato with black beans",
        "Vegetable curry with brown rice",
        "Grilled vegetables with quinoa",
        "Lentil dal with steamed vegetables",
        "Stuffed zucchini with vegetables",
        "Roasted vegetables with chickpeas",
        "Vegetable soup with whole grain bread"
    ]
    
    # Safe snack options
    snack_options = [
        "Mixed nuts and seeds",
        "Apple slices with almond butter",
        "Carrot sticks with hummus",
        "Berries with Greek yogurt",
        "Cucumber slices with tahini",
        "Roasted chickpeas",
        "Homemade trail mix"
    ]
    
    # Adjust for non-vegetarian users
    if not is_vegetarian:
        lunch_options.extend([
            "Grilled chicken salad with olive oil dressing",
            "Baked salmon with steamed vegetables",
            "Turkey and vegetable wrap"
        ])
        dinner_options.extend([
            "Grilled chicken with roasted vegetables",
            "Baked fish with quinoa and vegetables",
            "Lean beef stir-fry with brown rice"
        ])
    
    # Adjust for allergies
    if has_egg_allergy:
        breakfast_options = [opt for opt in breakfast_options if 'egg' not in opt.lower()]
    
    if has_dairy_allergy:
        breakfast_options = [opt for opt in breakfast_options if 'yogurt' not in opt.lower()]
        snack_options = [opt for opt in snack_options if 'yogurt' not in opt.lower()]
    
    if has_gluten_allergy:
        breakfast_options = [opt for opt in breakfast_options if 'toast' not in opt.lower() and 'bread' not in opt.lower()]
        lunch_options = [opt for opt in lunch_options if 'bread' not in opt.lower() and 'wrap' not in opt.lower()]
        dinner_options = [opt for opt in dinner_options if 'bread' not in opt.lower()]
    
    # Ensure we have enough options
    while len(breakfast_options) < days:
        breakfast_options.extend(breakfast_options)
    while len(lunch_options) < days:
        lunch_options.extend(lunch_options)
    while len(dinner_options) < days:
        dinner_options.extend(dinner_options)
    while len(snack_options) < days:
        snack_options.extend(snack_options)
    
    # Generate meal plan
    meal_plan = {
        "breakfast": breakfast_options[:days],
        "lunch": lunch_options[:days],
        "dinner": dinner_options[:days],
        "snacks": snack_options[:days],
        "dailyCalories": int(user_profile.get('calorieTarget', 2000)),
        "macronutrients": {
            "protein": 100,
            "carbs": 250,
            "fats": 70
        }
    }
    
    print(f"[FALLBACK] Generated fallback meal plan with {days} days")
    return meal_plan

def generate_fallback_recipes(meal_names: List[str]) -> List[dict]:
    """
    Generate fallback recipes when OpenAI API fails.
    This provides basic recipes for common meals.
    """
    print(f"[FALLBACK] Generating fallback recipes for {len(meal_names)} meals...")
    
    # Common diabetes-friendly recipes
    recipe_templates = {
        "oatmeal": {
            "name": "Diabetes-Friendly Oatmeal",
            "ingredients": [
                "1/2 cup rolled oats",
                "1 cup water or unsweetened almond milk",
                "1/4 cup fresh berries",
                "1 tbsp chopped nuts",
                "1/2 tsp cinnamon",
                "1 tsp vanilla extract"
            ],
            "instructions": [
                "Bring water or almond milk to a boil",
                "Add oats and reduce heat to medium",
                "Cook for 5-7 minutes, stirring occasionally",
                "Add cinnamon and vanilla",
                "Top with berries and nuts",
                "Serve warm"
            ],
            "nutritional_info": {
                "calories": 250,
                "protein": 8,
                "carbs": 42,
                "fat": 6
            }
        },
        "quinoa salad": {
            "name": "Diabetes-Friendly Quinoa Salad",
            "ingredients": [
                "1 cup cooked quinoa",
                "1 cup mixed vegetables (cucumber, tomatoes, bell peppers)",
                "2 tbsp olive oil",
                "1 tbsp lemon juice",
                "1/4 cup fresh herbs (parsley, mint)",
                "Salt and pepper to taste"
            ],
            "instructions": [
                "Cook quinoa according to package instructions",
                "Let quinoa cool completely",
                "Dice vegetables into small pieces",
                "Mix quinoa with vegetables",
                "Whisk together olive oil and lemon juice",
                "Add dressing to salad and toss",
                "Season with salt, pepper, and herbs"
            ],
            "nutritional_info": {
                "calories": 320,
                "protein": 12,
                "carbs": 45,
                "fat": 12
            }
        },
        "vegetable soup": {
            "name": "Diabetes-Friendly Vegetable Soup",
            "ingredients": [
                "2 cups mixed vegetables (carrots, celery, onions)",
                "4 cups low-sodium vegetable broth",
                "1 can diced tomatoes",
                "1 cup leafy greens (spinach or kale)",
                "1 tsp herbs (thyme, basil)",
                "Salt and pepper to taste"
            ],
            "instructions": [
                "Heat oil in large pot over medium heat",
                "Add onions and cook until soft",
                "Add other vegetables and cook for 5 minutes",
                "Add broth and diced tomatoes",
                "Bring to boil, then simmer for 20 minutes",
                "Add leafy greens and herbs",
                "Season with salt and pepper"
            ],
            "nutritional_info": {
                "calories": 150,
                "protein": 5,
                "carbs": 25,
                "fat": 3
            }
        }
    }
    
    fallback_recipes = []
    
    for meal_name in meal_names:
        meal_lower = meal_name.lower()
        
        # Try to match with existing templates
        if "oatmeal" in meal_lower:
            recipe = recipe_templates["oatmeal"].copy()
            recipe["name"] = meal_name
        elif "quinoa" in meal_lower or "salad" in meal_lower:
            recipe = recipe_templates["quinoa salad"].copy()
            recipe["name"] = meal_name
        elif "soup" in meal_lower:
            recipe = recipe_templates["vegetable soup"].copy()
            recipe["name"] = meal_name
        else:
            # Generic fallback recipe
            recipe = {
                "name": meal_name,
                "ingredients": [
                    "2 cups mixed vegetables",
                    "1 cup whole grains (quinoa, brown rice, or oats)",
                    "1 tbsp healthy oil (olive or avocado)",
                    "Herbs and spices to taste"
                ],
                "instructions": [
                    "Prepare whole grains according to package instructions",
                    "Cook vegetables until tender",
                    "Combine ingredients",
                    "Season with herbs and spices",
                    "Serve warm"
                ],
                "nutritional_info": {
                    "calories": 280,
                    "protein": 10,
                    "carbs": 40,
                    "fat": 8
                }
            }
        
        fallback_recipes.append(recipe)
    
    print(f"[FALLBACK] Generated {len(fallback_recipes)} fallback recipes")
    return fallback_recipes

# Health Check Endpoint for Azure App Service
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and load balancers"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Diabetes Diet Manager API",
        "version": "1.0.0"
    }

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
    # Electronic Signature Fields
    electronic_signature: Optional[str] = None
    signature_timestamp: Optional[str] = None
    signature_ip_address: Optional[str] = None
    research_consent: Optional[bool] = False

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
    
    # Timezone for proper date filtering
    timezone: Optional[str] = "UTC"

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
    # Electronic Signature Fields
    electronic_signature: str
    signature_timestamp: str
    signature_ip_address: Optional[str] = None
    research_consent: Optional[bool] = False

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

def get_today_utc_boundaries():
    """
    Get today's UTC boundaries for proper daily filtering.
    Returns start and end of today in UTC.
    """
    now_utc = datetime.utcnow()
    
    # Get start of today (00:00:00 UTC)
    start_of_today = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get start of tomorrow (00:00:00 UTC next day)
    start_of_tomorrow = start_of_today + timedelta(days=1)
    
    return start_of_today, start_of_tomorrow

def get_user_timezone_boundaries(user_timezone: str = "UTC"):
    """
    Get today's boundaries in the user's timezone, converted to UTC.
    This ensures proper daily reset at midnight in the user's local time.
    """
    try:
        # For simplicity, just use UTC boundaries for now
        # The user mentioned that time is working correctly across the site
        return get_today_utc_boundaries()
    except Exception as e:
        print(f"Error getting timezone boundaries: {e}")
        # Fall back to UTC boundaries
        return get_today_utc_boundaries()

def filter_today_records(records: List[Dict[str, Any]], user_timezone: str = "UTC") -> List[Dict[str, Any]]:
    """
    Filter consumption records to only include those from today (user's timezone).
    This ensures proper daily reset at midnight.
    """
    start_of_today_utc, start_of_tomorrow_utc = get_user_timezone_boundaries(user_timezone)
    
    today_records = []
    for record in records:
        try:
            timestamp_str = record.get("timestamp", "")
            if not timestamp_str:
                continue
                
            # Parse the timestamp
            record_timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            
            # Remove timezone info for comparison (already in UTC)
            record_timestamp_utc = record_timestamp.replace(tzinfo=None)
            
            # Check if the record is from today
            if start_of_today_utc <= record_timestamp_utc < start_of_tomorrow_utc:
                today_records.append(record)
                
        except Exception as e:
            print(f"Error parsing timestamp for record: {e}")
            continue
    
    return today_records

async def generate_consumption_aware_meal_plan(base_meal_plan: dict, consumption_analysis: dict, remaining_meals: list, user_profile: dict) -> dict:
    """
    Generate a consumption-aware meal plan that properly shows consumed meals vs recommendations.
    This replaces the flawed adaptation logic that was removing consumed meals from display.
    """
    try:
        print(f"[generate_consumption_aware_meal_plan] Creating consumption-aware meal plan")
        
        # Create a new meal plan based on the original
        consumption_aware_plan = base_meal_plan.copy()
        warnings = []
        
        # Get key metrics
        calories_consumed = consumption_analysis["total_calories_consumed"]
        calories_planned = consumption_analysis["total_calories_planned"]
        remaining_calories = max(0, calories_planned - calories_consumed)
        adherence_by_meal = consumption_analysis["adherence_by_meal"]
        meals_consumed = consumption_analysis["meals_consumed"]
        
        print(f"[consumption_aware] Calories consumed: {calories_consumed}, Planned: {calories_planned}, Remaining: {remaining_calories}")
        
        # Process each meal type
        for meal_type in ["breakfast", "lunch", "dinner", "snack"]:
            consumed_meals = meals_consumed.get(meal_type, [])
            
            if consumed_meals:
                # User has consumed this meal type - show what was actually consumed
                consumed_names = [meal["food_name"] for meal in consumed_meals]
                consumed_calories = sum(meal["nutritional_info"].get("calories", 0) for meal in consumed_meals)
                
                # Show the consumed meal(s) with clear labeling to distinguish from recommendations
                if len(consumed_names) == 1:
                    consumption_aware_plan["meals"][meal_type] = f"You ate: {consumed_names[0]} ✓ ({consumed_calories} cal)"
                else:
                    consumption_aware_plan["meals"][meal_type] = f"You ate: {', '.join(consumed_names)} ✓ ({consumed_calories} cal)"
                
                # Check if consumption was excessive for this meal type
                if meal_type == "snack" and consumed_calories > 200:
                    warnings.append(f"🍪 Snack calories ({consumed_calories}) exceeded recommended portion. This was quite heavy - consider compensating with lighter meals tomorrow.")
                elif meal_type in ["breakfast", "lunch", "dinner"] and consumed_calories > 600:
                    warnings.append(f"🍽️ {meal_type.title()} calories ({consumed_calories}) were quite high. This was heavy - balance it out with lighter portions for remaining meals today and tomorrow.")
                
                # Check diabetes suitability
                for meal in consumed_meals:
                    diabetes_rating = meal.get("medical_rating", {}).get("diabetes_suitability", "").lower()
                    if diabetes_rating in ["low", "poor", "not suitable"]:
                        warnings.append(f"⚠️ {meal['food_name']} may not be ideal for diabetes management. Try to choose more diabetes-friendly options for your remaining meals.")
                        
            elif meal_type in remaining_meals:
                # User hasn't consumed this meal type yet - show recommendation
                original_meal = base_meal_plan.get("meals", {}).get(meal_type, "")
                
                # Adjust recommendation based on remaining calories
                if remaining_calories < 200:
                    if meal_type == "snack":
                        consumption_aware_plan["meals"][meal_type] = "Recommended: No additional snacks needed - you've reached your daily calorie goal"
                    else:
                        consumption_aware_plan["meals"][meal_type] = f"Recommended: Light {original_meal.lower()}" if original_meal else "Recommended: Light, low-calorie option"
                elif remaining_calories < 300:
                    if meal_type == "snack":
                        consumption_aware_plan["meals"][meal_type] = "Recommended: Optional small piece of fruit or vegetables if genuinely hungry"
                    else:
                        consumption_aware_plan["meals"][meal_type] = f"Recommended: {original_meal} (lighter portion)" if original_meal else "Recommended: Balanced, moderate portion"
                else:
                    # Normal recommendation
                    consumption_aware_plan["meals"][meal_type] = f"Recommended: {original_meal}" if original_meal else f"Recommended: Healthy {meal_type} option"
                    
            else:
                # Meal time has passed and user didn't consume - just show what was planned
                original_meal = base_meal_plan.get("meals", {}).get(meal_type, "")
                consumption_aware_plan["meals"][meal_type] = original_meal or f"No {meal_type} logged"
        
        # Generate appropriate warnings and comprehensive guidance
        if remaining_calories <= 0:
            if remaining_calories < -300:
                warnings.append("🚨 You've significantly exceeded your daily calorie goal. You shouldn't strictly eat anything more today.")
                warnings.append("💡 Tomorrow, focus on much lighter portions, more vegetables, and perhaps skip snacks to compensate.")
                warnings.append("🏃‍♂️ Consider adding extra physical activity if possible to help balance today's intake.")
            else:
                warnings.append("🚨 You've reached or exceeded your daily calorie goal. You shouldn't strictly eat anything more today.")
                warnings.append("💡 Tomorrow, focus on lighter portions and more vegetables to compensate for today's intake.")
        elif remaining_calories < 200:
            warnings.append("⚠️ You're very close to your daily calorie goal. Only eat if genuinely hungry and choose very light options.")
            warnings.append("💭 Consider having just water, herbal tea, or a small piece of fruit if needed.")
        elif remaining_calories < 400:
            warnings.append("📊 You have limited calories remaining. Choose nutrient-dense, low-calorie foods for the rest of the day.")
        
        # Add warnings to the plan
        if warnings:
            consumption_aware_plan["consumption_warnings"] = warnings
            consumption_aware_plan["notes"] = (consumption_aware_plan.get("notes", "") + " " + " ".join(warnings)).strip()
        
        # Update metadata
        consumption_aware_plan["type"] = "consumption_aware"
        consumption_aware_plan["remaining_calories"] = remaining_calories
        consumption_aware_plan["total_consumed_calories"] = calories_consumed
        consumption_aware_plan["last_updated"] = datetime.utcnow().isoformat()
        
        print(f"[consumption_aware] Generated consumption-aware meal plan with {len(warnings)} warnings")
        
        return consumption_aware_plan
        
    except Exception as e:
        print(f"[generate_consumption_aware_meal_plan] Error: {e}")
        import traceback
        print(traceback.format_exc())
        return base_meal_plan


async def trigger_meal_plan_recalibration(user_email: str, user_profile: dict):
    """
    Comprehensive meal plan recalibration system that triggers after every food log.
    Ensures dietary restrictions are respected and meal plan is updated immediately.
    """
    try:
        print(f"[RECALIBRATION] Starting meal plan recalibration for user {user_email}")
        
        # Get today's consumption including the new log
        today_consumption = await get_today_consumption_records_async(user_email, user_timezone="UTC")
        
        # Calculate calories consumed so far
        calories_consumed = sum(r.get("nutritional_info", {}).get("calories", 0) for r in today_consumption)
        
        # Get user's dietary restrictions and preferences
        dietary_restrictions = user_profile.get('dietaryRestrictions', [])
        dietary_features = user_profile.get('dietaryFeatures', [])
        allergies = user_profile.get('allergies', [])
        diet_type = user_profile.get('dietType', [])
        food_preferences = user_profile.get('foodPreferences', [])
        strong_dislikes = user_profile.get('strongDislikes', [])
        target_calories = int(user_profile.get('calorieTarget', '2000'))
        remaining_calories = max(0, target_calories - calories_consumed)
        
        # Check if user is vegetarian or has restrictions - check all possible fields
        is_vegetarian = (
            'vegetarian' in [r.lower() for r in dietary_restrictions] or 
            'vegetarian' in [d.lower() for d in diet_type] or
            any('vegetarian' in f.lower() for f in dietary_features)
        )
        no_eggs = (
            any('egg' in r.lower() for r in dietary_restrictions) or 
            any('egg' in a.lower() for a in allergies) or
            any('no eggs' in f.lower() for f in dietary_features)
        )
        
        print(f"[RECALIBRATION] User dietary profile: vegetarian={is_vegetarian}, no_eggs={no_eggs}")
        print(f"[RECALIBRATION] Dietary restrictions: {dietary_restrictions}")
        print(f"[RECALIBRATION] Dietary features: {dietary_features}")
        print(f"[RECALIBRATION] Cuisine preferences: {diet_type}")
        print(f"[RECALIBRATION] Allergies: {allergies}")
        print(f"[RECALIBRATION] Calories consumed: {calories_consumed}, remaining: {remaining_calories}")
        
        # Get current meal plan to use as base
        try:
            meal_plans = await get_user_meal_plans(user_email)
            base_meal_plan = meal_plans[0] if meal_plans else None
            
            if not base_meal_plan:
                # Create a basic meal plan if none exists
                base_meal_plan = {
                    "id": f"base_{user_email}_{datetime.utcnow().date().isoformat()}",
                    "date": datetime.utcnow().date().isoformat(),
                    "type": "basic",
                    "meals": {
                        "breakfast": "Healthy breakfast option",
                        "lunch": "Balanced lunch option", 
                        "dinner": "Nutritious dinner option",
                        "snack": "Healthy snack option"
                    },
                    "dailyCalories": target_calories,
                    "created_at": datetime.utcnow().isoformat(),
                    "notes": "Basic meal plan for recalibration"
                }
        except Exception as e:
            print(f"[RECALIBRATION] Error getting meal plans: {e}")
            base_meal_plan = {
                "id": f"fallback_{user_email}_{datetime.utcnow().date().isoformat()}",
                "date": datetime.utcnow().date().isoformat(),
                "type": "fallback",
                "meals": {
                    "breakfast": "Healthy breakfast option",
                    "lunch": "Balanced lunch option", 
                    "dinner": "Nutritious dinner option",
                    "snack": "Healthy snack option"
                },
                "dailyCalories": target_calories,
                "created_at": datetime.utcnow().isoformat(),
                "notes": "Fallback meal plan for recalibration"
            }
        
        # Analyze consumption vs plan
        consumption_analysis = await analyze_consumption_vs_plan(today_consumption, base_meal_plan)
        
        # Determine remaining meals
        current_hour = datetime.utcnow().hour
        remaining_meals = get_remaining_meals_by_time(current_hour)
        
        # Generate consumption-aware meal plan
        fresh_meal_plan = await generate_consumption_aware_meal_plan(
            base_meal_plan,
            consumption_analysis,
            remaining_meals,
            user_profile
        )
        
        # Save the updated meal plan
        if fresh_meal_plan:
            await save_meal_plan(user_email, fresh_meal_plan)
            print(f"[RECALIBRATION] Successfully updated consumption-aware meal plan for user {user_email}")
        
        return fresh_meal_plan
        
    except Exception as e:
        print(f"[RECALIBRATION] Error in meal plan recalibration: {e}")
        import traceback
        print(traceback.format_exc())
        return None

async def generate_fresh_adaptive_meal_plan(user_email: str, today_consumption: list, remaining_calories: int, 
                                          is_vegetarian: bool, no_eggs: bool, dietary_restrictions: list, allergies: list,
                                          diet_type: list = None, food_preferences: list = None, strong_dislikes: list = None):
    """
    Generate a fresh, adaptive meal plan that respects dietary restrictions and current consumption.
    """
    try:
        # Set default values if None
        if diet_type is None:
            diet_type = []
        if food_preferences is None:
            food_preferences = []
        if strong_dislikes is None:
            strong_dislikes = []
        
        today = datetime.utcnow().date()
        current_hour = datetime.utcnow().hour
        
        # Determine what meals are still needed today
        remaining_meals = get_remaining_meals_by_time(current_hour)
        
        # Build restriction warnings for AI
        restriction_warnings = []
        if is_vegetarian:
            restriction_warnings.append("STRICTLY VEGETARIAN - NO MEAT, POULTRY, FISH, OR SEAFOOD")
        if no_eggs:
            restriction_warnings.append("NO EGGS - Avoid all egg-based dishes and ingredients")
        if any('nut' in a.lower() for a in allergies):
            restriction_warnings.append("NUT ALLERGY - Avoid all nuts and nut-based products")
        
        restriction_text = "\n".join([f"⚠️ {warning}" for warning in restriction_warnings])
        
        # Analyze what's been consumed today
        meals_consumed_today = {}
        for record in today_consumption:
            meal_type = record.get("meal_type", "snack")
            food_name = record.get("food_name", "")
            if meal_type not in meals_consumed_today:
                meals_consumed_today[meal_type] = []
            meals_consumed_today[meal_type].append(food_name)
        
        consumed_summary = ""
        for meal_type, foods in meals_consumed_today.items():
            consumed_summary += f"{meal_type.title()}: {', '.join(foods)}\n"
        
        # Build cuisine preference text
        cuisine_text = f"PREFERRED CUISINE TYPE: {', '.join(diet_type) if diet_type else 'Mixed international'}"
        
        # Build additional preferences
        food_preferences_text = f"Food Preferences: {', '.join(food_preferences) if food_preferences else 'None specified'}"
        strong_dislikes_text = f"Strong Dislikes: {', '.join(strong_dislikes) if strong_dislikes else 'None specified'}"
        
        # Calculate total calories already consumed
        calories_consumed = sum(r.get("nutritional_info", {}).get("calories", 0) for r in today_consumption)
        
        # Build intelligent snack recommendation based on remaining calories
        snack_recommendation = ""
        if remaining_calories <= 100:
            snack_recommendation = "No additional snacks needed - you've reached your calorie goal for today"
        elif remaining_calories <= 200:
            snack_recommendation = "Optional light snack only if genuinely hungry (e.g., cucumber slices, herbal tea)"
        elif remaining_calories <= 300:
            snack_recommendation = "Light snack if needed (e.g., 1 small apple, handful of berries)"
        else:
            snack_recommendation = "<specific diverse snack from preferred cuisine>"
        
        # Generate diverse meal options using AI
        prompt = f"""You are a registered dietitian AI creating a fresh, adaptive meal plan for TODAY that respects dietary restrictions and avoids repetition.

USER DIETARY RESTRICTIONS:
{restriction_text if restriction_warnings else "No specific restrictions"}

CUISINE PREFERENCES:
{cuisine_text}
{food_preferences_text}
{strong_dislikes_text}

CURRENT CONSUMPTION TODAY:
{consumed_summary if consumed_summary else "No meals logged yet today"}

REMAINING CALORIES: {remaining_calories} kcal
REMAINING MEALS NEEDED: {', '.join(remaining_meals)}

CRITICAL REQUIREMENTS:
1. ALL dishes must be diabetes-friendly (low glycemic index)
2. ALL dishes must be completely vegetarian and egg-free if restricted
3. STRICTLY FOLLOW THE CUISINE TYPE: {', '.join(diet_type) if diet_type else 'Mixed international'}
4. Provide DIVERSE, SPECIFIC dish names - avoid repetition
5. Consider what user already ate today to suggest complementary meals
6. Adapt portion sizes based on remaining calories
7. Focus on variety - no similar dishes
8. Avoid foods listed in strong dislikes
9. Incorporate food preferences where appropriate
10. **INTELLIGENT SNACK RECOMMENDATIONS** - Be smart about snack needs:
    - If remaining calories ≤ 100: "No additional snacks needed - you've reached your calorie goal"
    - If remaining calories ≤ 200: "Optional light snack only if genuinely hungry"
    - If remaining calories ≤ 300: "Light snack if needed (small portion)"
    - Only recommend full snacks if remaining calories > 300

CUISINE-SPECIFIC MEAL EXAMPLES:
- If Western: "Grilled chicken salad with vinaigrette", "Turkey sandwich with whole grain bread", "Baked salmon with roasted vegetables"
- If Chinese/East Asian: "Steamed fish with vegetables", "Tofu stir-fry with brown rice", "Chicken and vegetable soup"
- If South Asian: "Dal curry with roti", "Vegetable curry with quinoa", "Chicken tikka with cucumber salad"
- If Mediterranean: "Greek salad with grilled chicken", "Hummus with vegetable sticks", "Grilled fish with olive oil"

Generate a complete meal plan for the remaining meals today:

{{
  "meals": {{
    "breakfast": "<specific diverse dish from preferred cuisine>",
    "lunch": "<specific diverse dish from preferred cuisine>",
    "dinner": "<specific diverse dish from preferred cuisine>",
    "snack": "{snack_recommendation}"
  }}
}}

SNACK LOGIC:
- Current remaining calories: {remaining_calories}
- Snack recommendation: {snack_recommendation}
- Use this EXACT snack recommendation if it's a message, otherwise generate a specific snack dish

Ensure maximum variety within the specified cuisine type and completely avoid any meat, poultry, fish, seafood, or egg-based ingredients if restricted."""

        try:
            model_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
            if not model_name:
                raise Exception("AZURE_OPENAI_DEPLOYMENT_NAME not configured")
                
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,  # Higher temperature for more creativity/variety
                max_tokens=600
            )

            ai_content = response.choices[0].message.content
            if not ai_content:
                raise Exception("No content in AI response")
                
            start_idx = ai_content.find('{')
            end_idx = ai_content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                import json
                ai_json = json.loads(ai_content[start_idx:end_idx])
                
                # Apply safety filter to ensure dietary compliance
                safe_meals = {}
                for meal_type, dish in ai_json.get("meals", {}).items():
                    safe_meals[meal_type] = sanitize_vegetarian_meal(dish, is_vegetarian, no_eggs)
                
                # Create the meal plan
                meal_plan = {
                    "id": f"adaptive_{user_email}_{today.isoformat()}_{int(datetime.utcnow().timestamp())}",
                    "date": today.isoformat(),
                    "type": "adaptive_recalibrated",
                    "meals": safe_meals,
                    "dailyCalories": int(remaining_calories) + sum(r.get("nutritional_info", {}).get("calories", 0) for r in today_consumption),
                    "remaining_calories": remaining_calories,
                    "created_at": datetime.utcnow().isoformat(),
                    "consumption_triggered": True,
                    "notes": f"Adaptive meal plan updated after food logging. Remaining calories: {remaining_calories}"
                }
                
                return meal_plan
                
        except Exception as ai_error:
            print(f"[generate_fresh_adaptive_meal_plan] AI error: {ai_error}")
            # Fall back to safe vegetarian options
            return generate_safe_vegetarian_fallback(user_email, remaining_calories, is_vegetarian, no_eggs)
            
    except Exception as e:
        print(f"[generate_fresh_adaptive_meal_plan] Error: {e}")
        return None

def sanitize_vegetarian_meal(meal_text: str, is_vegetarian: bool, no_eggs: bool) -> str:
    """
    Ensure meal is vegetarian and egg-free with strong enforcement.
    """
    if not meal_text:
        return "Vegetarian meal option"
    
    meal_lower = meal_text.lower()
    
    # Check for non-vegetarian ingredients
    non_veg_keywords = ['chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'turkey', 'lamb', 'meat', 'seafood', 'shrimp', 'bacon', 'ham', 'duck', 'goose']
    egg_keywords = ['egg', 'eggs', 'omelet', 'omelette', 'scrambled', 'poached', 'fried egg', 'boiled egg']
    
    if is_vegetarian and any(keyword in meal_lower for keyword in non_veg_keywords):
        return "Vegetarian lentil curry with brown rice and steamed vegetables"
    if no_eggs and any(keyword in meal_lower for keyword in egg_keywords):
        return "Overnight oats with almond milk, chia seeds, and fresh berries"
    
    return meal_text

def generate_safe_vegetarian_fallback(user_email: str, remaining_calories: int, is_vegetarian: bool, no_eggs: bool):
    """
    Generate safe vegetarian fallback meal plan with intelligent snack recommendations.
    """
    today = datetime.utcnow().date()
    
    # Diverse vegetarian options
    vegetarian_options = {
        "breakfast": [
            "Steel-cut oats with almond milk and fresh berries",
            "Quinoa breakfast bowl with coconut yogurt and mango",
            "Chia seed pudding with vanilla and strawberries",
            "Smoothie bowl with spinach, banana, and granola"
        ],
        "lunch": [
            "Mediterranean chickpea salad with cucumber and herbs",
            "Quinoa Buddha bowl with roasted vegetables and tahini",
            "Lentil soup with whole grain bread and mixed greens",
            "Vegetable curry with brown rice and cilantro"
        ],
        "dinner": [
            "Thai-inspired tofu curry with jasmine rice",
            "Stuffed bell peppers with quinoa and vegetables",
            "Lentil dal with naan bread and steamed broccoli",
            "Vegetable stir-fry with tofu and brown rice"
        ],
        "snack": [
            "Apple slices with almond butter",
            "Roasted chickpeas with paprika and lime",
            "Hummus with cucumber slices and whole grain crackers",
            "Mixed nuts and dried fruit (if no nut allergy)"
        ]
    }
    
    # Select diverse options
    import random
    selected_meals = {}
    for meal_type, options in vegetarian_options.items():
        if meal_type == "snack":
            # Apply intelligent snack logic based on remaining calories
            if remaining_calories <= 100:
                selected_meals[meal_type] = "No additional snacks needed - you've reached your calorie goal for today"
            elif remaining_calories <= 200:
                selected_meals[meal_type] = "Optional light snack only if genuinely hungry (e.g., cucumber slices, herbal tea)"
            elif remaining_calories <= 300:
                selected_meals[meal_type] = "Light snack if needed (e.g., 1 small apple, handful of berries)"
            else:
                selected_meals[meal_type] = random.choice(options)
        else:
            selected_meals[meal_type] = random.choice(options)
    
    return {
        "id": f"safe_vegetarian_{user_email}_{today.isoformat()}",
        "date": today.isoformat(),
        "type": "safe_vegetarian_fallback",
        "meals": selected_meals,
        "dailyCalories": 2000,
        "remaining_calories": remaining_calories,
        "created_at": datetime.utcnow().isoformat(),
        "notes": f"Safe vegetarian fallback meal plan. Remaining calories: {remaining_calories}"
    }

async def get_today_consumption_records_async(user_email: str, user_timezone: str = "UTC") -> List[Dict[str, Any]]:
    """
    Get today's consumption records for a user using proper timezone boundaries.
    """
    try:
        # Get recent consumption history (last 3 days to ensure we have today's data)
        recent_consumption = await get_user_consumption_history(user_email, limit=200)
        
        # Filter to today's records using timezone-aware boundaries
        today_records = filter_today_records(recent_consumption, user_timezone)
        
        return today_records
        
    except Exception as e:
        print(f"Error getting today's consumption records: {e}")
        return []

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
    
    # Check if user has electronic signature and valid consent
    user_has_consent = user.get("consent_given", False)
    user_has_signature = user.get("electronic_signature", "") != ""
    user_policy_version = user.get("policy_version", "")
    CURRENT_POLICY_VERSION = "1.0.0"
    
    # Get form data directly from the request
    form = await request.form()
    consent_given = form.get('consent_given', 'false').lower() == 'true'
    consent_timestamp = form.get('consent_timestamp')
    policy_version = form.get('policy_version', CURRENT_POLICY_VERSION)
    electronic_signature = form.get('electronic_signature', '')
    signature_timestamp = form.get('signature_timestamp', '')
    research_consent = form.get('research_consent', 'false').lower() == 'true'
    
    # Check if user needs to sign consent
    needs_consent_signature = (
        not user_has_consent or 
        not user_has_signature or 
        user_policy_version != CURRENT_POLICY_VERSION
    )
    
    if needs_consent_signature:
        if not consent_given or not electronic_signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Electronic signature and consent are required to access services"
            )
    
    # Update user's consent information
    try:
        # Use existing consent data if user already has consent and no new consent provided
        final_consent_given = consent_given if (needs_consent_signature and consent_given) else user.get("consent_given", False)
        final_consent_timestamp = consent_timestamp if consent_timestamp else user.get("consent_timestamp")
        final_policy_version = policy_version if policy_version else user.get("policy_version", CURRENT_POLICY_VERSION)
        final_electronic_signature = electronic_signature if electronic_signature else user.get("electronic_signature", "")
        final_signature_timestamp = signature_timestamp if signature_timestamp else user.get("signature_timestamp", "")
        final_research_consent = research_consent if needs_consent_signature else user.get("research_consent", False)
        
        # Build a new dictionary with only the fields we want to update
        update_dict = {
            "id": user["id"],  # Required for upsert
            "type": "user",    # Required for querying
            "consent_given": final_consent_given,
            "consent_timestamp": final_consent_timestamp,
            "policy_version": final_policy_version,
            "electronic_signature": final_electronic_signature,
            "signature_timestamp": final_signature_timestamp,
            "research_consent": final_research_consent,
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
            "signature_ip_address": user.get("signature_ip_address"),
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
        "consent_given": final_consent_given,
        "consent_timestamp": final_consent_timestamp,
        "policy_version": final_policy_version
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
        "last_consent_update": data.consent_timestamp,
        # Electronic Signature Fields
        "electronic_signature": data.electronic_signature,
        "signature_timestamp": data.signature_timestamp,
        "signature_ip_address": data.signature_ip_address,
        "research_consent": data.research_consent
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

def enforce_dietary_restrictions(meal_plan_data: dict, user_profile: dict) -> dict:
    """
    Comprehensive dietary restriction enforcement function.
    Ensures all meals strictly adhere to user's dietary restrictions, allergies, and preferences.
    """
    print("[enforce_dietary_restrictions] Starting dietary compliance check...")
    
    # Extract user dietary information
    dietary_restrictions = user_profile.get('dietaryRestrictions', [])
    dietary_features = user_profile.get('dietaryFeatures', [])
    food_allergies = user_profile.get('allergies', [])
    strong_dislikes = user_profile.get('strongDislikes', [])
    diet_type = user_profile.get('dietType', [])
    
    # Convert to lowercase for case-insensitive matching
    restrictions_lower = [r.lower() for r in dietary_restrictions]
    features_lower = [f.lower() for f in dietary_features]
    allergies_lower = [a.lower() for a in food_allergies]
    dislikes_lower = [d.lower() for d in strong_dislikes]
    diet_type_lower = [dt.lower() for dt in diet_type]
    
    # Build comprehensive banned ingredients list
    banned_ingredients = set()
    
    # Add allergy-related banned ingredients
    for allergy in allergies_lower:
        if 'shellfish' in allergy:
            banned_ingredients.update(['shrimp', 'crab', 'lobster', 'clams', 'mussels', 'oysters', 'scallops'])
        elif 'tree nuts' in allergy or 'nuts' in allergy:
            banned_ingredients.update(['almonds', 'walnuts', 'pecans', 'cashews', 'pistachios', 'hazelnuts', 'macadamia', 'brazil nuts'])
        elif 'peanuts' in allergy:
            banned_ingredients.update(['peanuts', 'peanut butter', 'peanut oil'])
        elif 'dairy' in allergy or 'milk' in allergy:
            banned_ingredients.update(['milk', 'cheese', 'butter', 'cream', 'yogurt', 'ice cream'])
        elif 'eggs' in allergy or 'egg' in allergy:
            banned_ingredients.update(['eggs', 'egg', 'omelet', 'omelette', 'mayonnaise'])
        elif 'wheat' in allergy or 'gluten' in allergy:
            banned_ingredients.update(['wheat', 'flour', 'bread', 'pasta', 'noodles'])
        elif 'soy' in allergy:
            banned_ingredients.update(['soy', 'tofu', 'soy sauce', 'tempeh', 'miso'])
        else:
            banned_ingredients.add(allergy)
    
    # Add dietary restriction-related banned ingredients
    for restriction in restrictions_lower:
        if 'vegetarian' in restriction:
            banned_ingredients.update(['chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'turkey', 'lamb', 'meat', 'seafood', 'shrimp', 'bacon', 'ham'])
        elif 'vegan' in restriction:
            banned_ingredients.update(['chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'turkey', 'lamb', 'meat', 'seafood', 'shrimp', 'bacon', 'ham'])
            banned_ingredients.update(['milk', 'cheese', 'butter', 'cream', 'yogurt', 'ice cream', 'eggs', 'egg'])
        elif 'no dairy' in restriction or 'dairy-free' in restriction:
            banned_ingredients.update(['milk', 'cheese', 'butter', 'cream', 'yogurt', 'ice cream'])
        elif 'gluten-free' in restriction:
            banned_ingredients.update(['wheat', 'flour', 'bread', 'pasta', 'noodles'])
        elif 'low sodium' in restriction:
            banned_ingredients.update(['salt', 'soy sauce', 'pickles', 'olives', 'bacon', 'ham'])
        elif 'kosher' in restriction:
            banned_ingredients.update(['pork', 'shellfish', 'bacon', 'ham'])
        elif 'halal' in restriction:
            banned_ingredients.update(['pork', 'alcohol', 'bacon', 'ham'])
    
    # Add dietary features enforcement (this is where vegetarian preference is often stored)
    for feature in features_lower:
        if 'vegetarian' in feature:
            banned_ingredients.update(['chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'turkey', 'lamb', 'meat', 'seafood', 'shrimp', 'bacon', 'ham'])
            # If specifically "vegetarian (no eggs)", also ban eggs
            if 'no eggs' in feature:
                banned_ingredients.update(['eggs', 'egg', 'omelet', 'omelette', 'mayonnaise'])
        elif 'vegan' in feature:
            banned_ingredients.update(['chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'turkey', 'lamb', 'meat', 'seafood', 'shrimp', 'bacon', 'ham'])
            banned_ingredients.update(['milk', 'cheese', 'butter', 'cream', 'yogurt', 'ice cream', 'eggs', 'egg'])
        elif 'gluten-free' in feature:
            banned_ingredients.update(['wheat', 'flour', 'bread', 'pasta', 'noodles'])
        elif 'lactose-free' in feature:
            banned_ingredients.update(['milk', 'cheese', 'butter', 'cream', 'yogurt', 'ice cream'])
    
    # Add strong dislikes
    banned_ingredients.update(dislikes_lower)
    
    # Diet type enforcement
    if 'vegetarian' in diet_type_lower:
        banned_ingredients.update(['chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'turkey', 'lamb', 'meat', 'seafood', 'shrimp', 'bacon', 'ham'])
    
    print(f"[enforce_dietary_restrictions] Dietary restrictions: {dietary_restrictions}")
    print(f"[enforce_dietary_restrictions] Dietary features: {dietary_features}")
    print(f"[enforce_dietary_restrictions] Diet type: {diet_type}")
    print(f"[enforce_dietary_restrictions] Allergies: {food_allergies}")
    print(f"[enforce_dietary_restrictions] Banned ingredients: {banned_ingredients}")
    
    def sanitize_meal(meal: str) -> str:
        """Sanitize a meal to remove banned ingredients"""
        meal_lower = meal.lower()
        
        # Check for banned ingredients
        for banned in banned_ingredients:
            if banned in meal_lower:
                print(f"[enforce_dietary_restrictions] Found banned ingredient '{banned}' in meal '{meal}' - replacing")
                
                # Get appropriate replacement based on diet type
                if 'vegetarian' in diet_type_lower or 'vegetarian' in restrictions_lower:
                    if 'breakfast' in meal_lower:
                        return "Oatmeal with fresh berries and almond milk"
                    elif 'lunch' in meal_lower:
                        return "Quinoa salad with mixed vegetables and tahini dressing"
                    elif 'dinner' in meal_lower:
                        return "Lentil curry with brown rice and steamed vegetables"
                    else:
                        return "Mixed nuts and fresh fruit"
                else:
                    if 'breakfast' in meal_lower:
                        return "Scrambled eggs with whole grain toast"
                    elif 'lunch' in meal_lower:
                        return "Grilled chicken salad with olive oil dressing"
                    elif 'dinner' in meal_lower:
                        return "Baked salmon with roasted vegetables"
                    else:
                        return "Apple with almonds"
        
        return meal
    
    # Sanitize all meals in the meal plan
    sanitized_plan = meal_plan_data.copy()
    
    for meal_type in ['breakfast', 'lunch', 'dinner', 'snacks']:
        if meal_type in sanitized_plan:
            if isinstance(sanitized_plan[meal_type], list):
                sanitized_plan[meal_type] = [sanitize_meal(meal) for meal in sanitized_plan[meal_type]]
            elif isinstance(sanitized_plan[meal_type], str):
                sanitized_plan[meal_type] = sanitize_meal(sanitized_plan[meal_type])
    
    # Also sanitize nested meal structures
    if 'meals' in sanitized_plan:
        for meal_type in ['breakfast', 'lunch', 'dinner', 'snack']:
            if meal_type in sanitized_plan['meals']:
                if isinstance(sanitized_plan['meals'][meal_type], list):
                    sanitized_plan['meals'][meal_type] = [sanitize_meal(meal) for meal in sanitized_plan['meals'][meal_type]]
                elif isinstance(sanitized_plan['meals'][meal_type], str):
                    sanitized_plan['meals'][meal_type] = sanitize_meal(sanitized_plan['meals'][meal_type])
    
    print("[enforce_dietary_restrictions] Dietary compliance check completed")
    return sanitized_plan

def generate_meal_plan_prompt(user_profile: UserProfile) -> str:
    """Legacy function - now redirects to comprehensive profiling"""
    # This function is deprecated - the main endpoint now uses comprehensive profiling
    return "This function has been replaced with comprehensive profile analysis"

def generate_recipe_prompt(meal_name: str, user_profile: UserProfile) -> str:
    """Legacy function - now redirects to comprehensive profile handling"""
    # This function is deprecated - the main endpoint now uses comprehensive profiling
    return "This function has been replaced with comprehensive profile analysis"

# ============================================================================
# INTELLIGENT MEAL DIVERSITY & CALORIE-AWARE PLANNING SYSTEM
# ============================================================================

class IntelligentMealPlanner:
    """
    Advanced AI-powered meal planning system that ensures diversity, 
    intelligently manages calories, and provides context-aware suggestions.
    """
    
    def __init__(self):
        self.meal_categories = {
            "breakfast": {
                "base_proteins": ["tofu scramble", "chickpea flour pancakes", "almond butter", "cottage cheese", "hemp seeds", "chia seeds"],
                "base_carbs": ["steel-cut oats", "quinoa porridge", "whole grain toast", "sweet potato", "brown rice", "buckwheat pancakes"],
                "vegetables": ["spinach", "mushrooms", "bell peppers", "tomatoes", "avocado", "zucchini"],
                "healthy_fats": ["olive oil", "avocado", "nuts", "seeds", "tahini", "coconut"],
                "flavors": ["cinnamon", "vanilla", "berries", "banana", "lemon", "herbs"]
            },
            "lunch": {
                "base_proteins": ["lentils", "chickpeas", "black beans", "tofu", "tempeh", "quinoa"],
                "base_carbs": ["brown rice", "quinoa", "whole grain pasta", "sweet potato", "barley", "bulgur"],
                "vegetables": ["kale", "broccoli", "cauliflower", "carrots", "cucumbers", "spinach"],
                "healthy_fats": ["olive oil", "avocado", "tahini", "nuts", "seeds", "olives"],
                "flavors": ["garlic", "ginger", "lemon", "herbs", "spices", "nutritional yeast"]
            },
            "dinner": {
                "base_proteins": ["lentil curry", "bean stew", "stuffed vegetables", "tofu dishes", "tempeh", "legume soups"],
                "base_carbs": ["brown rice", "quinoa", "whole grain pasta", "barley", "millet", "cauliflower rice"],
                "vegetables": ["broccoli", "asparagus", "Brussels sprouts", "zucchini", "eggplant", "peppers"],
                "healthy_fats": ["olive oil", "coconut oil", "nuts", "seeds", "avocado", "tahini"],
                "flavors": ["curry spices", "Italian herbs", "Mediterranean", "Asian seasonings", "Mexican spices", "Middle Eastern"]
            },
            "snack": {
                "quick_options": ["apple with almond butter", "hummus with veggies", "mixed nuts", "berries with yogurt", "veggie sticks", "homemade energy balls"],
                "substantial_options": ["smoothie bowl", "avocado toast", "trail mix", "roasted chickpeas", "vegetable soup", "quinoa salad"],
                "light_options": ["herbal tea", "cucumber water", "celery sticks", "small fruit", "handful of nuts", "vegetable broth"]
            }
        }
    
    def get_meal_diversity_score(self, meals_dict: dict) -> dict:
        """Calculate diversity score to avoid repetitive ingredients."""
        all_ingredients = []
        for meal_type, meal_text in meals_dict.items():
            if meal_text:
                # Extract key ingredients from meal text
                ingredients = self._extract_ingredients_from_text(meal_text)
                all_ingredients.extend(ingredients)
        
        # Count ingredient frequency
        ingredient_counts = {}
        for ingredient in all_ingredients:
            ingredient_counts[ingredient] = ingredient_counts.get(ingredient, 0) + 1
        
        # Calculate diversity metrics
        total_ingredients = len(all_ingredients)
        unique_ingredients = len(set(all_ingredients))
        repeated_ingredients = [ing for ing, count in ingredient_counts.items() if count > 1]
        
        diversity_score = unique_ingredients / total_ingredients if total_ingredients > 0 else 0
        
        return {
            "diversity_score": diversity_score,
            "repeated_ingredients": repeated_ingredients,
            "total_ingredients": total_ingredients,
            "unique_ingredients": unique_ingredients
        }
    
    def _extract_ingredients_from_text(self, meal_text: str) -> list:
        """Extract key ingredients from meal description."""
        # Common ingredients to look for
        common_ingredients = [
            "oats", "quinoa", "rice", "pasta", "bread", "toast", "tofu", "tempeh",
            "chickpeas", "lentils", "beans", "yogurt", "almond", "cashew", "walnut",
            "spinach", "kale", "broccoli", "cauliflower", "avocado", "tomato",
            "mushroom", "pepper", "carrot", "cucumber", "sweet potato", "potato"
        ]
        
        found_ingredients = []
        meal_lower = meal_text.lower()
        
        for ingredient in common_ingredients:
            if ingredient in meal_lower:
                found_ingredients.append(ingredient)
        
        return found_ingredients
    
    async def generate_intelligent_meal_plan(self, user_email: str, profile: dict, 
                                           consumed_today: list, remaining_calories: int) -> dict:
        """
        Generate an intelligent, diverse meal plan that adapts to calorie constraints
        and avoids repetitive ingredients.
        """
        try:
            print(f"[INTELLIGENT_PLANNER] Generating smart meal plan for {user_email}")
            print(f"[INTELLIGENT_PLANNER] Remaining calories: {remaining_calories}")
            
            # Analyze what's already been consumed
            consumed_analysis = self._analyze_consumption_today(consumed_today)
            
            # Get dietary preferences and restrictions
            dietary_features = profile.get('dietaryFeatures', [])
            diet_type = profile.get('dietType', [])
            allergies = profile.get('allergies', [])
            strong_dislikes = profile.get('strongDislikes', [])
            
            # Generate diverse meal suggestions with AI
            meal_suggestions = await self._generate_diverse_meals_with_ai(
                consumed_analysis, remaining_calories, dietary_features, 
                diet_type, allergies, strong_dislikes
            )
            
            # Validate diversity
            diversity_score = self.get_meal_diversity_score(meal_suggestions)
            
            # If diversity is poor, regenerate with explicit diversity constraints
            if diversity_score["diversity_score"] < 0.7:
                print(f"[INTELLIGENT_PLANNER] Poor diversity detected ({diversity_score['diversity_score']:.2f}), regenerating...")
                meal_suggestions = await self._generate_diverse_meals_with_ai(
                    consumed_analysis, remaining_calories, dietary_features, 
                    diet_type, allergies, strong_dislikes, 
                    avoid_ingredients=diversity_score["repeated_ingredients"]
                )
            
            # Create the final meal plan
            today = datetime.utcnow().date()
            intelligent_plan = {
                "id": f"intelligent_{user_email}_{today.isoformat()}_{int(datetime.utcnow().timestamp())}",
                "date": today.isoformat(),
                "type": "intelligent_adaptive",
                "meals": meal_suggestions,
                "dailyCalories": int(profile.get('calorieTarget', '2000')),
                "remaining_calories": remaining_calories,
                "diversity_score": diversity_score["diversity_score"],
                "consumed_today": consumed_analysis,
                "created_at": datetime.utcnow().isoformat(),
                "notes": f"Intelligent meal plan with {diversity_score['unique_ingredients']} unique ingredients"
            }
            
            print(f"[INTELLIGENT_PLANNER] Generated plan with diversity score: {diversity_score['diversity_score']:.2f}")
            return intelligent_plan
            
        except Exception as e:
            print(f"[INTELLIGENT_PLANNER] Error: {str(e)}")
            return None
    
    def _analyze_consumption_today(self, consumed_today: list) -> dict:
        """Analyze what's been consumed today to inform meal planning."""
        calories_consumed = 0
        protein_consumed = 0
        carbs_consumed = 0
        fat_consumed = 0
        
        meal_types_eaten = set()
        ingredients_used = []
        
        for record in consumed_today:
            nutrition = record.get("nutritional_info", {})
            calories_consumed += nutrition.get("calories", 0)
            protein_consumed += nutrition.get("protein", 0)
            carbs_consumed += nutrition.get("carbohydrates", 0)
            fat_consumed += nutrition.get("fat", 0)
            
            meal_types_eaten.add(record.get("meal_type", ""))
            
            # Extract ingredients from food name
            food_name = record.get("food_name", "")
            ingredients = self._extract_ingredients_from_text(food_name)
            ingredients_used.extend(ingredients)
        
        return {
            "calories_consumed": calories_consumed,
            "protein_consumed": protein_consumed,
            "carbs_consumed": carbs_consumed,
            "fat_consumed": fat_consumed,
            "meal_types_eaten": list(meal_types_eaten),
            "ingredients_used": list(set(ingredients_used)),
            "total_meals": len(consumed_today)
        }
    
    async def _generate_diverse_meals_with_ai(self, consumed_analysis: dict, remaining_calories: int, 
                                            dietary_features: list, diet_type: list, allergies: list, 
                                            strong_dislikes: list, avoid_ingredients: list = None) -> dict:
        """Generate diverse meals using AI with explicit diversity constraints."""
        
        if avoid_ingredients is None:
            avoid_ingredients = []
        
        # Build comprehensive AI prompt for intelligent meal generation
        prompt = self._build_intelligent_meal_prompt(
            consumed_analysis, remaining_calories, dietary_features, 
            diet_type, allergies, strong_dislikes, avoid_ingredients
        )
        
        try:
            # Call AI with the intelligent prompt
            api_result = await robust_openai_call(
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an advanced AI nutritionist and meal planning expert with deep knowledge of cuisine diversity, ingredient combinations, and calorie management. You excel at creating varied, delicious meal plans that avoid repetition while meeting nutritional goals."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,  # Higher temperature for more creativity
                max_tokens=800,
                max_retries=3,
                timeout=30,
                context="intelligent_meal_planning"
            )
            
            if api_result["success"]:
                import json
                meal_response = json.loads(api_result["content"])
                return meal_response.get("meals", {})
            else:
                print(f"[INTELLIGENT_PLANNER] AI failed: {api_result['error']}")
                return self._generate_fallback_diverse_meals(remaining_calories, diet_type)
                
        except Exception as e:
            print(f"[INTELLIGENT_PLANNER] AI generation error: {str(e)}")
            return self._generate_fallback_diverse_meals(remaining_calories, diet_type)
    
    def _build_intelligent_meal_prompt(self, consumed_analysis: dict, remaining_calories: int, 
                                     dietary_features: list, diet_type: list, allergies: list, 
                                     strong_dislikes: list, avoid_ingredients: list) -> str:
        """Build a sophisticated prompt for intelligent meal generation."""
        
        # Get current time context
        current_hour = datetime.utcnow().hour
        meal_time_context = ""
        if current_hour < 10:
            meal_time_context = "It's morning - focus on energizing breakfast options."
        elif current_hour < 14:
            meal_time_context = "It's midday - focus on satisfying lunch options."
        elif current_hour < 18:
            meal_time_context = "It's afternoon - focus on hearty dinner options."
        else:
            meal_time_context = "It's evening - focus on lighter dinner options."
        
        # Build dietary restrictions
        dietary_restrictions = []
        if any("vegetarian" in f.lower() for f in dietary_features):
            dietary_restrictions.append("STRICTLY VEGETARIAN - No meat, poultry, fish, or seafood")
        if any("no eggs" in f.lower() for f in dietary_features):
            dietary_restrictions.append("NO EGGS - No egg-based dishes")
        if any("vegan" in f.lower() for f in dietary_features):
            dietary_restrictions.append("STRICTLY VEGAN - No animal products")
        
        # Build allergy warnings
        allergy_warnings = []
        for allergy in allergies:
            allergy_warnings.append(f"ALLERGY WARNING: No {allergy}")
        
        # Build calorie strategy
        calorie_strategy = ""
        if remaining_calories > 1200:
            calorie_strategy = "HIGH CALORIE REMAINING - Focus on substantial, satisfying meals with healthy fats and proteins."
        elif remaining_calories > 800:
            calorie_strategy = "MODERATE CALORIES REMAINING - Balance portions thoughtfully, include fiber-rich foods."
        elif remaining_calories > 400:
            calorie_strategy = "LOW CALORIES REMAINING - Focus on nutrient-dense, lower-calorie options with high satiety."
        else:
            calorie_strategy = "VERY LOW CALORIES REMAINING - Suggest light, optional meals only if genuinely hungry."
        
        # Determine cuisine style
        cuisine_style = "International"
        if diet_type:
            diet_lower = [d.lower() for d in diet_type]
            if any("mediterranean" in d for d in diet_lower):
                cuisine_style = "Mediterranean"
            elif any("asian" in d or "chinese" in d or "korean" in d for d in diet_lower):
                cuisine_style = "Asian"
            elif any("indian" in d or "south asian" in d for d in diet_lower):
                cuisine_style = "Indian"
            elif any("mexican" in d or "latin" in d for d in diet_lower):
                cuisine_style = "Mexican"
        
        prompt = f"""🧠 INTELLIGENT MEAL PLANNING CHALLENGE 🧠

You are an advanced AI nutritionist creating a diverse, intelligent meal plan that AVOIDS REPETITION and maximizes variety.

📊 CONSUMPTION ANALYSIS:
- Already consumed today: {consumed_analysis['calories_consumed']} calories
- Protein consumed: {consumed_analysis['protein_consumed']}g
- Carbs consumed: {consumed_analysis['carbs_consumed']}g
- Fat consumed: {consumed_analysis['fat_consumed']}g
- Meal types eaten: {', '.join(consumed_analysis['meal_types_eaten']) if consumed_analysis['meal_types_eaten'] else 'None'}
- Ingredients already used: {', '.join(consumed_analysis['ingredients_used']) if consumed_analysis['ingredients_used'] else 'None'}
- Total meals logged: {consumed_analysis['total_meals']}

🎯 CALORIE MANAGEMENT:
- Remaining calories: {remaining_calories}
- Strategy: {calorie_strategy}
- Context: {meal_time_context}

🍽️ CUISINE PREFERENCES:
- Primary cuisine style: {cuisine_style}
- Use authentic {cuisine_style} ingredients and flavor profiles

🚫 DIETARY RESTRICTIONS:
{chr(10).join(dietary_restrictions) if dietary_restrictions else "No specific restrictions"}

🚨 ALLERGIES:
{chr(10).join(allergy_warnings) if allergy_warnings else "No known allergies"}

🎭 DIVERSITY REQUIREMENTS:
- CRITICAL: Each meal MUST use completely different base ingredients
- AVOID these ingredients that might cause repetition: {', '.join(avoid_ingredients) if avoid_ingredients else 'None specified'}
- AVOID ingredients already consumed today: {', '.join(consumed_analysis['ingredients_used']) if consumed_analysis['ingredients_used'] else 'None'}
- Use different cooking methods (steamed, roasted, raw, sautéed, etc.)
- Vary textures (crunchy, creamy, chewy, smooth, etc.)
- Include different color profiles for visual appeal

💡 INTELLIGENT SUGGESTIONS:
1. **Breakfast**: If not eaten, suggest energizing options with protein + complex carbs
2. **Lunch**: If not eaten, suggest satisfying options with diverse vegetables + proteins
3. **Dinner**: If not eaten, suggest comforting options with different flavor profiles from lunch
4. **Snack**: Only if remaining calories > 200, suggest light options that complement the day

🎨 CREATIVITY REQUIREMENTS:
- Use seasonal ingredients where possible
- Include different preparation methods for variety
- Suggest dishes that would photographically look different from each other
- Include a mix of warm and cool dishes if appropriate
- Consider different spice levels and flavor intensities

Generate a JSON response with this EXACT structure:
{{
  "meals": {{
    "breakfast": "<specific, diverse {cuisine_style} breakfast dish>",
    "lunch": "<specific, diverse {cuisine_style} lunch dish using different ingredients>",
    "dinner": "<specific, diverse {cuisine_style} dinner dish using different ingredients and methods>",
    "snack": "<specific, diverse {cuisine_style} snack or 'Light snack only if needed' if calories very low>"
  }}
}}

🏆 SUCCESS CRITERIA:
- Zero ingredient overlap between meals
- All meals respect dietary restrictions and allergies
- Calorie distribution is intelligent based on remaining calories
- Each meal sounds delicious and authentic to {cuisine_style} cuisine
- Visual and textural variety across all meals
- Nutritionally balanced overall"""

        return prompt
    
    def _generate_fallback_diverse_meals(self, remaining_calories: int, diet_type: list) -> dict:
        """Generate diverse fallback meals if AI fails."""
        
        # Determine cuisine style for fallback
        cuisine_style = "International"
        if diet_type:
            diet_lower = [d.lower() for d in diet_type]
            if any("mediterranean" in d for d in diet_lower):
                cuisine_style = "Mediterranean"
            elif any("asian" in d or "chinese" in d or "korean" in d for d in diet_lower):
                cuisine_style = "Asian"
            elif any("indian" in d or "south asian" in d for d in diet_lower):
                cuisine_style = "Indian"
            elif any("mexican" in d or "latin" in d for d in diet_lower):
                cuisine_style = "Mexican"
        
        # Get diverse options based on cuisine style
        if cuisine_style == "Mediterranean":
            meals = {
                "breakfast": "Greek yogurt parfait with nuts, honey, and fresh figs",
                "lunch": "Mediterranean quinoa salad with roasted vegetables and olives",
                "dinner": "Stuffed bell peppers with herbs, rice, and pine nuts",
                "snack": "Hummus with fresh vegetable sticks and olive tapenade"
            }
        elif cuisine_style == "Asian":
            meals = {
                "breakfast": "Congee with shiitake mushrooms and scallions",
                "lunch": "Asian lettuce wraps with seasoned tofu and peanut sauce",
                "dinner": "Miso-glazed eggplant with brown rice and steamed bok choy",
                "snack": "Edamame with sea salt and sesame seeds"
            }
        elif cuisine_style == "Indian":
            meals = {
                "breakfast": "Upma with curry leaves, mustard seeds, and vegetables",
                "lunch": "Rajma (kidney bean curry) with quinoa and cucumber raita",
                "dinner": "Palak paneer with cauliflower rice and mint chutney",
                "snack": "Roasted chickpeas with turmeric and chili powder"
            }
        elif cuisine_style == "Mexican":
            meals = {
                "breakfast": "Breakfast burrito bowl with black beans and avocado",
                "lunch": "Mexican street corn salad with lime and cilantro",
                "dinner": "Stuffed poblano peppers with quinoa and pepitas",
                "snack": "Guacamole with jicama sticks and lime"
            }
        else:  # International
            meals = {
                "breakfast": "Overnight chia pudding with berries and almond butter",
                "lunch": "Rainbow Buddha bowl with tahini dressing",
                "dinner": "Stuffed acorn squash with wild rice and cranberries",
                "snack": "Trail mix with dried fruit and raw nuts"
            }
        
        # Adjust for low calories
        if remaining_calories < 400:
            meals["snack"] = "Light snack only if genuinely hungry"
        
        return meals


# Initialize the intelligent meal planner
intelligent_planner = IntelligentMealPlanner()

# ============================================================================
# STABLE MEAL PLAN MANAGEMENT & CONSUMPTION TRACKING SYSTEM
# ============================================================================

class StableMealPlanManager:
    """
    Manages stable meal plans with intelligent recalibration based on actual consumption.
    Prevents constant reloading and only recalibrates when user deviates from plan.
    """
    
    def __init__(self):
        self.daily_meal_plans = {}  # Cache for daily meal plans
        self.consumption_cache = {}  # Cache for consumption data
        self.plan_lock = asyncio.Lock()  # For thread safety
        
    def clear_cache_for_user(self, user_email: str):
        """Clear cached meal plans for a specific user."""
        try:
            today = datetime.utcnow().date().isoformat()
            cache_key = f"{user_email}_{today}"
            
            if cache_key in self.daily_meal_plans:
                del self.daily_meal_plans[cache_key]
                print(f"[STABLE_PLAN] Cleared cached meal plan for {user_email}")
            
            if cache_key in self.consumption_cache:
                del self.consumption_cache[cache_key]
                print(f"[STABLE_PLAN] Cleared consumption cache for {user_email}")
                
        except Exception as e:
            print(f"[STABLE_PLAN] Error clearing cache: {str(e)}")

    def clear_all_cache(self):
        """Clear all cached meal plans."""
        try:
            self.daily_meal_plans.clear()
            self.consumption_cache.clear()
            print(f"[STABLE_PLAN] Cleared all caches")
        except Exception as e:
            print(f"[STABLE_PLAN] Error clearing all caches: {str(e)}")

    async def get_stable_todays_meal_plan(self, user_email: str, profile: dict) -> dict:
        """
        Get a stable meal plan for today that doesn't constantly regenerate.
        Only recalibrates when consumption deviates from the plan.
        """
        try:
            today = datetime.utcnow().date().isoformat()
            cache_key = f"{user_email}_{today}"
            
            print(f"[STABLE_PLAN] Getting stable meal plan for {user_email} on {today}")
            
            # Get today's consumption
            today_consumption = await get_today_consumption_records_async(user_email, user_timezone="UTC")
            
            # Check if we have a cached plan for today
            if cache_key in self.daily_meal_plans:
                cached_plan = self.daily_meal_plans[cache_key]
                print(f"[STABLE_PLAN] Found cached plan from {cached_plan.get('created_at', 'unknown')}")
                
                # Check if we need to recalibrate based on consumption changes
                needs_recalibration = await self._needs_recalibration(
                    cached_plan, today_consumption, user_email
                )
                
                if not needs_recalibration:
                    print(f"[STABLE_PLAN] Using cached plan - no recalibration needed")
                    # Add consumption status to the cached plan
                    enhanced_plan = await self._add_consumption_status(cached_plan, today_consumption)
                    return enhanced_plan
                else:
                    print(f"[STABLE_PLAN] Recalibration needed - consumption deviated from plan")
            
            # Generate new meal plan or recalibrate existing one
            new_plan = await self._generate_stable_meal_plan(user_email, profile, today_consumption)
            
            # Cache the new plan
            self.daily_meal_plans[cache_key] = new_plan
            print(f"[STABLE_PLAN] Generated and cached new meal plan")
            
            # Add consumption status
            enhanced_plan = await self._add_consumption_status(new_plan, today_consumption)
            return enhanced_plan
            
        except Exception as e:
            print(f"[STABLE_PLAN] Error: {str(e)}")
            return None
    
    async def _needs_recalibration(self, cached_plan: dict, today_consumption: list, user_email: str) -> bool:
        """
        Determine if the meal plan needs recalibration based on consumption patterns.
        Enhanced to be more sensitive to new food logs.
        """
        try:
            # Check if consumption has changed since last check
            consumption_hash = self._hash_consumption(today_consumption)
            cache_key = f"{user_email}_{datetime.utcnow().date().isoformat()}"
            
            if cache_key in self.consumption_cache:
                if self.consumption_cache[cache_key] == consumption_hash:
                    print(f"[STABLE_PLAN] No new consumption since last check")
                    return False
            
            # Update consumption cache
            self.consumption_cache[cache_key] = consumption_hash
            
            # Always recalibrate if consumption has changed
            print(f"[STABLE_PLAN] Consumption changed - forcing recalibration")
            return True
            
        except Exception as e:
            print(f"[STABLE_PLAN] Error checking recalibration needs: {str(e)}")
            return True  # Default to recalibration on error
    
    def _hash_consumption(self, consumption: list) -> str:
        """Create a hash of consumption data to detect changes."""
        import hashlib
        consumption_str = json.dumps([
            {
                "food": record.get("food_name", ""),
                "meal_type": record.get("meal_type", ""),
                "calories": record.get("nutritional_info", {}).get("calories", 0)
            }
            for record in consumption
        ], sort_keys=True)
        return hashlib.md5(consumption_str.encode()).hexdigest()
    
    async def _calculate_deviation_score(self, planned_meals: dict, consumed_meals: list) -> float:
        """
        Calculate how much the consumed meals deviate from the planned meals.
        Returns a score from 0.0 (perfect match) to 1.0 (complete deviation).
        """
        try:
            if not consumed_meals:
                return 0.0  # No consumption yet, no deviation
            
            # Group consumed meals by meal type
            consumed_by_type = {}
            for record in consumed_meals:
                meal_type = record.get("meal_type", "snack")
                food_name = record.get("food_name", "").lower()
                
                if meal_type not in consumed_by_type:
                    consumed_by_type[meal_type] = []
                consumed_by_type[meal_type].append(food_name)
            
            # Calculate similarity for each meal type
            total_comparisons = 0
            total_deviation = 0.0
            
            for meal_type, planned_meal in planned_meals.items():
                if meal_type in consumed_by_type:
                    consumed_foods = consumed_by_type[meal_type]
                    
                    # Check if any consumed food matches planned meal
                    meal_matched = any(
                        self._meals_similar(planned_meal, consumed_food)
                        for consumed_food in consumed_foods
                    )
                    
                    print(f"[DEVIATION] {meal_type}: planned='{planned_meal}', consumed={consumed_foods}, matched={meal_matched}")
                    
                    if not meal_matched:
                        total_deviation += 1.0  # Full deviation for this meal type
                    
                    total_comparisons += 1
            
            if total_comparisons == 0:
                return 0.0
            
            deviation_score = total_deviation / total_comparisons
            return deviation_score
            
        except Exception as e:
            print(f"[STABLE_PLAN] Error calculating deviation: {str(e)}")
            return 0.0
    
    def _meals_similar(self, planned_meal: str, consumed_meal: str) -> bool:
        """Check if planned and consumed meals are similar enough."""
        # Normalize both meal descriptions for comparison
        planned_normalized = planned_meal.lower().strip()
        consumed_normalized = consumed_meal.lower().strip()
        
        # Remove "✅ You ate: " prefix if present
        if consumed_normalized.startswith('✅ you ate:'):
            consumed_normalized = consumed_normalized[11:].strip()
        
        print(f"[SIMILARITY] Comparing: planned='{planned_normalized}' vs consumed='{consumed_normalized}'")
        
        # Check for exact match first (high confidence)
        if planned_normalized == consumed_normalized:
            print(f"[SIMILARITY] Exact match found!")
            return True
        
        # Check for very high similarity (>80% string match)
        string_sim = self._string_similarity(planned_normalized, consumed_normalized)
        print(f"[SIMILARITY] String similarity: {string_sim:.2f}")
        if string_sim > 0.8:
            print(f"[SIMILARITY] High string similarity match!")
            return True
        
        # Extract key ingredients from both meals
        planned_ingredients = self._extract_key_ingredients(planned_meal)
        consumed_ingredients = self._extract_key_ingredients(consumed_meal)
        
        print(f"[SIMILARITY] Planned ingredients: {planned_ingredients}")
        print(f"[SIMILARITY] Consumed ingredients: {consumed_ingredients}")
        
        # Check for overlap in key ingredients
        if not planned_ingredients or not consumed_ingredients:
            print(f"[SIMILARITY] No ingredients found in one or both meals")
            return False
        
        overlap = len(planned_ingredients.intersection(consumed_ingredients))
        similarity_ratio = overlap / len(planned_ingredients.union(consumed_ingredients))
        
        print(f"[SIMILARITY] Ingredient overlap: {overlap}, ratio: {similarity_ratio:.2f}")
        
        # Consider meals similar if they share >40% of key ingredients
        is_similar = similarity_ratio > 0.4
        print(f"[SIMILARITY] Final result: {is_similar}")
        return is_similar
    
    def _string_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity using a simple ratio approach."""
        try:
            # Remove common filler words
            filler_words = {'a', 'an', 'the', 'with', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for', 'from', 'by'}
            
            def clean_string(s):
                words = s.split()
                return ' '.join(word for word in words if word not in filler_words)
            
            clean_str1 = clean_string(str1)
            clean_str2 = clean_string(str2)
            
            # Calculate similarity based on common words
            words1 = set(clean_str1.split())
            words2 = set(clean_str2.split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            
            return intersection / union if union > 0 else 0.0
        except Exception:
            return 0.0
    
    def _extract_key_ingredients(self, meal_text: str) -> set:
        """Extract key ingredients from meal description."""
        key_ingredients = [
            "oats", "quinoa", "rice", "pasta", "bread", "toast", "tofu", "tempeh",
            "chickpeas", "lentils", "beans", "yogurt", "almond", "cashew", "walnut",
            "spinach", "kale", "broccoli", "cauliflower", "avocado", "tomato",
            "mushroom", "pepper", "carrot", "cucumber", "sweet potato", "potato",
            "salmon", "chicken", "beef", "pork", "fish", "turkey", "egg", "cheese",
            "daikon", "radish", "spaghetti", "wedges", "sandwich", "bowl", "salad"
        ]
        
        found_ingredients = set()
        meal_lower = meal_text.lower()
        
        for ingredient in key_ingredients:
            if ingredient in meal_lower:
                found_ingredients.add(ingredient)
        
        # Also extract meaningful words that might be ingredients
        words = meal_lower.split()
        meaningful_words = [
            word for word in words 
            if len(word) > 3 and word not in {
                'with', 'and', 'the', 'for', 'from', 'this', 'that', 'they', 'them',
                'your', 'have', 'will', 'been', 'were', 'are', 'was', 'can', 'could',
                'would', 'should', 'might', 'must', 'shall', 'may', 'does', 'did',
                'bowl', 'plate', 'cup', 'glass', 'piece', 'slice', 'serving'
            }
        ]
        
        # Add meaningful words as potential ingredients
        for word in meaningful_words:
            found_ingredients.add(word)
        
        return found_ingredients
    
    async def _generate_stable_meal_plan(self, user_email: str, profile: dict, today_consumption: list) -> dict:
        """Generate a new stable meal plan using the intelligent planner."""
        try:
            # Calculate remaining calories
            calories_consumed = sum(r.get("nutritional_info", {}).get("calories", 0) for r in today_consumption)
            target_calories = int(profile.get('calorieTarget', '2000'))
            remaining_calories = max(0, target_calories - calories_consumed)
            
            # Use the intelligent meal planner
            intelligent_plan = await intelligent_planner.generate_intelligent_meal_plan(
                user_email, profile, today_consumption, remaining_calories
            )
            
            if intelligent_plan:
                # Mark as stable plan
                intelligent_plan["type"] = "stable_intelligent"
                intelligent_plan["stability_version"] = "1.0"
                return intelligent_plan
            else:
                # Fallback to diverse meals
                today = datetime.utcnow().date()
                return {
                    "id": f"stable_fallback_{user_email}_{today.isoformat()}",
                    "date": today.isoformat(),
                    "type": "stable_fallback",
                    "meals": intelligent_planner._generate_fallback_diverse_meals(remaining_calories, profile.get('dietType', [])),
                    "dailyCalories": target_calories,
                    "created_at": datetime.utcnow().isoformat(),
                    "stability_version": "1.0",
                    "notes": "Stable fallback meal plan"
                }
                
        except Exception as e:
            print(f"[STABLE_PLAN] Error generating stable plan: {str(e)}")
            return None
    
    async def _add_consumption_status(self, meal_plan: dict, today_consumption: list) -> dict:
        """
        Add consumption status to meal plan showing what user actually ate.
        Enhanced to properly handle multiple food items per meal type.
        """
        try:
            enhanced_plan = meal_plan.copy()
            meals = enhanced_plan.get("meals", {})
            
            # Group consumption by meal type with timestamps for ordering
            consumed_by_type = {}
            for record in today_consumption:
                meal_type = record.get("meal_type", "snack")
                food_name = record.get("food_name", "")
                timestamp = record.get("timestamp", "")
                
                if meal_type not in consumed_by_type:
                    consumed_by_type[meal_type] = []
                consumed_by_type[meal_type].append({
                    "food_name": food_name,
                    "timestamp": timestamp,
                    "calories": record.get("nutritional_info", {}).get("calories", 0)
                })
            
            # Sort each meal type by timestamp (earliest first)
            for meal_type in consumed_by_type:
                consumed_by_type[meal_type].sort(key=lambda x: x["timestamp"])
            
            # Create enhanced meals with consumption status
            enhanced_meals = {}
            consumption_status = {}
            
            for meal_type in ["breakfast", "lunch", "dinner", "snack"]:
                planned_meal = meals.get(meal_type, "")
                
                if meal_type in consumed_by_type:
                    # Show what was actually consumed
                    consumed_items = consumed_by_type[meal_type]
                    
                    if len(consumed_items) == 1:
                        # Single item
                        item = consumed_items[0]
                        enhanced_meals[meal_type] = f"✅ You ate: {item['food_name']}"
                    else:
                        # Multiple items - show as a list
                        food_names = [item['food_name'] for item in consumed_items]
                        total_calories = sum(item['calories'] for item in consumed_items)
                        enhanced_meals[meal_type] = f"✅ You ate: {', '.join(food_names)} (Total: {total_calories:.0f} cal)"
                    
                    # Enhanced consumption status
                    consumption_status[meal_type] = {
                        "consumed": True,
                        "planned": planned_meal,
                        "actual": [item['food_name'] for item in consumed_items],
                        "total_items": len(consumed_items),
                        "total_calories": sum(item['calories'] for item in consumed_items),
                        "matched": any(self._meals_similar(planned_meal.lower(), item['food_name'].lower()) for item in consumed_items)
                    }
                else:
                    # Show planned meal
                    enhanced_meals[meal_type] = planned_meal
                    consumption_status[meal_type] = {
                        "consumed": False,
                        "planned": planned_meal,
                        "actual": [],
                        "total_items": 0,
                        "total_calories": 0,
                        "matched": False
                    }
            
            enhanced_plan["meals"] = enhanced_meals
            enhanced_plan["consumption_status"] = consumption_status
            enhanced_plan["last_updated"] = datetime.utcnow().isoformat()
            
            print(f"[STABLE_PLAN] Enhanced meal plan with consumption status: {enhanced_meals}")
            
            return enhanced_plan
            
        except Exception as e:
            print(f"[STABLE_PLAN] Error adding consumption status: {str(e)}")
            return meal_plan

# Initialize the stable meal plan manager
stable_meal_manager = StableMealPlanManager()

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
        dietary_features = user_profile.get("dietaryFeatures", []) or user_profile.get("diet_features", [])
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
                "dietary_features": dietary_features,
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
- Dietary Features: {', '.join(profile['dietary_features']) if profile['dietary_features'] else 'None'}
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
            days = specific_data.get('days', 7) if specific_data else 7
            prompt = f"""You are a comprehensive health coach AI creating adaptive meal plans for multiple health conditions.

{condition_context}
{dietary_context}
{metrics_context}
{consumption_context}
{plan_context}

Create a personalized {days}-day meal plan that:
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
    "duration_days": {days},
    "dailyCalories": {profile['calorie_target']},
    "health_focus": [list of their health conditions],
    "breakfast": [{', '.join([f'"Day {i+1}: [specific meal]"' for i in range(days)])}],
    "lunch": [{', '.join([f'"Day {i+1}: [specific meal]"' for i in range(days)])}],
    "dinner": [{', '.join([f'"Day {i+1}: [specific meal]"' for i in range(days)])}],
    "snacks": [{', '.join([f'"Day {i+1}: [specific snack]"' for i in range(days)])}],
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
            "breakfast": ["Oatmeal with berries", "Whole grain toast with eggs", "Cottage cheese with granola", "Scrambled eggs with spinach", "Smoothie bowl", "Avocado toast", "Pancakes with fruit"],
            "lunch": ["Grilled chicken salad", "Quinoa bowl", "Turkey sandwich", "Vegetable soup", "Pasta salad", "Chicken wrap", "Buddha bowl"],
            "dinner": ["Baked salmon with vegetables", "Grilled chicken with rice", "Beef stir-fry", "Vegetable curry", "Baked cod with quinoa", "Turkey meatballs", "Roasted vegetables with protein"],
            "snacks": ["Apple with almonds", "Mixed nuts", "Carrot sticks with hummus", "Cheese and crackers", "Berries with cottage cheese", "Protein smoothie", "Whole grain crackers"]
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
            # Use the robust OpenAI call with better error handling
            api_result = await robust_openai_call(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a meal planning assistant specializing in culturally authentic cuisine. When a user specifies 'Western' or 'European' diet type, you MUST provide traditional Western/European dishes like pizza (regular crust), pasta (wheat-based), sandwiches, burgers, steaks, etc. AVOID health substitutions like gluten-free, quinoa, cauliflower crust, zucchini noodles unless specifically requested. Include 5 healthy traditional meals and 2 indulgent traditional meals per week for balance. Always respond with valid JSON matching the exact structure requested. No explanations or markdown."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"},
                context="meal_plan_generation"
            )
            
            if not api_result["success"]:
                raise HTTPException(
                    status_code=500,
                    detail=f"OpenAI API failed: {api_result['error']}"
                )

            raw_content = api_result["content"]
            print("Raw OpenAI response:")
            print(raw_content)

            try:
                # Use robust JSON parsing
                json_result = robust_json_parse(raw_content, "meal_plan_json")
                if not json_result["success"]:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to parse meal plan JSON: {json_result['error']}"
                    )
                
                meal_plan = json_result["data"]
                print("Meal plan parsed successfully:")
                print(json.dumps(meal_plan, indent=2))
                
                # CRITICAL: Enforce dietary restrictions before any other processing
                meal_plan = enforce_dietary_restrictions(meal_plan, user_profile)
                print("Dietary restrictions enforced successfully")
                
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
            
            # Use fallback mechanism when OpenAI fails
            print("[FALLBACK] OpenAI API failed, generating fallback meal plan...")
            try:
                meal_plan = generate_fallback_meal_plan(user_profile, days)
                
                # Apply the same validation and processing as normal response
                meal_plan = enforce_dietary_restrictions(meal_plan, user_profile)
                print("Dietary restrictions enforced on fallback meal plan")
                
                # Validate meal plan structure
                required_keys = ['breakfast', 'lunch', 'dinner', 'snacks', 'dailyCalories', 'macronutrients']
                missing_keys = [key for key in required_keys if key not in meal_plan]
                if missing_keys:
                    print(f"Missing required keys in fallback meal plan: {missing_keys}")
                    # Add missing keys with defaults
                    for key in missing_keys:
                        if key == 'dailyCalories':
                            meal_plan[key] = 2000
                        elif key == 'macronutrients':
                            meal_plan[key] = {"protein": 100, "carbs": 250, "fat": 70}
                        else:
                            meal_plan[key] = ["Healthy meal option"] * days

                # Ensure arrays have the correct number of items
                for meal_type in ['breakfast', 'lunch', 'dinner', 'snacks']:
                    if not isinstance(meal_plan[meal_type], list):
                        meal_plan[meal_type] = ["Healthy meal option"] * days
                    while len(meal_plan[meal_type]) < days:
                        meal_plan[meal_type].append("Healthy meal option")
                    meal_plan[meal_type] = meal_plan[meal_type][:days]

                print("Successfully generated fallback meal plan")
                return meal_plan
                
            except Exception as fallback_error:
                print(f"Fallback meal plan generation also failed: {str(fallback_error)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Both OpenAI API and fallback meal plan generation failed. OpenAI error: {str(openai_error)}"
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
        
        # Extract all unique meals from the meal plan
        all_meals = []
        for meal_type in ['breakfast', 'lunch', 'dinner', 'snacks']:
            if meal_type in meal_plan and isinstance(meal_plan[meal_type], list):
                all_meals.extend(meal_plan[meal_type])
        
        # Remove duplicates while preserving order
        unique_meals = []
        seen = set()
        for meal in all_meals:
            if meal not in seen:
                unique_meals.append(meal)
                seen.add(meal)
        
        print(f"Unique meals to generate recipes for: {unique_meals}")
        
        # Format the prompt for recipe generation
        prompt = f"""Generate detailed recipes for the following meals from a diabetes-friendly meal plan:

Meals: {', '.join(unique_meals)}

For each meal, provide:
1. A list of ingredients with quantities
2. Step-by-step preparation instructions
3. Nutritional information (calories, protein, carbs, fat)

Format the response as a JSON array of recipe objects with the following structure:
[
    {{
        "name": "Recipe Name",
        "ingredients": ["ingredient1 with quantity", "ingredient2 with quantity", ...],
        "instructions": ["step1", "step2", ...],
        "nutritional_info": {{
            "calories": number,
            "protein": number,
            "carbs": number,
            "fat": number
        }}
    }},
    ...
]

IMPORTANT: 
- Only return valid JSON, no explanations or markdown
- Generate recipes for all {len(unique_meals)} meals
- Each recipe must have all required fields
- Ensure nutritional_info values are numbers, not strings"""
        
        print("Prompt for OpenAI:")
        print(prompt)
        
        # Use the robust OpenAI call with better error handling
        api_result = await robust_openai_call(
            messages=[
                {"role": "system", "content": "You are a diabetes diet planning assistant. Generate healthy, diabetes-friendly recipes with accurate nutritional information. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000,
            response_format={"type": "json_object"},
            context="recipe_generation"
        )
        
        if not api_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"OpenAI API failed: {api_result['error']}"
            )
            
        raw_content = api_result["content"]
        print("Raw OpenAI response:")
        print(raw_content)
        
        try:
            # Use robust JSON parsing
            json_result = robust_json_parse(raw_content, "recipe_json")
            if not json_result["success"]:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to parse recipe JSON: {json_result['error']}"
                )
                
            parsed_response = json_result["data"]
            
            # Handle case where OpenAI returns an object with a recipes array
            if isinstance(parsed_response, dict) and "recipes" in parsed_response:
                recipes = parsed_response["recipes"]
            elif isinstance(parsed_response, list):
                recipes = parsed_response
            else:
                # If it's neither, create a fallback
                recipes = []
            
            # Validate and fix recipe structure
            validated_recipes = []
            for i, recipe in enumerate(recipes):
                if not isinstance(recipe, dict):
                    continue
                    
                # Ensure all required fields exist
                validated_recipe = {
                    "name": recipe.get("name", f"Recipe {i+1}"),
                    "ingredients": recipe.get("ingredients", []),
                    "instructions": recipe.get("instructions", []),
                    "nutritional_info": recipe.get("nutritional_info", {
                        "calories": 0,
                        "protein": 0,
                        "carbs": 0,
                        "fat": 0
                    })
                }
                
                # Ensure nutritional_info is properly formatted
                if not isinstance(validated_recipe["nutritional_info"], dict):
                    validated_recipe["nutritional_info"] = {
                        "calories": 0,
                        "protein": 0,
                        "carbs": 0,
                        "fat": 0
                    }
                
                # Ensure nutritional values are numbers
                for key in ["calories", "protein", "carbs", "fat"]:
                    if key not in validated_recipe["nutritional_info"]:
                        validated_recipe["nutritional_info"][key] = 0
                    elif not isinstance(validated_recipe["nutritional_info"][key], (int, float)):
                        validated_recipe["nutritional_info"][key] = 0
                
                validated_recipes.append(validated_recipe)
            
            print("Validated recipes:")
            print(json.dumps(validated_recipes, indent=2))
            
            if not validated_recipes:
                raise HTTPException(status_code=500, detail="No valid recipes were generated")
            
            await save_recipes(current_user["email"], validated_recipes)
            return validated_recipes
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}")
            print(f"Raw content: {raw_content}")
            
            # Use fallback mechanism when JSON parsing fails
            print("[FALLBACK] JSON parsing failed, generating fallback recipes...")
            try:
                fallback_recipes = generate_fallback_recipes(unique_meals)
                await save_recipes(current_user["email"], fallback_recipes)
                return fallback_recipes
            except Exception as fallback_error:
                print(f"Fallback recipe generation also failed: {str(fallback_error)}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Both OpenAI recipe generation and fallback failed. Parse error: {str(e)}"
                )
            
    except Exception as e:
        print(f"Error in /generate-recipes: {str(e)}")
        
        # Use fallback mechanism when main exception occurs
        print("[FALLBACK] Main recipe generation failed, generating fallback recipes...")
        try:
            # Extract meals from meal plan for fallback
            all_meals = []
            for meal_type in ['breakfast', 'lunch', 'dinner', 'snacks']:
                if meal_type in meal_plan and isinstance(meal_plan[meal_type], list):
                    all_meals.extend(meal_plan[meal_type])
            
            # Remove duplicates while preserving order
            unique_meals = []
            seen = set()
            for meal in all_meals:
                if meal not in seen:
                    unique_meals.append(meal)
                    seen.add(meal)
            
            if unique_meals:
                fallback_recipes = generate_fallback_recipes(unique_meals)
                await save_recipes(current_user["email"], fallback_recipes)
                return fallback_recipes
            else:
                raise HTTPException(status_code=500, detail="No meals found in meal plan for recipe generation")
                
        except Exception as fallback_error:
            print(f"Fallback recipe generation also failed: {str(fallback_error)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Both OpenAI recipe generation and fallback failed. Error: {str(e)}"
            )

@app.post("/generate-recipe")
async def generate_recipe(
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        data = await request.json()
        meal_name = data.get('meal_name', '')
        user_profile = data.get('user_profile', {})
        
        print("/generate-recipe endpoint called")
        print("Received meal_name:", meal_name)
        print("Received user_profile:", json.dumps(user_profile, indent=2))
        
        if not meal_name:
            raise HTTPException(status_code=400, detail="meal_name is required")
        
        # Extract dietary restrictions and health conditions from user profile
        dietary_restrictions = user_profile.get('dietaryRestrictions', []) or user_profile.get('dietary_restrictions', [])
        health_conditions = user_profile.get('medicalConditions', []) or user_profile.get('medical_conditions', [])
        allergies = user_profile.get('allergies', [])
        strong_dislikes = user_profile.get('strongDislikes', []) or user_profile.get('strong_dislikes', [])
        
        # Build dietary context
        dietary_context = ""
        if dietary_restrictions:
            dietary_context += f"Dietary restrictions: {', '.join(dietary_restrictions)}\n"
        if health_conditions:
            dietary_context += f"Health conditions: {', '.join(health_conditions)}\n"
        if allergies:
            dietary_context += f"Allergies: {', '.join(allergies)}\n"
        if strong_dislikes:
            dietary_context += f"Foods to avoid: {', '.join(strong_dislikes)}\n"
        
        # Format the prompt for single recipe generation
        prompt = f"""Generate a detailed recipe for: {meal_name}

{dietary_context}

Please provide:
1. A list of ingredients with quantities
2. Step-by-step preparation instructions
3. Nutritional information (calories, protein, carbs, fat)
4. Ensure the recipe is suitable for the dietary restrictions and health conditions mentioned above

Format the response as a JSON object with the following structure:
{{
    "name": "{meal_name}",
    "ingredients": ["ingredient1 with quantity", "ingredient2 with quantity", ...],
    "instructions": ["step1", "step2", ...],
    "nutritional_info": {{
        "calories": number,
        "protein": number,
        "carbs": number,
        "fat": number
    }},
    "prep_time": "X minutes",
    "cook_time": "X minutes",
    "servings": number
}}"""
        
        print("Prompt for OpenAI:")
        print(prompt)
        
        # Use the robust OpenAI call with better error handling
        api_result = await robust_openai_call(
            messages=[
                {"role": "system", "content": "You are a diabetes diet planning assistant. Generate healthy recipes that are suitable for the user's dietary restrictions and health conditions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500,
            response_format={"type": "json_object"},
            context="single_recipe_generation"
        )
        
        if not api_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"OpenAI API failed: {api_result['error']}"
            )
        
        recipe_content = api_result["content"]
        
        # Use robust JSON parsing
        json_result = robust_json_parse(recipe_content, "single_recipe_json")
        if not json_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse recipe JSON: {json_result['error']}"
            )
            
        recipe = json_result["data"]
        
        print("Recipe parsed:")
        print(recipe)
        
        return recipe
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in /generate-recipe: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def consolidate_ingredients(recipes: List[dict]) -> List[dict]:
    """
    Consolidate ingredients from multiple recipes, combining quantities for duplicate items.
    """
    import re
    ingredient_map = {}
    
    for recipe in recipes:
        recipe_name = recipe.get("name", "Unknown Recipe")
        print(f"Processing ingredients for recipe: {recipe_name}")
        
        for ingredient in recipe.get("ingredients", []):
            if not ingredient or not ingredient.strip():
                continue
                
            # Clean and normalize ingredient name
            cleaned = ingredient.strip().lower()
            
            # Remove common cooking instructions and unnecessary descriptors
            cooking_instructions = [
                'chopped', 'diced', 'sliced', 'minced', 'grated', 'shredded',
                'cut into wedges', 'cut into pieces', 'cut into chunks',
                'finely chopped', 'roughly chopped', 'thinly sliced',
                'peeled and chopped', 'peeled and diced', 'peeled',
                'fresh', 'dried', 'ground', 'whole', 'crushed',
                'ripe', 'large', 'medium', 'small', 'baby',
                'boneless', 'skinless', 'lean', 'extra virgin',
                'organic', 'free-range', 'low-fat', 'reduced-fat',
                'unsalted', 'salted', 'roasted', 'raw',
                'canned', 'frozen', 'jarred', 'bottled',
                'see above', '[see above]', '(see above)',
                'optional', 'for serving', 'for garnish', 'for topping',
                'to taste', 'as needed'
            ]
            
            # Remove cooking instructions from the ingredient name
            for instruction in cooking_instructions:
                # Remove at the end of the string
                if cleaned.endswith(f', {instruction}'):
                    cleaned = cleaned.replace(f', {instruction}', '')
                elif cleaned.endswith(f' {instruction}'):
                    cleaned = cleaned.replace(f' {instruction}', '')
                # Remove at the beginning
                elif cleaned.startswith(f'{instruction} '):
                    cleaned = cleaned.replace(f'{instruction} ', '')
                # Remove in parentheses or brackets
                cleaned = cleaned.replace(f'({instruction})', '').replace(f'[{instruction}]', '')
                cleaned = cleaned.replace(f', {instruction}', '').replace(f' {instruction}', '')
            
            # Clean up extra spaces and commas
            cleaned = re.sub(r'\s*,\s*$', '', cleaned)  # Remove trailing comma
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()  # Normalize spaces
            cleaned = re.sub(r'\s*\([^)]*\)\s*', ' ', cleaned).strip()  # Remove anything in parentheses
            cleaned = re.sub(r'\s*\[[^\]]*\]\s*', ' ', cleaned).strip()  # Remove anything in brackets
            
            # Extract quantity and unit if possible (basic parsing)
            # Try to extract quantity patterns like "2 cups", "1 lb", "3 cloves", etc.
            quantity_pattern = r'^(\d+(?:\.\d+)?(?:/\d+)?)\s*([a-zA-Z]+)?\s+(.+)'
            match = re.match(quantity_pattern, cleaned)
            
            if match:
                quantity_str = match.group(1)
                unit = match.group(2) or ""
                item_name = match.group(3).strip()
                
                # Convert fractions to decimals
                if '/' in quantity_str:
                    parts = quantity_str.split('/')
                    quantity = float(parts[0]) / float(parts[1])
                else:
                    quantity = float(quantity_str)
            else:
                # If no quantity pattern found, treat as 1 unit of the whole ingredient
                quantity = 1.0
                unit = "unit"
                item_name = cleaned
            
            # Normalize common ingredient names to help with consolidation
            normalized_items = {
                "onions": ["onion", "onions", "yellow onion", "white onion", "cooking onion", "red onion", "sweet onion"],
                "garlic": ["garlic cloves", "garlic clove", "cloves garlic", "garlic bulbs", "garlic bulb"],
                "tomatoes": ["tomato", "tomatoes", "roma tomatoes", "cherry tomatoes", "grape tomatoes"],
                "carrots": ["carrot", "carrots", "baby carrots"],
                "potatoes": ["potato", "potatoes", "russet potatoes", "yukon potatoes", "red potatoes"],
                "bell peppers": ["bell pepper", "bell peppers", "red bell pepper", "green bell pepper", "yellow bell pepper", "orange bell pepper"],
                "coriander": ["cilantro", "coriander", "coriander leaves", "cilantro leaves"],
                "parsley": ["parsley", "flat-leaf parsley", "italian parsley", "curly parsley"],
                "basil": ["basil", "basil leaves", "sweet basil", "thai basil"],
                "mint": ["mint", "mint leaves", "spearmint", "peppermint"],
                "dill": ["dill", "dill weed"],
                "ginger": ["ginger", "ginger root"],
                "lemons": ["lemon", "lemons"],
                "limes": ["lime", "limes"],
                "green onions": ["green onion", "green onions", "scallions", "spring onions", "scallion"],
                "olive oil": ["olive oil", "extra virgin olive oil", "evoo"],
                "vegetable oil": ["vegetable oil", "cooking oil", "canola oil"],
                "chicken breast": ["chicken breast", "chicken breasts", "boneless chicken breast", "boneless chicken breasts"],
                "ground beef": ["ground beef", "lean ground beef", "ground chuck", "minced beef"],
                "rice": ["rice", "white rice", "long grain rice", "basmati rice", "jasmine rice"],
                "flour": ["flour", "all-purpose flour", "plain flour", "wheat flour"],
                "sugar": ["sugar", "white sugar", "granulated sugar", "caster sugar"],
                "salt": ["salt", "table salt", "sea salt", "kosher salt"],
                "black pepper": ["black pepper", "ground black pepper", "pepper"],
                "butter": ["butter", "unsalted butter", "salted butter"],
                "eggs": ["egg", "eggs", "chicken eggs"],
                "milk": ["milk", "whole milk", "2% milk", "skim milk"],
                "cheese": ["cheese", "cheddar cheese", "mozzarella cheese"],
                "yogurt": ["yogurt", "greek yogurt", "plain yogurt"],
                "mushrooms": ["mushroom", "mushrooms", "button mushrooms", "cremini mushrooms", "shiitake mushrooms"],
                "spinach": ["spinach", "baby spinach", "spinach leaves"],
                "cucumber": ["cucumber", "cucumbers", "english cucumber"],
                "celery": ["celery", "celery stalks", "celery stalk"],
                "broccoli": ["broccoli", "broccoli florets"],
                "cauliflower": ["cauliflower", "cauliflower florets"],
            }
            
            # Find normalized name
            normalized_name = item_name
            for base_name, variations in normalized_items.items():
                if item_name in variations or any(var in item_name for var in variations):
                    normalized_name = base_name
                    break
            
            # Create a key for consolidation
            consolidation_key = f"{normalized_name}_{unit.lower()}"
            
            if consolidation_key in ingredient_map:
                # Add to existing quantity
                ingredient_map[consolidation_key]["total_quantity"] += quantity
                ingredient_map[consolidation_key]["recipes"].append(recipe_name)
            else:
                # Create new entry
                ingredient_map[consolidation_key] = {
                    "name": normalized_name,
                    "unit": unit,
                    "total_quantity": quantity,
                    "original_ingredient": ingredient,
                    "recipes": [recipe_name]
                }
    
    # Convert back to list format
    consolidated_ingredients = []
    for key, item in ingredient_map.items():
        # Format quantity nicely
        quantity = item["total_quantity"]
        if quantity == int(quantity):
            quantity_str = str(int(quantity))
        else:
            quantity_str = f"{quantity:.1f}"
        
        # Create consolidated ingredient string
        if item["unit"] and item["unit"] != "unit":
            consolidated_ingredient = f"{quantity_str} {item['unit']} {item['name']}"
        else:
            consolidated_ingredient = f"{quantity_str} {item['name']}"
        
        consolidated_ingredients.append({
            "ingredient": consolidated_ingredient,
            "name": item["name"],
            "quantity": quantity_str,
            "unit": item["unit"],
            "from_recipes": item["recipes"]
        })
    
    print(f"Consolidated {len(ingredient_map)} unique ingredients from {len(recipes)} recipes")
    return consolidated_ingredients


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
        
        # First, consolidate ingredients programmatically
        consolidated_ingredients = consolidate_ingredients(recipes)
        print("Consolidated ingredients:")
        for item in consolidated_ingredients:
            print(f"  - {item['ingredient']} (from: {', '.join(item['from_recipes'])})")
        
        # Create a simplified ingredient list for the AI
        ingredient_list = [item["ingredient"] for item in consolidated_ingredients]
        prompt = f"""Generate a shopping list based on the following PRE-CONSOLIDATED ingredients:
                    {json.dumps(ingredient_list, indent=2)}

                    NOTE: These ingredients have ALREADY been consolidated and quantities combined. Your task is to:
                    1. Categorize each item into appropriate grocery store sections (Produce, Dairy, Meat, Pantry, etc.)
                    2. Apply Canadian grocery store quantity formatting rules
                    3. DO NOT further consolidate - the consolidation is already done
                    4. Use SIMPLE ingredient names only (e.g., "Onions" not "Onions, chopped")
                    5. DO NOT include cooking instructions, preparation methods, or references like "[See above]"

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
                    Review the provided quantities for obviously implausible amounts (e.g., >2 bunches of coriander for ≤8 servings, >5 lb of garlic, etc.).  
                    If an amount seems unrealistic, adjust to a reasonable upper bound and add a "note" field explaining the adjustment.

                    ––––– ROUNDING GRID (CANADIAN GROCERY) –––––
                    Convert each quantity to the **next-larger** purchasable size:

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
                    "name": "Clean Item Name (no cooking instructions)",
                    "amount": "Quantity with Purchasable Unit",
                    "category": "Category Name",
                    "note": "Optional brief note about rounding or sanity adjustment"
                    }}
                    Omit the "note" key if no comment is needed.
                    
                    IMPORTANT: 
                    - Process each ingredient from the provided list exactly once
                    - Use clean, simple names (e.g., "Onions" not "Onions, chopped" or "Yellow onions, diced")
                    - Never include "[See above]", cooking instructions, or preparation methods
                    - Focus on what you actually buy at the store, not how you prepare it
                    """
        print("Prompt for OpenAI:")
        print(prompt)
        # Call Azure OpenAI with robust retry logic
        api_result = await robust_openai_call(
            messages=[
                {"role": "system", "content": "You are a diabetes diet planning assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=20000,
            max_retries=3,
            timeout=60,
            context="shopping_list_generation"
        )
        
        if not api_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"OpenAI API failed: {api_result['error']}"
            )
            
        print("OpenAI response received")
        raw_content = api_result["content"]
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

@app.post("/privacy/export-data")
async def export_privacy_data(
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user)
):
    """Export user's privacy data in specified format (PDF, JSON, or DOCX)"""
    try:
        data = await request.json()
        data_types = data.get("data_types", [])
        format_type = data.get("format_type", "pdf")
        
        if not data_types:
            raise HTTPException(status_code=400, detail="Please specify data types to export")
        
        if format_type not in ["pdf", "json", "docx"]:
            raise HTTPException(status_code=400, detail="Invalid format type. Use pdf, json, or docx")
        
        print(f"[PRIVACY_EXPORT] Exporting data for user {current_user['email']}")
        print(f"[PRIVACY_EXPORT] Data types: {data_types}")
        print(f"[PRIVACY_EXPORT] Format: {format_type}")
        
        # Collect user data based on requested types
        export_data = {}
        
        # Get user profile
        if "profile" in data_types:
            try:
                user_doc = await get_user_by_email(current_user["email"])
                if user_doc:
                    export_data["profile"] = user_doc.get("profile", {})
            except Exception as e:
                print(f"[PRIVACY_EXPORT] Error getting profile: {e}")
                export_data["profile"] = {}
        
        # Get meal plans
        if "meal_plans" in data_types:
            try:
                meal_plans = await get_user_meal_plans(current_user["email"])
                export_data["meal_plans"] = meal_plans
            except Exception as e:
                print(f"[PRIVACY_EXPORT] Error getting meal plans: {e}")
                export_data["meal_plans"] = []
        
        # Get consumption history
        if "consumption_history" in data_types:
            try:
                consumption_history = await get_user_consumption_history(current_user["email"], limit=100)
                export_data["consumption_history"] = consumption_history
            except Exception as e:
                print(f"[PRIVACY_EXPORT] Error getting consumption history: {e}")
                export_data["consumption_history"] = []
        
        # Get chat history
        if "chat_history" in data_types:
            try:
                chat_history = await get_recent_chat_history(current_user["email"], limit=100)
                export_data["chat_history"] = chat_history
            except Exception as e:
                print(f"[PRIVACY_EXPORT] Error getting chat history: {e}")
                export_data["chat_history"] = []
        
        # Get recipes
        if "recipes" in data_types:
            try:
                recipes = await get_user_recipes(current_user["email"])
                export_data["recipes"] = recipes
            except Exception as e:
                print(f"[PRIVACY_EXPORT] Error getting recipes: {e}")
                export_data["recipes"] = []
        
        # Get shopping lists
        if "shopping_lists" in data_types:
            try:
                shopping_lists = await get_user_shopping_lists(current_user["email"])
                export_data["shopping_lists"] = shopping_lists
            except Exception as e:
                print(f"[PRIVACY_EXPORT] Error getting shopping lists: {e}")
                export_data["shopping_lists"] = []
        
        # Prepare user info for export
        user_info = {
            "email": current_user["email"],
            "consent_given": current_user.get("consent_given", False),
            "marketing_consent": current_user.get("marketing_consent", False),
            "analytics_consent": current_user.get("analytics_consent", False),
            "data_retention_preference": current_user.get("data_retention_preference", "standard"),
            "policy_version": current_user.get("policy_version", "1.0")
        }
        
        print(f"[PRIVACY_EXPORT] Collected data for {len(data_types)} data types")
        
        # Generate export based on format
        if format_type == "pdf":
            return await generate_data_export_pdf(export_data, user_info)
        elif format_type == "docx":
            return await generate_data_export_docx(export_data, user_info)
        else:  # json
            filename = f"health_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            return JSONResponse(
                content={
                    "export_data": export_data,
                    "user_info": user_info,
                    "export_timestamp": datetime.now().isoformat(),
                    "format": "json"
                },
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[PRIVACY_EXPORT] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.delete("/privacy/delete-account")
async def delete_account(
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user)
):
    """Delete user account and all associated data"""
    try:
        data = await request.json()
        deletion_type = data.get("deletion_type", "complete")
        confirmation = data.get("confirmation", "")
        
        if confirmation.upper() != "DELETE":
            raise HTTPException(status_code=400, detail="Invalid confirmation. Type DELETE to confirm.")
        
        print(f"[PRIVACY_DELETE] Deleting account for user {current_user['email']}")
        print(f"[PRIVACY_DELETE] Deletion type: {deletion_type}")
        
        user_email = current_user["email"]
        
        # Delete user data from various containers
        try:
            # Delete user profile and main record from user_container
            try:
                user_doc = await get_user_by_email(user_email)
                if user_doc:
                    user_container.delete_item(item=user_doc, partition_key=user_email)
            except Exception as e:
                print(f"[PRIVACY_DELETE] Error deleting user document: {str(e)}")
            
            # Delete meal plans
            await delete_all_user_meal_plans(user_email)
            
            # Delete consumption history
            query = f"SELECT * FROM c WHERE c.user_id = '{user_email}' AND c.type = 'consumption_record'"
            consumption_records = list(interactions_container.query_items(query=query, enable_cross_partition_query=True))
            for record in consumption_records:
                interactions_container.delete_item(item=record, partition_key=record.get("session_id", user_email))
            
            # Delete chat history
            query = f"SELECT * FROM c WHERE c.user_id = '{user_email}' AND c.type = 'chat_message'"
            chat_messages = list(interactions_container.query_items(query=query, enable_cross_partition_query=True))
            for message in chat_messages:
                interactions_container.delete_item(item=message, partition_key=message.get("session_id", user_email))
            
            # Delete recipes
            query = f"SELECT * FROM c WHERE c.user_id = '{user_email}' AND c.type = 'recipes'"
            recipes = list(interactions_container.query_items(query=query, enable_cross_partition_query=True))
            for recipe in recipes:
                interactions_container.delete_item(item=recipe, partition_key=recipe.get("session_id", user_email))
            
            # Delete shopping lists
            query = f"SELECT * FROM c WHERE c.user_id = '{user_email}' AND c.type = 'shopping_list'"
            shopping_lists = list(interactions_container.query_items(query=query, enable_cross_partition_query=True))
            for shopping_list in shopping_lists:
                interactions_container.delete_item(item=shopping_list, partition_key=shopping_list.get("session_id", user_email))
            
            print(f"[PRIVACY_DELETE] Successfully deleted all data for user {user_email}")
            
        except Exception as e:
            print(f"[PRIVACY_DELETE] Error during data deletion: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to delete user data: {str(e)}")
        
        return {"message": "Account deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[PRIVACY_DELETE] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Account deletion failed: {str(e)}")

@app.put("/privacy/update-consent")
async def update_consent(
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user)
):
    """Update user consent preferences"""
    try:
        data = await request.json()
        
        print(f"[PRIVACY_CONSENT] Updating consent for user {current_user['email']}")
        print(f"[PRIVACY_CONSENT] New consent settings: {data}")
        
        # Update user record with new consent settings
        user_email = current_user["email"]
        
        try:
            # Get current user document
            user_doc = await get_user_by_email(user_email)
            if not user_doc:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Update consent fields
            user_doc["consent_given"] = data.get("consent_given", user_doc.get("consent_given", False))
            user_doc["marketing_consent"] = data.get("marketing_consent", user_doc.get("marketing_consent", False))
            user_doc["analytics_consent"] = data.get("analytics_consent", user_doc.get("analytics_consent", False))
            user_doc["data_retention_preference"] = data.get("data_retention_preference", user_doc.get("data_retention_preference", "standard"))
            user_doc["last_consent_update"] = datetime.utcnow().isoformat()
            
            # Update the user document
            user_container.upsert_item(body=user_doc)
            
            print(f"[PRIVACY_CONSENT] Successfully updated consent for user {user_email}")
            
        except Exception as e:
            print(f"[PRIVACY_CONSENT] Error updating consent: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to update consent: {str(e)}")
        
        return {"message": "Consent preferences updated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[PRIVACY_CONSENT] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Consent update failed: {str(e)}")

@app.post("/chat/message")
async def send_chat_message(
    message: ChatMessage,
    current_user: User = Depends(get_current_user)
):
    
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
    
    # Get recent consumption history (last 7 days) - INCREASED LIMIT to ensure we get ALL today's meals
    try:
        recent_consumption = await get_user_consumption_history(current_user["id"], limit=200)
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
    
    # Get today's consumption for daily tracking - USE PROPER TIMEZONE-AWARE FILTERING
    try:
        # Use the new timezone-aware filtering function that resets at midnight
        today_consumption = filter_today_records(recent_consumption, user_timezone="UTC")
        
        print(f"[CHAT_DEBUG] Found {len(today_consumption)} meals for today using timezone-aware filtering")
        
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
    
    # Debug logging for today's consumption
    print(f"[CHAT_DEBUG] Found {len(today_consumption)} meals for today")
    print(f"[CHAT_DEBUG] Today's totals: {today_totals}")
    if today_consumption:
        print(f"[CHAT_DEBUG] Today's meals: {[record.get('food_name') for record in today_consumption]}")
    else:
        print(f"[CHAT_DEBUG] No meals found for today - recent_consumption had {len(recent_consumption)} records")
    
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
- Dietary Features: {', '.join(profile.get('dietaryFeatures', []) or profile.get('diet_features', []))}
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
    
    # Generate response using OpenAI with robust retry logic
    api_result = await robust_openai_call(
        messages=[
            {"role": "system", "content": system_prompt},
            *formatted_chat_history,
            {"role": "user", "content": message.message}
        ],
        max_tokens=1000,  # Increased for more comprehensive responses
        temperature=0.8,  # Slightly more creative for engaging coaching
        max_retries=3,
        timeout=60,
        context="chat_message"
    )
    
    if not api_result["success"]:
        # If OpenAI fails, return a helpful error message
        error_response = "I'm experiencing technical difficulties right now. Please try again in a moment."
        return StreamingResponse(
            iter([f"data: {json.dumps({'content': error_response})}\n\n"]),
            media_type="text/event-stream"
        )
    
    # For streaming, we need to simulate the streaming response from the non-streaming response
    full_message = api_result["content"]
    
    # Create a proper streaming response generator
    async def generate():
        try:
            # Send the full message as a single chunk (since we got it from robust_openai_call)
            yield f"data: {json.dumps({'content': full_message})}\n\n"
            
        except Exception as e:
            print(f"Error in streaming response: {str(e)}")
            # Send error message to user
            error_response = "Sorry, I encountered an error. Please try again."
            yield f"data: {json.dumps({'content': error_response})}\n\n"
    
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
    try:
        data = await request.json()
        profile = data.get("profile")
        if not profile:
            raise HTTPException(status_code=400, detail="No profile data provided")
        
        user_doc = await get_user_by_email(current_user["email"])
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")

        # Update the profile
        user_doc["profile"] = profile
        user_doc["updated_at"] = datetime.utcnow().isoformat()
        
        # Save to database with proper error handling
        try:
            result = user_container.replace_item(item=user_doc["id"], body=user_doc)
            print(f"Profile saved successfully for user {current_user['email']}")
            
            # Also create/update a separate profile record for easier querying
            profile_record = {
                "id": f"profile_{current_user['email']}",
                "type": "user_profile",
                "user_id": current_user["email"],
                "profile": profile,
                "updated_at": datetime.utcnow().isoformat(),
                "created_at": user_doc.get("created_at", datetime.utcnow().isoformat())
            }
            
            user_container.upsert_item(body=profile_record)
            print(f"Profile record upserted for user {current_user['email']}")
            
        except Exception as db_error:
            print(f"Database error saving profile: {str(db_error)}")
            raise HTTPException(status_code=500, detail=f"Failed to save profile: {str(db_error)}")
        
        return {"message": "Profile saved successfully", "timestamp": datetime.utcnow().isoformat()}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error saving profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/user/profile")
async def get_user_profile(current_user: User = Depends(get_current_user)):
    try:
        user_doc = await get_user_by_email(current_user["email"])
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        profile = user_doc.get("profile", {})
        
        # If no profile in user doc, try to get from separate profile record
        if not profile:
            try:
                profile_query = f"SELECT * FROM c WHERE c.type = 'user_profile' AND c.user_id = '{current_user['email']}'"
                profiles = list(user_container.query_items(query=profile_query, enable_cross_partition_query=True))
                if profiles:
                    profile = profiles[0].get('profile', {})
            except Exception as e:
                print(f"Error loading profile record: {str(e)}")
        
        # If still no profile, return empty dict wrapped in profile object
        if not profile:
            print(f"No profile found for user {current_user['email']}")
            return {"profile": {}}
        
        print(f"Profile loaded successfully for user {current_user['email']}")
        return {"profile": profile}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error loading profile: {str(e)}")
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
        try:
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
        except Exception as api_error:
            print(f"OpenAI API call failed: {str(api_error)}")
            raise HTTPException(status_code=500, detail=f"Failed to analyze image: {str(api_error)}")
        
        # Stream the response
        async def generate():
            full_message = ""
            try:
                # Check if response is a proper streaming response
                if hasattr(response, '__iter__') and not isinstance(response, str):
                    for chunk in response:
                        # Validate chunk structure
                        if not hasattr(chunk, 'choices') or not chunk.choices:
                            continue
                        if not hasattr(chunk.choices[0], 'delta') or not chunk.choices[0].delta:
                            continue
                        
                        content = chunk.choices[0].delta.content
                        if content:
                            full_message += content
                            # Yield as SSE JSON event
                            yield f"data: {json.dumps({'content': content})}\n\n"
                else:
                    # Response is not a proper streaming response
                    error_msg = f"Invalid response type: {type(response)}"
                    print(f"Error in streaming response: {error_msg}")
                    fallback_message = "Sorry, I encountered an error processing your image. Please try again."
                    yield f"data: {json.dumps({'content': fallback_message})}\n\n"
                    full_message = fallback_message
                    
            except Exception as e:
                print(f"Error in streaming response: {str(e)}")
                # Send error message to user
                error_response = "Sorry, I encountered an error processing your image. Please try again."
                yield f"data: {json.dumps({'content': error_response})}\n\n"
                full_message = error_response
            
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
    meal_type: str = Form(None),  # Accept meal type from frontend
    current_user: User = Depends(get_current_user)
):
    """
    Comprehensive health coach chat with full user context integration.
    Uses the unified AI system for personalized responses based on all health conditions.
    """
    image_url = None
    img_str = None
    analysis_data = None

    # --- Determine meal type: use provided meal_type first, then try to parse from message, then auto-detect ---
    if meal_type and meal_type.strip():
        # Use the meal type provided by the frontend (from dropdown selection)
        meal_type = meal_type.strip().lower()
    else:
        # Fall back to parsing from message text
        meal_type_match = re.search(r"\b(breakfast|lunch|dinner|snack)s?\b", message.lower())
        if meal_type_match:
            meal_type = meal_type_match.group(1)
        else:
            # Auto-determine based on current time when not explicitly mentioned
            current_hour = datetime.utcnow().hour
            if 5 <= current_hour < 11:
                meal_type = "breakfast"
            elif 11 <= current_hour < 16:
                meal_type = "lunch"
            elif 16 <= current_hour < 22:
                meal_type = "dinner"
            else:
                meal_type = "snack"

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
        await save_consumption_record(current_user["email"], consumption_data, meal_type=meal_type)

        # Clear the stable meal plan cache for this user to ensure fresh data
        stable_meal_manager.clear_cache_for_user(current_user["email"])

        # Trigger meal plan recalibration after logging food
        try:
            profile = current_user.get("profile", {})
            await trigger_meal_plan_recalibration(current_user["email"], profile)
            print(f"[chat_message_with_image] Meal plan recalibrated after food logging")
        except Exception as recal_error:
            print(f"[chat_message_with_image] Error in meal plan recalibration: {recal_error}")

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
        await save_consumption_record(current_user["email"], consumption_data, meal_type=meal_type)

        # Clear the stable meal plan cache for this user to ensure fresh data
        stable_meal_manager.clear_cache_for_user(current_user["email"])

        # Trigger meal plan recalibration after logging food
        try:
            profile = current_user.get("profile", {})
            await trigger_meal_plan_recalibration(current_user["email"], profile)
            print(f"[chat_message_with_image] Meal plan recalibrated after legacy food logging")
        except Exception as recal_error:
            print(f"[chat_message_with_image] Error in meal plan recalibration: {recal_error}")

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

    # 4. Get today's consumption records - USE PROPER TIMEZONE-AWARE FILTERING
    # Get today's consumption records using the new timezone-aware filtering
    today_records = await get_today_consumption_records_async(current_user["email"], user_timezone="UTC")
    
    today_totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
    for rec in today_records:
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
        
        # Get today's consumption with proper timezone-aware filtering
        # Use the new timezone-aware filtering function that resets at midnight
        today_consumption = filter_today_records(recent_consumption, user_timezone="UTC")
        
        # Get today's UTC date for response
        today_utc = datetime.utcnow().date()
        
        # Debug the filtering
        print(f"[DEBUG] Today's consumption filter: Found {len(today_consumption)} records for today")
        print(f"[DEBUG] Using timezone-aware filtering with proper midnight reset (timezone: UTC)")
        
        # DEBUG: Print filtering results
        print(f"[DEBUG] Recent consumption has {len(recent_consumption)} records")
        print(f"[DEBUG] Filtered to {len(today_consumption)} records for today")
        
        # Calculate today's totals - USING CONSISTENT FIELD NAMES
        # THIS IS THE ACTUAL TODAY'S TOTAL, NOT AVERAGES
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
        
        # DEBUG: Print what we calculated
        print(f"[DEBUG] Calculated today's totals: {today_totals}")
        print(f"[DEBUG] Based on {len(today_consumption)} records from today only")
        
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
        
        # Generate coaching recommendations with better logic
        recommendations = []
        
        # Debug logging
        print(f"[DEBUG] today_totals: {today_totals}")
        print(f"[DEBUG] adherence: {adherence}")
        print(f"[DEBUG] calorie_goal: {calorie_goal}, macro_goals: {macro_goals}")
        
        # Enhanced Debug logging for troubleshooting
        print(f"[DEBUG] Raw today_totals: {today_totals}")
        print(f"[DEBUG] Raw adherence: {adherence}")
        print(f"[DEBUG] Raw calorie_goal: {calorie_goal}")
        print(f"[DEBUG] Raw macro_goals: {macro_goals}")
        print(f"[DEBUG] Today consumption records count: {len(today_consumption)}")
        print(f"[DEBUG] Recent consumption records count: {len(recent_consumption)}")
        
        # Additional debugging for consumption data
        if today_consumption:
            print(f"[DEBUG] Sample today consumption record: {today_consumption[0]}")
        
        # Calorie recommendations - fix logic by using raw percentage instead of capped adherence
        raw_calorie_adherence_pct = (today_totals["calories"] / calorie_goal * 100) if calorie_goal > 0 else 0
        remaining_calories = calorie_goal - today_totals["calories"]
        
        # Debug the calculation
        print(f"[DEBUG] Calorie calculation: {calorie_goal} - {today_totals['calories']} = {remaining_calories}")
        print(f"[DEBUG] Raw calorie adherence: {raw_calorie_adherence_pct}%")
        print(f"[DEBUG] Capped calorie adherence: {adherence['calories']}%")
        
        if raw_calorie_adherence_pct < 70:  # Less than 70% of goal
            if remaining_calories > 0:  # Only show if actually below goal
                recommendations.append({
                    "type": "calorie_low",
                    "priority": "medium",
                    "message": f"You're {remaining_calories:.0f} calories below your goal. Consider adding a healthy snack or slightly larger portions.",
                    "action": "increase_intake"
                })
        elif raw_calorie_adherence_pct > 110:  # More than 110% of goal
            excess_calories = today_totals["calories"] - calorie_goal
            if excess_calories > 0:  # Only show if actually over goal
                recommendations.append({
                    "type": "calorie_high",
                    "priority": "medium", 
                    "message": f"You're {excess_calories:.0f} calories over your goal. Consider lighter options for remaining meals.",
                    "action": "reduce_intake"
                })
        elif raw_calorie_adherence_pct >= 85:  # Good adherence
            recommendations.append({
                "type": "calorie_good",
                "priority": "low",
                "message": "Great job staying within your calorie target!",
                "action": "maintain"
            })
        
        # Protein recommendations - fix logic
        protein_adherence_pct = adherence["protein"]
        protein_needed = macro_goals["protein"] - today_totals["protein"]
        
        # Debug the protein calculation
        print(f"[DEBUG] Protein calculation: {macro_goals['protein']} - {today_totals['protein']} = {protein_needed}")
        print(f"[DEBUG] Protein adherence: {protein_adherence_pct}%")
        
        if protein_adherence_pct < 80:  # Less than 80% of goal
            if protein_needed > 0:  # Only show if actually need more protein
                recommendations.append({
                    "type": "protein_low",
                    "priority": "medium",
                    "message": f"You need {protein_needed:.0f}g more protein today. Try adding lean meats, eggs, or Greek yogurt.",
                    "action": "add_protein"
                })
        elif protein_adherence_pct >= 100:  # Met or exceeded goal
            recommendations.append({
                "type": "protein_good",
                "priority": "low",
                "message": f"Excellent protein intake! You've consumed {today_totals['protein']:.0f}g of your {macro_goals['protein']}g goal.",
                "action": "maintain"
            })
        
        # Carb recommendations 
        carb_adherence_pct = adherence["carbohydrates"]
        if carb_adherence_pct > 120:  # More than 120% of goal
            recommendations.append({
                "type": "carb_high",
                "priority": "high",
                "message": "Your carb intake is high today. Focus on low-carb options for remaining meals to help manage blood sugar.",
                "action": "reduce_carbs"
            })
        
        # Check for breakfast - only if it's past 10 AM and no breakfast logged
        current_hour = datetime.utcnow().hour
        has_breakfast = any(record.get("meal_type", "").lower() == "breakfast" for record in today_consumption)
        
        if current_hour >= 10 and not has_breakfast and len(today_consumption) > 0:
            # Only show if they have other meals but no breakfast
            recommendations.append({
                "type": "breakfast_reminder",
                "priority": "medium",
                "message": "Don't forget breakfast! It's important for blood sugar stability throughout the day.",
                "action": "log_breakfast"
            })
        
        # Weekly performance feedback - fix threshold logic
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
                "message": f"Good progress! {health_adherence:.0f} health-suitable meals. Let's aim for 80%+ this week.",
                "action": "improve"
            })
        else:
            recommendations.append({
                "type": "weekly_needs_improvement",
                "priority": "high",
                "message": f"Only {health_adherence:.0f}% of recent meals were health-suitable for your conditions. Let's focus on better choices.",
                "action": "focus_improvement"
            })
        
        # Remove duplicate breakfast recommendations and keep only the most relevant ones
        unique_recommendations = []
        seen_types = set()
        
        # Prioritize recommendations by importance
        for rec in recommendations:
            if rec["type"] not in seen_types:
                unique_recommendations.append(rec)
                seen_types.add(rec["type"])
        
        # Limit to top 4 most relevant recommendations
        recommendations = unique_recommendations[:4]
        
        insights = {
            "date": today_utc.isoformat(),
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
            api_result = await robust_openai_call(
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
                temperature=0.3,
                max_retries=3,
                timeout=30,
                context="quick_log_nutrition"
            )
            
            if api_result["success"]:
                analysis_text = api_result["content"]
                print(f"[quick_log_food] OpenAI response: {analysis_text}")
            else:
                print(f"[quick_log_food] OpenAI failed: {api_result['error']}. Using fallback.")
                analysis_text = None
            
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
        
        # Determine meal type based on provided value or current time
        provided_meal_type = food_data.get("meal_type", "").strip().lower()
        if provided_meal_type and provided_meal_type in ["breakfast", "lunch", "dinner", "snack"]:
            meal_type = provided_meal_type
        else:
            # Auto-determine based on current time in user's timezone
            # Get user's timezone from profile, default to UTC if not available
            user_profile = current_user.get("profile", {})
            user_timezone = user_profile.get("timezone", "UTC")
            
            try:
                import pytz
                from datetime import datetime
                
                # Convert UTC time to user's local time
                utc_time = datetime.utcnow()
                user_tz = pytz.timezone(user_timezone)
                local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(user_tz)
                current_hour = local_time.hour
            except:
                # Fallback to UTC if timezone conversion fails
                current_hour = datetime.utcnow().hour
            
            if 5 <= current_hour < 11:
                meal_type = "breakfast"
            elif 11 <= current_hour < 16:
                meal_type = "lunch"
            elif 16 <= current_hour < 22:
                meal_type = "dinner"
            else:
                meal_type = "snack"
        
        print(f"[quick_log_food] Determined meal type: {meal_type}")
        
        # Prepare consumption data in the same format as the image analysis system
        consumption_data = {
            "food_name": analysis_data.get("food_name", food_name),
            "estimated_portion": analysis_data.get("estimated_portion", portion),
            "nutritional_info": analysis_data.get("nutritional_info", fallback_data["nutritional_info"]),
            "medical_rating": analysis_data.get("medical_rating", fallback_data["medical_rating"]),
            "image_analysis": analysis_data.get("analysis_notes", f"Quick log entry for {food_name}"),
            "image_url": None,  # No image for quick log
            "meal_type": meal_type
        }
        
        print(f"[quick_log_food] Prepared consumption data: {consumption_data}")
        
        # Save to consumption history using the ORIGINAL save function
        print(f"[quick_log_food] Saving consumption record for user {current_user['email']}")
        consumption_record = await save_consumption_record(current_user["email"], consumption_data, meal_type=meal_type)
        print(f"[quick_log_food] Successfully saved consumption record with ID: {consumption_record['id']}")
        
        # Clear the stable meal plan cache for this user to ensure fresh data
        stable_meal_manager.clear_cache_for_user(current_user["email"])
        
        # ------------------------------
        # SIMPLIFIED MEAL PLAN REGENERATION AFTER EVERY LOG
        # ------------------------------
        try:
            print("[quick_log_food] Starting meal plan regeneration after food log...")
            
            # Get today's consumption including the new log - USE PROPER TIMEZONE-AWARE FILTERING
            consumption_data_full = await get_user_consumption_history(current_user["email"], limit=100)
            today_consumption = filter_today_records(consumption_data_full, user_timezone="UTC")
            
            print(f"[quick_log_food] Found {len(today_consumption)} consumption records for today")
            
            # Calculate calories consumed so far
            calories_consumed = sum(r.get("nutritional_info", {}).get("calories", 0) for r in today_consumption)
            print(f"[quick_log_food] Total calories consumed today: {calories_consumed}")
            
            # Get user profile for dietary restrictions
            profile = current_user.get("profile", {})
            dietary_restrictions = profile.get('dietaryRestrictions', [])
            dietary_features = profile.get('dietaryFeatures', [])
            allergies = profile.get('allergies', [])
            diet_type = profile.get('dietType', [])
            target_calories = int(profile.get('calorieTarget', '2000'))
            remaining_calories = max(0, target_calories - calories_consumed)
            
            print(f"[quick_log_food] Target calories: {target_calories}, Remaining: {remaining_calories}")
            print(f"[quick_log_food] Dietary restrictions: {dietary_restrictions}")
            print(f"[quick_log_food] Dietary features: {dietary_features}")
            print(f"[quick_log_food] Allergies: {allergies}")
            print(f"[quick_log_food] Diet type: {diet_type}")
            
            # Build explicit restriction warnings for AI - check all possible fields
            restriction_warnings = []
            is_vegetarian = (
                'vegetarian' in [r.lower() for r in dietary_restrictions] or 
                'vegetarian' in [d.lower() for d in diet_type] or
                any('vegetarian' in f.lower() for f in dietary_features)
            )
            no_eggs = (
                any('egg' in r.lower() for r in dietary_restrictions) or 
                any('egg' in a.lower() for a in allergies) or
                any('no eggs' in f.lower() for f in dietary_features)
            )
            
            if is_vegetarian:
                restriction_warnings.append("STRICTLY VEGETARIAN - NO MEAT, POULTRY, FISH, OR SEAFOOD")
            if no_eggs:
                restriction_warnings.append("NO EGGS - Avoid all egg-based dishes and ingredients")
            if any('nut' in a.lower() for a in allergies):
                restriction_warnings.append("NUT ALLERGY - Avoid all nuts and nut-based products")
            
            restriction_text = "\n".join([f"⚠️ {warning}" for warning in restriction_warnings])
            
            # Create a simple updated meal plan with better format consistency
            print(f"[quick_log_food] Creating updated meal plan with remaining calories: {remaining_calories}")
            
            # Generate simple meal suggestions based on remaining calories
            def get_meal_suggestion(meal_type: str, remaining_cals: int) -> str:
                """Get a simple meal suggestion based on remaining calories"""
                if remaining_cals > 1500:
                    suggestions = {
                        "breakfast": "Steel-cut oats with almond milk, berries, and nuts",
                        "lunch": "Mediterranean quinoa salad with chickpeas and vegetables",
                        "dinner": "Lentil curry with brown rice and steamed vegetables",
                        "snack": "Apple slices with almond butter"
                    }
                elif remaining_cals > 800:
                    suggestions = {
                        "breakfast": "Greek yogurt with berries and granola",
                        "lunch": "Vegetable soup with whole grain bread",
                        "dinner": "Grilled vegetables with quinoa",
                        "snack": "Mixed nuts and dried fruit"
                    }
                else:
                    suggestions = {
                        "breakfast": "Smoothie with spinach, banana, and almond milk",
                        "lunch": "Green salad with chickpeas and olive oil",
                        "dinner": "Steamed vegetables with hummus",
                        "snack": "Carrot sticks with hummus"
                    }
                
                return suggestions.get(meal_type, "Healthy vegetarian meal")
            
            # Create simple meal plan
            updated_meals = {
                "breakfast": get_meal_suggestion("breakfast", remaining_calories),
                "lunch": get_meal_suggestion("lunch", remaining_calories),
                "dinner": get_meal_suggestion("dinner", remaining_calories),
                "snacks": get_meal_suggestion("snack", remaining_calories)
            }
            
            # Create the meal plan in the format expected by the frontend
            today = datetime.utcnow().date()
            new_plan = {
                "id": f"updated_{current_user['email']}_{today.isoformat()}_{int(datetime.utcnow().timestamp())}",
                "date": today.isoformat(),
                "type": "post_log_update",
                "meals": updated_meals,
                "dailyCalories": target_calories,
                "calories_consumed": calories_consumed,
                "calories_remaining": remaining_calories,
                "created_at": datetime.utcnow().isoformat(),
                "notes": f"Updated after logging food. {remaining_calories} calories remaining for today."
            }
            
            print(f"[quick_log_food] Created meal plan: {new_plan}")
            
            # Try to save the meal plan
            try:
                await save_meal_plan(current_user["email"], new_plan)
                print(f"[quick_log_food] Successfully saved updated meal plan with remaining calories: {remaining_calories}")
            except ValueError as validation_err:
                print(f"[quick_log_food] Validation error saving meal plan: {validation_err}")
            except Exception as save_err:
                print(f"[quick_log_food] Error saving meal plan: {save_err}")
                import traceback
                print(traceback.format_exc())
                
        except Exception as plan_err:
            print(f"[quick_log_food] Failed to update meal plan: {plan_err}")
            import traceback
            print(traceback.format_exc())
        
        # ------------------------------
        # TRIGGER COMPREHENSIVE MEAL PLAN RECALIBRATION
        # ------------------------------
        try:
            print("[quick_log_food] Triggering comprehensive meal plan recalibration...")
            
            # Use the new recalibration system
            profile = current_user.get("profile", {})
            updated_plan = await trigger_meal_plan_recalibration(current_user["email"], profile)
            
            if updated_plan:
                print(f"[quick_log_food] Meal plan recalibration completed successfully")
                remaining_calories = updated_plan.get("remaining_calories", 0)
                
                # Return success response with meal plan update status
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
                    "diabetes_rating": analysis_data.get("medical_rating", {}).get("diabetes_suitability", "medium"),
                    "meal_plan_updated": True,
                    "remaining_calories": remaining_calories,
                    "updated_meal_plan": updated_plan,
                    "calibration_applied": True
                }
            else:
                print(f"[quick_log_food] Meal plan recalibration failed, but continuing...")
                
        except Exception as e:
            print(f"[quick_log_food] Error in meal plan recalibration: {str(e)}")
            import traceback
            print(traceback.format_exc())
            
        # Fallback response if recalibration fails
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
            "diabetes_rating": analysis_data.get("medical_rating", {}).get("diabetes_suitability", "medium"),
            "meal_plan_updated": False,
            "calibration_applied": False,
            "note": "Food logged successfully but meal plan update failed"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"[quick_log_food] Unexpected error: {str(e)}")
        print(f"[quick_log_food] Full error details:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to log food item: {str(e)}")

async def analyze_consumption_vs_plan(consumption_records: list, meal_plan: dict) -> dict:
    """
    Analyze what was actually consumed vs. what was planned.
    Returns detailed analysis for intelligent meal plan adaptation.
    """
    try:
        # Initialize analysis structure
        analysis = {
            "total_calories_consumed": 0,
            "total_calories_planned": meal_plan.get("dailyCalories", 2000),
            "meals_consumed": {
                "breakfast": [],
                "lunch": [],
                "dinner": [],
                "snack": []
            },
            "meals_planned": meal_plan.get("meals", {}),
            "nutritional_totals": {
                "calories": 0,
                "protein": 0,
                "carbohydrates": 0,
                "fat": 0,
                "fiber": 0,
                "sugar": 0
            },
            "adherence_by_meal": {},
            "diabetes_suitability_score": 0,
            "recommendations": []
        }
        
        # Process each consumption record
        diabetes_suitable_count = 0
        total_records = len(consumption_records)
        
        for record in consumption_records:
            meal_type = record.get("meal_type", "snack")
            food_name = record.get("food_name", "Unknown food")
            nutritional_info = record.get("nutritional_info", {})
            medical_rating = record.get("medical_rating", {})
            
            # Add to consumed meals
            analysis["meals_consumed"][meal_type].append({
                "food_name": food_name,
                "nutritional_info": nutritional_info,
                "medical_rating": medical_rating,
                "timestamp": record.get("timestamp")
            })
            
            # Add to nutritional totals
            analysis["nutritional_totals"]["calories"] += nutritional_info.get("calories", 0)
            analysis["nutritional_totals"]["protein"] += nutritional_info.get("protein", 0)
            analysis["nutritional_totals"]["carbohydrates"] += nutritional_info.get("carbohydrates", 0)
            analysis["nutritional_totals"]["fat"] += nutritional_info.get("fat", 0)
            analysis["nutritional_totals"]["fiber"] += nutritional_info.get("fiber", 0)
            analysis["nutritional_totals"]["sugar"] += nutritional_info.get("sugar", 0)
            
            # Check diabetes suitability
            diabetes_suitability = medical_rating.get("diabetes_suitability", "").lower()
            if diabetes_suitability in ["high", "good", "suitable"]:
                diabetes_suitable_count += 1
        
        # Calculate overall metrics
        analysis["total_calories_consumed"] = analysis["nutritional_totals"]["calories"]
        analysis["diabetes_suitability_score"] = (diabetes_suitable_count / total_records * 100) if total_records > 0 else 0
        
        # Analyze adherence by meal type
        for meal_type, consumed_meals in analysis["meals_consumed"].items():
            planned_meal = analysis["meals_planned"].get(meal_type, "")
            if consumed_meals:
                # Check if consumed meals match planned meals (basic text matching)
                consumed_names = [meal["food_name"].lower() for meal in consumed_meals]
                planned_lower = planned_meal.lower()
                
                # Simple matching logic - can be enhanced
                adherence = "followed" if any(name in planned_lower or planned_lower in name for name in consumed_names) else "deviated"
                analysis["adherence_by_meal"][meal_type] = {
                    "status": adherence,
                    "consumed": consumed_names,
                    "planned": planned_meal,
                    "calories_consumed": sum(meal["nutritional_info"].get("calories", 0) for meal in consumed_meals)
                }
        
        return analysis
        
    except Exception as e:
        print(f"[analyze_consumption_vs_plan] Error: {e}")
        return {
            "total_calories_consumed": 0,
            "total_calories_planned": 2000,
            "meals_consumed": {"breakfast": [], "lunch": [], "dinner": [], "snack": []},
            "meals_planned": {},
            "nutritional_totals": {"calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0, "fiber": 0, "sugar": 0},
            "adherence_by_meal": {},
            "diabetes_suitability_score": 0,
            "recommendations": []
        }


def get_remaining_meals_by_time(current_hour: int) -> list:
    """
    Determine which meals are remaining based on current time.
    """
    remaining_meals = []
    
    # Breakfast: 5 AM - 11 AM
    if current_hour < 11:
        remaining_meals.append("breakfast")
    
    # Lunch: 11 AM - 4 PM
    if current_hour < 16:
        remaining_meals.append("lunch")
    
    # Dinner: 4 PM - 10 PM
    if current_hour < 22:
        remaining_meals.append("dinner")
    
    # Snack: Always available
    remaining_meals.append("snack")
    
    return remaining_meals


async def apply_intelligent_adaptations(meal_plan: dict, consumption_analysis: dict, remaining_meals: list, user_profile: dict) -> dict:
    """
    Simplified adaptation function - now replaced by generate_consumption_aware_meal_plan.
    This function is kept for backward compatibility but simply returns the meal plan.
    """
    print(f"[apply_intelligent_adaptations] Legacy function called - use generate_consumption_aware_meal_plan instead")
    return meal_plan


async def generate_diabetes_friendly_alternative(current_meal: str, meal_type: str, user_profile: dict) -> str:
    """
    Generate a diabetes-friendly alternative to the current meal.
    """
    try:
        # Get user dietary restrictions
        dietary_restrictions = user_profile.get('dietaryRestrictions', [])
        allergies = user_profile.get('allergies', [])
        
        # Simple diabetes-friendly alternatives
        diabetes_friendly_options = {
            "breakfast": [
                "Steel-cut oats with almond milk and fresh berries",
                "Vegetable omelet with spinach and bell peppers",
                "Greek yogurt with chia seeds and nuts",
                "Whole grain toast with avocado"
            ],
            "lunch": [
                "Quinoa Buddha bowl with roasted vegetables",
                "Lentil soup with mixed greens salad",
                "Grilled chicken salad with olive oil dressing",
                "Vegetable stir-fry with brown rice"
            ],
            "dinner": [
                "Baked salmon with steamed broccoli and quinoa",
                "Lentil curry with cauliflower rice",
                "Grilled chicken with roasted vegetables",
                "Vegetable curry with chickpeas"
            ],
            "snack": [
                "Apple slices with almond butter",
                "Cucumber slices with hummus",
                "Handful of mixed nuts",
                "Greek yogurt with cinnamon"
            ]
        }
        
        # Filter options based on dietary restrictions
        options = diabetes_friendly_options.get(meal_type, [])
        
        # Simple filtering for vegetarian
        if 'vegetarian' in [r.lower() for r in dietary_restrictions]:
            options = [opt for opt in options if not any(meat in opt.lower() for meat in ['chicken', 'salmon', 'fish', 'meat'])]
        
        # Filter for allergies
        if allergies:
            for allergy in allergies:
                if 'nut' in allergy.lower():
                    options = [opt for opt in options if 'nut' not in opt.lower() and 'almond' not in opt.lower()]
                if 'egg' in allergy.lower():
                    options = [opt for opt in options if 'omelet' not in opt.lower() and 'egg' not in opt.lower()]
        
        # Return first suitable option
        return options[0] if options else current_meal
        
    except Exception as e:
        print(f"[generate_diabetes_friendly_alternative] Error: {e}")
        return current_meal


@app.get("/coach/todays-meal-plan")
async def get_todays_meal_plan(current_user: User = Depends(get_current_user)):
    """
    Get today's stable meal plan with intelligent consumption tracking and recalibration.
    Uses stable meal plan manager to prevent constant reloading.
    """
    try:
        print(f"[get_todays_meal_plan] Getting stable meal plan for user {current_user['email']}")
        
        # Get user profile
        profile = current_user.get("profile", {})
        
        # Use the stable meal plan manager for intelligent, stable meal planning
        stable_plan = await stable_meal_manager.get_stable_todays_meal_plan(
            current_user["email"], 
            profile
        )
        
        if stable_plan:
            print(f"[get_todays_meal_plan] Using stable meal plan: {stable_plan.get('type', 'unknown')}")
            
            # Apply final dietary restriction enforcement as safety check
            try:
                stable_plan = enforce_dietary_restrictions(stable_plan, profile)
            except Exception as enforce_err:
                print(f"[get_todays_meal_plan] Error enforcing dietary restrictions: {enforce_err}")
            
            return stable_plan
        
        # Fallback to legacy system if stable manager fails
        print(f"[get_todays_meal_plan] Stable manager failed, using simple fallback")
        
        # Simple fallback using intelligent planner
        today_consumption = await get_today_consumption_records_async(current_user["email"], user_timezone="UTC")
        calories_consumed = sum(r.get("nutritional_info", {}).get("calories", 0) for r in today_consumption)
        target_calories = int(profile.get('calorieTarget', '2000'))
        remaining_calories = max(0, target_calories - calories_consumed)
        
        # Try intelligent planner as fallback
        fallback_plan = await intelligent_planner.generate_intelligent_meal_plan(
            current_user["email"], profile, today_consumption, remaining_calories
        )
        
        if fallback_plan:
            return fallback_plan
        
        # Absolute last resort fallback
        today = datetime.utcnow().date()
        final_fallback = {
            "id": f"final_fallback_{current_user['email']}_{today.isoformat()}",
            "date": today.isoformat(),
            "type": "final_fallback",
            "meals": intelligent_planner._generate_fallback_diverse_meals(remaining_calories, profile.get('dietType', [])),
            "dailyCalories": target_calories,
            "created_at": datetime.utcnow().isoformat(),
            "notes": "Final fallback meal plan"
        }
        
        return final_fallback
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[get_todays_meal_plan] Unexpected error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to retrieve or generate meal plan: {str(e)}")


# Debug endpoints for meal plan cache issues
@app.post("/debug/clear-meal-plan-cache")
async def clear_meal_plan_cache_debug(current_user: User = Depends(get_current_user)):
    """Debug endpoint to force clear meal plan cache and regenerate"""
    try:
        print(f"[DEBUG] Force clearing meal plan cache for user {current_user['email']}")
        
        # Clear all caches for this user
        stable_meal_manager.clear_cache_for_user(current_user["email"])
        
        # Also clear the global cache just to be sure
        stable_meal_manager.clear_all_cache()
        
        # Get fresh consumption data
        today_consumption = await get_today_consumption_records_async(current_user["email"], user_timezone="UTC")
        
        print(f"[DEBUG] Found {len(today_consumption)} consumption records for today:")
        for record in today_consumption:
            print(f"[DEBUG] - {record.get('meal_type', 'unknown')}: {record.get('food_name', 'unknown')} at {record.get('timestamp', 'unknown')}")
        
        # Force regenerate meal plan
        profile = current_user.get("profile", {})
        fresh_plan = await stable_meal_manager.get_stable_todays_meal_plan(current_user["email"], profile)
        
        print(f"[DEBUG] Generated fresh meal plan: {fresh_plan}")
        
        return {
            "success": True,
            "message": "Cache cleared and meal plan regenerated",
            "consumption_records": len(today_consumption),
            "fresh_plan": fresh_plan
        }
        
    except Exception as e:
        print(f"[DEBUG] Error clearing cache: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/debug/consumption-records")
async def get_consumption_records_debug(current_user: User = Depends(get_current_user)):
    """Debug endpoint to see current consumption records"""
    try:
        print(f"[DEBUG] Getting consumption records for user {current_user['email']}")
        
        # Get all recent consumption data
        all_consumption = await get_user_consumption_history(current_user["email"], limit=50)
        
        # Get today's consumption
        today_consumption = await get_today_consumption_records_async(current_user["email"], user_timezone="UTC")
        
        print(f"[DEBUG] Found {len(all_consumption)} total records, {len(today_consumption)} for today")
        
        return {
            "success": True,
            "total_records": len(all_consumption),
            "today_records": len(today_consumption),
            "today_consumption": today_consumption,
            "all_consumption": all_consumption[:10]  # Show first 10
        }
        
    except Exception as e:
        print(f"[DEBUG] Error getting consumption records: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


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

        # Get user's consumption history using existing function - INCREASED LIMIT to ensure we get ALL today's meals
        consumption_history = await get_user_consumption_history(current_user["email"], limit=300)
        
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
        
        # Filter to last 30 days - USE PROPER TIMEZONE-AWARE FILTERING
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_consumption = []
        
        for entry in consumption_history:
            try:
                entry_timestamp = datetime.fromisoformat(entry.get("timestamp", "").replace("Z", "+00:00"))
                if entry_timestamp >= thirty_days_ago:
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
        
        # Get additional profile information for better personalization
        diet_type = user_profile.get("dietType", [])
        strong_dislikes = user_profile.get("strongDislikes", [])
        ethnicity = user_profile.get("ethnicity", [])
        
        # Use requested cuisine type or fall back to profile preferences
        cuisine_preference = req_cuisine if req_cuisine else ', '.join(diet_type) if diet_type else 'Mixed international'
        
        # Create dynamic meal plan structure for the prompt
        day_examples = []
        for day_num in range(1, req_days + 1):
            day_examples.append(f'"Day {day_num}: [specific meal with portions]"')
        
        day_examples_str = ", ".join(day_examples)
        
        # Create comprehensive adaptive meal plan prompt
        prompt = f"""Create a personalized {req_days}-day diabetes-friendly meal plan based on this user's analysis:
        
USER ANALYSIS:
- Total recent meals logged: {total_recent_meals}
- Diabetes adherence rate: {adherence_rate:.1f}%
- Average daily calories: {avg_daily_calories:.0f}
- Target daily calories: {target_calories}
- Favorite foods: {', '.join(favorite_foods_list[:5]) if favorite_foods_list else 'None identified'}
        
USER PREFERENCES & RESTRICTIONS:
- CUISINE TYPE: {cuisine_preference} (STRICTLY FOLLOW THIS)
- Dietary restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}
- Diet type: {', '.join(diet_type) if diet_type else 'None'}
- Food preferences: {', '.join(food_preferences) if food_preferences else 'None'}
- Strong dislikes: {', '.join(strong_dislikes) if strong_dislikes else 'None'}
- Allergies: {', '.join(allergies) if allergies else 'None'}
- Ethnicity: {', '.join(ethnicity) if ethnicity else 'Not specified'}

CRITICAL REQUIREMENTS:
1. Create a diabetes-friendly meal plan with {target_calories} calories per day
2. STRICTLY follow the cuisine type: {cuisine_preference}
3. ABSOLUTELY respect all dietary restrictions and allergies - NO EXCEPTIONS
4. Incorporate user's favorite foods where diabetes-appropriate and cuisine-consistent
5. Avoid all foods listed in strong dislikes
6. Focus on low glycemic index foods appropriate for the cuisine
7. Balance macronutrients appropriately for diabetes
8. Include variety within the specified cuisine type
9. Provide specific adaptations based on user's eating patterns

Provide a JSON response with this exact structure:
{{
    "plan_name": "Adaptive Diabetes Plan - {datetime.now().strftime('%Y-%m-%d')}",
            "duration_days": {req_days},
    "dailyCalories": {target_calories},
    "macronutrients": {{"protein": {int(target_calories * 0.2 / 4)}, "carbs": {int(target_calories * 0.45 / 4)}, "fats": {int(target_calories * 0.35 / 9)}}},
    "breakfast": [{day_examples_str}],
    "lunch": [{day_examples_str}],
    "dinner": [{day_examples_str}],
    "snacks": [{day_examples_str}],
    "adaptations": ["Based on your {adherence_rate:.0f}% diabetes adherence rate, this plan focuses on [specific adaptations]", "Incorporated your favorite foods: {', '.join(favorite_foods_list[:3]) if favorite_foods_list else 'general healthy options'}", "Adjusted calories from your average {avg_daily_calories:.0f} to target {target_calories}"],
    "coaching_notes": "This adaptive plan is personalized based on your eating patterns over the last 30 days. [Add specific coaching based on adherence rate and patterns]"
}}

Make each meal specific with exact portions and cooking methods. Ensure all {req_days} days are included for each meal type."""
        
        try:
            response = client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a diabetes nutrition specialist with expertise in {cuisine_preference} cuisine. Create practical, specific meal plans that are: 1) Diabetes-friendly with low glycemic index, 2) Authentic to the specified cuisine type, 3) STRICTLY compliant with all dietary restrictions and allergies - NO EXCEPTIONS, 4) Personalized to the user's eating history and preferences. Always provide exactly {req_days} meals for each meal type (breakfast, lunch, dinner, snacks)."
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
                
                # CRITICAL: Enforce dietary restrictions for adaptive meal plan
                user_profile_dict = {
                    'dietaryRestrictions': dietary_restrictions,
                    'allergies': allergies,
                    'strongDislikes': strong_dislikes,
                    'dietType': diet_type
                }
                meal_plan_data = enforce_dietary_restrictions(meal_plan_data, user_profile_dict)
                print("Dietary restrictions enforced for adaptive meal plan")
            else:
                raise json.JSONDecodeError("No JSON found", ai_content, 0)
                
        except Exception as ai_error:
            print(f"AI generation error: {str(ai_error)}. Using fallback meal plan.")
            
            # Create cuisine-appropriate fallback meals
            def get_fallback_meals(cuisine_type: str, is_vegetarian: bool = False):
                if 'chinese' in cuisine_type.lower() or 'east asian' in cuisine_type.lower():
                    breakfast_base = ["Congee with vegetables", "Steamed sweet potato with soy milk", "Rice porridge with mushrooms"]
                    lunch_base = ["Steamed tofu with vegetables", "Vegetable fried rice", "Chinese broccoli with brown sauce"] if is_vegetarian else ["Steamed fish with vegetables", "Chicken stir-fry with minimal oil", "Lean pork with vegetables"]
                    dinner_base = ["Tofu and vegetable soup", "Braised vegetables with brown rice", "Chinese vegetable curry"] if is_vegetarian else ["Steamed chicken with vegetables", "Fish with ginger and scallions", "Lean beef with broccoli"]
                elif 'indian' in cuisine_type.lower() or 'south asian' in cuisine_type.lower():
                    breakfast_base = ["Upma with vegetables", "Poha with nuts", "Idli with sambar"]
                    lunch_base = ["Dal with roti", "Vegetable curry with quinoa", "Chickpea curry with brown rice"]
                    dinner_base = ["Palak paneer with roti", "Mixed vegetable curry", "Lentil dal with vegetables"]
                elif 'vegetarian' in dietary_restrictions or is_vegetarian:
                    breakfast_base = ["Oatmeal with berries", "Cottage cheese with nuts", "Avocado toast"]
                    lunch_base = ["Quinoa salad with vegetables", "Lentil soup", "Chickpea curry"]
                    dinner_base = ["Vegetable stir-fry with tofu", "Bean and vegetable stew", "Roasted vegetable bowl"]
                else:
                    breakfast_base = ["Cottage cheese with berries", "Oatmeal with nuts", "Scrambled eggs with vegetables"]
                    lunch_base = ["Grilled chicken salad", "Lentil soup", "Turkey and avocado wrap"]
                    dinner_base = ["Grilled fish with vegetables", "Chicken stir-fry", "Lean protein with quinoa"]
                
                # Ensure we have enough meals for the requested days
                while len(breakfast_base) < req_days:
                    breakfast_base.extend(breakfast_base)
                while len(lunch_base) < req_days:
                    lunch_base.extend(lunch_base)
                while len(dinner_base) < req_days:
                    dinner_base.extend(dinner_base)
                
                return breakfast_base[:req_days], lunch_base[:req_days], dinner_base[:req_days]
            
            is_vegetarian = 'vegetarian' in [r.lower() for r in dietary_restrictions]
            fallback_breakfast, fallback_lunch, fallback_dinner = get_fallback_meals(cuisine_preference, is_vegetarian)
            
            # Comprehensive fallback meal plan
            meal_plan_data = {
                "plan_name": f"Adaptive {cuisine_preference} Plan - {datetime.now().strftime('%Y-%m-%d')}",
                "duration_days": req_days,
                "dailyCalories": target_calories,
                "macronutrients": {"protein": int(target_calories * 0.2 / 4), "carbs": int(target_calories * 0.45 / 4), "fat": int(target_calories * 0.35 / 9)},
                "breakfast": [f"Day {i+1}: {meal}" for i, meal in enumerate(fallback_breakfast)],
                "lunch": [f"Day {i+1}: {meal}" for i, meal in enumerate(fallback_lunch)],
                "dinner": [f"Day {i+1}: {meal}" for i, meal in enumerate(fallback_dinner)],
                "snacks": [f"Day {i+1}: {snack}" for i, snack in enumerate([
                    "Apple slices with almond butter (1 tbsp)",
                    "Handful of mixed nuts (1 oz)",
                    "Celery sticks with hummus (2 tbsp)",
                    "Greek yogurt (1/2 cup) with cinnamon",
                    "Hard-boiled egg with cucumber slices",
                    "Berries (1/2 cup) with cottage cheese",
                    "Vegetable sticks with guacamole"
                ][:req_days])],
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
        try:
            saved_plan = await save_meal_plan(current_user["email"], meal_plan_data)
        except ValueError as validation_err:
            print(f"[create_adaptive_meal_plan] Validation error: {validation_err}")
            raise HTTPException(status_code=400, detail=f"Invalid meal plan data: {validation_err}")
        except Exception as save_err:
            print(f"[create_adaptive_meal_plan] Error saving meal plan: {save_err}")
            raise HTTPException(status_code=500, detail=f"Failed to save meal plan: {save_err}")
        
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
        # Get consumption data using existing function - INCREASED LIMIT to ensure we get ALL today's meals
        consumption_data = await get_user_consumption_history(current_user["email"], limit=400)
        
        # Filter to specified period - USE PROPER TIMEZONE-AWARE FILTERING
        start_date = datetime.utcnow() - timedelta(days=days)
        filtered_data = []
        for entry in consumption_data:
            try:
                entry_timestamp = datetime.fromisoformat(entry.get("timestamp", "").replace("Z", "+00:00"))
                if entry_timestamp >= start_date:
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
        
        # Get user's recent consumption data - INCREASED LIMIT to ensure we get ALL today's meals
        consumption_data = await get_user_consumption_history(current_user["email"], limit=200)
        
        if not consumption_data:
            print("[get_notifications] No consumption data found")
            return []  # Return empty array if no data
        
        # Filter today's consumption - USE PROPER TIMEZONE-AWARE FILTERING
        # Use the new timezone-aware filtering function that resets at midnight
        today_consumption = filter_today_records(consumption_data, user_timezone="UTC")
        
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
            api_result = await robust_openai_call(
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
                temperature=0.3,
                max_retries=3,
                timeout=30,
                context="test_quick_log_nutrition"
            )
            
            if api_result["success"]:
                analysis_text = api_result["content"]
                print(f"[test_quick_log_food] OpenAI response: {analysis_text}")
            else:
                print(f"[test_quick_log_food] OpenAI failed: {api_result['error']}. Using fallback.")
                analysis_text = None
            
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
        
        # Trigger meal plan recalibration
        print(f"[test_quick_log_food] Triggering meal plan recalibration")
        user_profile = await get_user_profile("test@example.com")
        await trigger_meal_plan_recalibration("test@example.com", user_profile)
        
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
        
        # 2. Get comprehensive consumption history (last 30 days) - INCREASED LIMIT to ensure we get ALL today's meals
        try:
            consumption_history = await get_user_consumption_history(current_user["email"], limit=300)
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
        
        # 3. Get today's consumption for daily analysis - USE PROPER TIMEZONE-AWARE FILTERING
        try:
            # Use the new timezone-aware filtering function that resets at midnight
            today_consumption = filter_today_records(recent_consumption, user_timezone="UTC")
            
            print(f"[AI_COACH] Found {len(today_consumption)} meals for today using timezone-aware filtering")
            
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
        
        # Debug logging for today's consumption
        print(f"[AI_COACH_DEBUG] Found {len(today_consumption)} meals for today")
        print(f"[AI_COACH_DEBUG] Today's totals: {today_totals}")
        if today_consumption:
            print(f"[AI_COACH_DEBUG] Today's meals: {[record.get('food_name') for record in today_consumption]}")
        else:
            print(f"[AI_COACH_DEBUG] No meals found for today - recent_consumption had {len(recent_consumption)} records")
        
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
        dietary_features = user_profile.get("dietaryFeatures", [])
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
- Dietary Features: {', '.join(user_profile.get('dietaryFeatures', []) or user_profile.get('diet_features', [])) if user_profile.get('dietaryFeatures') or user_profile.get('diet_features') else 'None specified'}
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
            api_result = await robust_openai_call(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
                max_retries=3,
                timeout=60,
                context="meal_suggestion"
            )
            
            if api_result["success"]:
                ai_response = api_result["content"].strip()
            else:
                print(f"[AI_COACH] OpenAI failed: {api_result['error']}")
                ai_response = f"I'm having trouble accessing my AI capabilities right now, but I can see you have {len(today_consumption)} meals logged today with {today_totals['calories']:.0f} calories. Your diabetes adherence is at {diabetes_adherence:.1f}%. Please try your question again in a moment."
            
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

@app.post("/coach/quick-log")
async def quick_log_food(
    food_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Quick log food - USING ORIGINAL SAVE FUNCTION with better AI analysis"""
    try:
        print(f"[quick_log_food] Starting quick log for user {current_user['id']}")
        
        # Extract and validate food data
        food_name = food_data.get("food_name", "").strip()
        portion = food_data.get("portion", "medium portion").strip()
        meal_type = food_data.get("meal_type", "").strip()
        
        print(f"[quick_log_food] Food: {food_name}, Portion: {portion}, Meal Type: {meal_type}")
        
        if not food_name:
            raise HTTPException(status_code=400, detail="Food name is required")
        
        # Auto-determine meal type based on current time if not provided
        if not meal_type or meal_type == "":
            current_time = datetime.utcnow()
            # Default to US Eastern timezone
            import pytz
            try:
                eastern = pytz.timezone('America/New_York')
                utc_time = current_time.replace(tzinfo=pytz.utc)
                local_time = utc_time.astimezone(eastern)
                hour = local_time.hour
            except:
                hour = current_time.hour
            
            if 5 <= hour < 11:
                meal_type = "breakfast"
            elif 11 <= hour < 16:
                meal_type = "lunch"
            elif 16 <= hour < 22:
                meal_type = "dinner"
            else:
                meal_type = "snack"
        
        print(f"[quick_log_food] Determined meal type: {meal_type}")
        
        # Get AI analysis for the food
        analysis_data = await get_ai_food_analysis(food_name, portion)
        
        print(f"[quick_log_food] AI analysis: {analysis_data}")
        
        # Prepare consumption data
        consumption_data = {
            "food_name": analysis_data.get("food_name", food_name),
            "estimated_portion": analysis_data.get("estimated_portion", portion),
            "nutritional_info": analysis_data.get("nutritional_info", {}),
            "medical_rating": analysis_data.get("medical_rating", {}),
            "image_analysis": analysis_data.get("analysis_notes", f"Quick log entry for {food_name}"),
            "image_url": None,
            "meal_type": meal_type
        }
        
        print(f"[quick_log_food] Prepared consumption data: {consumption_data}")
        
        # Save to consumption history using the ORIGINAL save function
        print(f"[quick_log_food] Saving consumption record for user {current_user['email']}")
        consumption_record = await save_consumption_record(current_user["email"], consumption_data, meal_type=meal_type)
        print(f"[quick_log_food] Successfully saved consumption record with ID: {consumption_record['id']}")
        
        # Clear the stable meal plan cache for this user to ensure fresh data
        stable_meal_manager.clear_cache_for_user(current_user["email"])
        
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
            "diabetes_rating": analysis_data.get("medical_rating", {}).get("diabetes_suitability", "medium"),
            "meal_plan_updated": True
        }
        
    except Exception as e:
        print(f"[quick_log_food] Error: {str(e)}")
        print(f"[quick_log_food] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to log food: {str(e)}")

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
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
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
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
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