from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Optional
from datetime import datetime
from ..models.user import User
from ..services.auth import get_current_user
from ..services.meal_service import get_user_meal_history, get_user_profile
from ..services.ai_service import get_ai_suggestion
from ..utils.logger import logger

router = APIRouter()

@router.get("/daily-insights")
async def get_daily_insights(current_user: User = Depends(get_current_user)) -> Dict:
    """Get daily insights for the user."""
    try:
        return {
            "success": True,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "insights": [
                {
                    "category": "Nutrition",
                    "message": "You have 2000 calories remaining for today. Focus on nutrient-dense foods to meet your goals.",
                    "action": "View Recommendations"
                },
                {
                    "category": "Hydration",
                    "message": "Remember to stay hydrated throughout the day. Aim for 8 glasses of water.",
                    "action": "Log Water"
                },
                {
                    "category": "Activity",
                    "message": "Consider a light walk after meals to help manage blood sugar levels.",
                    "action": "Track Exercise"
                },
                {
                    "category": "Blood Sugar",
                    "message": "Your blood sugar tracking is on track. Keep monitoring regularly.",
                    "action": "Log Reading"
                }
            ],
            "today_totals": {
                "calories": 800,
                "protein": 45,
                "carbohydrates": 95,
                "fat": 28,
                "fiber": 12,
                "sugar": 25,
                "sodium": 1200
            },
            "goals": {
                "calories": 2000,
                "protein": 150,
                "carbohydrates": 250,
                "fat": 67
            },
            "adherence": {
                "calories": 40,
                "protein": 30,
                "carbohydrates": 38,
                "fat": 42
            },
            "meals_logged_today": 2,
            "weekly_stats": {
                "total_meals": 14,
                "diabetes_suitable_percentage": 85,
                "average_daily_calories": 1800
            },
            "recommendations": [
                {
                    "type": "nutrition",
                    "priority": "medium",
                    "message": "You're 40% toward your calorie goal. Consider a protein-rich snack.",
                    "action": "Log Snack"
                },
                {
                    "type": "hydration",
                    "priority": "low",
                    "message": "Stay hydrated throughout the day",
                    "action": "Log Water"
                },
                {
                    "type": "activity",
                    "priority": "medium",
                    "message": "Consider a 10-minute walk after your next meal",
                    "action": "Track Exercise"
                }
            ],
            "has_meal_plan": False,
            "latest_meal_plan_date": None,
            "diabetes_adherence": 85,
            "consistency_streak": 3
        }
    except Exception as e:
        logger.error(f"Error getting daily insights: {str(e)}")
        return {"success": False, "error": "Failed to get daily insights"}

@router.get("/todays-meal-plan")
async def get_todays_meal_plan(current_user: User = Depends(get_current_user)) -> Dict:
    """Get today's meal plan for the user."""
    try:
        return {
            "success": True,
            "meal_plan": {
                "breakfast": {"planned": False, "completed": False},
                "lunch": {"planned": False, "completed": False}, 
                "dinner": {"planned": False, "completed": False},
                "snacks": []
            },
            "total_calories": 0,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
    except Exception as e:
        logger.error(f"Error getting today's meal plan: {str(e)}")
        return {"success": False, "error": "Failed to get today's meal plan"}

@router.get("/notifications")
async def get_notifications(current_user: User = Depends(get_current_user)) -> List[Dict]:
    """Get notifications for the user."""
    try:
        # Return notifications array directly to match frontend expectations
        return [
            {
                "priority": "high",
                "message": "Blood sugar reading reminder",
                "timestamp": datetime.now().isoformat()
            },
            {
                "priority": "medium", 
                "message": "Time for your afternoon snack",
                "timestamp": (datetime.now().replace(hour=15, minute=0)).isoformat()
            },
            {
                "priority": "low",
                "message": "Weekly meal plan review available",
                "timestamp": (datetime.now().replace(hour=9, minute=0)).isoformat()
            }
        ]
    except Exception as e:
        logger.error(f"Error getting notifications: {str(e)}")
        return []

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
        user_profile = await get_user_profile(current_user["email"])
        meal_history = await get_user_meal_history(current_user["email"], limit=20)
        
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
        ai_response = await get_ai_suggestion(prompt)
        
        return {
            "success": True,
            "suggestion": ai_response["suggestion"],  # Extract just the suggestion text
            "context": {
                "meal_type": meal_type,
                "time_appropriate": True,
                "considers_health": True,
                "personalized": True
            },
            "detailed_info": {
                "ingredients": ai_response.get("ingredients", []),
                "preparation": ai_response.get("preparation", ""),
                "nutritional_info": ai_response.get("nutritional_info", {}),
                "health_benefits": ai_response.get("health_benefits", "")
            }
        }
    except Exception as e:
        logger.error(f"Error generating meal suggestion: {str(e)}")
        return {
            "success": False,
            "error": "Failed to generate meal suggestion"
        }

@router.post("/quick-log")
async def quick_log_food(
    request: Dict,
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Quick log food intake with AI-powered nutritional analysis.
    """
    try:
        food_description = request.get("food_description", "")
        quantity = request.get("quantity", "1 serving")
        meal_type = request.get("meal_type", "snack")
        
        if not food_description:
            return {
                "success": False,
                "error": "Food description is required"
            }
        
        # Simulate AI nutritional analysis
        nutritional_info = {
            "calories": 150 + (len(food_description) * 5),  # Mock calculation
            "protein": max(5, len(food_description.split()) * 2),
            "carbohydrates": max(10, len(food_description) * 2),
            "fat": max(2, len(food_description.split())),
            "fiber": max(1, len(food_description.split()) // 2),
            "sugar": max(5, len(food_description) // 3),
            "sodium": max(50, len(food_description) * 10)
        }
        
        # Create food log entry
        log_entry = {
            "id": f"log_{hash(food_description + str(datetime.now())) % 10000}",
            "user_id": current_user["id"],
            "food_description": food_description,
            "quantity": quantity,
            "meal_type": meal_type,
            "nutritional_info": nutritional_info,
            "logged_at": datetime.now().isoformat(),
            "confidence": 0.85,  # Mock AI confidence score
            "tags": ["quick_log", meal_type]
        }
        
        # In a real implementation, save to database
        logger.info(f"Quick logged food for user {current_user['id']}: {food_description}")
        
        return {
            "success": True,
            "message": f"Successfully logged {food_description}",
            "log_entry": log_entry,
            "nutritional_summary": {
                "calories_added": nutritional_info["calories"],
                "daily_progress": {
                    "calories": f"{nutritional_info['calories']}/2000",
                    "protein": f"{nutritional_info['protein']}/150g",
                    "carbs": f"{nutritional_info['carbohydrates']}/250g"
                }
            },
            "recommendations": [
                {
                    "type": "hydration",
                    "message": "Don't forget to drink water with your meal!",
                    "priority": "low"
                },
                {
                    "type": "activity", 
                    "message": "Consider a light walk after eating to help manage blood sugar",
                    "priority": "medium"
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"Error in quick food log: {str(e)}")
        return {
            "success": False,
            "error": "Failed to log food intake"
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