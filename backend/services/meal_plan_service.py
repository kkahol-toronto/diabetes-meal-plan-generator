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
        
        # Generate meal plan with AI
        meal_plan_data = await _generate_ai_meal_plan(
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


async def _generate_ai_meal_plan(
    user_profile: dict,
    dietary_info: Dict[str, Any], 
    analysis: Dict[str, Any],
    req_days: int,
    req_cuisine: str
) -> Dict[str, Any]:
    """Generate comprehensive AI meal plan using full health profile and adaptive intelligence."""
    
    print(f"[comprehensive_meal_plan] Generating truly adaptive meal plan for user")
    
    # Extract comprehensive health information
    medical_conditions = user_profile.get("medicalConditions", []) or user_profile.get("medical_conditions", [])
    current_medications = user_profile.get("currentMedications", [])
    dietary_restrictions = user_profile.get("dietaryRestrictions", [])
    dietary_features = user_profile.get("dietaryFeatures", []) or user_profile.get("diet_features", [])
    allergies = user_profile.get("allergies", [])
    food_preferences = user_profile.get("foodPreferences", [])
    strong_dislikes = user_profile.get("strongDislikes", [])
    primary_goals = user_profile.get("primaryGoals", [])
    lab_values = user_profile.get("labValues", {})
    age = user_profile.get("age")
    weight = user_profile.get("weight")
    height = user_profile.get("height")
    bmi = user_profile.get("bmi")
    exercise_frequency = user_profile.get("exerciseFrequency")
    work_activity_level = user_profile.get("workActivityLevel")
    eating_schedule = user_profile.get("eatingSchedule")
    meal_prep_capability = user_profile.get("mealPrepCapability")
    available_appliances = user_profile.get("availableAppliances", [])
    
    # CRITICAL: Use user's profile dietType as primary cuisine preference
    profile_cuisine = ', '.join(dietary_info["diet_type"]) if dietary_info["diet_type"] else ''
    cuisine_preference = req_cuisine if req_cuisine else profile_cuisine if profile_cuisine else 'Mixed international'
    
    # Log for debugging
    print(f"[meal_plan_service] Profile dietType: {dietary_info['diet_type']}")
    print(f"[meal_plan_service] Final cuisine preference: {cuisine_preference}")
    target_calories = analysis["target_calories"]
    
    # Calculate macro targets based on health conditions
    protein_target = max(80, int(target_calories * 0.20 / 4))  # 20% of calories from protein
    carb_target = max(150, int(target_calories * 0.45 / 4))    # 45% from carbs (diabetes-friendly)
    fat_target = max(55, int(target_calories * 0.35 / 9))      # 35% from fat
    
    # Adjust macros based on specific conditions
    if any('diabetes' in condition.lower() for condition in medical_conditions):
        carb_target = int(carb_target * 0.8)  # Reduce carbs for diabetes
        protein_target = int(protein_target * 1.2)  # Increase protein
    
    if any('hypertension' in condition.lower() or 'blood pressure' in condition.lower() for condition in medical_conditions):
        # Emphasize low sodium in prompt
        pass
    
    # Build comprehensive prompt with all health context
    prompt = f"""You are an expert clinical nutritionist and diabetes specialist creating a personalized {req_days}-day meal plan. Use ALL the comprehensive health information provided to create truly adaptive, medically-appropriate meal recommendations.

COMPREHENSIVE PATIENT PROFILE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MEDICAL CONDITIONS: {', '.join(medical_conditions) if medical_conditions else 'None specified'}
CURRENT MEDICATIONS: {', '.join(current_medications) if current_medications else 'None specified'}
DIETARY RESTRICTIONS: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}
DIETARY FEATURES: {', '.join(dietary_features) if dietary_features else 'Standard'}
ALLERGIES: {', '.join(allergies) if allergies else 'None'}
FOOD PREFERENCES: {', '.join(food_preferences) if food_preferences else 'None specified'}
STRONG DISLIKES: {', '.join(strong_dislikes) if strong_dislikes else 'None specified'}
PRIMARY HEALTH GOALS: {', '.join(primary_goals) if primary_goals else 'General wellness'}

PHYSICAL PROFILE:
- Age: {age if age else 'Not specified'}
- Weight: {weight if weight else 'Not specified'} lbs
- Height: {height if height else 'Not specified'} inches  
- BMI: {bmi if bmi else 'Not specified'}
- Exercise Frequency: {exercise_frequency if exercise_frequency else 'Not specified'}
- Work Activity Level: {work_activity_level if work_activity_level else 'Not specified'}

LIFESTYLE FACTORS:
- Preferred Eating Schedule: {eating_schedule if eating_schedule else 'Standard 3 meals + snacks'}
- Meal Prep Capability: {meal_prep_capability if meal_prep_capability else 'Moderate'}
- Available Appliances: {', '.join(available_appliances) if available_appliances else 'Standard kitchen'}
- Preferred Cuisine: {cuisine_preference}

LAB VALUES: {dict(lab_values) if lab_values else 'None provided'}

NUTRITIONAL TARGETS:
- Daily Calories: {target_calories} kcal
- Protein Target: {protein_target}g ({protein_target*4}kcal)
- Carbohydrate Target: {carb_target}g ({carb_target*4}kcal) - LOW GLYCEMIC FOCUS
- Fat Target: {fat_target}g ({fat_target*9}kcal) - HEART-HEALTHY FATS

CONSUMPTION ANALYSIS:
- Historical Adherence Rate: {analysis['adherence_rate']:.0f}%
- Average Daily Calories: {analysis.get('avg_daily_calories', 'Not available')}

CRITICAL REQUIREMENTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. MEDICAL CONDITION COMPLIANCE:
   - Design every meal to support management of: {', '.join(medical_conditions) if medical_conditions else 'general health'}
   - Consider medication timing and food interactions for: {', '.join(current_medications) if current_medications else 'no medications listed'}
   
2. DIABETES-SPECIFIC REQUIREMENTS (if applicable):
   - Low glycemic index foods only
   - Complex carbohydrates with fiber
   - Portion control for blood sugar stability
   - Balanced macronutrients at each meal
   
3. DIETARY COMPLIANCE:
   - Strictly follow ALL dietary restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}
   - Completely avoid ALL allergies: {', '.join(allergies) if allergies else 'None'}
   - Incorporate preferred foods: {', '.join(food_preferences) if food_preferences else 'None specified'}
   - Avoid disliked foods: {', '.join(strong_dislikes) if strong_dislikes else 'None specified'}

4. PERSONALIZATION:
   - Match eating schedule: {eating_schedule if eating_schedule else 'Standard'}
   - Consider prep capability: {meal_prep_capability if meal_prep_capability else 'Moderate'}
   - Use available appliances: {', '.join(available_appliances) if available_appliances else 'Standard kitchen'}
   - Support goals: {', '.join(primary_goals) if primary_goals else 'General wellness'}

5. VARIETY & PRACTICALITY:
   - Each day should be different with varied foods
   - Include specific portion sizes
   - Provide realistic, preparable meals
   - **STRICTLY FOLLOW CULTURAL CUISINE PREFERENCES: {cuisine_preference} - DO NOT GENERATE FOODS FROM OTHER CUISINES**

Return EXACTLY this JSON structure:
{{
    "plan_name": "Comprehensive Adaptive Plan - {datetime.now().strftime('%Y-%m-%d')}",
    "duration_days": {req_days},
    "dailyCalories": {target_calories},
    "macronutrients": {{
        "protein": {protein_target},
        "carbohydrates": {carb_target},
        "fat": {fat_target}
    }},
    "breakfast": [
        // {req_days} different breakfast meals with specific portions
    ],
    "lunch": [
        // {req_days} different lunch meals with specific portions
    ],
    "dinner": [
        // {req_days} different dinner meals with specific portions
    ],
    "snacks": [
        // {req_days} different healthy snacks with portions
    ],
    "adaptations": [
        // 3-5 specific adaptations explaining how this plan addresses the patient's medical conditions, medications, and goals
    ],
    "coaching_notes": "Comprehensive coaching advice specific to this patient's health conditions, medications, and lifestyle factors",
    "medical_considerations": [
        // 2-3 specific medical considerations for this patient's conditions and medications
    ]
}}

CRITICAL: Make every meal selection intentional based on the patient's specific medical conditions, medications, dietary needs, and preferences. This is medical nutrition therapy, not generic meal planning."""

    try:
        print(f"[comprehensive_meal_plan] Sending comprehensive prompt to AI")
        api_result = await robust_openai_call(
            messages=[
                {
                    "role": "system", 
                    "content": f"You are a clinical nutritionist and certified diabetes educator specializing in medical nutrition therapy. You create personalized meal plans that address specific medical conditions, medication interactions, and comprehensive health profiles. Always provide medically-appropriate, evidence-based nutrition recommendations in valid JSON format."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,  # Increased for comprehensive response
            temperature=0.6,  # Slightly lower for more consistent medical advice
            max_retries=3,
            timeout=45,       # Longer timeout for comprehensive analysis
            context="comprehensive_adaptive_meal_plan"
        )
        
        if api_result["success"]:
            try:
                # Parse JSON response
                start_idx = api_result["content"].find('{')
                end_idx = api_result["content"].rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = api_result["content"][start_idx:end_idx]
                    meal_plan = json.loads(json_str)
                    
                    # Validate required fields
                    required_fields = ["breakfast", "lunch", "dinner", "snacks", "adaptations", "coaching_notes"]
                    if all(field in meal_plan for field in required_fields):
                        print(f"[comprehensive_meal_plan] Successfully generated comprehensive meal plan")
                        return meal_plan
                    else:
                        print(f"[comprehensive_meal_plan] Missing required fields, using fallback")
                        
            except json.JSONDecodeError as e:
                print(f"[comprehensive_meal_plan] JSON parsing error: {e}")
                
    except Exception as e:
        print(f"[comprehensive_meal_plan] Error generating comprehensive plan: {e}")
    
    # Enhanced fallback with health context
    print(f"[comprehensive_meal_plan] Using enhanced fallback meal plan")
    return _create_comprehensive_fallback_plan(req_days, target_calories, cuisine_preference, dietary_info, medical_conditions, dietary_restrictions)


def _create_fallback_adaptive_plan(req_days: int, target_calories: int, cuisine: str, dietary_info: Dict[str, Any]) -> Dict[str, Any]:
    """Create fallback adaptive meal plan."""
    print(f"[fallback_plan] Creating fallback plan for {req_days} days, {target_calories} calories, cuisine: {cuisine}")
    
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
    
    fallback_plan = {
        "plan_name": f"Adaptive {cuisine} Plan - {datetime.now().strftime('%Y-%m-%d')}",
        "duration_days": req_days,
        "dailyCalories": target_calories,
        "breakfast": breakfast,
        "lunch": lunch,
        "dinner": dinner,
        "snacks": snacks,
        "macronutrients": {
            "protein": 25,
            "carbs": 45,
            "fats": 30
        },
        "adaptations": [f"Adapted for {cuisine} cuisine with dietary restrictions"],
        "coaching_notes": "Basic adaptive plan with dietary compliance"
    }
    
    print(f"[fallback_plan] Created fallback plan: {fallback_plan}")
    return fallback_plan


def _create_comprehensive_fallback_plan(
    req_days: int, 
    target_calories: int, 
    cuisine: str, 
    dietary_info: Dict[str, Any],
    medical_conditions: List[str],
    dietary_restrictions: List[str]
) -> Dict[str, Any]:
    """Create comprehensive fallback meal plan with health context."""
    print(f"[comprehensive_fallback] Creating enhanced fallback plan for {req_days} days, {target_calories} calories")
    print(f"[comprehensive_fallback] Medical conditions: {medical_conditions}")
    print(f"[comprehensive_fallback] Dietary restrictions: {dietary_restrictions}")

    # Generate meals based on health conditions and restrictions
    is_vegetarian = dietary_info.get("is_vegetarian", False)
    no_eggs = dietary_info.get("no_eggs", False)
    
    # Diabetes-friendly options by default
    breakfast_options = []
    lunch_options = []
    dinner_options = []
    snack_options = []
    
    if is_vegetarian:
        breakfast_options = [
            "Steel-cut oats with berries and almonds (1 cup)",
            "Whole grain toast with avocado and tomato (2 slices)",
            "Greek yogurt with walnuts and cinnamon (1 cup)",
            "Chia pudding with unsweetened almond milk (3/4 cup)",
            "Vegetable omelet with spinach (if eggs allowed)"
        ]
        lunch_options = [
            "Quinoa salad with mixed vegetables and olive oil (1.5 cups)",
            "Lentil soup with whole grain roll (1 bowl + 1 roll)",
            "Vegetable wrap with hummus and greens (1 large wrap)",
            "Black bean and vegetable bowl with brown rice (1.5 cups)",
            "Chickpea salad with cucumber and herbs (1.5 cups)"
        ]
        dinner_options = [
            "Chickpea curry with cauliflower rice (1 cup curry, 1 cup rice)",
            "Vegetable stir-fry with tofu and brown rice (1.5 cups)",
            "Pasta with marinara sauce and vegetables (1 cup pasta)",
            "Stuffed bell peppers with quinoa (2 peppers)",
            "Lentil dal with roasted vegetables (1 cup dal)"
        ]
        snack_options = [
            "Apple slices with almond butter (1 medium apple, 2 tbsp)",
            "Mixed nuts and seeds (1/4 cup)",
            "Hummus with cucumber slices (3 tbsp hummus)",
            "Greek yogurt with berries (1/2 cup)",
            "Vegetable sticks with guacamole (1/4 cup guac)"
        ]
    else:
        breakfast_options = [
            "Vegetable omelet with whole grain toast (2 eggs, 1 slice)" if not no_eggs else "Greek yogurt with nuts (1 cup)",
            "Oatmeal with protein powder and berries (1 cup)",
            "Greek yogurt parfait with granola (1 cup yogurt)",
            "Smoothie with protein powder and spinach (12 oz)",
            "Cottage cheese with fruit and nuts (1 cup)"
        ]
        lunch_options = [
            "Grilled chicken salad with olive oil dressing (4 oz chicken)",
            "Turkey and avocado wrap (4 oz turkey, whole grain wrap)",
            "Salmon quinoa bowl with vegetables (4 oz salmon)",
            "Chicken and vegetable soup with side salad (1 bowl)",
            "Tuna salad with mixed greens (4 oz tuna)"
        ]
        dinner_options = [
            "Baked salmon with roasted vegetables (5 oz salmon)",
            "Grilled chicken with sweet potato (5 oz chicken)",
            "Lean beef with cauliflower mash (4 oz beef)",
            "Turkey meatballs with zucchini noodles (5 oz turkey)",
            "Baked cod with green beans (5 oz cod)"
        ]
        snack_options = [
            "Greek yogurt with nuts (1/2 cup yogurt)",
            "Hard-boiled eggs with vegetables (2 eggs)" if not no_eggs else "Cottage cheese with berries (1/2 cup)",
            "Apple with peanut butter (1 medium apple, 2 tbsp)",
            "String cheese with cucumber (1 string cheese)",
            "Mixed nuts and olives (1/4 cup mix)"
        ]
    
    # Remove egg options if no_eggs is True
    if no_eggs:
        breakfast_options = [opt for opt in breakfast_options if 'egg' not in opt.lower() and 'omelet' not in opt.lower()]
        snack_options = [opt for opt in snack_options if 'egg' not in opt.lower()]
    
    # Cycle through options for each day
    breakfast = [breakfast_options[i % len(breakfast_options)] for i in range(req_days)]
    lunch = [lunch_options[i % len(lunch_options)] for i in range(req_days)]
    dinner = [dinner_options[i % len(dinner_options)] for i in range(req_days)]
    snacks = [snack_options[i % len(snack_options)] for i in range(req_days)]
    
    # Create adaptations based on health conditions
    adaptations = []
    if any('diabetes' in condition.lower() for condition in medical_conditions):
        adaptations.append("All meals are designed with low glycemic index foods to support blood sugar management")
        adaptations.append("Portions are controlled and balanced to prevent blood sugar spikes")
    
    if any('hypertension' in condition.lower() for condition in medical_conditions):
        adaptations.append("Low sodium options selected to support blood pressure management")
    
    if 'vegetarian' in ' '.join(dietary_restrictions).lower():
        adaptations.append("All meals are vegetarian-friendly with plant-based proteins")
    
    if not adaptations:
        adaptations = [f"Basic {cuisine} meal plan adapted for your dietary needs and health goals"]
    
    # Create medical considerations
    medical_considerations = []
    if medical_conditions:
        medical_considerations.append(f"This plan considers your medical conditions: {', '.join(medical_conditions[:2])}")
    if dietary_restrictions:
        medical_considerations.append(f"Strict adherence to dietary restrictions: {', '.join(dietary_restrictions[:2])}")
    
    return {
        "plan_name": f"Comprehensive Fallback Plan - {datetime.now().strftime('%Y-%m-%d')}",
        "duration_days": req_days,
        "dailyCalories": target_calories,
        "macronutrients": {
            "protein": max(80, int(target_calories * 0.20 / 4)),
            "carbohydrates": max(120, int(target_calories * 0.40 / 4)),  # Lower for diabetes
            "fat": max(55, int(target_calories * 0.35 / 9))
        },
        "breakfast": breakfast,
        "lunch": lunch,
        "dinner": dinner,
        "snacks": snacks,
        "adaptations": adaptations,
        "coaching_notes": f"This comprehensive plan considers your medical conditions ({', '.join(medical_conditions) if medical_conditions else 'general health'}), dietary restrictions, and nutritional needs. For optimal personalization, please regenerate your meal plan when our AI system is available.",
        "medical_considerations": medical_considerations if medical_considerations else ["Standard nutritional guidelines applied", "Consult healthcare provider for specific medical advice"]
    }