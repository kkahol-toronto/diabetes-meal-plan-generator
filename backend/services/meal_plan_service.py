"""
Meal Plan Service
Optimized service for meal plan generation and retrieval.
Extracted from main.py to improve performance and reduce response times.
"""

import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from services.openai_service import robust_openai_call
from services.consumption_analysis import (
    get_today_consumption_records_async,
    trigger_meal_plan_recalibration,
    generate_fresh_adaptive_meal_plan,
    generate_safe_vegetarian_fallback
)
from services.database_service import (
    get_user_meal_plans_cached,
    save_meal_plan_with_cache_invalidation,
    get_user_consumption_history_cached
)
from utils import filter_today_records


async def get_todays_meal_plan_optimized(user_email: str, user_profile: dict) -> Dict[str, Any]:
    """
    Optimized today's meal plan retrieval with streamlined processing.
    
    Args:
        user_email: User's email identifier
        user_profile: User's profile data
        
    Returns:
        Dict containing today's meal plan
    """
    try:
        print(f"[meal_plan_optimized] Getting meal plan for {user_email}")
        
        # Get timezone from profile  
        user_timezone = user_profile.get("timezone", "UTC")
        today = datetime.utcnow().date()
        
        # Fetch meal plans efficiently with caching
        meal_plans = await get_user_meal_plans_cached(user_email)
        
        # Find today's plan or derive from recent plan
        todays_plan = _find_or_derive_todays_plan(meal_plans, today, user_email)
        
        # Check if user has dietary restrictions requiring fresh generation
        dietary_info = _extract_dietary_info(user_profile)
        
        if dietary_info["needs_fresh_generation"]:
            print("[meal_plan_optimized] Generating fresh plan for dietary restrictions")
            todays_plan = await _generate_fresh_dietary_plan(
                user_email, user_profile, dietary_info, todays_plan
            )
        
        # Apply real-time calibration if consumption exists today
        todays_plan = await _apply_consumption_calibration(
            user_email, user_profile, todays_plan, user_timezone
        )
        
        # Ensure plan is properly formatted for frontend
        todays_plan = _normalize_meal_plan_format(todays_plan)
        
        return todays_plan
        
    except Exception as e:
        print(f"[meal_plan_optimized] Error: {str(e)}")
        return _create_fallback_plan(user_email, today)


def _find_or_derive_todays_plan(meal_plans: List[dict], today: datetime.date, user_email: str) -> Dict[str, Any]:
    """Find today's plan or derive from most recent plan."""
    
    # Look for today's plan
    for plan in meal_plans:
        plan_date = plan.get("date")
        if plan_date:
            try:
                if datetime.fromisoformat(plan_date).date() == today:
                    return plan
            except:
                continue
    
    # Derive from most recent plan
    if meal_plans:
        latest_plan = meal_plans[0]  # Assuming sorted by recency
        
        derived_meals = {}
        for meal_type in ["breakfast", "lunch", "dinner", "snacks"]:
            meal_val = latest_plan.get(meal_type)
            if isinstance(meal_val, list) and meal_val:
                derived_meals[meal_type.replace("snacks", "snack")] = meal_val[0]
            elif isinstance(meal_val, str):
                derived_meals[meal_type.replace("snacks", "snack")] = meal_val
            else:
                derived_meals[meal_type.replace("snacks", "snack")] = "Healthy meal option"
        
        return {
            "id": f"derived_{latest_plan.get('id', 'plan')}_{today.isoformat()}",
            "date": today.isoformat(),
            "type": "derived_from_latest",
            "meals": derived_meals,
            "dailyCalories": latest_plan.get("dailyCalories", 2000),
            "created_at": datetime.utcnow().isoformat(),
            "notes": "Derived from recent meal plan"
        }
    
    return None


