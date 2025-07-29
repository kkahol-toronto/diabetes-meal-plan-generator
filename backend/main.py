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
from routers.consumption_coaching_system import router as consumption_coaching_router
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

# Include consumption & coaching system router
app.include_router(consumption_coaching_router, tags=["consumption", "coaching"])

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
app.include_router(export_router, tags=["export"])
app.include_router(chat_router, tags=["chat"])
app.include_router(user_profile_router, tags=["user"])
app.include_router(consumption_analysis_router, tags=["consumption_analysis"])

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
        response = get_openai_client().chat.completions.create(
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

# Debug timezone endpoint moved to routers/utility.py

@app.post("/debug/cleanup-meal-plans")
async def cleanup_meal_plans(current_user: User = Depends(get_current_user)):
    """Clean up meal plans with duplicated text and regenerate fresh ones"""
    try:
        user_email = current_user["email"]
        print(f"[CLEANUP] Starting meal plan cleanup for user: {user_email}")
        
        # Delete all existing meal plans for this user
        from database import delete_all_user_meal_plans
        await delete_all_user_meal_plans(user_email)
        print(f"[CLEANUP] Deleted all existing meal plans for user: {user_email}")
        
        # Generate a fresh meal plan
        profile = current_user.get("profile", {})
        
        # Get today's consumption
        today_consumption = await get_today_consumption_records_async(user_email, profile.get("timezone", "UTC"))
        calories_consumed = sum(r.get("nutritional_info", {}).get("calories", 0) for r in today_consumption)
        target_calories = int(profile.get('calorieTarget', '2000'))
        remaining_calories = max(0, target_calories - calories_consumed)
        
        # Get dietary restrictions
        dietary_restrictions = profile.get('dietaryRestrictions', [])
        allergies = profile.get('allergies', [])
        diet_type = profile.get('dietType', [])
        
        # Check if user is vegetarian or has restrictions
        is_vegetarian = 'vegetarian' in [r.lower() for r in dietary_restrictions] or 'vegetarian' in [d.lower() for d in diet_type]
        no_eggs = any('egg' in r.lower() for r in dietary_restrictions) or any('egg' in a.lower() for a in allergies)
        
        # Generate fresh adaptive meal plan
        fresh_plan = await generate_fresh_adaptive_meal_plan(
            user_email,
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
            from database import save_meal_plan
            await save_meal_plan(user_email, fresh_plan)
            print(f"[CLEANUP] Generated and saved fresh meal plan for user: {user_email}")
            
            return {
                "success": True,
                "message": "Meal plans cleaned and fresh plan generated",
                "plan_id": fresh_plan.get("id"),
                "meals": fresh_plan.get("meals", {})
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to generate fresh meal plan")
            
    except Exception as e:
        print(f"[CLEANUP] Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

# Consumption & Coaching System endpoints moved to routers/consumption_coaching_system.py
# (17 endpoints including: /consumption/history, /consumption/analytics, /consumption/progress, 
#  /coach/daily-insights, /coach/nutrition-score-breakdown, /coach/quick-log, 
#  /coach/todays-meal-plan, /coach/adaptive-meal-plan, /coach/consumption-insights, 
#  /coach/notifications, /coach/meal-suggestion, /consumption/fix-meal-types, and others)


# Privacy data export functions moved to routers/privacy_data.py

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
