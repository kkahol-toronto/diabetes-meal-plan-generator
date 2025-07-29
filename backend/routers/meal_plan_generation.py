from fastapi import APIRouter, HTTPException, Depends, status, Request, Body, File, UploadFile, Form
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse, Response
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
import os
import json
import random
import re
import asyncio
from datetime import datetime, timedelta
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
from routers.auth import get_current_user
from services.openai_service import robust_openai_call, get_openai_client
from services.consumption_analysis import (
    sanitize_vegetarian_meal,
    generate_safe_vegetarian_fallback
)
from database import (
    get_user_by_email,
    save_meal_plan, get_user_meal_plans, get_meal_plan_by_id,
    save_shopping_list, get_user_shopping_lists,
    save_recipes, get_user_recipes,
    user_container
)
import traceback
import sys
import uuid
from io import BytesIO
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# ============================================================================
# FALLBACK MEAL PLAN AND RECIPE GENERATION FUNCTIONS
# ============================================================================

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
    breakfast_options = BREAKFAST_OPTIONS.copy()
    
    # Safe lunch options
    lunch_options = LUNCH_OPTIONS.copy()
    
    # Safe dinner options
    dinner_options = DINNER_OPTIONS.copy()
    
    # Safe snack options
    snack_options = SNACK_OPTIONS.copy()
    
    # Adjust for non-vegetarian users
    if not is_vegetarian:
        lunch_options.extend(NON_VEG_LUNCH_ADDITIONS)
        dinner_options.extend(NON_VEG_DINNER_ADDITIONS)
    
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
    recipe_templates = RECIPE_TEMPLATES
    
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

# ============================================================================
# DIETARY RESTRICTIONS ENFORCEMENT
# ============================================================================