def _extract_dietary_info(user_profile: dict) -> Dict[str, Any]:
    """Extract and analyze dietary restrictions efficiently."""
    
    dietary_restrictions = user_profile.get("dietaryRestrictions", [])
    dietary_features = user_profile.get("dietaryFeatures", []) or user_profile.get("diet_features", [])
    allergies = user_profile.get("allergies", [])
    diet_type = user_profile.get("dietType", [])
    
    # Combine all dietary info
    all_dietary_info = []
    for field in [dietary_restrictions, dietary_features, diet_type]:
        if isinstance(field, list):
            all_dietary_info.extend([str(item).lower() for item in field])
        elif isinstance(field, str) and field:
            all_dietary_info.append(field.lower())
    
    is_vegetarian = any('vegetarian' in info for info in all_dietary_info)
    no_eggs = any(
        'no egg' in info or 'egg-free' in info or 'no eggs' in info or
        ('vegetarian' in info and 'no egg' in info)
        for info in all_dietary_info
    ) or any('egg' in str(allergy).lower() for allergy in allergies)
    
    return {
        "is_vegetarian": is_vegetarian,
        "no_eggs": no_eggs,
        "dietary_restrictions": dietary_restrictions,
        "allergies": allergies,
        "diet_type": diet_type,
        "needs_fresh_generation": is_vegetarian or no_eggs or len(dietary_restrictions) > 0
    }


