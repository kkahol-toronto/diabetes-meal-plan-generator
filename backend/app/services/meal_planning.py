import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pytz

from app.services.openai_service import robust_openai_call, robust_json_parse, generate_fallback_meal_plan
from models import UserProfile
from database import (
    get_user_consumption_history, 
    get_consumption_analytics,
    get_user_meal_plans,
    save_meal_plan
)

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
        import pytz
        from datetime import datetime, time
        
        # Get the user's timezone
        user_tz = pytz.timezone(user_timezone)
        
        # Get current time in user's timezone
        utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
        user_now = utc_now.astimezone(user_tz)
        
        # Get start of today in user's timezone (midnight)
        start_of_today_user = user_now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get start of tomorrow in user's timezone
        start_of_tomorrow_user = start_of_today_user + timedelta(days=1)
        
        # Convert to UTC for database queries
        start_of_today_utc = start_of_today_user.astimezone(pytz.utc).replace(tzinfo=None)
        start_of_tomorrow_utc = start_of_tomorrow_user.astimezone(pytz.utc).replace(tzinfo=None)
        
        print(f"[TIMEZONE] User timezone: {user_timezone}")
        print(f"[TIMEZONE] User local time: {user_now}")
        print(f"[TIMEZONE] Start of today (user timezone): {start_of_today_user}")
        print(f"[TIMEZONE] Start of today (UTC): {start_of_today_utc}")
        print(f"[TIMEZONE] Start of tomorrow (UTC): {start_of_tomorrow_utc}")
        
        return start_of_today_utc, start_of_tomorrow_utc
        
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
    
    print(f"[FILTER_DEBUG] Filtering {len(records)} records for timezone: {user_timezone}")
    print(f"[FILTER_DEBUG] Start of today (UTC): {start_of_today_utc}")
    print(f"[FILTER_DEBUG] Start of tomorrow (UTC): {start_of_tomorrow_utc}")
    
    today_records = []
    for i, record in enumerate(records):
        try:
            timestamp_str = record.get("timestamp", "")
            if not timestamp_str:
                continue
                
            # Parse the timestamp
            record_timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            
            # Remove timezone info for comparison (already in UTC)
            record_timestamp_utc = record_timestamp.replace(tzinfo=None)
            
            # Check if the record is from today
            is_today = start_of_today_utc <= record_timestamp_utc < start_of_tomorrow_utc
            
            # Debug print for first few records
            if i < 5:  # Only print first 5 records to avoid spam
                food_name = record.get("food_name", "Unknown")
                print(f"[FILTER_DEBUG] Record {i}: {food_name} at {record_timestamp_utc} - Included: {is_today}")
            
            if is_today:
                today_records.append(record)
                
        except Exception as e:
            print(f"Error parsing timestamp for record: {e}")
            continue
    
    print(f"[FILTER_DEBUG] Filtered to {len(today_records)} records for today")
    return today_records

def get_remaining_meals_by_time(current_hour: int) -> List[str]:
    """
    Determine which meals are still needed today based on current time.
    """
    remaining_meals = []
    
    if current_hour < 11:  # Before 11 AM - breakfast and all other meals
        remaining_meals = ["breakfast", "lunch", "dinner", "snack"]
    elif current_hour < 15:  # 11 AM - 3 PM - lunch and dinner
        remaining_meals = ["lunch", "dinner", "snack"]
    elif current_hour < 19:  # 3 PM - 7 PM - dinner and snack
        remaining_meals = ["dinner", "snack"]
    elif current_hour < 22:  # 7 PM - 10 PM - just snack
        remaining_meals = ["snack"]
    else:  # After 10 PM - no more meals recommended
        remaining_meals = []
    
    return remaining_meals

