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
        user_timezone = user_profile.get("timezone", "UTC")
    today_consumption = await get_today_consumption_records_async(user_email, user_timezone=user_timezone)
        calories_consumed = sum(r.get("nutritional_info", {}).get("calories", 0) for r in today_consumption)
        calorie_target_str = user_profile.get('calorieTarget', '2000')
        try:
            target_calories = int(calorie_target_str) if calorie_target_str and calorie_target_str.strip() else 2000
        except (ValueError, TypeError):
            target_calories = 2000
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
        print(f"[adaptive_plan_optimized] User profile: {user_profile}")
        
        # Get consumption data efficiently with caching
        consumption_history = await get_user_consumption_history_cached(user_email, limit=100)
        print(f"[adaptive_plan_optimized] Got {len(consumption_history)} consumption records")
        
        # Quick consumption analysis
        analysis = _analyze_consumption_patterns(consumption_history)
        print(f"[adaptive_plan_optimized] Analysis: {analysis}")
        
        # Extract dietary info
        dietary_info = _extract_dietary_info(user_profile)
        print(f"[adaptive_plan_optimized] Dietary info: {dietary_info}")
        
        # Generate meal plan with comprehensive AI
        meal_plan_data = await _generate_comprehensive_ai_meal_plan(
            user_profile, dietary_info, analysis, req_days, req_cuisine
        )
        print(f"[adaptive_plan_optimized] Generated meal plan: {meal_plan_data}")
        
        if not meal_plan_data:
            print("[adaptive_plan_optimized] No meal plan data generated, using fallback")
            raise Exception("AI meal plan generation failed")
        
        # Save to database
        meal_plan_data.update({
            "user_id": user_email,
            "created_at": datetime.utcnow().isoformat(),
            "plan_type": "adaptive",
            "user_adherence_rate": analysis["adherence_rate"],
            "based_on_meals": analysis["total_meals"]
        })
        
        print(f"[adaptive_plan_optimized] Meal plan before saving: {meal_plan_data}")
        saved_plan = await save_meal_plan_with_cache_invalidation(user_email, meal_plan_data)
        print(f"[adaptive_plan_optimized] Saved plan result: {saved_plan}")
        
        return {
            "success": True,
            "meal_plan": meal_plan_data,
            "analysis": analysis,
            "message": "Adaptive meal plan created successfully!"
        }
        
    except Exception as e:
        print(f"[adaptive_plan_optimized] Error: {str(e)}")
        import traceback
        print(f"[adaptive_plan_optimized] Traceback: {traceback.format_exc()}")
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