async def _generate_fresh_dietary_plan(
    user_email: str, 
    user_profile: dict, 
    dietary_info: Dict[str, Any],
    existing_plan: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Generate fresh meal plan respecting dietary restrictions."""
    
    try:
        # Get today's consumption for calorie calculation
        today_consumption = await get_today_consumption_records_async(user_email, user_timezone="UTC")
        calories_consumed = sum(r.get("nutritional_info", {}).get("calories", 0) for r in today_consumption)
        target_calories = int(user_profile.get('calorieTarget', '2000'))
        remaining_calories = max(0, target_calories - calories_consumed)
        
        # Use the optimized fresh generation service
        fresh_plan = await generate_fresh_adaptive_meal_plan(
            user_email,
            today_consumption,
            remaining_calories,
            dietary_info["is_vegetarian"],
            dietary_info["no_eggs"],
            dietary_info["dietary_restrictions"],
            dietary_info["allergies"],
            dietary_info["diet_type"],
            user_profile.get('foodPreferences', []),
            user_profile.get('strongDislikes', [])
        )
        
        if fresh_plan:
            return fresh_plan
        else:
            # Fallback to safe vegetarian plan
            return generate_safe_vegetarian_fallback(
                user_email,
                remaining_calories,
                dietary_info["is_vegetarian"],
                dietary_info["no_eggs"]
            )
            
    except Exception as e:
        print(f"[fresh_dietary_plan] Error: {e}")
        return existing_plan or _create_fallback_plan(user_email, datetime.utcnow().date())


async def _apply_consumption_calibration(
    user_email: str,
    user_profile: dict, 
    todays_plan: Dict[str, Any],
    user_timezone: str
) -> Dict[str, Any]:
    """Apply consumption-based calibration if needed."""
    
    try:
        # Check if user has consumed anything today
        today_consumption = await get_today_consumption_records_async(user_email, user_timezone=user_timezone)
        
        if today_consumption:
            print(f"[meal_plan_calibration] Applying calibration for {len(today_consumption)} consumption records")
            updated_plan = await trigger_meal_plan_recalibration(user_email, user_profile)
            if updated_plan:
                return updated_plan
                
    except Exception as e:
        print(f"[meal_plan_calibration] Error: {e}")
    
    return todays_plan


def _normalize_meal_plan_format(plan: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure meal plan is in correct format for frontend."""
    
    if not plan or not plan.get("meals"):
        return plan
    
    # Clean up any duplicate text patterns
    meals = plan.get("meals", {})
    for meal_key, meal_text in meals.items():
        if isinstance(meal_text, str):
            # Remove duplicate "Recommended:" prefixes
            while "Recommended: Recommended:" in meal_text:
                meal_text = meal_text.replace("Recommended: Recommended:", "Recommended:")
            
            # Remove duplicate "(recommended)" suffixes
            while "(recommended) (recommended)" in meal_text:
                meal_text = meal_text.replace("(recommended) (recommended)", "(recommended)")
            
            meals[meal_key] = meal_text
    
    plan["meals"] = meals
    return plan


def _create_fallback_plan(user_email: str, today: datetime.date) -> Dict[str, Any]:
    """Create a basic fallback meal plan."""
    
    return {
        "id": f"fallback_{user_email}_{today.isoformat()}",
        "date": today.isoformat(),
        "type": "fallback_basic",
        "meals": {
            "breakfast": "Steel-cut oats with almond milk and fresh berries",
            "lunch": "Quinoa Buddha bowl with roasted vegetables",
            "dinner": "Lentil curry with brown rice and steamed broccoli", 
            "snack": "Apple slices with almond butter"
        },
        "dailyCalories": 2000,
        "created_at": datetime.utcnow().isoformat(),
        "notes": "Basic fallback meal plan"
    }


async def create_adaptive_meal_plan_optimized(
    user_email: str,
    user_profile: dict,
    req_days: int = 7,
    req_cuisine: str = ""
) -> Dict[str, Any]:
    """
    Optimized adaptive meal plan creation with streamlined processing.
    
    Args:
        user_email: User's email identifier
        user_profile: User's profile data
        req_days: Number of days for the plan
        req_cuisine: Requested cuisine type
        
    Returns:
        Dict containing the adaptive meal plan and analysis
    """
    try:
        print(f"[adaptive_plan_optimized] Creating {req_days}-day plan for {user_email}")
        
        # Get consumption data efficiently with caching
        consumption_history = await get_user_consumption_history_cached(user_email, limit=100)
        
        # Quick consumption analysis
        analysis = _analyze_consumption_patterns(consumption_history)
        
        # Extract dietary info
        dietary_info = _extract_dietary_info(user_profile)
        
        # Generate meal plan with AI
        meal_plan_data = await _generate_ai_meal_plan(
            user_profile, dietary_info, analysis, req_days, req_cuisine
        )
        
        # Save to database
        meal_plan_data.update({
            "user_id": user_email,
            "created_at": datetime.utcnow().isoformat(),
            "plan_type": "adaptive",
            "user_adherence_rate": analysis["adherence_rate"],
            "based_on_meals": analysis["total_meals"]
        })
        
        saved_plan = await save_meal_plan_with_cache_invalidation(user_email, meal_plan_data)
        
        return {
            "success": True,
            "meal_plan": meal_plan_data,
            "analysis": analysis,
            "message": "Adaptive meal plan created successfully!"
        }
        
    except Exception as e:
        print(f"[adaptive_plan_optimized] Error: {str(e)}")
        raise Exception(f"Failed to create adaptive meal plan: {str(e)}")


def _analyze_consumption_patterns(consumption_history: List[dict]) -> Dict[str, Any]:
    """Quick consumption pattern analysis."""
    
    if not consumption_history:
        return {
            "total_meals": 0,
            "adherence_rate": 0.0,
            "favorite_foods": [],
            "avg_daily_calories": 2000,
            "target_calories": 2000
        }
    
    # Filter to last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_consumption = []
    
    for entry in consumption_history:
        try:
            entry_timestamp = datetime.fromisoformat(entry.get("timestamp", "").replace("Z", "+00:00"))
            if entry_timestamp >= thirty_days_ago:
                recent_consumption.append(entry)
        except:
            continue
    
    # Quick analysis
    favorite_foods = {}
    diabetes_friendly_count = 0
    total_calories = 0
    
    for entry in recent_consumption:
        food_name = entry.get("food_name", "").lower()
        favorite_foods[food_name] = favorite_foods.get(food_name, 0) + 1
        
        nutrition = entry.get("nutritional_info", {})
        total_calories += nutrition.get("calories", 0)
        
        medical_rating = entry.get("medical_rating", {})
        if medical_rating.get("diabetes_suitability", "").lower() in ["high", "good", "suitable"]:
            diabetes_friendly_count += 1
    
    total_meals = len(recent_consumption)
    adherence_rate = (diabetes_friendly_count / total_meals * 100) if total_meals > 0 else 0
    avg_daily_calories = (total_calories / 30) if total_calories > 0 else 2000
    
    top_favorites = sorted(favorite_foods.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "total_meals": total_meals,
        "adherence_rate": round(adherence_rate, 1),
        "favorite_foods": [food for food, count in top_favorites],
        "avg_daily_calories": round(avg_daily_calories, 0),
        "target_calories": max(1200, int(avg_daily_calories)) if avg_daily_calories > 1200 else 2000
    }


async def _generate_ai_meal_plan(
    user_profile: dict,
    dietary_info: Dict[str, Any], 
    analysis: Dict[str, Any],
    req_days: int,
    req_cuisine: str
) -> Dict[str, Any]:
    """Generate AI meal plan with optimized prompt."""
    
    cuisine_preference = req_cuisine if req_cuisine else ', '.join(dietary_info["diet_type"]) if dietary_info["diet_type"] else 'Mixed international'
    target_calories = analysis["target_calories"]
    
    # Streamlined prompt for faster processing
    prompt = f"""Create a {req_days}-day diabetes meal plan:

USER PROFILE:
- Cuisine: {cuisine_preference}
- Diet: {', '.join(dietary_info['diet_type']) or 'Standard'}
- Restrictions: {', '.join(dietary_info['dietary_restrictions']) or 'None'}
- Allergies: {', '.join(dietary_info['allergies']) or 'None'}
- Target calories: {target_calories}/day
- Adherence rate: {analysis['adherence_rate']:.0f}%

REQUIREMENTS:
{'- VEGETARIAN: No meat, poultry, fish, seafood' if dietary_info['is_vegetarian'] else ''}
{'- NO EGGS: Avoid eggs and egg-based dishes' if dietary_info['no_eggs'] else ''}
- Diabetes-friendly (low glycemic index)
- Specific dish names with portions

Return JSON:
{{
    "plan_name": "Adaptive Plan - {datetime.now().strftime('%Y-%m-%d')}",
    "duration_days": {req_days},
    "dailyCalories": {target_calories},
    "breakfast": ["{req_days} specific breakfast dishes"],
    "lunch": ["{req_days} specific lunch dishes"], 
    "dinner": ["{req_days} specific dinner dishes"],
    "snacks": ["{req_days} specific snacks"],
    "adaptations": ["Brief adaptation notes"],
    "coaching_notes": "Brief coaching advice"
}}"""

    try:
        api_result = await robust_openai_call(
            messages=[
                {"role": "system", "content": f"You are a dietitian specializing in {cuisine_preference} diabetes meal planning. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,  # Reduced for faster response
            temperature=0.7,
            max_retries=2,    # Reduced for faster response
            timeout=30,       # Shorter timeout
            context="adaptive_meal_plan"
        )
        
        if api_result["success"]:
            start_idx = api_result["content"].find('{')
            end_idx = api_result["content"].rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                json_str = api_result["content"][start_idx:end_idx]
                return json.loads(json_str)
                
    except Exception as e:
        print(f"[ai_meal_plan] Error: {e}")
    
    # Fallback meal plan
    return _create_fallback_adaptive_plan(req_days, target_calories, cuisine_preference, dietary_info)


def _create_fallback_adaptive_plan(req_days: int, target_calories: int, cuisine: str, dietary_info: Dict[str, Any]) -> Dict[str, Any]:
    """Create fallback adaptive meal plan."""
    
    # Simple cuisine-appropriate meals
    if 'indian' in cuisine.lower():
        breakfast = ["Upma with vegetables"] * req_days
        lunch = ["Dal with roti"] * req_days  
        dinner = ["Vegetable curry with quinoa"] * req_days
    else:
        breakfast = ["Oatmeal with berries"] * req_days
        lunch = ["Quinoa salad with vegetables"] * req_days
        dinner = ["Vegetable stir-fry with tofu"] * req_days
    
    snacks = ["Apple with almond butter"] * req_days
    
    return {
        "plan_name": f"Adaptive {cuisine} Plan - {datetime.now().strftime('%Y-%m-%d')}",
        "duration_days": req_days,
        "dailyCalories": target_calories,
        "breakfast": breakfast,
        "lunch": lunch,
        "dinner": dinner,
        "snacks": snacks,
        "adaptations": [f"Adapted for {cuisine} cuisine with dietary restrictions"],
        "coaching_notes": "Basic adaptive plan with dietary compliance"
    }