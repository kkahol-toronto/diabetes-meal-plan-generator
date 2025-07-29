from fastapi import FastAPI, HTTPException, Depends, status, Request, Body, File, UploadFile, Form
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from models import (
    Token, TokenData, User, UserInDB, Patient, UserProfile, 
    MealPlanRequest, ChatMessage, RegistrationData, ImageAnalysisRequest
)
from utils import (
    get_password_hash, verify_password, create_access_token,
    get_today_utc_boundaries, get_user_timezone_boundaries, filter_today_records,
    robust_json_parse, generate_registration_code, send_registration_code,
    validate_and_normalize_profile, calculate_profile_completeness,
    SECRET_KEY, ALGORITHM, pwd_context, twilio_client, oauth2_scheme
)
from constants import (
    APP_TITLE, APP_VERSION, ACCESS_TOKEN_EXPIRE_MINUTES,
    DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE, DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT,
    CREATIVE_TEMPERATURE, PRECISE_TEMPERATURE, MEAL_PLAN_MAX_TOKENS, RECIPE_MAX_TOKENS,
    CHAT_MAX_TOKENS, PROTEIN_SUGGESTION_MAX_TOKENS, MEAL_SUGGESTION_MAX_TOKENS,
    ANALYSIS_MAX_TOKENS, SHORT_TIMEOUT, LONG_MAX_TOKENS,
    DEFAULT_CALORIE_TARGET, SNACK_CALORIE_LIMIT,
    BREAKFAST_OPTIONS, LUNCH_OPTIONS, DINNER_OPTIONS, SNACK_OPTIONS,
    NON_VEG_LUNCH_ADDITIONS, NON_VEG_DINNER_ADDITIONS, RECIPE_TEMPLATES,
    DEFAULT_PATIENT_PROFILE, PDF_TITLE, MAX_BACKOFF_SECONDS, BASE_BACKOFF_MULTIPLIER
)
from routers.auth import router as auth_router, get_current_user
from routers.meal_plan_generation import router as meal_plan_generation_router
from services.openai_service import robust_openai_call, get_openai_client
from services.consumption_analysis import (
    generate_consumption_aware_meal_plan,
    trigger_meal_plan_recalibration,
    generate_fresh_adaptive_meal_plan,
    analyze_consumption_vs_plan,
    get_remaining_meals_by_time,
    sanitize_vegetarian_meal,
    generate_safe_vegetarian_fallback,
    get_today_consumption_records_async,
    apply_intelligent_adaptations,
    generate_diabetes_friendly_alternative
)
from services.coaching_system import (
    get_consumption_progress_data,
    calculate_consistency_streak,
    calculate_personalized_weights,
    calculate_score_decay,
    get_daily_coaching_insights_data,
    get_nutrition_score_breakdown_data,
    detect_food_exploitation,
    quick_log_food_data,
    generate_personalized_protein_suggestions
)
import os
from dotenv import load_dotenv
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
# Handle pending consumption import gracefully due to event loop issues
try:
    from pending_consumption import pending_consumption_manager
except RuntimeError as e:
    if "no running event loop" in str(e):
        print(f"Warning: Could not import pending_consumption_manager due to event loop issue: {e}")
        pending_consumption_manager = None
    else:
        raise
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
# Suppress Azure CosmosDB HTTP logs
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)

# Load environment variables
load_dotenv(override=True)