def enforce_dietary_restrictions(meal_plan_data: dict, user_profile: dict) -> dict:
    """
    Comprehensive dietary restriction enforcement function.
    Ensures all meals strictly adhere to user's dietary restrictions, allergies, and preferences.
    """
    print("[enforce_dietary_restrictions] Starting dietary compliance check...")
    
    # Extract user dietary information from ALL possible fields
    dietary_restrictions = user_profile.get('dietaryRestrictions', [])
    dietary_features = user_profile.get('dietaryFeatures', [])  # CRITICAL: Include dietaryFeatures
    food_allergies = user_profile.get('allergies', [])
    strong_dislikes = user_profile.get('strongDislikes', [])
    diet_type = user_profile.get('dietType', [])
    
    # Convert to lowercase for case-insensitive matching
    restrictions_lower = [r.lower() for r in dietary_restrictions]
    features_lower = [f.lower() for f in dietary_features]  # CRITICAL: Include dietary features
    allergies_lower = [a.lower() for a in food_allergies]
    dislikes_lower = [d.lower() for d in strong_dislikes]
    diet_type_lower = [dt.lower() for dt in diet_type]
    
    # Combine all dietary restrictions into one comprehensive list
    all_restrictions = restrictions_lower + features_lower + diet_type_lower
    
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
    
    # Add dietary restriction-related banned ingredients - check ALL restriction sources
    for restriction in all_restrictions:
        if 'vegetarian' in restriction:
            # COMPREHENSIVE meat and poultry ban for vegetarians
            banned_ingredients.update(['chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'turkey', 'lamb', 'meat', 'seafood', 'shrimp', 'bacon', 'ham', 'duck', 'goose', 'veal', 'venison', 'rabbit', 'sausage', 'pepperoni', 'salami', 'prosciutto', 'chorizo', 'ground beef', 'ground turkey', 'chicken breast', 'chicken thigh', 'steak', 'roast beef', 'pork chop', 'fish fillet', 'crab', 'lobster', 'scallops', 'mussels', 'clams', 'oysters', 'cod', 'tilapia', 'halibut', 'sardines', 'anchovies', 'mackerel'])
            # CRITICAL: Handle "vegetarian (no eggs)" pattern specifically - check for both singular and plural
            if 'no egg' in restriction or '(no egg' in restriction or 'no eggs' in restriction or '(no eggs' in restriction:
                banned_ingredients.update(['eggs', 'egg', 'omelet', 'omelette', 'scrambled', 'poached', 'fried egg', 'boiled egg', 'hard-boiled', 'soft-boiled', 'egg white', 'egg yolk', 'egg sandwich', 'french toast', 'quiche', 'frittata', 'carbonara', 'mayonnaise', 'mayo', 'hollandaise', 'custard', 'meringue'])
                print(f"[enforce_dietary_restrictions] VEGETARIAN (NO EGGS) detected: {restriction}")
        elif 'vegan' in restriction:
            banned_ingredients.update(['chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'turkey', 'lamb', 'meat', 'seafood', 'shrimp', 'bacon', 'ham', 'duck', 'goose', 'veal', 'venison'])
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
        elif 'egg-free' in restriction or 'no egg' in restriction or 'no eggs' in restriction:
            banned_ingredients.update(['eggs', 'egg', 'omelet', 'omelette', 'scrambled', 'poached', 'fried egg', 'boiled egg', 'hard-boiled', 'soft-boiled', 'egg white', 'egg yolk', 'egg sandwich', 'french toast', 'quiche', 'frittata', 'carbonara', 'mayonnaise', 'mayo', 'hollandaise', 'custard', 'meringue'])
            print(f"[enforce_dietary_restrictions] EGG-FREE detected: {restriction}")
    
    # Add strong dislikes
    banned_ingredients.update(dislikes_lower)
    
    # Additional diet type enforcement (already handled above in all_restrictions loop)
    # This section kept for backward compatibility but functionality moved to comprehensive loop above
    
    print(f"[enforce_dietary_restrictions] Banned ingredients: {banned_ingredients}")
    
    def sanitize_meal(meal: str) -> str:
        """Sanitize a meal to remove banned ingredients"""
        meal_lower = meal.lower()
        
        # Check for banned ingredients
        for banned in banned_ingredients:
            if banned in meal_lower:
                print(f"[enforce_dietary_restrictions] Found banned ingredient '{banned}' in meal '{meal}' - replacing")
                
                # Get appropriate replacement based on diet type
                if 'vegetarian' in all_restrictions:
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
                        return "Greek yogurt with berries"
        
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

# ============================================================================
# MAIN MEAL PLAN GENERATION ENDPOINT
# ============================================================================

@router.post("/generate-meal-plan")
async def generate_meal_plan(
    request: Request,
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
        user_doc["profile"]["calorieTarget"] = user_profile.get("calorieTarget", DEFAULT_CALORIE_TARGET)
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
                return set(re.findall(r"\w+", meal.lower()))

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

        # Define a robust JSON structure based on selected days - SAFE VEGETARIAN OPTIONS
        example_meals = {
            "breakfast": ["Oatmeal with berries", "Whole grain toast with avocado", "Greek yogurt with granola", "Quinoa breakfast bowl", "Smoothie bowl", "Avocado toast", "Chia pudding with fruit"],
            "lunch": ["Quinoa and vegetable salad", "Quinoa bowl with beans", "Vegetable wrap", "Vegetable soup", "Pasta with marinara", "Hummus and vegetable wrap", "Buddha bowl"],
            "dinner": ["Lentil curry with vegetables", "Vegetable stir-fry with tofu", "Bean and vegetable stew", "Vegetable curry", "Quinoa with roasted vegetables", "Chickpea curry", "Roasted vegetables with grains"],
            "snacks": ["Apple with almonds", "Plant-based yogurt", "Carrot sticks with hummus", "Mixed nuts", "Fruit and nut bars", "Berries with seeds", "Green smoothie"]
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

🚨 ABSOLUTE PRIORITY: DIETARY RESTRICTIONS MUST BE FOLLOWED WITHOUT EXCEPTION 🚨

CRITICAL INSTRUCTIONS:
1. DIETARY COMPLIANCE (TOP PRIORITY): Absolutely MUST follow ALL dietary restrictions, features, and allergies listed above. If patient has "Vegetarian (no eggs)" selected, completely exclude ALL eggs, omelets, quiche, french toast, mayonnaise, and all egg-containing dishes.
2. MEDICAL SAFETY: Carefully consider all medical conditions, medications, and lab values. Ensure meals are appropriate for diabetes management and any other health conditions.
3. DIET TYPE ADHERENCE: **CRITICALLY IMPORTANT** - Follow the specified Diet Type exactly, but ALWAYS respect dietary restrictions above all else:
   - If "Western" or "European": Include traditional European/Western dishes modified for dietary restrictions:
     * BREAKFAST: Oatmeal with berries, avocado toast, quinoa breakfast bowl, smoothie bowls, chia pudding (modify based on restrictions)
     * LUNCH: Vegetable sandwiches, salads with appropriate proteins, quinoa bowls, vegetable soups (adapt proteins to dietary needs)
     * DINNER: Pasta with marinara, vegetable stir-fries, grain bowls, lentil dishes (choose proteins based on dietary requirements)
     * SNACKS: Fresh fruit, nuts, hummus with vegetables, yogurt (select based on dietary restrictions)
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
                        "content": "You are a medical nutrition specialist creating meal plans for diabetic patients. CRITICAL PRIORITY ORDER: 1) DIETARY RESTRICTIONS AND ALLERGIES (absolutely no exceptions) 2) Medical conditions (diabetes-friendly foods) 3) Cultural cuisine preferences. If a user has 'Vegetarian (no eggs)' or any egg restrictions, you MUST completely avoid eggs, omelets, french toast, quiche, mayonnaise, and all egg-containing dishes. For vegetarians, exclude all meat, poultry, fish, and seafood. Only after ensuring complete dietary compliance, then incorporate authentic cultural dishes from their preferred cuisine type. Always respond with valid JSON matching the exact structure requested. No explanations or markdown."
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
                
                # EXTRA SAFETY CHECK: Additional vegetarian/egg-free enforcement
                dietary_features = user_profile.get('dietaryFeatures', [])
                dietary_restrictions = user_profile.get('dietaryRestrictions', [])
                allergies = user_profile.get('allergies', [])
                
                print(f"[generate-meal-plan] POST-GENERATION DIETARY CHECK:")
                print(f"  Dietary Features: {dietary_features}")
                print(f"  Dietary Restrictions: {dietary_restrictions}")
                print(f"  Allergies: {allergies}")
                
                # Check if user has vegetarian (no eggs) restriction
                has_egg_restriction = any('vegetarian (no eggs)' in str(feature).lower() or 
                                        'vegetarian (no egg)' in str(feature).lower() or
                                        'no eggs' in str(feature).lower() or 
                                        'no egg' in str(feature).lower() or
                                        'egg-free' in str(feature).lower() 
                                        for feature in dietary_features + dietary_restrictions + allergies)
                
                print(f"[generate-meal-plan] Has egg restriction detected: {has_egg_restriction}")
                
                # CRITICAL: Final validation - scan generated meals for egg ingredients
                if has_egg_restriction:
                    print("⚠️ WARNING: User has egg restrictions. Validating meal plan...")
                    egg_containing_meals = []
                    for meal_type in ['breakfast', 'lunch', 'dinner', 'snacks']:
                        meals = meal_plan.get(meal_type, [])
                        for i, meal in enumerate(meals):
                            meal_name = meal.get('name', '').lower() if isinstance(meal, dict) else str(meal).lower()
                            # Also check ingredients if available
                            ingredients = []
                            if isinstance(meal, dict) and 'ingredients' in meal:
                                ingredients = [str(ing).lower() for ing in meal.get('ingredients', [])]
                            
                            egg_words = ['egg', 'omelet', 'omelette', 'french toast', 'quiche', 'frittata', 'scrambled', 'mayonnaise', 'mayo']
                            meal_has_eggs = any(egg_word in meal_name for egg_word in egg_words)
                            ingredients_have_eggs = any(any(egg_word in ing for egg_word in egg_words) for ing in ingredients)
                            
                            if meal_has_eggs or ingredients_have_eggs:
                                egg_containing_meals.append(f"{meal_type}[{i}]: {meal_name} (ingredients: {ingredients[:3]})")
                    
                    if egg_containing_meals:
                        print(f"🚨 CRITICAL ERROR: Found egg-containing meals despite restrictions:")
                        for meal in egg_containing_meals:
                            print(f"  - {meal}")
                        # Note: In a production system, you might want to regenerate here
                    else:
                        print("✅ Meal plan validated - no egg-containing meals found")
                
                is_vegetarian = any('vegetarian' in str(feature).lower() for feature in dietary_features + dietary_restrictions)
                
                if has_egg_restriction or is_vegetarian:
                    print(f"[EXTRA SAFETY] Applying additional vegetarian/egg-free enforcement: vegetarian={is_vegetarian}, no_eggs={has_egg_restriction}")
                    for meal_type in ['breakfast', 'lunch', 'dinner', 'snacks']:
                        if meal_type in meal_plan and isinstance(meal_plan[meal_type], list):
                            meal_plan[meal_type] = [
                                sanitize_vegetarian_meal(meal, is_vegetarian, has_egg_restriction) 
                                for meal in meal_plan[meal_type]
                            ]
                
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

                # Meal plan generation complete - no automatic save
                # User must explicitly save via the "Save Meal Plan + PDF" button
                print("[/generate-meal-plan] Meal plan generated successfully - ready for user to save")

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
                            meal_plan[key] = {"protein": 100, "carbs": 250, "fats": 70}
                        else:
                            meal_plan[key] = ["Healthy meal option"] * days

                # Ensure arrays have the correct number of items
                for meal_type in ['breakfast', 'lunch', 'dinner', 'snacks']:
                    if not isinstance(meal_plan[meal_type], list):
                        meal_plan[meal_type] = ["Healthy meal option"] * days
                    while len(meal_plan[meal_type]) < days:
                        meal_plan[meal_type].append("Healthy meal option")
                    meal_plan[meal_type] = meal_plan[meal_type][:days]

                # Save the fallback meal plan to the database
                try:
                    saved_meal_plan = await save_meal_plan(current_user["email"], meal_plan)
                    print("[/generate-meal-plan] Fallback meal plan saved to database successfully")
                except Exception as save_error:
                    print(f"[/generate-meal-plan] Failed to save fallback meal plan to database: {save_error}")
                    # Continue anyway - we can still return the generated plan

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

# ============================================================================
# RECIPE GENERATION ENDPOINTS
# ============================================================================

@router.post("/generate-recipes")
async def generate_recipes(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    try:
        data = await request.json()
        meal_plan = data.get('meal_plan', {})
        print("/generate-recipes endpoint called")
        print("Received meal_plan:", meal_plan)
        
        # Extract all meals from the meal plan (including duplicates)
        all_meals = []
        for meal_type in ['breakfast', 'lunch', 'dinner', 'snacks']:
            if meal_type in meal_plan and isinstance(meal_plan[meal_type], list):
                all_meals.extend(meal_plan[meal_type])
        
        # Create unique recipes but track all meal instances
        unique_meals = []
        seen = set()
        meal_instances = {}
        
        for meal in all_meals:
            if meal not in seen:
                unique_meals.append(meal)
                seen.add(meal)
                meal_instances[meal] = 1
            else:
                meal_instances[meal] += 1
        
        print(f"Total meals in plan: {len(all_meals)}")
        print(f"Unique meals to generate recipes for: {unique_meals}")
        print(f"Meal instances: {meal_instances}")
        
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
- Generate recipes for all {len(unique_meals)} unique meals (total meal instances in plan: {len(all_meals)})
- Each recipe must have all required fields
- Ensure nutritional_info values are numbers, not strings
- Make sure to provide complete recipe details for every unique meal"""
        
        print("Prompt for OpenAI:")
        print(prompt)
        
        # Use the robust OpenAI call with better error handling
        api_result = await robust_openai_call(
            messages=[
                {"role": "system", "content": "You are a diabetes diet planning assistant. Generate healthy, diabetes-friendly recipes with accurate nutritional information. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=DEFAULT_TEMPERATURE,
            max_tokens=MEAL_PLAN_MAX_TOKENS,
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

@router.post("/generate-recipe")
async def generate_recipe(
    request: Request,
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

# ============================================================================
# SHOPPING LIST GENERATION FUNCTIONALITY
# ============================================================================

def consolidate_ingredients(recipes: List[dict], user_profile: dict = None) -> List[dict]:
    """
    Consolidate ingredients from multiple recipes, combining quantities for duplicate items.
    Respects dietary restrictions to avoid consolidating restricted ingredients.
    """
    import re
    ingredient_map = {}
    
    # Extract dietary restrictions to respect during consolidation
    dietary_restrictions = []
    if user_profile:
        dietary_features = user_profile.get('dietaryFeatures', [])
        dietary_restrictions_field = user_profile.get('dietaryRestrictions', [])
        allergies = user_profile.get('allergies', [])
        
        # Combine all dietary restriction sources
        all_restrictions = dietary_features + dietary_restrictions_field + allergies
        dietary_restrictions = [str(r).lower() for r in all_restrictions if r]
        
        print(f"[consolidate_ingredients] Dietary restrictions detected: {dietary_restrictions}")
    
    # Check for egg restrictions
    has_egg_restriction = any(
        'vegetarian (no eggs)' in restriction or 'vegetarian (no egg)' in restriction or
        'no eggs' in restriction or 'no egg' in restriction or 'egg-free' in restriction or
        'avoid eggs' in restriction
        for restriction in dietary_restrictions
    )
    
    print(f"[consolidate_ingredients] Has egg restriction: {has_egg_restriction}")
    
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
            # CRITICAL: Build normalization map while respecting dietary restrictions
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
            
            # CRITICAL FIX: Only include egg normalization if user doesn't have egg restrictions
            if not has_egg_restriction:
                normalized_items["eggs"] = ["egg", "eggs", "chicken eggs"]
            else:
                print(f"[consolidate_ingredients] SKIPPING egg normalization due to dietary restriction")
            
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

@router.post("/generate-shopping-list")
async def generate_shopping_list(
    request: Request,
    recipes: List[dict],
    current_user: User = Depends(get_current_user)
):
    try:
        print("/generate-shopping-list endpoint called")
        print("Received recipes:")
        print(recipes)
        
        # Get user profile to respect dietary restrictions during consolidation
        user_profile = current_user.get("profile", {})
        print(f"[generate-shopping-list] User profile dietary info: {user_profile.get('dietaryFeatures', [])}")
        
        # First, consolidate ingredients programmatically while respecting dietary restrictions
        consolidated_ingredients = consolidate_ingredients(recipes, user_profile)
        print("Consolidated ingredients:")
        for item in consolidated_ingredients:
            print(f"  - {item['ingredient']} (from: {', '.join(item['from_recipes'])})")
        
        # CRITICAL: Final dietary restriction check - filter out any restricted ingredients
        dietary_features = user_profile.get('dietaryFeatures', [])
        dietary_restrictions = user_profile.get('dietaryRestrictions', [])
        allergies = user_profile.get('allergies', [])
        all_restrictions = dietary_features + dietary_restrictions + allergies
        
        has_egg_restriction = any(
            'vegetarian (no eggs)' in str(restriction).lower() or 'vegetarian (no egg)' in str(restriction).lower() or
            'no eggs' in str(restriction).lower() or 'no egg' in str(restriction).lower() or 
            'egg-free' in str(restriction).lower() or 'avoid eggs' in str(restriction).lower()
            for restriction in all_restrictions
        )
        
        # Filter out restricted ingredients
        filtered_ingredients = []
        for item in consolidated_ingredients:
            ingredient_name = item["ingredient"].lower()
            should_exclude = False
            
            if has_egg_restriction and ('egg' in ingredient_name):
                print(f"[generate-shopping-list] EXCLUDING egg ingredient due to dietary restriction: {item['ingredient']}")
                should_exclude = True
                
            if not should_exclude:
                filtered_ingredients.append(item)
        
        print(f"[generate-shopping-list] Filtered {len(consolidated_ingredients)} -> {len(filtered_ingredients)} ingredients after dietary restrictions")
        
        # Create a simplified ingredient list for the AI
        ingredient_list = [item["ingredient"] for item in filtered_ingredients]
        
        # Add dietary restriction information to the prompt
        restriction_info = ""
        if has_egg_restriction:
            restriction_info = "CRITICAL: This user has egg restrictions (Vegetarian no eggs). DO NOT include eggs, mayonnaise, or any egg-containing products in the shopping list."
        
        prompt = f"""Generate a shopping list based on the following PRE-CONSOLIDATED ingredients:
                    {json.dumps(ingredient_list, indent=2)}
                    
                    {restriction_info}

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
        raise HTTPException(status_code=500, detail=str(e))