from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import os
from models import User, UserProfile
from routers.auth import get_current_user
from database import (
    get_user_by_email,
    get_user_consumption_history,
    get_user_meal_plans,
)
from services.openai_service import robust_openai_call, get_openai_client
from constants import (
    DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE, CHAT_MAX_TOKENS,
    CREATIVE_TEMPERATURE, PRECISE_TEMPERATURE
)

# Create router
router = APIRouter()

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