#print the environment variables
print(os.getenv("AZURE_OPENAI_KEY"))
print(os.getenv("AZURE_OPENAI_ENDPOINT"))
print(os.getenv("AZURE_OPENAI_API_VERSION"))
print(os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"))
print(os.getenv("AZURE_OPENAI_MODEL_NAME"))
print(os.getenv("AZURE_OPENAI_MODEL_VERSION"))
print(os.getenv("INTERACTIONS_CONTAINER"))

app = FastAPI(title=APP_TITLE)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication router
app.include_router(auth_router, tags=["authentication"])

# Include meal plan generation router
app.include_router(meal_plan_generation_router, tags=["meal_plans"])

# Include utility router
from routers.utility import router as utility_router
app.include_router(utility_router, tags=["utility"])

# Include privacy router
from routers.privacy_data import router as privacy_router
app.include_router(privacy_router, tags=["privacy"])

# Include test router
from routers.test_endpoints import router as test_router
app.include_router(test_router, tags=["testing"])

# Include admin router
from routers.admin_endpoints import router as admin_router
app.include_router(admin_router, tags=["admin"])

# Include export router
from routers.export_system import router as export_router
from routers.chat_system import router as chat_router
from routers.user_profile_system import router as user_profile_router
from routers.consumption_analysis import router as consumption_analysis_router
from routers.ai_coach_system import router as ai_coach_router
from routers.ai_coach_comprehensive import router as ai_coach_comprehensive_router
from routers.meal_plan_crud import router as meal_plan_crud_router
from routers.meal_plans import router as meal_plans_router
from routers.pending_consumption_system import router as pending_consumption_router
from routers.pdf_generation_system import router as pdf_generation_router
from routers.coaching_insights_system import router as coaching_insights_router
from routers.consumption_management import router as consumption_management_router
app.include_router(export_router, tags=["export"])
app.include_router(chat_router, tags=["chat"])
app.include_router(user_profile_router, tags=["user"])
app.include_router(consumption_analysis_router, tags=["consumption_analysis"])
app.include_router(ai_coach_router, tags=["ai_coach"])
app.include_router(ai_coach_comprehensive_router, tags=["ai_coach_comprehensive"])
app.include_router(meal_plan_crud_router, tags=["meal_plans"])
app.include_router(meal_plans_router, tags=["meal_plans"])
app.include_router(pending_consumption_router, tags=["pending_consumption"])
app.include_router(pdf_generation_router, tags=["pdf_generation"])
app.include_router(coaching_insights_router, tags=["coaching_insights"])
app.include_router(consumption_management_router, tags=["consumption_management"])

# OpenAI client is now imported from services.openai_service

# Twilio client is now imported from utils

# robust_openai_call function is now imported from services.openai_service

# JSON parsing utility function is now imported from utils


# Health endpoint moved to routers/utility.py

# Security configuration is now imported from utils
# ACCESS_TOKEN_EXPIRE_MINUTES is now imported from constants

# oauth2_scheme is now imported from utils

# Authentication functions are now imported from utils

# Timezone utility functions are now imported from utils

# Consumption analysis functions moved to services/consumption_analysis.py










# get_current_user is now imported from routers.auth

# Registration utility functions are now imported from utils

# Login endpoint moved to routers/auth.py

# Register endpoint moved to routers/auth.py

# Admin create-patient endpoint moved to routers/auth.py

# Admin patients endpoint moved to routers/auth.py

# Admin endpoints moved to routers/admin_endpoints.py

# Admin patient profile endpoints moved to routers/admin_endpoints.py

# Remaining admin endpoints moved to routers/admin_endpoints.py

# Remaining admin endpoints moved to routers/admin_endpoints.py

# Remaining admin endpoints moved to routers/admin_endpoints.py

# Remaining admin endpoints moved to routers/admin_endpoints.py

# Remaining admin endpoints moved to routers/admin_endpoints.py


def generate_meal_plan_prompt(user_profile: UserProfile) -> str:
    """Legacy function - now redirects to comprehensive profiling"""
    # This function is deprecated - the main endpoint now uses comprehensive profiling
    return "This function has been replaced with comprehensive profile analysis"

def generate_recipe_prompt(meal_name: str, user_profile: UserProfile) -> str:
    """Legacy function - now redirects to comprehensive profile handling"""
    # This function is deprecated - the main endpoint now uses comprehensive profiling
    return "This function has been replaced with comprehensive profile analysis"

# Comprehensive AI Health Coach System moved to routers/ai_coach_system.py

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    return {"message": "Welcome to Diabetes Diet Manager API"}


# Recipe generation endpoints moved to routers/meal_plan_generation.py

# Shopping list endpoint moved to routers/meal_plan_generation.py


# Privacy endpoints moved to routers/privacy_data.py

@app.exception_handler(Exception)
async def global_exception_handler(request: FastAPIRequest, exc: Exception):
    print(f"Global exception handler: {exc}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )

# Test-echo endpoint moved to routers/utility.py

# Export test-minimal endpoint moved to routers/utility.py

# Meal Plan CRUD operations moved to routers/meal_plan_crud.py

# PDF generation endpoints moved to routers/pdf_generation_system.py

# Additional meal plan endpoints moved to routers/meal_plan_crud.py

# Consumption endpoints moved to routers/consumption_management.py

# ======================================================================
# PENDING CONSUMPTION ENDPOINTS moved to routers/pending_consumption_system.py
# ======================================================================

# PUT, DELETE endpoints moved to routers/pending_consumption_system.py

# POST chat endpoint moved to routers/pending_consumption_system.py

# Consumption progress endpoint moved to routers/coaching_insights_system.py





# Daily insights endpoint moved to routers/coaching_insights_system.py

# First nutrition-score-breakdown endpoint (delegating) removed - duplicate resolved

# detect_food_exploitation function moved to routers/coaching_insights_system.py

@app.post("/coach/quick-log")
async def quick_log_food(
    food_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Quick log food - USING ORIGINAL SAVE FUNCTION with better AI analysis"""
    try:
        # Get user profile
        profile = current_user.get("profile", {})
        
        # Use the extracted coaching system function
        return await quick_log_food_data(food_data, current_user["email"], profile)
    except Exception as e:
        print(f"[quick_log_food] Error: {str(e)}")
        import traceback
        print(f"[quick_log_food] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to log food item: {str(e)}")


def generate_personalized_protein_suggestions(user_profile: dict) -> str:
    """Generate personalized protein suggestions based on user dietary restrictions."""
    from services.coaching_system import generate_personalized_protein_suggestions as get_suggestions
    return get_suggestions(user_profile)

# Second nutrition-score-breakdown endpoint (full implementation) moved to routers/coaching_insights_system.py

# detect_food_exploitation function (full implementation) moved to routers/coaching_insights_system.py

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
        
        Guidelines for diabetes_suitability rating:
        - "high": Vegetables, lean proteins, nuts, low-sugar fruits, whole grains in moderate portions, foods with fiber ≥3g and sugar ≤10g
        - "medium": Foods with moderate carbs/sugar (10-25g sugar, moderate fiber), dairy products, starchy vegetables
        - "low": High-sugar foods (>25g sugar), refined grains, processed foods, high-sodium items (>600mg)
        
        Be more generous with "high" ratings for genuinely healthy foods. Base estimates on standard nutritional databases.
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
        
        # ------------------------------
        # SIMPLIFIED MEAL PLAN REGENERATION AFTER EVERY LOG
        # ------------------------------
        try:
            print("[quick_log_food] Starting meal plan regeneration after food log...")
            
            # Get today's consumption including the new log - USE PROPER TIMEZONE-AWARE FILTERING
            consumption_data_full = await get_user_consumption_history(current_user["email"], limit=100)
            user_timezone = current_user.get("profile", {}).get("timezone", "UTC")
            today_consumption = filter_today_records(consumption_data_full, user_timezone=user_timezone)
            
            print(f"[quick_log_food] Found {len(today_consumption)} consumption records for today")
            
            # Calculate calories consumed so far
            calories_consumed = sum(r.get("nutritional_info", {}).get("calories", 0) for r in today_consumption)
            print(f"[quick_log_food] Total calories consumed today: {calories_consumed}")
            
            # Get user profile for dietary restrictions
            profile = current_user.get("profile", {})
            dietary_restrictions = profile.get('dietaryRestrictions', [])
            dietary_features = profile.get('dietaryFeatures', []) or profile.get('diet_features', [])
            allergies = profile.get('allergies', [])
            diet_type = profile.get('dietType', [])
            target_calories = int(profile.get('calorieTarget', '2000'))
            remaining_calories = max(0, target_calories - calories_consumed)
            
            print(f"[quick_log_food] Target calories: {target_calories}, Remaining: {remaining_calories}")
            print(f"[quick_log_food] Dietary restrictions: {dietary_restrictions}")
            print(f"[quick_log_food] Dietary features: {dietary_features}")
            print(f"[quick_log_food] Allergies: {allergies}")
            print(f"[quick_log_food] Diet type: {diet_type}")
            
            # FIXED: Build explicit restriction warnings for AI with comprehensive detection
            all_dietary_info = []
            for field in [dietary_restrictions, dietary_features, diet_type]:
                if isinstance(field, list):
                    all_dietary_info.extend([str(item).lower() for item in field])
                elif isinstance(field, str) and field:
                    all_dietary_info.append(field.lower())
            
            restriction_warnings = []
            if any('vegetarian' in info for info in all_dietary_info):
                restriction_warnings.append("VEGETARIAN - Exclude meat, poultry, fish, and seafood")
            
            # Check for egg restrictions in ALL fields including dietaryFeatures  
            if (any('egg' in r.lower() for r in dietary_restrictions) or 
                any('egg' in a.lower() for a in allergies) or
                any('no egg' in feature.lower() or 'no eggs' in feature.lower() or 'vegetarian (no egg' in feature.lower() or 'vegetarian (no eggs' in feature.lower() for feature in dietary_features)):
                restriction_warnings.append("EGG-FREE - Avoid eggs and egg-containing dishes")
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



def generate_personalized_protein_suggestions(user_profile: dict) -> str:
    """Generate personalized protein suggestions based on user dietary restrictions."""
    from services.coaching_system import generate_personalized_protein_suggestions as get_suggestions
    return get_suggestions(user_profile)

@app.get("/coach/todays-meal-plan")
async def get_todays_meal_plan(current_user: User = Depends(get_current_user)):
    """
    Get today's adaptive meal plan based on recent consumption and health conditions.
    Returns the most recent meal plan or creates a new one if needed.
    """
    try:
        print(f"[get_todays_meal_plan] Getting today's meal plan for user {current_user['email']}")
        
        # Get user profile for timezone
        profile = current_user.get("profile", {})
        
        # DEBUG: Print timezone information
        user_timezone = profile.get("timezone", "UTC")
        print(f"[TIMEZONE_DEBUG] User: {current_user['email']}")
        print(f"[TIMEZONE_DEBUG] Profile timezone: {user_timezone}")
        
        # Calculate and print day boundaries
        try:
            import pytz
            user_tz = pytz.timezone(user_timezone)
            utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
            user_now = utc_now.astimezone(user_tz)
            start_of_today_user = user_now.replace(hour=0, minute=0, second=0, microsecond=0)
            start_of_tomorrow_user = start_of_today_user + timedelta(days=1)
            start_of_today_utc = start_of_today_user.astimezone(pytz.utc).replace(tzinfo=None)
            start_of_tomorrow_utc = start_of_tomorrow_user.astimezone(pytz.utc).replace(tzinfo=None)
            
            print(f"[TIMEZONE_DEBUG] User local time: {user_now}")
            print(f"[TIMEZONE_DEBUG] Start of today (user timezone): {start_of_today_user}")
            print(f"[TIMEZONE_DEBUG] Start of today (UTC): {start_of_today_utc}")
            print(f"[TIMEZONE_DEBUG] Start of tomorrow (UTC): {start_of_tomorrow_utc}")
        except Exception as tz_error:
            print(f"[TIMEZONE_DEBUG] Error calculating timezone boundaries: {tz_error}")
        
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
                """Convert legacy meal-plan keys (breakfast, lunch, dinner, snacks arrays) into
                the new shape { 'meals': { breakfast: str, lunch: str, dinner: str, snack: str } } expected by the dashboard."""
                val = latest_plan.get(meal_key)
                if isinstance(val, list):
                    # For today's personalized meal plan display, always use Day 1 (index 0)
                    # This ensures we show "Day 1: [meal]" as today's meal, not some random weekday
                    return val[0] if val else ""
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
                    # For today's display, always use Day 1 (index 0) from multi-day plans
                    # This prevents showing "Day 2", "Day 3" etc. in today's meal plan
                    return val[0] if val else ""
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
Dietary Features: {', '.join(dietary_features) or 'None'}
Allergies: {', '.join(allergies) or 'None'}
Health Conditions: {', '.join(profile.get('medical_conditions', [])) or 'None'}

🚨 CRITICAL DIETARY ENFORCEMENT 🚨
{restriction_text if restriction_warnings else ""}

ABSOLUTE REQUIREMENTS:
- ALL dishes must be diabetes-friendly (low glycemic index)
- All dishes must follow dietary restrictions, dietary features, and allergies
- Provide specific dish names, not generic descriptions
- Each meal should be balanced and nutritious
- Ensure ingredients comply with dietary restrictions

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
                    api_result = await robust_openai_call(
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7, # Slightly higher temperature for more creativity
                        max_tokens=500,
                        max_retries=3,
                        timeout=30,
                        context="todays_meal_plan_refinement"
                    )

                    if api_result["success"]:
                        import json as _json
                        ai_json = _json.loads(api_result["content"])
                    else:
                        print(f"[todays_meal_plan] OpenAI failed: {api_result['error']}. Skipping refinement.")
                        return todays_plan
                    
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
                    try:
                        await save_meal_plan(current_user["email"], todays_plan)
                        print("[get_todays_meal_plan] Saved AI-generated concrete meals for today.")
                    except ValueError as validation_err:
                        print(f"[get_todays_meal_plan] Validation error saving concrete meals: {validation_err}")
                        # Don't save invalid/empty meal plans
                    except Exception as save_err:
                        print(f"[get_todays_meal_plan] Error saving concrete meals: {save_err}")
                except Exception as gen_err:
                    print(f"[get_todays_meal_plan] Error during concrete meal generation or parsing: {gen_err}")
                    import traceback
                    print(traceback.format_exc())

        # ------------------
        # ADVANCED REAL-TIME CALIBRATION SYSTEM
        # ------------------
        try:
            # Get today's consumption with detailed analysis
            today_consumption_full = await get_today_consumption_records_async(current_user["email"], user_timezone="UTC")
            
            print(f"[CALIBRATION] Starting advanced calibration with {len(today_consumption_full)} consumption records")
            
            # Analyze what was actually consumed vs. planned
            consumption_analysis = await analyze_consumption_vs_plan(today_consumption_full, todays_plan)
            
            # Get current time to determine what meals are remaining
            now = datetime.utcnow()
            current_hour = now.hour
            
            # Determine remaining meal types based on time of day
            remaining_meals = get_remaining_meals_by_time(current_hour)
            
            print(f"[CALIBRATION] Current hour: {current_hour}, Remaining meals: {remaining_meals}")
            print(f"[CALIBRATION] Consumption analysis: {consumption_analysis}")
            
            # Apply consumption-aware meal plan generation
            todays_plan = await generate_consumption_aware_meal_plan(
                todays_plan, 
                consumption_analysis, 
                remaining_meals,
                current_user.get("profile", {})
            )
            
            # Mark plan as calibrated if any consumption has occurred
            if len(today_consumption_full) > 0:
                todays_plan["type"] = "real_time_calibrated"
                todays_plan["last_calibrated"] = datetime.utcnow().isoformat()
                todays_plan["calibration_trigger"] = "consumption_logged"
                
                # Save calibrated plan
                try:
                    if "id" not in todays_plan or todays_plan["id"].startswith("derived_") or todays_plan["id"].startswith("fallback_"):
                        todays_plan["id"] = f"calibrated_{current_user['email']}_{today.isoformat()}_{int(datetime.utcnow().timestamp())}"
                        todays_plan["created_at"] = datetime.utcnow().isoformat()
                    
                    await save_meal_plan(current_user["email"], todays_plan)
                    print("[CALIBRATION] Saved real-time calibrated meal plan")
                except Exception as save_err:
                    print(f"[CALIBRATION] Error saving calibrated plan: {save_err}")

        except Exception as e:
            print(f"[CALIBRATION] Advanced calibration error: {e}")
            import traceback
            print(traceback.format_exc())

        # ALWAYS GENERATE FRESH VEGETARIAN MEAL PLANS - Don't use old plans that may contain non-vegetarian dishes
        profile = current_user.get("profile", {})
        dietary_restrictions = profile.get('dietaryRestrictions', [])
        dietary_features = profile.get('dietaryFeatures', []) or profile.get('diet_features', [])
        allergies = profile.get('allergies', [])
        diet_type = profile.get('dietType', [])
        
        # FIXED: Check if user is vegetarian or has egg restrictions from ALL sources including dietaryFeatures
        all_dietary_info = []
        for field in [dietary_restrictions, dietary_features, diet_type]:
            if isinstance(field, list):
                all_dietary_info.extend([str(item).lower() for item in field])
            elif isinstance(field, str) and field:
                all_dietary_info.append(field.lower())
        
        is_vegetarian = any('vegetarian' in info for info in all_dietary_info)
        
        # CRITICAL FIX: Check for egg restrictions in ALL fields including dietaryFeatures - handle both singular and plural
        no_eggs = (
            any('egg' in r.lower() for r in dietary_restrictions) or 
            any('egg' in a.lower() for a in allergies) or
            any('no egg' in feature.lower() or 'no eggs' in feature.lower() or 'vegetarian (no egg' in feature.lower() or 'vegetarian (no eggs' in feature.lower() for feature in dietary_features)
        )
        
        # Always generate fresh diverse meals for users with dietary restrictions
        if is_vegetarian or no_eggs:
            print(f"[get_todays_meal_plan] User has dietary restrictions - generating fresh diverse vegetarian meal plan")
            
            # Use the new comprehensive recalibration system
            today_consumption = await get_today_consumption_records_async(current_user["email"], user_timezone="UTC")
            calories_consumed = sum(r.get("nutritional_info", {}).get("calories", 0) for r in today_consumption)
            target_calories = int(profile.get('calorieTarget', '2000'))
            remaining_calories = max(0, target_calories - calories_consumed)
            
            # Generate fresh adaptive meal plan
            fresh_plan = await generate_fresh_adaptive_meal_plan(
                current_user["email"],
                today_consumption,
                remaining_calories,
                is_vegetarian,
                no_eggs,
                dietary_restrictions,
                allergies,
                profile.get('dietType', []),
                profile.get('foodPreferences', []),
                profile.get('strongDislikes', [])
            )
            
            # Try to generate fresh adaptive vegetarian meal plan
            fresh_plan = await generate_fresh_adaptive_meal_plan(
                current_user["email"],
                today_consumption,
                remaining_calories,
                is_vegetarian,
                no_eggs,
                dietary_restrictions,
                allergies,
                profile.get('dietType', []),
                profile.get('foodPreferences', []),
                profile.get('strongDislikes', [])
            )
            
            if fresh_plan:
                todays_plan = fresh_plan
                print(f"[get_todays_meal_plan] Generated fresh adaptive vegetarian meal plan")
            else:
                # Fallback to safe vegetarian meals
                todays_plan = generate_safe_vegetarian_fallback(
                    current_user["email"],
                    remaining_calories,
                    is_vegetarian,
                    no_eggs
                )
                print(f"[get_todays_meal_plan] Used safe vegetarian fallback")
                
        # Even for non-vegetarian users, ensure we use the recalibration system if consumption has occurred
        elif todays_plan:
            # Check if we have consumption today and need to recalibrate
            today_consumption = await get_today_consumption_records_async(current_user["email"], user_timezone="UTC")
            if today_consumption:
                print(f"[get_todays_meal_plan] User has consumption today - triggering recalibration")
                try:
                    updated_plan = await trigger_meal_plan_recalibration(current_user["email"], profile)
                    if updated_plan:
                        todays_plan = updated_plan
                        print(f"[get_todays_meal_plan] Successfully recalibrated meal plan")
                except Exception as recal_err:
                    print(f"[get_todays_meal_plan] Error in recalibration: {recal_err}")
                    # Continue with existing plan
        
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

        # Clean up any duplicate "Recommended: " prefixes that may have accumulated
        for _meal_key, _meal_text in todays_plan.get("meals", {}).items():
            if _meal_text:
                # Remove multiple "Recommended: " prefixes with safety limits
                max_iterations = 10  # Prevent infinite loops
                iterations = 0
                
                # Remove multiple "Recommended: " prefixes
                while "Recommended: Recommended: " in _meal_text and iterations < max_iterations:
                    _meal_text = _meal_text.replace("Recommended: Recommended: ", "Recommended: ")
                    iterations += 1
                
                # Reset for next loop
                iterations = 0
                
                # Also handle case variations
                while "recommended: recommended: " in _meal_text.lower() and iterations < max_iterations:
                    _meal_text = _meal_text.replace("recommended: recommended: ", "Recommended: ", 1)
                    # Fix the case of the remaining "recommended:"
                    _meal_text = _meal_text.replace("recommended:", "Recommended:", 1)
                    iterations += 1
                
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
        
        # COMPREHENSIVE USER PROFILE ANALYSIS for truly personalized meal planning
        print(f"[create_adaptive_meal_plan] COMPREHENSIVE PROFILE ANALYSIS for user: {current_user['email']}")
        
        # Helper function to get profile value with fallbacks
        def get_profile_value(profile, new_key, old_key=None, default='Not provided'):
            value = profile.get(new_key)
            if not value and old_key:
                value = profile.get(old_key)
            if isinstance(value, list) and value:
                return ', '.join(str(v) for v in value)
            elif isinstance(value, list):
                return default
            return str(value) if value else default

        # Extract comprehensive health and lifestyle profile
        medical_conditions = user_profile.get("medicalConditions", []) or user_profile.get("medical_conditions", [])
        current_medications = user_profile.get("currentMedications", [])
        primary_goals = user_profile.get("primaryGoals", [])
        
        # Physical characteristics
        age = user_profile.get("age")
        weight = user_profile.get("weight")
        height = user_profile.get("height")
        bmi = user_profile.get("bmi")
        
        # Vital signs for medical considerations
        systolic_bp = user_profile.get("systolicBP") or user_profile.get("systolic_bp")
        diastolic_bp = user_profile.get("diastolicBP") or user_profile.get("diastolic_bp")
        
        # Activity and lifestyle
        work_activity_level = user_profile.get("workActivityLevel")
        exercise_frequency = user_profile.get("exerciseFrequency") 
        exercise_types = user_profile.get("exerciseTypes", [])
        wants_weight_loss = user_profile.get("wantsWeightLoss") or user_profile.get("weight_loss_goal")
        
        # Dietary preferences
        dietary_restrictions = user_profile.get("dietaryRestrictions", [])
        food_preferences = user_profile.get("foodPreferences", [])
        allergies = user_profile.get("allergies", [])
        calorie_target = user_profile.get("calorieTarget", "2000")
        diet_type = user_profile.get("dietType", [])
        dietary_features = user_profile.get("dietaryFeatures", []) or user_profile.get("diet_features", [])
        strong_dislikes = user_profile.get("strongDislikes", [])
        ethnicity = user_profile.get("ethnicity", [])
        
        # Lab values for medical considerations
        lab_values = user_profile.get("labValues", {})
        
        try:
            target_calories = int(calorie_target)
        except:
            target_calories = int(avg_daily_calories) if avg_daily_calories > 1200 else 2000
        
        # CRITICAL: Enhanced dietary restriction detection for patterns like "Vegetarian (no eggs)"
        # Check multiple possible field names and formats
        all_dietary_info = []
        for field_name in ["dietaryRestrictions", "dietary_restrictions", "dietaryFeatures", "dietary_features", 
                          "dietType", "diet_type", "restrictions", "diet_preferences"]:
            field_value = user_profile.get(field_name, [])
            if isinstance(field_value, list):
                all_dietary_info.extend([str(item).lower() for item in field_value])
            elif isinstance(field_value, str) and field_value:
                all_dietary_info.append(field_value.lower())
        
        print(f"[create_adaptive_meal_plan] All dietary info collected: {all_dietary_info}")
        
        # Enhanced vegetarian detection
        is_vegetarian = any(
            'vegetarian' in info or 'veg' in info or 'plant-based' in info 
            for info in all_dietary_info
        )
        
        # Enhanced egg restriction detection - specifically handle "vegetarian (no eggs)" pattern - check both singular and plural
        no_eggs = any(
            'no egg' in info or 'egg-free' in info or 'no eggs' in info or 'avoid egg' in info or 'avoid eggs' in info or
            ('vegetarian' in info and '(no egg' in info) or ('vegetarian' in info and 'no egg' in info) or
            ('vegetarian' in info and '(no eggs' in info) or ('vegetarian' in info and 'no eggs' in info)
            for info in all_dietary_info
        ) or any(
            'egg' in str(allergy).lower() for allergy in allergies
        )
        
        print(f"[create_adaptive_meal_plan] DIETARY RESTRICTION ANALYSIS:")
        print(f"[create_adaptive_meal_plan] Is vegetarian: {is_vegetarian}")
        print(f"[create_adaptive_meal_plan] No eggs: {no_eggs}")
        
        print(f"[create_adaptive_meal_plan] COMPREHENSIVE PROFILE ANALYSIS:")
        print(f"[create_adaptive_meal_plan] Medical conditions: {medical_conditions}")
        print(f"[create_adaptive_meal_plan] Current medications: {current_medications}")  
        print(f"[create_adaptive_meal_plan] Primary health goals: {primary_goals}")
        print(f"[create_adaptive_meal_plan] Age: {age}, Weight: {weight}kg, Height: {height}cm, BMI: {bmi}")
        print(f"[create_adaptive_meal_plan] BP: {systolic_bp}/{diastolic_bp}, Wants weight loss: {wants_weight_loss}")
        print(f"[create_adaptive_meal_plan] Activity: {work_activity_level}, Exercise: {exercise_frequency}")
        print(f"[create_adaptive_meal_plan] Dietary features: {dietary_features}")
        print(f"[create_adaptive_meal_plan] All dietary info found: {all_dietary_info}")
        print(f"[create_adaptive_meal_plan] Is vegetarian: {is_vegetarian}, No eggs: {no_eggs}")
        print(f"[create_adaptive_meal_plan] Lab values: {lab_values}")
        
        # Use requested cuisine type or fall back to profile preferences
        cuisine_preference = req_cuisine if req_cuisine else ', '.join(diet_type) if diet_type else 'Mixed international'
        
        # Create dynamic meal plan structure for the prompt - WITHOUT Day X: prefixes
        # since the weekly breakdown view already shows days separately
        day_examples = []
        for day_num in range(1, req_days + 1):
            day_examples.append(f'"[specific meal with portions for day {day_num}]"')
        
        day_examples_str = ", ".join(day_examples)
        
        # Create comprehensive medical profile summary for AI
        comprehensive_profile_summary = f"""
COMPREHENSIVE HEALTH PROFILE ANALYSIS:

CONSUMPTION PATTERN ANALYSIS:
- Total recent meals logged: {total_recent_meals}
- Diabetes adherence rate: {adherence_rate:.1f}%
- Average daily calories: {avg_daily_calories:.0f}
- Target daily calories: {target_calories}
- Favorite foods from history: {', '.join(favorite_foods_list[:5]) if favorite_foods_list else 'None identified'}

PATIENT DEMOGRAPHICS:
- Name: {get_profile_value(user_profile, 'name')}
- Age: {age or 'Not specified'}
- Gender: {get_profile_value(user_profile, 'gender')}
- Ethnicity: {get_profile_value(user_profile, 'ethnicity', default='Not specified')}

VITAL SIGNS & MEASUREMENTS:
- Height: {height or 'Not specified'} cm
- Weight: {weight or 'Not specified'} kg
- BMI: {bmi or 'Not calculated'}
- Blood Pressure: {systolic_bp or 'Not specified'}/{diastolic_bp or 'Not specified'} mmHg

MEDICAL CONDITIONS & MEDICATIONS:
- Medical Conditions: {', '.join(medical_conditions) if medical_conditions else 'None specified'}
- Current Medications: {', '.join(current_medications) if current_medications else 'None specified'}
- Lab Values: {lab_values if lab_values else 'Not provided'}

HEALTH GOALS & TARGETS:
- Primary Health Goals: {', '.join(primary_goals) if primary_goals else 'General wellness'}
- Weight Loss Goal: {'Yes' if wants_weight_loss else 'No'}
- Calorie Target: {target_calories} kcal/day

DIETARY INFORMATION:
- PREFERRED CUISINE TYPE: {', '.join(diet_type) if diet_type else 'Mixed international'} (CRITICALLY IMPORTANT - MUST FOLLOW)
- Dietary Features: {', '.join(dietary_features) if dietary_features else 'None specified'}
- Dietary Restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}
- Food Preferences: {', '.join(food_preferences) if food_preferences else 'None'}
- Food Allergies: {', '.join(allergies) if allergies else 'None'}
- Strong Dislikes: {', '.join(strong_dislikes) if strong_dislikes else 'None'}
- Ethnicity: {', '.join(ethnicity) if ethnicity else 'Not specified'}

PHYSICAL ACTIVITY & LIFESTYLE:
- Work Activity Level: {work_activity_level or 'Not specified'}
- Exercise Frequency: {exercise_frequency or 'Not specified'}
- Exercise Types: {', '.join(exercise_types) if exercise_types else 'Not specified'}
        """

        # Create comprehensive adaptive meal plan prompt
        prompt = f"""Create a medically-appropriate, personalized {req_days}-day meal plan based on this comprehensive health profile:

{comprehensive_profile_summary}

CRITICAL MEDICAL & DIETARY REQUIREMENTS:
1. **MEDICAL CONDITIONS**: Address ALL medical conditions listed above - especially diabetes management, blood pressure control, cholesterol management
2. **MEDICATION CONSIDERATIONS**: Consider how meals interact with medications (timing, absorption, blood sugar impacts)
3. **TARGET CALORIES**: Create meal plan with {target_calories} calories per day appropriate for their goals
4. **HEALTH GOALS**: Directly address their primary health goals: {', '.join(primary_goals) if primary_goals else 'general wellness'}
5. **CUISINE PREFERENCE**: STRICTLY follow the cuisine type: {', '.join(diet_type) if diet_type else 'Mixed international'}
6. **DIETARY RESTRICTIONS**: ABSOLUTELY respect all dietary restrictions and allergies - NO EXCEPTIONS
7. {'**Vegetarian Required**: Exclude meat, poultry, fish, and seafood from all meals' if is_vegetarian else ''}
8. {'**Egg-Free Required**: Avoid eggs and egg-containing dishes' if no_eggs else ''}
9. {'**Vegetarian + Egg-Free**: This person requires both meat-free and egg-free options' if is_vegetarian and no_eggs else ''}
9. **DIETARY FEATURES**: Incorporate dietary features like {', '.join(dietary_features) if dietary_features else 'standard nutrition'}
10. **ACTIVITY LEVEL**: Consider their {exercise_frequency or 'moderate'} activity level for meal timing and portions
11. **WEIGHT MANAGEMENT**: {'Include weight loss considerations' if wants_weight_loss else 'Focus on maintenance'}
12. **BLOOD PRESSURE**: {'Consider low-sodium options due to blood pressure readings' if systolic_bp and str(systolic_bp).isdigit() and int(systolic_bp) > 130 else ''}
13. **FAVORITE FOODS**: Incorporate user's favorite foods where medically appropriate and cuisine-consistent
14. **PERSONALIZATION**: Adapt based on their eating patterns and {adherence_rate:.0f}% diabetes adherence rate

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

        print(f"[create_adaptive_meal_plan] SENDING COMPREHENSIVE HEALTH PROFILE TO AI:")
        print(f"[create_adaptive_meal_plan] ✅ Medical conditions: {medical_conditions}")
        print(f"[create_adaptive_meal_plan] ✅ Medications: {current_medications}")
        print(f"[create_adaptive_meal_plan] ✅ Health goals: {primary_goals}")
        print(f"[create_adaptive_meal_plan] ✅ Physical stats: Age={age}, Weight={weight}kg, BMI={bmi}, BP={systolic_bp}/{diastolic_bp}")
        print(f"[create_adaptive_meal_plan] ✅ Activity: Work={work_activity_level}, Exercise={exercise_frequency}")
        print(f"[create_adaptive_meal_plan] ✅ Diet preferences: {diet_type}, Features: {dietary_features}")
        print(f"[create_adaptive_meal_plan] ✅ Restrictions: {dietary_restrictions}, Allergies: {allergies}")
        print(f"[create_adaptive_meal_plan] ✅ Consumption analysis: {total_recent_meals} meals, {adherence_rate:.1f}% diabetes-friendly")
        print(f"[create_adaptive_meal_plan] ✅ Target calories: {target_calories} (from {calorie_target})")
        print(f"[create_adaptive_meal_plan] ✅ Lab values: {lab_values}")
        print(f"[create_adaptive_meal_plan] Profile summary length: {len(comprehensive_profile_summary)} chars")
        
        try:
            response = get_openai_client().chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a medical nutrition specialist with expertise in {', '.join(diet_type) if diet_type else 'international'} cuisine. Create meal plans that are: 1) **Medically appropriate** for their conditions and medications, 2) **Goal-focused** on {', '.join(primary_goals) if primary_goals else 'general wellness'}, 3) **Culturally authentic** with traditional {', '.join(diet_type) if diet_type else 'international'} dishes, 4) **Dietary compliant** with all restrictions and allergies, 5) **Personalized** to their preferences. {'**Vegetarian Required**: Exclude all meat, poultry, fish, and seafood. Include plant-based proteins, dairy (if allowed), and eggs (if allowed). ' if is_vegetarian else ''}{'**Egg-Free Required**: Avoid eggs and egg-containing dishes like omelets, quiche, french toast, carbonara, and mayonnaise-based items. ' if no_eggs else ''}{'**Note**: This person needs both vegetarian AND egg-free meals. ' if is_vegetarian and no_eggs else ''}Medical considerations: {', '.join(medical_conditions) if medical_conditions else 'diabetes management'}. Provide exactly {req_days} meal names without day prefixes."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=DEFAULT_MAX_TOKENS,
                temperature=DEFAULT_TEMPERATURE
            )
            
            # Parse AI response
            ai_content = response.choices[0].message.content
            # Extract JSON from response
            start_idx = ai_content.find('{')
            end_idx = ai_content.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                json_str = ai_content[start_idx:end_idx]
                meal_plan_data = json.loads(json_str)
                
                # CRITICAL: Enforce dietary restrictions for adaptive meal plan using enhanced detection
                enhanced_dietary_restrictions = dietary_restrictions.copy()
                if is_vegetarian:
                    enhanced_dietary_restrictions.append("vegetarian")
                if no_eggs:
                    enhanced_dietary_restrictions.append("no eggs")
                    
                user_profile_dict = {
                    'dietaryRestrictions': enhanced_dietary_restrictions,
                    'allergies': allergies,
                    'strongDislikes': strong_dislikes,
                    'dietType': diet_type
                }
                meal_plan_data = enforce_dietary_restrictions(meal_plan_data, user_profile_dict)
                
                # Apply additional safety sanitization for vegetarian/egg-free meals
                if is_vegetarian or no_eggs:
                    for meal_type in ['breakfast', 'lunch', 'dinner', 'snacks']:
                        if meal_type in meal_plan_data:
                            if isinstance(meal_plan_data[meal_type], list):
                                meal_plan_data[meal_type] = [
                                    sanitize_vegetarian_meal(meal, is_vegetarian, no_eggs) 
                                    for meal in meal_plan_data[meal_type]
                                ]
                            elif isinstance(meal_plan_data[meal_type], str):
                                meal_plan_data[meal_type] = sanitize_vegetarian_meal(meal_plan_data[meal_type], is_vegetarian, no_eggs)
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
                    breakfast_base = ["Oatmeal with berries", "Greek yogurt with nuts", "Avocado toast"]
                    lunch_base = ["Quinoa salad with vegetables", "Lentil soup", "Chickpea curry"]
                    dinner_base = ["Vegetable stir-fry with tofu", "Bean and vegetable stew", "Roasted vegetable bowl"]
                else:
                    breakfast_base = ["Greek yogurt with berries", "Oatmeal with nuts", "Cottage cheese with vegetables"]
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
            
            # Use the enhanced dietary detection for fallback meals too
            fallback_breakfast, fallback_lunch, fallback_dinner = get_fallback_meals(cuisine_preference, is_vegetarian)
            
            # Comprehensive fallback meal plan - WITHOUT Day X: prefixes
            meal_plan_data = {
                "plan_name": f"Adaptive {cuisine_preference} Plan - {datetime.now().strftime('%Y-%m-%d')}",
                "duration_days": req_days,
                "dailyCalories": target_calories,
                "macronutrients": {"protein": int(target_calories * 0.2 / 4), "carbs": int(target_calories * 0.45 / 4), "fats": int(target_calories * 0.35 / 9)},
                "breakfast": fallback_breakfast,
                "lunch": fallback_lunch,
                "dinner": fallback_dinner,
                "snacks": [
                    "Apple slices with almond butter (1 tbsp)",
                    "Handful of mixed nuts (1 oz)",
                    "Celery sticks with hummus (2 tbsp)",
                    "Greek yogurt (1/2 cup) with cinnamon",
                    "Hard-boiled egg with cucumber slices" if not ('vegetarian' in [r.lower() for r in dietary_restrictions] or any('egg' in a.lower() for a in allergies)) else "Berries (1/2 cup) with cottage cheese",
                    "Berries (1/2 cup) with cottage cheese",
                    "Vegetable sticks with guacamole"
                ][:req_days],
                "adaptations": [
                    f"Medical focus: Addresses {', '.join(medical_conditions) if medical_conditions else 'diabetes management'} with appropriate nutrition",
                    f"Health goals: Targets {', '.join(primary_goals) if primary_goals else 'general wellness'} through meal selection",
                    f"Activity level: Meals adapted for {exercise_frequency or 'moderate'} activity level and {work_activity_level or 'standard'} work demands",
                    f"Medication considerations: {'Meal timing optimized for medication schedules' if current_medications else 'Standard meal timing'}",
                    f"Dietary compliance: {adherence_rate:.0f}% diabetes adherence rate with personalized food choices",
                    f"Weight management: {'Supports weight loss goals' if wants_weight_loss else 'Maintains healthy weight'}",
                    f"Cultural preferences: Authentic {', '.join(diet_type) if diet_type else 'international'} cuisine selections",
                    f"Consumption patterns: Based on analysis of {total_recent_meals} recent meals and favorite foods"
                ],
                "coaching_notes": f"This medically-adaptive plan integrates your complete health profile including medical conditions, medications, health goals, and eating patterns. Your {adherence_rate:.0f}% diabetes adherence rate shows {'excellent' if adherence_rate >= 80 else 'good' if adherence_rate >= 60 else 'room for improvement'} progress. The plan addresses your specific health goals: {', '.join(primary_goals) if primary_goals else 'general wellness'}."
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
        user_timezone = current_user.get("profile", {}).get("timezone", "UTC")
        today_consumption = filter_today_records(consumption_data, user_timezone=user_timezone)
        
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

# Test create-sample-data endpoint moved to routers/test_endpoints.py

# Remaining test endpoints also moved to routers/test_endpoints.py
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

# AI Coach meal-suggestion endpoint moved to routers/ai_coach_comprehensive.py
# Function body moved to routers/ai_coach_comprehensive.py
# Complete function implementation moved to routers/ai_coach_comprehensive.py

# All AI Coach functionality moved to routers/ai_coach_comprehensive.py:
# - Main endpoint: /coach/meal-suggestion
# - Helper functions: get_ai_suggestion, log_meal_suggestion, build_meal_suggestion_prompt, analyze_meal_patterns

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
            user_timezone = user_profile.get("timezone", "UTC")
            today_consumption = filter_today_records(recent_consumption, user_timezone=user_timezone)
            
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
            # Get user's timezone for analytics
            user_timezone = current_user.get("profile", {}).get("timezone", "UTC")
            weekly_analytics = await get_consumption_analytics(current_user["email"], 7, user_timezone)
            monthly_analytics = await get_consumption_analytics(current_user["email"], 30, user_timezone)
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
        consistency_streak = calculate_consistency_streak(recent_consumption, user_profile.get("timezone", "UTC"))
        
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
        response = get_openai_client().chat.completions.create(
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

# Consumption fix-meal-types endpoint moved to routers/consumption_management.py

# Privacy data export functions moved to routers/privacy_data.py

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
