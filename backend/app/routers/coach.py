from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Optional
from datetime import datetime
from ..models.user import User
from ..services.auth import get_current_user
from ..services.meal_service import get_user_meal_history, get_user_profile
from ..services.ai_service import get_ai_suggestion
from ..utils.logger import logger

router = APIRouter()

@router.post("/meal-suggestion")
async def get_meal_suggestion(
    request: Dict,
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Generate AI-powered meal suggestions based on user's query context, preferences, and nutritional needs.
    """
    try:
        meal_type = request.get("meal_type", "")
        remaining_calories = request.get("remaining_calories", 500)
        preferences = request.get("preferences", "")
        context = request.get("context", {})
        
        # Get user's profile and meal history
        user_profile = await get_user_profile(current_user.email)
        meal_history = await get_user_meal_history(current_user.email, limit=20)
        
        # Analyze meal patterns and preferences
        meal_patterns = analyze_meal_patterns(meal_history)
        dietary_restrictions = user_profile.get("dietary_restrictions", [])
        health_conditions = user_profile.get("health_conditions", [])
        
        # Build context-aware prompt
        prompt = build_meal_suggestion_prompt(
            meal_type=meal_type,
            remaining_calories=remaining_calories,
            meal_patterns=meal_patterns,
            dietary_restrictions=dietary_restrictions,
            health_conditions=health_conditions,
            context=context,
            preferences=preferences
        )
        
        # Get AI suggestion
        suggestion = await get_ai_suggestion(prompt)
        
        return {
            "success": True,
            "suggestion": suggestion,
            "context": {
                "meal_type": meal_type,
                "time_appropriate": True,
                "considers_health": True,
                "personalized": True
            }
        }
    except Exception as e:
        logger.error(f"Error generating meal suggestion: {str(e)}")
        return {
            "success": False,
            "error": "Failed to generate meal suggestion"
        }

def build_meal_suggestion_prompt(
    meal_type: str,
    remaining_calories: int,
    meal_patterns: Dict,
    dietary_restrictions: List[str],
    health_conditions: List[str],
    context: Dict,
    preferences: str
) -> str:
    """
    Build a context-aware prompt for meal suggestions.
    """
    query_context = context.get("query_context", "")
    current_hour = context.get("current_hour", 0)
    is_late_meal = context.get("is_late_meal", False)
    todays_meals = context.get("todays_meals", [])
    
    # Build a natural language prompt based on all available context
    prompt_parts = [
        f'Based on the user\'s query "{query_context}", suggest a {meal_type} that:',
        f"1. Fits within {remaining_calories} remaining calories",
    ]
    
    if dietary_restrictions:
        prompt_parts.append(f"2. Considers their dietary restrictions: {', '.join(dietary_restrictions)}")
    
    if health_conditions:
        prompt_parts.append(f"3. Is appropriate for their health conditions: {', '.join(health_conditions)}")
    
    if todays_meals:
        prompt_parts.append(f"4. Avoids repetition with today's meals: {', '.join([m['name'] for m in todays_meals])}")
    
    prompt_parts.extend([
        "5. " + ("Provides a lighter option since it's a late meal" if is_late_meal else "Provides a satisfying portion"),
        f"6. Matches their usual meal patterns for {meal_type}",
    ])
    
    if preferences:
        prompt_parts.append(f"7. {preferences}")
    
    prompt_parts.extend([
        "\nInclude:",
        "- Specific ingredients and portions",
        "- Brief preparation instructions",
        "- Nutritional breakdown",
        "- Health benefits",
        "- Any relevant tips or modifications"
    ])
    
    return "\n".join(prompt_parts)

def analyze_meal_patterns(meal_history: List[Dict]) -> Dict:
    """
    Analyze user's meal patterns to provide more personalized suggestions.
    """
    patterns = {
        "breakfast": [],
        "lunch": [],
        "dinner": [],
        "snack": []
    }
    
    # Group meals by type and analyze patterns
    for meal in meal_history:
        meal_type = meal.get("meal_type", "").lower()
        if meal_type in patterns:
            # Check if this meal already exists in patterns
            meal_entry = next(
                (m for m in patterns[meal_type] if m["name"] == meal["food_name"]),
                None
            )
            
            if meal_entry:
                meal_entry["frequency"] += 1
            else:
                patterns[meal_type].append({
                    "name": meal["food_name"],
                    "frequency": 1,
                    "calories": meal.get("nutritional_info", {}).get("calories", 0),
                    "last_consumed": meal.get("timestamp")
                })
    
    return patterns 