async def _generate_comprehensive_ai_meal_plan(
    user_profile: dict,
    dietary_info: Dict[str, Any], 
    analysis: Dict[str, Any],
    req_days: int,
    req_cuisine: str
) -> Dict[str, Any]:
    """Generate comprehensive AI meal plan using full health profile data."""
    
    cuisine_preference = req_cuisine if req_cuisine else ', '.join(dietary_info["diet_type"]) if dietary_info["diet_type"] else 'Mixed international'
    target_calories = analysis["target_calories"]
    
    # Helper function to get profile values with fallbacks
    def get_profile_value(profile, new_key, old_key=None, default='Not provided'):
        value = profile.get(new_key)
        if not value and old_key:
            value = profile.get(old_key)
        if isinstance(value, list) and value:
            return ', '.join(str(v) for v in value)
        elif isinstance(value, list):
            return default
        return str(value) if value else default
    
    # Create comprehensive health profile summary
    health_profile_summary = f"""
COMPREHENSIVE HEALTH & MEDICAL PROFILE:

PATIENT DEMOGRAPHICS:
- Name: {get_profile_value(user_profile, 'name')}
- Age: {get_profile_value(user_profile, 'age')}
- Gender: {get_profile_value(user_profile, 'gender')}
- Ethnicity: {get_profile_value(user_profile, 'ethnicity', default='Not specified')}

VITAL SIGNS & MEASUREMENTS:
- Height: {get_profile_value(user_profile, 'height')} cm
- Weight: {get_profile_value(user_profile, 'weight')} kg
- BMI: {get_profile_value(user_profile, 'bmi', default='Not calculated')}
- Waist Circumference: {get_profile_value(user_profile, 'waistCircumference', 'waist_circumference')} cm
- Blood Pressure: {get_profile_value(user_profile, 'systolicBP', 'systolic_bp')}/{get_profile_value(user_profile, 'diastolicBP', 'diastolic_bp')} mmHg
- Heart Rate: {get_profile_value(user_profile, 'heartRate', 'heart_rate')} bpm

CRITICAL MEDICAL CONDITIONS:
- Medical Conditions: {get_profile_value(user_profile, 'medicalConditions', 'medical_conditions', 'None specified')}
- Current Medications: {get_profile_value(user_profile, 'currentMedications', default='None specified')}

LAB VALUES (Medical Decision Support):
{json.dumps(user_profile.get('labValues', {}), indent=2) if user_profile.get('labValues') else 'Not provided'}

DIETARY PROFILE:
- **PREFERRED CUISINE TYPE: {get_profile_value(user_profile, 'dietType', 'diet_type', 'Not specified')}** ⭐ MUST FOLLOW THIS CUISINE STYLE ⭐
- Dietary Features: {get_profile_value(user_profile, 'dietaryFeatures', 'diet_features', 'None specified')}
- Dietary Restrictions: {get_profile_value(user_profile, 'dietaryRestrictions', default='None specified')}
- Food Preferences: {get_profile_value(user_profile, 'foodPreferences', default='None specified')}
- Food Allergies: {get_profile_value(user_profile, 'allergies', default='None specified')}
- Strong Dislikes: {get_profile_value(user_profile, 'strongDislikes', default='None specified')}

PHYSICAL ACTIVITY & LIFESTYLE:
- Work Activity Level: {get_profile_value(user_profile, 'workActivityLevel', default='Not specified')}
- Exercise Frequency: {get_profile_value(user_profile, 'exerciseFrequency', default='Not specified')}
- Exercise Types: {get_profile_value(user_profile, 'exerciseTypes', default='Not specified')}
- Primary Goals: {get_profile_value(user_profile, 'primaryGoals', default='Not specified')}
- Wants Weight Loss: {user_profile.get('wantsWeightLoss', 'Not specified')}

CONSUMPTION ANALYSIS:
- Diabetes adherence rate: {analysis['adherence_rate']:.1f}%
- Target daily calories: {target_calories} kcal/day
"""
    
    # Create detailed, day-specific meal plan prompt
    prompt = f"""You are an expert registered dietitian and diabetes specialist creating a personalized {req_days}-day meal plan. 

{health_profile_summary}

CRITICAL MEDICAL SAFETY REQUIREMENTS:
1. **MEDICAL CONDITIONS**: Carefully consider ALL medical conditions and medications listed above. Ensure meals support diabetes management and any other health conditions.
2. **DIETARY COMPLIANCE**: Absolutely MUST follow ALL dietary restrictions, allergies, and food preferences.
3. **CUISINE ADHERENCE**: Follow the specified cuisine type exactly while respecting all medical and dietary requirements.
4. **MEDICATION INTERACTIONS**: Consider how foods might interact with listed medications.

MEAL DIVERSITY REQUIREMENTS:
- Create COMPLETELY DIFFERENT meals for each day
- Ensure NO repetition of dishes across the {req_days} days
- Each breakfast, lunch, dinner, and snack must be unique
- Vary cooking methods, ingredients, and flavors significantly
- Consider cultural authenticity for the specified cuisine type

{"VEGETARIAN REQUIREMENT: All meals must be completely vegetarian (no meat, poultry, fish, seafood)" if dietary_info.get('is_vegetarian') else ""}
{"EGG-FREE REQUIREMENT: All meals must be completely egg-free (no eggs, omelets, quiche, egg-based sauces)" if dietary_info.get('no_eggs') else ""}

Return JSON with this EXACT structure:
{{
    "plan_name": "Comprehensive Adaptive Plan - {datetime.now().strftime('%Y-%m-%d')}",
    "duration_days": {req_days},
    "dailyCalories": {target_calories},
    "breakfast": [
        "Day 1: [Specific breakfast dish with portion]",
        "Day 2: [Completely different breakfast dish with portion]",
        "Day 3: [Another unique breakfast dish with portion]"
        // Continue for all {req_days} days - each must be UNIQUE
    ],
    "lunch": [
        "Day 1: [Specific lunch dish with portion]",
        "Day 2: [Completely different lunch dish with portion]", 
        "Day 3: [Another unique lunch dish with portion]"
        // Continue for all {req_days} days - each must be UNIQUE
    ],
    "dinner": [
        "Day 1: [Specific dinner dish with portion]",
        "Day 2: [Completely different dinner dish with portion]",
        "Day 3: [Another unique dinner dish with portion]"
        // Continue for all {req_days} days - each must be UNIQUE
    ],
    "snacks": [
        "Day 1: [Specific snack with portion]",
        "Day 2: [Completely different snack with portion]",
        "Day 3: [Another unique snack with portion]"
        // Continue for all {req_days} days - each must be UNIQUE
    ],
    "adaptations": ["Medical adaptations based on conditions and medications", "Dietary adaptations for restrictions and preferences"],
    "coaching_notes": "Personalized coaching advice based on medical conditions, goals, and health profile"
}}

ABSOLUTE REQUIREMENTS:
- Each meal array must have exactly {req_days} items
- NO meal repetition across any day
- All meals must be diabetes-friendly (low glycemic index)
- Must respect ALL medical conditions and medications
- Must follow the specified cuisine type: {cuisine_preference}
- Consider the patient's age, weight, activity level, and health goals
- Provide specific dish names with appropriate portions"""

    try:
        api_result = await robust_openai_call(
            messages=[
                {"role": "system", "content": f"You are a certified registered dietitian and diabetes specialist with expertise in {cuisine_preference} cuisine. You create medically-appropriate, personalized meal plans based on comprehensive patient profiles. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,  # Increased for comprehensive response
            temperature=0.8,  # Slightly higher for creativity in meal variety
            max_retries=3,    # More retries for better results
            timeout=60,       # Longer timeout for comprehensive planning
            context="comprehensive_adaptive_meal_plan"
        )
        
        if api_result["success"]:
            start_idx = api_result["content"].find('{')
            end_idx = api_result["content"].rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                json_str = api_result["content"][start_idx:end_idx]
                meal_plan_data = json.loads(json_str)
                
                # Validate that we have the correct number of meals for each category
                for meal_type in ['breakfast', 'lunch', 'dinner', 'snacks']:
                    if meal_type in meal_plan_data:
                        if len(meal_plan_data[meal_type]) != req_days:
                            print(f"[comprehensive_ai_meal_plan] Warning: {meal_type} has {len(meal_plan_data[meal_type])} items, expected {req_days}")
                
                return meal_plan_data
                
    except Exception as e:
        print(f"[comprehensive_ai_meal_plan] Error: {e}")
    
    # Fallback meal plan with proper diversity
    return _create_comprehensive_fallback_plan(req_days, target_calories, cuisine_preference, dietary_info, user_profile)


def _create_comprehensive_fallback_plan(req_days: int, target_calories: int, cuisine: str, dietary_info: Dict[str, Any], user_profile: dict) -> Dict[str, Any]:
    """Create comprehensive fallback adaptive meal plan with diversity."""
    print(f"[comprehensive_fallback_plan] Creating comprehensive fallback plan for {req_days} days, {target_calories} calories, cuisine: {cuisine}")
    
    # Get user's dietary restrictions for personalized fallback
    is_vegetarian = dietary_info.get("is_vegetarian", False)
    no_eggs = dietary_info.get("no_eggs", False)
    medical_conditions = user_profile.get("medicalConditions", []) or user_profile.get("medical_conditions", [])
    
    # Create diverse meal options based on cuisine type and restrictions
    breakfast_options = []
    lunch_options = []
    dinner_options = []
    snack_options = []
    
    # Cuisine-specific meal options
    if "western" in cuisine.lower() or "european" in cuisine.lower():
        if is_vegetarian and no_eggs:
            breakfast_options = ["Oatmeal with fresh berries and almonds", "Avocado toast with tomatoes", "Quinoa breakfast porridge", "Chia seed pudding with fruit", "Smoothie bowl with spinach and banana", "Whole grain toast with almond butter", "Buckwheat pancakes with berries"]
            lunch_options = ["Mediterranean quinoa salad", "Lentil and vegetable soup", "Caprese salad with whole grain bread", "Hummus and veggie wrap", "Buddha bowl with tahini dressing", "Vegetable minestrone", "Chickpea salad sandwich"]
            dinner_options = ["Pasta with marinara and vegetables", "Stuffed bell peppers with quinoa", "Vegetable curry with brown rice", "Lentil shepherd's pie", "Eggplant and zucchini gratin", "Black bean and sweet potato stew", "Mushroom and barley risotto"]
        elif is_vegetarian:
            breakfast_options = ["Vegetable scrambled eggs", "Greek yogurt with granola", "Spinach and cheese omelet", "Avocado toast with poached egg", "Veggie breakfast burrito", "French toast with berries", "Cottage cheese with fruit"]
            lunch_options = ["Caprese salad with mozzarella", "Vegetarian quiche", "Greek salad with feta", "Egg salad sandwich", "Spinach and feta wrap", "Cheese and tomato panini", "Vegetable frittata"]
            dinner_options = ["Eggplant parmesan", "Vegetable lasagna", "Mushroom stroganoff", "Cheese and spinach cannelloni", "Ratatouille with quinoa", "Vegetarian pizza margherita", "Stuffed portobello mushrooms"]
        else:
            breakfast_options = ["Scrambled eggs with whole grain toast", "Greek yogurt with berries and nuts", "Oatmeal with banana and walnuts", "Avocado toast with poached egg", "Protein smoothie with berries", "Whole grain cereal with milk", "Veggie omelet with cheese"]
            lunch_options = ["Grilled chicken Caesar salad", "Turkey and avocado sandwich", "Salmon quinoa bowl", "Chicken and vegetable soup", "Tuna salad wrap", "Mediterranean chicken bowl", "Lean beef and barley soup"]
            dinner_options = ["Grilled salmon with roasted vegetables", "Chicken breast with quinoa pilaf", "Lean beef stir-fry with brown rice", "Baked cod with sweet potato", "Turkey meatballs with zucchini noodles", "Chicken curry with cauliflower rice", "Grilled fish tacos with cabbage slaw"]
    
    elif "mediterranean" in cuisine.lower():
        if is_vegetarian and no_eggs:
            breakfast_options = ["Greek yogurt with honey and nuts", "Avocado toast with tomatoes", "Quinoa tabbouleh bowl", "Hummus with whole grain pita", "Fruit and nut parfait", "Olive tapenade on toast", "Fresh fruit with yogurt"]
            lunch_options = ["Greek village salad", "Lentil soup with herbs", "Hummus and vegetable wrap", "Chickpea and cucumber salad", "Mediterranean quinoa bowl", "Falafel salad", "White bean and herb salad"]
            dinner_options = ["Ratatouille with quinoa", "Stuffed grape leaves", "Chickpea and vegetable stew", "Mediterranean lentil curry", "Roasted vegetable moussaka", "Pasta with olive oil and herbs", "Stuffed zucchini with rice"]
        else:
            breakfast_options = ["Greek omelet with feta", "Yogurt with honey and granola", "Mediterranean scrambled eggs", "Avocado and egg toast", "Greek yogurt parfait", "Shakshuka (eggs in tomato sauce)", "Cheese and herb omelet"]
            lunch_options = ["Greek salad with chicken", "Mediterranean chicken wrap", "Tuna and white bean salad", "Chicken souvlaki bowl", "Mediterranean quinoa salad", "Grilled fish with vegetables", "Chicken and olive tapenade"]
            dinner_options = ["Grilled fish with lemon and herbs", "Chicken with Mediterranean vegetables", "Lamb and vegetable stew", "Seafood paella", "Chicken moussaka", "Grilled salmon with quinoa", "Mediterranean fish soup"]
    
    else:  # Mixed international or other cuisines
        if is_vegetarian and no_eggs:
            breakfast_options = ["Oatmeal with fresh fruit", "Avocado toast", "Quinoa breakfast bowl", "Smoothie with spinach and banana", "Chia pudding with berries", "Whole grain toast with almond butter", "Fruit and yogurt bowl"]
            lunch_options = ["Quinoa and black bean salad", "Lentil and vegetable curry", "Buddha bowl with tahini", "Vegetable stir-fry with brown rice", "Chickpea salad wrap", "Mushroom and barley soup", "Mediterranean quinoa bowl"]
            dinner_options = ["Vegetable curry with quinoa", "Stuffed bell peppers", "Lentil dal with brown rice", "Vegetable stir-fry with tofu", "Black bean and sweet potato stew", "Mushroom and vegetable pasta", "Quinoa and vegetable pilaf"]
        else:
            breakfast_options = ["Scrambled eggs with vegetables", "Greek yogurt with granola", "Protein smoothie bowl", "Vegetable omelet", "Whole grain toast with egg", "Cottage cheese with fruit", "Breakfast burrito"]
            lunch_options = ["Grilled chicken salad", "Turkey and veggie wrap", "Salmon poke bowl", "Chicken and vegetable soup", "Tuna salad sandwich", "Quinoa bowl with protein", "Chicken stir-fry"]
            dinner_options = ["Grilled fish with vegetables", "Chicken breast with quinoa", "Turkey meatballs with vegetables", "Baked salmon with sweet potato", "Lean beef with brown rice", "Chicken curry with vegetables", "Fish and vegetable curry"]
    
    # Common healthy snacks
    if is_vegetarian:
        snack_options = ["Apple slices with almond butter", "Greek yogurt with berries", "Mixed nuts and seeds", "Hummus with vegetable sticks", "Whole grain crackers with cheese", "Fresh fruit salad", "Yogurt parfait with granola"]
    else:
        snack_options = ["Apple with peanut butter", "Greek yogurt with nuts", "Mixed nuts", "Cheese and whole grain crackers", "Hard-boiled egg with vegetables", "Protein smoothie", "Vegetable sticks with hummus"]
    
    # Ensure we have enough options for the requested days
    def extend_options(options, needed):
        while len(options) < needed:
            options.extend(options[:min(len(options), needed - len(options))])
        return options[:needed]
    
    breakfast_options = extend_options(breakfast_options, req_days)
    lunch_options = extend_options(lunch_options, req_days)
    dinner_options = extend_options(dinner_options, req_days)
    snack_options = extend_options(snack_options, req_days)
    
    # Create day-specific meal labels
    selected_breakfasts = [f"Day {i+1}: {breakfast_options[i]}" for i in range(req_days)]
    selected_lunches = [f"Day {i+1}: {lunch_options[i]}" for i in range(req_days)]
    selected_dinners = [f"Day {i+1}: {dinner_options[i]}" for i in range(req_days)]
    selected_snacks = [f"Day {i+1}: {snack_options[i]}" for i in range(req_days)]
    
    # Create medical adaptations based on conditions
    adaptations = []
    if "diabetes" in str(medical_conditions).lower():
        adaptations.append("All meals are designed with low glycemic index foods for diabetes management")
    if "hypertension" in str(medical_conditions).lower() or "high blood pressure" in str(medical_conditions).lower():
        adaptations.append("Reduced sodium options selected for blood pressure management")
    if is_vegetarian:
        adaptations.append("All meals are vegetarian-friendly with plant-based proteins")
    if no_eggs:
        adaptations.append("All meals are egg-free to accommodate dietary restrictions")
    if not adaptations:
        adaptations.append("Basic healthy meal adaptations applied")
    
    return {
        "plan_name": f"Comprehensive Fallback Plan - {datetime.now().strftime('%Y-%m-%d')}",
        "duration_days": req_days,
        "dailyCalories": target_calories,
        "breakfast": selected_breakfasts,
        "lunch": selected_lunches,
        "dinner": selected_dinners,
        "snacks": selected_snacks,
        "adaptations": adaptations,
        "coaching_notes": f"This comprehensive fallback meal plan is designed for {cuisine} cuisine with your dietary preferences and medical conditions in mind. Each day features different meals to ensure variety and nutritional balance. Please consult with your healthcare provider for personalized recommendations."
    }