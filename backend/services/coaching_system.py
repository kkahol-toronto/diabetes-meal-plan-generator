"""
Coaching & Analytics System

This module provides comprehensive coaching intelligence and analytics for the diabetes meal planning system.
It includes personalized scoring, progress tracking, consistency analysis, and AI-driven daily insights.

Key Functions:
- get_consumption_progress_data: Progress tracking system
- calculate_consistency_streak: Streak calculations  
- calculate_personalized_weights: Personalized scoring weights
- calculate_score_decay: Score decay algorithms
- get_daily_coaching_insights_data: AI-driven coaching insights
- get_nutrition_score_breakdown_data: Nutrition scoring system
- detect_food_exploitation: Pattern analysis for gaming detection
- quick_log_food_data: Food logging system
- generate_personalized_protein_suggestions: Protein analysis
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import os
import random
import pytz
from services.openai_service import robust_openai_call, get_openai_client
from constants import (
    DEFAULT_CALORIE_TARGET, ANALYSIS_MAX_TOKENS, DEFAULT_TEMPERATURE
)
from utils import filter_today_records
from collections import defaultdict

# Import database functions that will be used
# These will be imported from database when the module is used
# from database import (
#     get_user_by_email, get_user_consumption_history, get_user_meal_plans, 
#     save_consumption_record, get_consumption_analytics
# )


async def get_consumption_progress_data(user_email: str, user_profile: dict) -> dict:
    """
    Returns user's daily calorie/macro goals, today's progress, and weekly/monthly averages.
    Always returns a valid set of goals, using smart defaults if needed.
    """
    # Import here to avoid circular imports
    from database import get_user_by_email, get_user_meal_plans, get_consumption_analytics
    from services.consumption_analysis import get_today_consumption_records_async
    
    # DEBUG: Print timezone information
    user_timezone = user_profile.get("timezone", "UTC")
    print(f"[TIMEZONE_DEBUG] User: {user_email}")
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

    # --- Try to get most recent meal plan for fallback ---
    recent_meal_plan = None
    meal_plans = await get_user_meal_plans(user_email)
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
    if user_profile.get("calorieTarget"):
        calorie_goal = parse_int(user_profile.get("calorieTarget"), smart_defaults["calories"])
    elif user_profile.get("calories_target"):
        calorie_goal = parse_int(user_profile.get("calories_target"), smart_defaults["calories"])
    elif recent_meal_plan and recent_meal_plan.get("dailyCalories"):
        calorie_goal = parse_int(recent_meal_plan.get("dailyCalories"), smart_defaults["calories"])
    else:
        calorie_goal = smart_defaults["calories"]

    # 2. Try to get macro goals from profile, then meal plan, then default
    macro_goals = user_profile.get("macroGoals")
    macro_from_meal_plan = recent_meal_plan.get("macronutrients") if recent_meal_plan else None
    macro_goal = None
    if macro_goals and isinstance(macro_goals, dict) and all(k in macro_goals for k in ["protein", "carbs", "fat"]):
        macro_goal = {
            "protein": parse_int(macro_goals.get("protein"), smart_defaults["macronutrients"]["protein"]),
            "carbs": parse_int(macro_goals.get("carbs"), smart_defaults["macronutrients"]["carbohydrates"]),
            "fat": parse_int(macro_goals.get("fat"), smart_defaults["macronutrients"]["fat"])
        }
    elif macro_from_meal_plan and all(k in macro_from_meal_plan for k in ["protein", "carbs", "fat"]):
        macro_goal = {
            "protein": parse_int(macro_from_meal_plan.get("protein"), smart_defaults["macronutrients"]["protein"]),
            "carbs": parse_int(macro_from_meal_plan.get("carbs"), smart_defaults["macronutrients"]["carbohydrates"]),
            "fat": parse_int(macro_from_meal_plan.get("fat"), smart_defaults["macronutrients"]["fat"])
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
    user_timezone = user_profile.get("timezone", "UTC")
    today_records = await get_today_consumption_records_async(user_email, user_timezone=user_timezone)
    
    today_totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
    for rec in today_records:
        ni = rec.get("nutritional_info", {})
        today_totals["calories"] += ni.get("calories", 0)
        today_totals["protein"] += ni.get("protein", 0)
        today_totals["carbs"] += ni.get("carbohydrates", 0)
        today_totals["fat"] += ni.get("fat", 0)

    # 5. Weekly and monthly averages (reuse analytics logic)
    weekly = await get_consumption_analytics(user_email, days=7, user_timezone=user_timezone)
    monthly = await get_consumption_analytics(user_email, days=30, user_timezone=user_timezone)

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


def calculate_consistency_streak(consumption_history: list, user_timezone: str = "UTC") -> int:
    """Calculate consistency streak based on daily logging patterns"""
    if not consumption_history:
        return 0
    
    from datetime import datetime, timedelta
    import pytz
    
    try:
        # Get user timezone for accurate daily boundaries
        user_tz = pytz.timezone(user_timezone)
    except:
        user_tz = pytz.UTC
    
    # Group consumption by date using user's timezone
    daily_logs = {}
    for record in consumption_history:
        try:
            # Parse timestamp and convert to user timezone
            timestamp_str = record.get("timestamp", "")
            if not timestamp_str:
                continue
                
            record_timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            # Convert to user timezone for accurate date calculation
            record_local = record_timestamp.astimezone(user_tz)
            record_date = record_local.date()
            
            if record_date not in daily_logs:
                daily_logs[record_date] = 0
            daily_logs[record_date] += 1
        except Exception as e:
            print(f"Error processing record timestamp in streak calculation: {e}")
            continue
    
    # Calculate streak from today backwards using user's timezone
    utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
    user_now = utc_now.astimezone(user_tz)
    today = user_now.date()
    
    streak = 0
    current_date = today
    
    # Check each day backwards - count any day with at least 1 meal logged
    for i in range(60):  # Check last 60 days max for longer streaks
        if current_date in daily_logs and daily_logs[current_date] >= 1:  # At least 1 meal logged
            streak += 1
        else:
            # Streak broken - stop counting
            break
        current_date -= timedelta(days=1)
    
    print(f"[STREAK_DEBUG] Calculated streak: {streak} days (timezone: {user_timezone})")
    print(f"[STREAK_DEBUG] Today: {today}, Total logged days: {len(daily_logs)}")
    
    return streak


def calculate_personalized_weights(user_profile: dict) -> dict:
    """
    Calculate personalized penalty weights and reward boosts based on user profile.
    This makes scoring more accurate for different user types and conditions.
    """
    try:
        # Default weights (baseline for healthy adults)
        weights = {
            "carb_penalty_multiplier": 8.0,      # Base carb penalty
            "sugar_penalty_multiplier": 10.0,    # Base sugar penalty
            "processed_penalty_multiplier": 5.0, # Base processed food penalty
            "healthy_bonus_multiplier": 15.0,    # Base healthy choice bonus
            "today_boost_cap": 20.0,             # Max today's boost percentage
            "sensitivity_factor": 1.0            # Overall sensitivity (1.0 = normal)
        }
        
        # Extract user characteristics
        age = user_profile.get("age", 35)
        medical_conditions = user_profile.get("medicalConditions", []) or user_profile.get("medical_conditions", [])
        activity_level = user_profile.get("workActivityLevel", "moderate")
        exercise_frequency = user_profile.get("exerciseFrequency", "2-3 times per week")
        primary_goals = user_profile.get("primaryGoals", [])
        readiness_to_change = user_profile.get("readinessToChange", "somewhat ready")
        
        # Convert to lowercase for easier matching
        medical_conditions_lower = [condition.lower() for condition in medical_conditions]
        
        # 1. AGE-BASED ADJUSTMENTS
        if age and isinstance(age, (int, float)):
            if age >= 65:
                # Older adults: More sensitive to sodium, more forgiving on carbs
                weights["processed_penalty_multiplier"] *= 1.3  # Higher sodium sensitivity
                weights["carb_penalty_multiplier"] *= 0.8       # Less strict on carbs
                weights["healthy_bonus_multiplier"] *= 1.2      # Reward healthy choices more
            elif age <= 25:
                # Younger adults: More resilient, but still encourage good habits
                weights["sensitivity_factor"] *= 0.9
                weights["today_boost_cap"] *= 1.1               # More immediate feedback
        
        # 2. DIABETES STAGE ADJUSTMENTS
        diabetes_severity = "none"
        for condition in medical_conditions_lower:
            if "prediabetes" in condition or "prediabetic" in condition:
                diabetes_severity = "prediabetes"
            elif "type 1 diabetes" in condition:
                diabetes_severity = "type1"
                break
            elif "type 2 diabetes" in condition or "diabetes" in condition:
                diabetes_severity = "type2"
                break
        
        if diabetes_severity == "prediabetes":
            # Prediabetic: Moderate sensitivity, high reward for good choices
            weights["carb_penalty_multiplier"] *= 1.1
            weights["sugar_penalty_multiplier"] *= 1.2
            weights["healthy_bonus_multiplier"] *= 1.3
            weights["today_boost_cap"] *= 1.2
        elif diabetes_severity == "type1":
            # Type 1: Focus on consistency, less penalty-based
            weights["carb_penalty_multiplier"] *= 0.9  # Less harsh on carbs (they can manage with insulin)
            weights["sugar_penalty_multiplier"] *= 1.1 # Still avoid sugar spikes
            weights["healthy_bonus_multiplier"] *= 1.1 # Moderate rewards
        elif diabetes_severity == "type2":
            # Type 2: Higher sensitivity to carbs and processed foods
            weights["carb_penalty_multiplier"] *= 1.3
            weights["sugar_penalty_multiplier"] *= 1.4
            weights["processed_penalty_multiplier"] *= 1.2
            weights["healthy_bonus_multiplier"] *= 1.4
        
        # 3. PHYSICAL ACTIVITY LEVEL ADJUSTMENTS
        if activity_level:
            activity_lower = activity_level.lower()
            if "sedentary" in activity_lower or "low" in activity_lower:
                # Sedentary: More strict on everything
                weights["sensitivity_factor"] *= 1.2
                weights["carb_penalty_multiplier"] *= 1.1
            elif "very active" in activity_lower or "high" in activity_lower:
                # Very active: More forgiving, higher calorie needs
                weights["sensitivity_factor"] *= 0.8
                weights["carb_penalty_multiplier"] *= 0.7  # Can handle more carbs
        
        # Exercise frequency adjustments
        if exercise_frequency:
            exercise_lower = exercise_frequency.lower()
            if "daily" in exercise_lower or "5" in exercise_lower:
                # Regular exercisers: More forgiving
                weights["carb_penalty_multiplier"] *= 0.8
                weights["healthy_bonus_multiplier"] *= 1.1
            elif "rarely" in exercise_lower or "never" in exercise_lower:
                # Sedentary: More strict
                weights["carb_penalty_multiplier"] *= 1.2
        
        # 4. HEALTH GOALS ADJUSTMENTS
        goals_lower = [goal.lower() for goal in primary_goals]
        
        if any("weight loss" in goal or "lose weight" in goal for goal in goals_lower):
            # Weight loss goals: More strict on processed foods and calories
            weights["processed_penalty_multiplier"] *= 1.2
            weights["healthy_bonus_multiplier"] *= 1.3
        
        if any("manage diabetes" in goal or "blood sugar" in goal for goal in goals_lower):
            # Diabetes management focus: Higher carb/sugar sensitivity
            weights["carb_penalty_multiplier"] *= 1.2
            weights["sugar_penalty_multiplier"] *= 1.3
        
        # 5. READINESS TO CHANGE ADJUSTMENTS
        if readiness_to_change:
            readiness_lower = readiness_to_change.lower()
            if "very ready" in readiness_lower or "highly motivated" in readiness_lower:
                # High motivation: More sensitive feedback
                weights["today_boost_cap"] *= 1.3
                weights["healthy_bonus_multiplier"] *= 1.2
            elif "not ready" in readiness_lower or "resistant" in readiness_lower:
                # Low motivation: Gentler approach
                weights["carb_penalty_multiplier"] *= 0.8
                weights["sugar_penalty_multiplier"] *= 0.9
                weights["today_boost_cap"] *= 1.4  # More immediate positive feedback
        
        # 6. MULTIPLE CONDITIONS ADJUSTMENTS
        if len(medical_conditions) >= 3:
            # Multiple health conditions: More sensitive overall
            weights["sensitivity_factor"] *= 1.1
            weights["healthy_bonus_multiplier"] *= 1.2  # Reward good choices more
        
        # Ensure weights stay within reasonable bounds
        for key, value in weights.items():
            if "multiplier" in key or key == "today_boost_cap":
                weights[key] = max(2.0, min(25.0, value))  # Keep between 2x and 25x
            elif key == "sensitivity_factor":
                weights[key] = max(0.5, min(2.0, value))   # Keep between 0.5x and 2.0x
        
        # Debug logging
        print(f"[PERSONALIZED_WEIGHTS] User profile analysis:")
        print(f"  - Age: {age}")
        print(f"  - Diabetes severity: {diabetes_severity}")
        print(f"  - Activity level: {activity_level}")
        print(f"  - Exercise frequency: {exercise_frequency}")
        print(f"  - Primary goals: {primary_goals}")
        print(f"  - Readiness to change: {readiness_to_change}")
        print(f"[PERSONALIZED_WEIGHTS] Calculated weights: {weights}")
        
        return weights
        
    except Exception as e:
        print(f"[PERSONALIZED_WEIGHTS] Error calculating weights: {e}")
        # Return default weights on error
        return {
            "carb_penalty_multiplier": 8.0,
            "sugar_penalty_multiplier": 10.0,
            "processed_penalty_multiplier": 5.0,
            "healthy_bonus_multiplier": 15.0,
            "today_boost_cap": 20.0,
            "sensitivity_factor": 1.0
        }


def calculate_score_decay(user_email: str, recent_consumption: list, user_timezone: str = "UTC") -> float:
    """
    Calculate gradual score decay if user hasn't logged healthy meals recently.
    Encourages consistency without harsh punishment.
    """
    try:
        from datetime import datetime, timedelta
        
        # Check last 3 days for healthy meal logging
        three_days_ago = datetime.utcnow() - timedelta(days=3)
        recent_healthy_count = 0
        total_recent_meals = 0
        
        for record in recent_consumption:
            try:
                record_time = datetime.fromisoformat(record.get("timestamp", "").replace("Z", "+00:00"))
                if record_time >= three_days_ago:
                    total_recent_meals += 1
                    medical_rating = record.get("medical_rating", {})
                    diabetes_suitability = medical_rating.get("diabetes_suitability", "medium").lower()
                    
                    if diabetes_suitability == "high":
                        recent_healthy_count += 1
                    elif diabetes_suitability == "medium":
                        recent_healthy_count += 0.5
            except:
                continue
        
        # Calculate decay factor
        if total_recent_meals == 0:
            # No meals logged in 3 days: gradual decay
            decay_factor = 2.0  # 2% decay per day
        else:
            healthy_ratio = recent_healthy_count / total_recent_meals
            if healthy_ratio < 0.3:  # Less than 30% healthy meals
                decay_factor = 1.0  # 1% decay per day
            else:
                decay_factor = 0.0  # No decay if maintaining healthy habits
        
        print(f"[SCORE_DECAY] Recent meals: {total_recent_meals}, healthy: {recent_healthy_count:.1f}, decay: {decay_factor}%/day")
        return decay_factor
        
    except Exception as e:
        print(f"[SCORE_DECAY] Error calculating decay: {e}")
        return 0.0  # No decay on error


# More functions will be added here for Part 2 and Part 3


async def get_daily_coaching_insights_data(user_email: str, user_profile: dict) -> dict:
    """Get daily insights - USING ORIGINAL LOGIC with better integration"""
    try:
        # Import here to avoid circular imports
        from database import get_user_meal_plans, get_user_consumption_history
        
        print(f"[get_daily_insights] Getting insights for user {user_email}")
        
        # DEBUG: Print timezone information
        user_timezone = user_profile.get("timezone", "UTC")
        print(f"[TIMEZONE_DEBUG] User: {user_email}")
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
        
        # Get recent meal plans
        try:
            recent_meal_plans = await get_user_meal_plans(user_email)
            recent_meal_plans = recent_meal_plans[:3]
        except Exception as e:
            print(f"Error fetching meal plans for coaching insights: {e}")
            recent_meal_plans = []
        
        # Get recent consumption history (last 7 days) - USING ORIGINAL FUNCTION
        try:
            recent_consumption = await get_user_consumption_history(user_email, limit=30)
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
        user_timezone = user_profile.get("timezone", "UTC")
        today_consumption = filter_today_records(recent_consumption, user_timezone=user_timezone)
        
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
        
        if user_profile.get("calorieTarget"):
            try:
                calorie_goal = int(user_profile["calorieTarget"])
            except:
                pass
        elif recent_meal_plans and recent_meal_plans[0].get("dailyCalories"):
            calorie_goal = recent_meal_plans[0]["dailyCalories"]
        
        if user_profile.get("macroGoals"):
            macro_goals.update(user_profile["macroGoals"])
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
        user_conditions = user_profile.get("medicalConditions", []) or user_profile.get("medical_conditions", [])
        
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
        
        # FIXED: Calculate today's separate score for immediate feedback
        today_suitable_count = 0
        today_records_count = len(today_consumption)
        
        for record in today_consumption:
            medical_rating = record.get("medical_rating", {})
            diabetes_suitability = medical_rating.get("diabetes_suitability", "medium").lower()
            
            if diabetes_suitability == "high":
                today_suitable_count += 1
            elif diabetes_suitability == "medium":
                today_suitable_count += 0.7
        
        # ENHANCED: Use personalized weights based on user profile
        personalized_weights = calculate_personalized_weights(user_profile)
        
        # Calculate score decay for consistency encouragement
        score_decay = calculate_score_decay(user_email, recent_consumption, user_timezone)
        
        # Calculate enhanced diabetes score with personalized weighting
        if total_recent_records > 0:
            base_score = (condition_suitable_count / total_recent_records * 100)
            
            # Apply personalized penalties and bonuses
            carb_penalty = (diabetes_score_factors["high_carb_meals"] / total_recent_records) * personalized_weights["carb_penalty_multiplier"]
            sugar_penalty = (diabetes_score_factors["high_sugar_meals"] / total_recent_records) * personalized_weights["sugar_penalty_multiplier"]
            processed_penalty = (diabetes_score_factors["processed_foods"] / total_recent_records) * personalized_weights["processed_penalty_multiplier"]
            healthy_bonus = (diabetes_score_factors["healthy_choices"] / total_recent_records) * personalized_weights["healthy_bonus_multiplier"]
            
            # Apply personalized today's boost for immediate feedback
            today_boost = 0
            if today_records_count > 0:
                today_score = (today_suitable_count / today_records_count) * 100
                # If today's meals are healthy (>60%), give a personalized boost
                if today_score > 60:
                    max_boost = personalized_weights["today_boost_cap"]
                    today_boost = min(max_boost, (today_score - 60) * 0.5)
            
            # Apply score decay for consistency
            consistency_penalty = score_decay
            
            # Calculate final score with all personalized factors
            raw_score = base_score - carb_penalty - sugar_penalty - processed_penalty + healthy_bonus + today_boost - consistency_penalty
            health_adherence = max(0, min(100, raw_score * personalized_weights["sensitivity_factor"]))
            
            # Enhanced debug logging for score calculation
            print(f"[DEBUG] Personalized Nutrition Score Calculation:")
            print(f"[DEBUG] - Base score: {base_score:.1f}%")
            print(f"[DEBUG] - Carb penalty: -{carb_penalty:.1f}% (weight: {personalized_weights['carb_penalty_multiplier']:.1f})")
            print(f"[DEBUG] - Sugar penalty: -{sugar_penalty:.1f}% (weight: {personalized_weights['sugar_penalty_multiplier']:.1f})") 
            print(f"[DEBUG] - Processed penalty: -{processed_penalty:.1f}% (weight: {personalized_weights['processed_penalty_multiplier']:.1f})")
            print(f"[DEBUG] - Healthy bonus: +{healthy_bonus:.1f}% (weight: {personalized_weights['healthy_bonus_multiplier']:.1f})")
            print(f"[DEBUG] - Today's boost: +{today_boost:.1f}% (max: {personalized_weights['today_boost_cap']:.1f}%)")
            print(f"[DEBUG] - Consistency penalty: -{consistency_penalty:.1f}%")
            print(f"[DEBUG] - Sensitivity factor: {personalized_weights['sensitivity_factor']:.2f}x")
            print(f"[DEBUG] - Final health adherence: {health_adherence:.1f}%")
            print(f"[DEBUG] - Today's meals: {today_records_count}, suitable: {today_suitable_count}")
            
        elif today_records_count > 0:
            # NEW: For new users, base score entirely on today's meals for immediate feedback
            today_score = (today_suitable_count / today_records_count) * 100
            health_adherence = max(0, min(100, today_score))
            print(f"[DEBUG] New user nutrition score based on today only: {health_adherence:.1f}%")
            
        else:
            # Default score for users with no data
            health_adherence = 0
            print(f"[DEBUG] No consumption data - nutrition score: 0%")
        
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
                "message": "Great job staying within your calorie goal! Your portion control is on track.",
                "action": "maintain"
            })
        
        # Macro recommendations with better thresholds
        # Protein
        if adherence["protein"] < 70:
            protein_needed = macro_goals["protein"] - today_totals["protein"]
            print(f"[RECOMMENDATIONS] Getting protein suggestions for user with profile: {user_profile.get('dietaryRestrictions', [])}")
            protein_suggestions = generate_personalized_protein_suggestions(user_profile)
            print(f"[RECOMMENDATIONS] Generated protein suggestions: {protein_suggestions}")
            recommendations.append({
                "type": "protein_low",
                "priority": "high",
                "message": f"You need {protein_needed:.0f}g more protein today. Try adding {protein_suggestions}.",
                "action": "increase_protein"
            })
        elif adherence["protein"] > 130:
            recommendations.append({
                "type": "protein_high",
                "priority": "low",
                "message": "You've exceeded your protein goal. This is generally fine, but balance with other nutrients.",
                "action": "balance_macros"
            })
        
        # Carbohydrates - diabetes-specific advice
        if adherence["carbohydrates"] > 120:
            recommendations.append({
                "type": "carb_high",
                "priority": "high",
                "message": "Your carb intake is high today. For diabetes management, consider choosing lower-carb options for remaining meals.",
                "action": "reduce_carbs"
            })
        elif adherence["carbohydrates"] < 50:
            recommendations.append({
                "type": "carb_low",
                "priority": "medium",
                "message": "Your carb intake is quite low. Include some healthy carbs like vegetables, fruits, or whole grains.",
                "action": "add_healthy_carbs"
            })
        
        # Fat recommendations
        if adherence["fat"] > 140:
            recommendations.append({
                "type": "fat_high", 
                "priority": "medium",
                "message": "Fat intake is high today. Choose leaner proteins and cooking methods for remaining meals.",
                "action": "reduce_fat"
            })
        elif adherence["fat"] < 60:
            recommendations.append({
                "type": "fat_low",
                "priority": "low",
                "message": "Consider adding healthy fats like avocado, nuts, or olive oil to support nutrient absorption.",
                "action": "add_healthy_fats"
            })
        
        # Health adherence recommendations with condition-specific advice
        if health_adherence < 60:
            primary_condition = user_conditions[0] if user_conditions else "your health condition"
            recommendations.append({
                "type": "health_low",
                "priority": "high",
                "message": f"Your food choices today aren't optimal for {primary_condition}. Consider diabetes-friendly alternatives for your next meals.",
                "action": "improve_choices"
            })
        elif health_adherence >= 80:
            recommendations.append({
                "type": "health_excellent",
                "priority": "low", 
                "message": f"Excellent! Your food choices are very suitable for managing {user_conditions[0] if user_conditions else 'your health'}.",
                "action": "keep_it_up"
            })
        
        # Consistency recommendations
        streak = calculate_consistency_streak(recent_consumption, user_timezone)
        if streak >= 7:
            recommendations.append({
                "type": "consistency_excellent",
                "priority": "low",
                "message": f"Amazing! You've logged meals for {streak} days straight. Your consistency is helping your health management.",
                "action": "maintain_streak"
            })
        elif streak < 3:
            recommendations.append({
                "type": "consistency_low",
                "priority": "medium",
                "message": "Try to log meals more consistently. Regular tracking helps optimize your health management.",
                "action": "improve_consistency"
            })
        
        # Sort recommendations by priority (high -> medium -> low)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        # Limit to top 5 recommendations to avoid overwhelming
        recommendations = recommendations[:5]
        
        # Build comprehensive insights response
        insights = {
            "date": today_utc.isoformat(),
            "user_timezone": user_timezone,
            "today_totals": today_totals,
            "goals": {
                "calories": calorie_goal,
                "protein": macro_goals["protein"],
                "carbohydrates": macro_goals["carbohydrates"], 
                "fat": macro_goals["fat"]
            },
            "adherence": adherence,
            "diabetes_adherence": health_adherence,  # Now represents overall health adherence
            "health_adherence": health_adherence,  # Add explicit health adherence field
            "health_conditions": user_conditions,  # Add user's health conditions
            "consistency_streak": calculate_consistency_streak(recent_consumption, user_timezone),
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
            ],
            # Add detailed score breakdown for UI transparency
            "score_breakdown": {
                "base_score": base_score if 'base_score' in locals() else 0,
                "carb_penalty": carb_penalty if 'carb_penalty' in locals() else 0,
                "sugar_penalty": sugar_penalty if 'sugar_penalty' in locals() else 0,
                "processed_penalty": processed_penalty if 'processed_penalty' in locals() else 0,
                "healthy_bonus": healthy_bonus if 'healthy_bonus' in locals() else 0,
                "today_boost": today_boost if 'today_boost' in locals() else 0,
                "consistency_penalty": consistency_penalty if 'consistency_penalty' in locals() else 0,
                "sensitivity_factor": personalized_weights["sensitivity_factor"] if 'personalized_weights' in locals() else 1.0,
                "personalized_weights": personalized_weights if 'personalized_weights' in locals() else {},
                "calculation_method": "personalized" if 'personalized_weights' in locals() else "standard"
            }
        }
        
        print(f"[get_daily_insights] Generated insights successfully")
        
        return insights
        
    except Exception as e:
        print(f"[get_daily_insights] Error: {str(e)}")
        import traceback
        print(f"[get_daily_insights] Traceback: {traceback.format_exc()}")
        raise Exception(f"Failed to get daily insights: {str(e)}")


# More functions will be added here for Part 3


async def get_nutrition_score_breakdown_data(user_email: str, user_profile: dict) -> dict:
    """
    Get detailed nutrition score breakdown for UI transparency.
    Shows users exactly how their score was calculated.
    """
    try:
        # Get the daily insights which contains the score breakdown
        insights = await get_daily_coaching_insights_data(user_email, user_profile)
        score_breakdown = insights.get("score_breakdown", {})
        
        # Add additional explanation for UI
        breakdown_with_explanations = {
            "current_score": insights.get("diabetes_adherence", 0),
            "breakdown": {
                "base_score": {
                    "value": score_breakdown.get("base_score", 0),
                    "explanation": "Based on the diabetes-suitability of your recent meals",
                    "icon": "📊"
                },
                "today_boost": {
                    "value": score_breakdown.get("today_boost", 0),
                    "explanation": "Bonus for healthy choices made today",
                    "icon": "⚡",
                    "is_positive": True
                },
                "healthy_bonus": {
                    "value": score_breakdown.get("healthy_bonus", 0),
                    "explanation": "Reward for high-fiber, low-glycemic food choices",
                    "icon": "🥬",
                    "is_positive": True
                },
                "carb_penalty": {
                    "value": -score_breakdown.get("carb_penalty", 0),
                    "explanation": "Reduction for high-carb meals (>45g carbs)",
                    "icon": "🍞",
                    "is_positive": False
                },
                "sugar_penalty": {
                    "value": -score_breakdown.get("sugar_penalty", 0),
                    "explanation": "Reduction for high-sugar meals (>15g sugar)",
                    "icon": "🍭",
                    "is_positive": False
                },
                "processed_penalty": {
                    "value": -score_breakdown.get("processed_penalty", 0),
                    "explanation": "Reduction for high-sodium processed foods (>800mg)",
                    "icon": "🥫",
                    "is_positive": False
                },
                "consistency_penalty": {
                    "value": -score_breakdown.get("consistency_penalty", 0),
                    "explanation": "Small reduction for inconsistent healthy logging",
                    "icon": "📅",
                    "is_positive": False
                }
            },
            "personalization": {
                "is_personalized": score_breakdown.get("calculation_method") == "personalized",
                "sensitivity_factor": score_breakdown.get("sensitivity_factor", 1.0),
                "explanation": "Your score is personalized based on your age, health conditions, activity level, and goals"
            },
            "tips": []
        }
        
        # Generate actionable tips based on the breakdown
        if score_breakdown.get("carb_penalty", 0) > 5:
            breakdown_with_explanations["tips"].append({
                "type": "carbs",
                "message": "Try choosing lower-carb alternatives like cauliflower rice or zucchini noodles",
                "icon": "💡"
            })
        
        if score_breakdown.get("sugar_penalty", 0) > 5:
            breakdown_with_explanations["tips"].append({
                "type": "sugar",
                "message": "Opt for naturally sweet foods like berries instead of processed desserts",
                "icon": "🫐"
            })
        
        if score_breakdown.get("processed_penalty", 0) > 3:
            breakdown_with_explanations["tips"].append({
                "type": "processed",
                "message": "Choose fresh, whole foods and cook at home when possible",
                "icon": "🍳"
            })
        
        if score_breakdown.get("today_boost", 0) > 10:
            breakdown_with_explanations["tips"].append({
                "type": "positive",
                "message": "Great job with today's healthy choices! Keep up the excellent work!",
                "icon": "🌟"
            })
        elif score_breakdown.get("today_boost", 0) == 0:
            breakdown_with_explanations["tips"].append({
                "type": "encouragement",
                "message": "Log some healthy meals today to boost your score!",
                "icon": "🎯"
            })
        
        return breakdown_with_explanations
        
    except Exception as e:
        print(f"[nutrition_score_breakdown] Error: {str(e)}")
        import traceback
        print(f"[nutrition_score_breakdown] Traceback: {traceback.format_exc()}")
        raise Exception(f"Failed to get score breakdown: {str(e)}")


def detect_food_exploitation(user_email: str, today_consumption: list, new_food_name: str) -> dict:
    """
    Detect if user is trying to exploit the scoring system by logging the same food repeatedly.
    Returns exploitation status and adjusted scoring.
    """
    try:
        from collections import Counter
        from datetime import datetime, timedelta
        
        # Count food occurrences today
        food_counts = Counter()
        for record in today_consumption:
            food_name = record.get("food_name", "").lower().strip()
            food_counts[food_name] += 1
        
        # Add the new food being logged
        new_food_lower = new_food_name.lower().strip()
        food_counts[new_food_lower] += 1
        
        exploitation_detected = False
        score_adjustment = 0
        warnings = []
        
        # Check for repetitive logging
        for food, count in food_counts.items():
            if count > 3:  # Same food more than 3 times in one day
                exploitation_detected = True
                excess_logs = count - 3
                score_adjustment -= (excess_logs * 2)  # 2% penalty per excess log
                warnings.append(f"'{food}' logged {count} times today (max recommended: 3)")
            elif count == 3:
                warnings.append(f"'{food}' logged 3 times today - consider adding variety")
        
        # Check for suspicious patterns (only "healthy" foods logged)
        healthy_foods = ["spinach", "broccoli", "kale", "lettuce", "cucumber", "celery"]
        if len(food_counts) >= 5 and all(any(healthy in food for healthy in healthy_foods) for food in food_counts.keys()):
            exploitation_detected = True
            score_adjustment -= 5  # 5% penalty for unrealistic all-healthy pattern
            warnings.append("Diet seems unrealistically limited to only healthy foods - add variety")
        
        # Check for meal variety (encourage diverse nutrition)
        if len(food_counts) == 1 and list(food_counts.values())[0] > 2:
            warnings.append("Try adding variety to your meals for better nutrition coverage")
        
        return {
            "exploitation_detected": exploitation_detected,
            "score_adjustment": score_adjustment,
            "warnings": warnings,
            "food_counts": dict(food_counts),
            "variety_score": len(food_counts),  # Higher is better
            "recommendation": "Add more variety to your meals" if len(food_counts) < 3 else "Good meal variety!"
        }
        
    except Exception as e:
        print(f"[FOOD_EXPLOITATION] Error: {e}")
        return {
            "exploitation_detected": False,
            "score_adjustment": 0,
            "warnings": [],
            "food_counts": {},
            "variety_score": 1,
            "recommendation": "Continue logging diverse meals"
        }


async def quick_log_food_data(food_data: dict, user_email: str, user_profile: dict) -> dict:
    """Quick log food - USING ORIGINAL SAVE FUNCTION with better AI analysis"""
    try:
        # Import here to avoid circular imports
        from database import save_consumption_record
        from services.consumption_analysis import trigger_meal_plan_recalibration, get_today_consumption_records_async
        
        print(f"[quick_log_food] Starting quick log for user {user_email}")
        print(f"[quick_log_food] Food data received: {food_data}")
        
        food_name = food_data.get("food_name", "").strip()
        portion = food_data.get("portion", "medium portion").strip()
        
        if not food_name:
            raise Exception("Food name is required")
        
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
        print(f"[quick_log_food] Saving consumption record for user {user_email}")
        
        # Get user timezone for proper meal type determination
        user_timezone = "UTC"  # Default fallback
        try:
            from database import get_user_by_email
            user_doc = await get_user_by_email(user_email)
            if user_doc and "profile" in user_doc:
                user_timezone = user_doc["profile"].get("timezone", "UTC")
        except Exception as e:
            print(f"[coaching_system] Could not get user timezone: {e}")
        
        consumption_record = await save_consumption_record(user_email, consumption_data, meal_type=meal_type, user_timezone=user_timezone)
        print(f"[quick_log_food] Successfully saved consumption record with ID: {consumption_record['id']}")
        
        # ------------------
        # TRIGGER MEAL PLAN RECALIBRATION AFTER FOOD LOG
        # ------------------
        try:
            print(f"[quick_log_food] Triggering meal plan recalibration for user {user_email}")
            updated_meal_plan = await trigger_meal_plan_recalibration(user_email, user_profile)
            meal_plan_updated = updated_meal_plan is not None
            print(f"[quick_log_food] Meal plan recalibration {'succeeded' if meal_plan_updated else 'failed'}")
        except Exception as recal_error:
            print(f"[quick_log_food] Meal plan recalibration failed: {str(recal_error)}")
            meal_plan_updated = False
        
        # Return comprehensive response
        return {
            "success": True,
            "message": "Food logged successfully and meal plan updated!",
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
            "meal_plan_updated": meal_plan_updated,
            "calibration_applied": meal_plan_updated,
            "note": "Food logged successfully and meal plan recalibrated!" if meal_plan_updated else "Food logged successfully!"
        }
        
    except Exception as e:
        print(f"[quick_log_food] Unexpected error: {str(e)}")
        import traceback
        print(f"[quick_log_food] Full error details:", traceback.format_exc())
        raise Exception(f"Failed to log food item: {str(e)}")


def generate_personalized_protein_suggestions(user_profile: dict) -> str:
    """
    Generate personalized protein suggestions based on user's dietary restrictions and preferences.
    CRITICAL: Must respect vegetarian and egg-free requirements.
    """
    try:
        print(f"[PROTEIN_SUGGESTIONS] Analyzing user profile: {user_profile}")
        
        # Get dietary restrictions and preferences
        dietary_restrictions = user_profile.get('dietaryRestrictions', [])
        dietary_features = user_profile.get('dietaryFeatures', []) or user_profile.get('diet_features', [])
        allergies = user_profile.get('allergies', [])
        diet_type = user_profile.get('dietType', [])
        
        # Combine all dietary info for comprehensive checking
        all_dietary_info = []
        for field in [dietary_restrictions, dietary_features, diet_type]:
            if isinstance(field, list):
                all_dietary_info.extend([str(item).lower() for item in field])
            elif isinstance(field, str) and field:
                all_dietary_info.append(field.lower())
        
        allergies_lower = [str(allergy).lower() for allergy in allergies]
        
        print(f"[PROTEIN_SUGGESTIONS] All dietary info: {all_dietary_info}")
        print(f"[PROTEIN_SUGGESTIONS] Allergies: {allergies_lower}")
        
        # ENHANCED VEGETARIAN DETECTION - Handle "Vegetarian (No Eggs)" pattern
        is_vegetarian = any(
            'vegetarian' in info or 'veg' in info or 'plant-based' in info 
            for info in all_dietary_info
        )
        
        is_vegan = any('vegan' in info for info in all_dietary_info)
        
        # ENHANCED EGG DETECTION - Handle multiple patterns
        no_eggs = (
            any('no egg' in info or 'egg-free' in info or 'no eggs' in info or '(no egg' in info or '(no eggs' in info for info in all_dietary_info) or 
            any('egg' in allergy for allergy in allergies_lower) or
            # Special handling for "Vegetarian (No Eggs)" pattern
            any('vegetarian' in info and '(no egg' in info for info in all_dietary_info)
        )
        
        no_dairy = (any('dairy-free' in info or 'no dairy' in info for info in all_dietary_info) or 
                    any('dairy' in allergy or 'milk' in allergy for allergy in allergies_lower))
        no_nuts = any('nut' in allergy for allergy in allergies_lower)
        no_soy = any('soy' in allergy for allergy in allergies_lower)  # FIX: Define no_soy variable
        
        print(f"[PROTEIN_SUGGESTIONS] Dietary analysis:")
        print(f"[PROTEIN_SUGGESTIONS]   - Vegetarian: {is_vegetarian}")
        print(f"[PROTEIN_SUGGESTIONS]   - Vegan: {is_vegan}")
        print(f"[PROTEIN_SUGGESTIONS]   - No eggs: {no_eggs}")
        print(f"[PROTEIN_SUGGESTIONS]   - No dairy: {no_dairy}")
        print(f"[PROTEIN_SUGGESTIONS]   - No nuts: {no_nuts}")
        print(f"[PROTEIN_SUGGESTIONS]   - No soy: {no_soy}")
        
        # Build protein suggestions based on restrictions
        protein_options = []
        
        if is_vegan:
            # Vegan protein sources - NO animal products
            print("[PROTEIN_SUGGESTIONS] User is VEGAN - providing plant-based options only")
            if not no_soy:
                protein_options.extend(["tofu", "tempeh"])
            if not no_nuts:
                protein_options.extend(["almond butter", "hemp seeds", "chia seeds"])
            protein_options.extend(["lentils", "chickpeas", "quinoa", "black beans", "nutritional yeast"])
            
        elif is_vegetarian:
            # Vegetarian protein sources - NO meat, fish, or poultry
            print("[PROTEIN_SUGGESTIONS] User is VEGETARIAN - providing plant-based options only")
            
            # CRITICAL: Never suggest eggs if user has "no eggs" restriction
            if not no_eggs:
                protein_options.append("eggs")
                print("[PROTEIN_SUGGESTIONS] Added eggs (allowed)")
            else:
                print("[PROTEIN_SUGGESTIONS] SKIPPED eggs (user has no-egg restriction)")
            
            if not no_dairy:
                protein_options.extend(["Greek yogurt", "cottage cheese", "paneer"])
            if not no_soy:
                protein_options.extend(["tofu", "tempeh"])
            if not no_nuts:
                protein_options.extend(["almond butter", "hemp seeds"])
            protein_options.extend(["lentils", "chickpeas", "quinoa", "black beans"])
            
        else:
            # Non-vegetarian protein sources - Include meat and fish
            print("[PROTEIN_SUGGESTIONS] User is NON-VEGETARIAN - including meat and fish")
            protein_options.extend(["lean meats like chicken or turkey", "fish like salmon or tuna"])
            if not no_eggs:
                protein_options.append("eggs")
            if not no_dairy:
                protein_options.extend(["Greek yogurt", "cottage cheese"])
            if not no_soy:
                protein_options.append("tofu")
            if not no_nuts:
                protein_options.extend(["nuts", "almond butter"])
            protein_options.extend(["lentils", "chickpeas", "quinoa"])
        
        print(f"[PROTEIN_SUGGESTIONS] Final protein options: {protein_options}")
        
        # Create a natural language suggestion
        if len(protein_options) == 0:
            result = "plant-based protein sources like beans and quinoa"
        elif len(protein_options) == 1:
            result = protein_options[0]
        elif len(protein_options) == 2:
            result = f"{protein_options[0]} or {protein_options[1]}"
        else:
            # Take top 3-4 options for readability
            top_options = protein_options[:3]
            if len(top_options) > 2:
                result = f"{', '.join(top_options[:-1])}, or {top_options[-1]}"
            elif len(top_options) == 2:
                result = f"{top_options[0]} or {top_options[1]}"
            else:
                result = top_options[0] if top_options else "beans and quinoa"
        
        print(f"[PROTEIN_SUGGESTIONS] Final suggestion: {result}")
        return result
            
    except Exception as e:
        print(f"[generate_personalized_protein_suggestions] Error: {e}")
        import traceback
        traceback.print_exc()
        # Safe fallback that works for most dietary restrictions
        return "plant-based protein sources like lentils and quinoa"


# ✅ COACHING SYSTEM MODULE COMPLETE 
# All 9 functions successfully extracted:
# Part 1: get_consumption_progress_data, calculate_consistency_streak, calculate_personalized_weights, calculate_score_decay
# Part 2: get_daily_coaching_insights_data 
# Part 3: get_nutrition_score_breakdown_data, detect_food_exploitation, quick_log_food_data, generate_personalized_protein_suggestions