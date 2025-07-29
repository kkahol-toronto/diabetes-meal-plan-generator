"""
Consumption Analysis & Meal Plan Recalibration System

This module provides intelligent analysis of user consumption patterns and 
dynamically recalibrates meal plans based on actual eating behavior.

Key Functions:
- generate_consumption_aware_meal_plan: Creates meal plans that adapt to actual consumption
- trigger_meal_plan_recalibration: Comprehensive meal plan updates after food logging
- generate_fresh_adaptive_meal_plan: AI-powered adaptive meal planning
- analyze_consumption_vs_plan: Analyzes what was consumed vs. planned
- sanitize_vegetarian_meal: Ensures dietary restriction compliance
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import os
import random
import re
from services.openai_service import get_openai_client
from constants import (
    CREATIVE_TEMPERATURE, MEAL_SUGGESTION_MAX_TOKENS, DEFAULT_CALORIE_TARGET
)
from utils import get_today_utc_boundaries, filter_today_records

# Import database functions that will be used
# These will be imported from database when the module is used
# from database import get_user_meal_plans, save_meal_plan, get_user_consumption_history


async def get_today_consumption_records_async(user_email: str, user_timezone: str = "UTC") -> List[Dict[str, Any]]:
    """
    Get today's consumption records for a user using proper timezone boundaries.
    """
    try:
        # Import here to avoid circular imports
        from database import get_user_consumption_history
        
        # Get recent consumption history (last 3 days to ensure we have today's data)
        recent_consumption = await get_user_consumption_history(user_email, limit=200)
        
        # Filter to today's records using timezone-aware boundaries
        today_records = filter_today_records(recent_consumption, user_timezone)
        
        return today_records
        
    except Exception as e:
        print(f"Error getting today's consumption records: {e}")
        return []


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


def sanitize_vegetarian_meal(meal_text: str, is_vegetarian: bool, no_eggs: bool) -> str:
    """
    Ensure meal is vegetarian and egg-free with strong enforcement.
    Also validates against corrupted or nonsensical meal data.
    """
    if not meal_text:
        return "Vegetarian meal option"
    
    meal_lower = meal_text.lower().strip()
    
    # Check for corrupted or nonsensical meal patterns
    def is_corrupted_meal(text: str) -> bool:
        """Check if meal text is corrupted or nonsensical"""
        suspicious_patterns = [
            r'^\d+\/\d+\s+\w+\s+fruit',  # "1/2 Lindt fruit" pattern
            r'^[0-9]+\/[0-9]+',          # Starts with fractions
            r'lindt',                     # Brand names that don't make sense as meals
            r'^[0-9]+\s+(g|ml|oz|cups?|tbsp|tsp)\s*$',  # Just quantities
            r'^[\d\s\/\-\.]+$',          # Only numbers and punctuation
            r'^[a-z]{1,2}$',             # Single letters or very short nonsense
            r'^\s*$',                    # Empty or whitespace only
        ]
        return any(re.search(pattern, text.lower()) for pattern in suspicious_patterns)
    
    # If corrupted, return a safe default
    if is_corrupted_meal(meal_text):
        print(f"[sanitize_vegetarian_meal] Detected corrupted meal text: '{meal_text}' - replacing with safe option")
        return "Healthy balanced meal option"
    
    # Check for non-vegetarian ingredients
    non_veg_keywords = ['chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'turkey', 'lamb', 'meat', 'seafood', 'shrimp', 'bacon', 'ham', 'duck', 'goose', 'crab', 'lobster', 'cod', 'tilapia', 'halibut', 'anchovy', 'sardine']
    
    # ENHANCED: Comprehensive egg detection including all egg-containing dishes and ingredients
    egg_keywords = [
        # Direct egg references
        'egg', 'eggs', 'egg white', 'egg yolk', 'whole egg', 'beaten egg', 'raw egg',
        # Egg-based dishes
        'omelet', 'omelette', 'scrambled', 'poached', 'fried egg', 'boiled egg', 'hard-boiled', 'soft-boiled',
        'egg sandwich', 'breakfast sandwich', 'egg muffin', 'egg wrap', 'egg salad', 'deviled egg',
        'eggs benedict', 'scotch egg', 'pickled egg', 'egg drop soup', 'egg roll',
        # Egg-containing foods and preparations  
        'mayonnaise', 'mayo', 'hollandaise', 'custard', 'meringue', 'eggnog', 'zabaglione',
        'french toast', 'pancake', 'waffle', 'crepe', 'quiche', 'frittata', 'strata', 'souffle',
        'carbonara', 'caesar dressing', 'caesar salad', 'aioli', 'tartar sauce', 'thousand island',
        # Baked goods that typically contain eggs
        'muffin', 'cake', 'cupcake', 'cookie', 'brownie', 'pastry', 'donut', 'danish', 'croissant',
        'brioche', 'challah', 'bagel', 'english muffin', 'scone', 'biscuit',
        # Other egg-containing items
        'pasta carbonara', 'egg noodles', 'fresh pasta', 'homemade pasta', 'batter', 'tempura',
        'fried chicken', 'breaded', 'coated', 'dumplings', 'gnocchi', 'egg bread'
    ]
    
    if is_vegetarian and any(keyword in meal_lower for keyword in non_veg_keywords):
        print(f"[sanitize_vegetarian_meal] Replacing non-vegetarian meal: '{meal_text}'")
        return "Vegetarian lentil curry with brown rice and steamed vegetables"
    
    if no_eggs and any(keyword in meal_lower for keyword in egg_keywords):
        print(f"[sanitize_vegetarian_meal] CRITICAL: Replacing egg-containing meal: '{meal_text}' - found egg ingredient")
        # Return a safe, guaranteed egg-free option
        return "Vegetarian quinoa bowl with roasted vegetables and tahini dressing"
    
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


async def apply_intelligent_adaptations(meal_plan: dict, consumption_analysis: dict, remaining_meals: list, user_profile: dict) -> dict:
    """
    Simplified adaptation function - now replaced by generate_consumption_aware_meal_plan.
    This function is kept for backward compatibility but simply returns the meal plan.
    """
    print(f"[apply_intelligent_adaptations] Legacy function called - use generate_consumption_aware_meal_plan instead")
    return meal_plan


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


async def trigger_meal_plan_recalibration(user_email: str, user_profile: dict):
    """
    Comprehensive meal plan recalibration system that triggers after every food log.
    Ensures dietary restrictions are respected and meal plan is updated immediately.
    """
    try:
        print(f"[RECALIBRATION] Starting meal plan recalibration for user {user_email}")
        
        # Import here to avoid circular imports
        from database import get_user_meal_plans, save_meal_plan
        
        # Get today's consumption including the new log
        user_timezone = user_profile.get("timezone", "UTC")
        today_consumption = await get_today_consumption_records_async(user_email, user_timezone=user_timezone)
        
        # Calculate calories consumed so far
        calories_consumed = sum(r.get("nutritional_info", {}).get("calories", 0) for r in today_consumption)
        
        # Get user's dietary restrictions and preferences
        dietary_restrictions = user_profile.get('dietaryRestrictions', [])
        dietary_features = user_profile.get('dietaryFeatures', []) or user_profile.get('diet_features', [])
        allergies = user_profile.get('allergies', [])
        diet_type = user_profile.get('dietType', [])
        food_preferences = user_profile.get('foodPreferences', [])
        strong_dislikes = user_profile.get('strongDislikes', [])
        
        # Handle empty or invalid calorie target
        calorie_target = user_profile.get('calorieTarget', DEFAULT_CALORIE_TARGET)
        if not calorie_target or calorie_target == '':
            calorie_target = DEFAULT_CALORIE_TARGET
        target_calories = int(calorie_target)
        remaining_calories = max(0, target_calories - calories_consumed)
        
        # FIXED: Comprehensive dietary restriction detection including dietaryFeatures
        # Check if user is vegetarian or has restrictions from ALL possible sources
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
        
        print(f"[RECALIBRATION] User dietary profile: vegetarian={is_vegetarian}, no_eggs={no_eggs}")
        print(f"[RECALIBRATION] Cuisine preferences: {diet_type}")
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
        
        # Build restriction warnings for AI with enhanced detection
        restriction_warnings = []
        if is_vegetarian:
            restriction_warnings.append("VEGETARIAN - Exclude meat, poultry, fish, and seafood. Plant-based proteins preferred")
        if no_eggs:
            restriction_warnings.append("EGG-FREE - Avoid eggs and egg-containing dishes like omelets, quiche, and french toast")
        if is_vegetarian and no_eggs:
            restriction_warnings.append("VEGETARIAN + EGG-FREE - Requires both meat-free and egg-free options")
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
                
            response = get_openai_client().chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=CREATIVE_TEMPERATURE,  # Higher temperature for more creativity/variety
                max_tokens=MEAL_SUGGESTION_MAX_TOKENS
            )

            ai_content = response.choices[0].message.content
            if not ai_content:
                raise Exception("No content in AI response")
                
            start_idx = ai_content.find('{')
            end_idx = ai_content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
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