async def analyze_consumption_vs_plan(consumption_records: list, meal_plan: dict) -> dict:
    """
    Analyze user's consumption against their meal plan to identify adherence and deviations.
    """
    try:
        print(f"[analyze_consumption_vs_plan] Analyzing {len(consumption_records)} consumption records against meal plan")
        
        # Extract meal plan targets
        target_calories = meal_plan.get("dailyCalories", 2000)
        
        # Calculate actual consumption
        total_calories_consumed = sum(r.get("nutritional_info", {}).get("calories", 0) for r in consumption_records)
        
        # Group consumption by meal type
        meals_consumed = {}
        for record in consumption_records:
            meal_type = record.get("meal_type", "snack")
            if meal_type not in meals_consumed:
                meals_consumed[meal_type] = []
            meals_consumed[meal_type].append(record)
        
        # Calculate adherence by meal type
        adherence_by_meal = {}
        for meal_type in ["breakfast", "lunch", "dinner", "snack"]:
            if meal_type in meals_consumed:
                meal_calories = sum(r.get("nutritional_info", {}).get("calories", 0) for r in meals_consumed[meal_type])
                target_meal_calories = target_calories / 4  # Simple division for now
                adherence_percentage = min(100, (meal_calories / target_meal_calories) * 100) if target_meal_calories > 0 else 0
                adherence_by_meal[meal_type] = {
                    "consumed": True,
                    "calories": meal_calories,
                    "target_calories": target_meal_calories,
                    "adherence_percentage": adherence_percentage
                }
            else:
                adherence_by_meal[meal_type] = {
                    "consumed": False,
                    "calories": 0,
                    "target_calories": target_calories / 4,
                    "adherence_percentage": 0
                }
        
        analysis = {
            "total_calories_consumed": total_calories_consumed,
            "total_calories_planned": target_calories,
            "calorie_adherence_percentage": min(100, (total_calories_consumed / target_calories) * 100) if target_calories > 0 else 0,
            "meals_consumed": meals_consumed,
            "adherence_by_meal": adherence_by_meal,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        
        print(f"[analyze_consumption_vs_plan] Analysis complete - {total_calories_consumed}/{target_calories} calories consumed")
        return analysis
        
    except Exception as e:
        print(f"[analyze_consumption_vs_plan] Error: {e}")
        return {
            "total_calories_consumed": 0,
            "total_calories_planned": 2000,
            "calorie_adherence_percentage": 0,
            "meals_consumed": {},
            "adherence_by_meal": {},
            "error": str(e)
        }

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
                
                # Check if meal already has "Recommended: " prefix to avoid duplication
                def add_recommended_prefix(meal_text: str, prefix: str) -> str:
                    if not meal_text:
                        return prefix
                    # If meal already starts with "Recommended: ", don't add it again
                    if meal_text.lower().startswith("recommended:"):
                        return meal_text
                    return f"{prefix} {meal_text}"
                
                # Adjust recommendation based on remaining calories
                if remaining_calories < 200:
                    if meal_type == "snack":
                        consumption_aware_plan["meals"][meal_type] = "Recommended: No additional snacks needed - you've reached your daily calorie goal"
                    else:
                        consumption_aware_plan["meals"][meal_type] = add_recommended_prefix(original_meal, "Recommended: Light") if original_meal else "Recommended: Light, low-calorie option"
                elif remaining_calories < 300:
                    if meal_type == "snack":
                        consumption_aware_plan["meals"][meal_type] = "Recommended: Optional small piece of fruit or vegetables if genuinely hungry"
                    else:
                        consumption_aware_plan["meals"][meal_type] = add_recommended_prefix(original_meal, "Recommended:") if original_meal else "Recommended: Balanced, moderate portion"
                else:
                    # Normal recommendation
                    consumption_aware_plan["meals"][meal_type] = add_recommended_prefix(original_meal, "Recommended:") if original_meal else f"Recommended: Healthy {meal_type} option"
                    
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

async def trigger_meal_plan_recalibration(user_email: str, user_profile: dict):
    """
    Comprehensive meal plan recalibration system that triggers after every food log.
    Ensures dietary restrictions are respected and meal plan is updated immediately.
    """
    try:
        print(f"[RECALIBRATION] Starting meal plan recalibration for user {user_email}")
        
        # Get today's consumption including the new log
        user_timezone = user_profile.get("timezone", "UTC")
        today_consumption = await get_today_consumption_records_async(user_email, user_timezone=user_timezone)
        
        # Calculate calories consumed so far
        calories_consumed = sum(r.get("nutritional_info", {}).get("calories", 0) for r in today_consumption)
        
        # Handle empty or invalid calorie target
        calorie_target = user_profile.get('calorieTarget', '2000')
        if not calorie_target or calorie_target == '':
            calorie_target = '2000'
        target_calories = int(calorie_target)
        remaining_calories = max(0, target_calories - calories_consumed)
        
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

def generate_meal_plan_prompt(user_profile: UserProfile) -> str:
    """
    Generate a comprehensive prompt for meal plan creation based on user profile.
    """
    # Extract key profile information
    name = user_profile.name or "User"
    age = user_profile.age or 45
    gender = user_profile.gender or "not specified"
    medical_conditions = user_profile.medicalConditions or user_profile.medical_conditions or []
    current_medications = user_profile.currentMedications or []
    allergies = user_profile.allergies or []
    dietary_restrictions = user_profile.dietaryRestrictions or []
    diet_type = user_profile.dietType or []
    calorie_target = user_profile.calorieTarget or "2000"
    
    # Build the prompt
    prompt = f"""You are a registered dietitian AI creating a personalized meal plan for a patient with diabetes.

PATIENT PROFILE:
- Age: {age}
- Gender: {gender}
- Medical Conditions: {', '.join(medical_conditions) if medical_conditions else 'Type 2 Diabetes'}
- Current Medications: {', '.join(current_medications) if current_medications else 'None specified'}
- Food Allergies: {', '.join(allergies) if allergies else 'None'}
- Dietary Restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}
- Diet Type Preferences: {', '.join(diet_type) if diet_type else 'Mixed'}
- Daily Calorie Target: {calorie_target}

REQUIREMENTS:
1. ALL meals must be diabetes-friendly (low glycemic index, balanced macronutrients)
2. Respect ALL dietary restrictions and allergies
3. Include portion sizes and approximate calories per meal
4. Provide variety across different days
5. Focus on whole foods, lean proteins, and complex carbohydrates
6. Limit refined sugars and processed foods

Please create a balanced meal plan with breakfast, lunch, dinner, and one snack option.

Return the response as JSON in this exact format:
{{
  "meals": {{
    "breakfast": "Detailed breakfast description with portion sizes",
    "lunch": "Detailed lunch description with portion sizes", 
    "dinner": "Detailed dinner description with portion sizes",
    "snack": "Healthy snack option with portion size"
  }},
  "dailyCalories": {calorie_target},
  "macronutrients": {{
    "protein": 100,
    "carbs": 200,
    "fats": 65
  }},
  "notes": "Additional dietary guidance and tips"
}}"""

    return prompt 