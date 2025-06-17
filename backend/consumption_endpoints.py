"""
AI Diabetes Coach - Consumption API Endpoints
Clean, new implementation with proper error handling and integration
"""

from fastapi import HTTPException, Depends
from typing import Dict, Any, List
import traceback

# Import the new consumption system
from consumption_system import consumption_tracker
from main import get_current_user

async def quick_log_food_endpoint(food_data: dict, current_user: Dict = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Quick log food endpoint - completely rebuilt
    """
    try:
        print(f"[QuickLogEndpoint] Processing request for user {current_user['id']}")
        print(f"[QuickLogEndpoint] Food data: {food_data}")
        
        # Validate input
        food_name = food_data.get("food_name", "").strip()
        portion = food_data.get("portion", "medium portion").strip()
        
        if not food_name:
            raise HTTPException(status_code=400, detail="Food name is required")
        
        # Use the consumption tracker
        result = await consumption_tracker.quick_log_food(
            user_id=current_user["id"],
            food_name=food_name,
            portion=portion
        )
        
        print(f"[QuickLogEndpoint] Successfully logged food: {result}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[QuickLogEndpoint] Error: {str(e)}")
        print(f"[QuickLogEndpoint] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to log food: {str(e)}")

async def get_consumption_history_endpoint(limit: int = 50, current_user: Dict = Depends(get_current_user)) -> List[Dict[str, Any]]:
    """
    Get consumption history endpoint - completely rebuilt
    """
    try:
        print(f"[ConsumptionHistoryEndpoint] Getting history for user {current_user['id']}")
        
        # Get consumption history
        history = await consumption_tracker.get_consumption_history(
            user_id=current_user["id"],
            limit=limit
        )
        
        print(f"[ConsumptionHistoryEndpoint] Retrieved {len(history)} records")
        
        return history
        
    except Exception as e:
        print(f"[ConsumptionHistoryEndpoint] Error: {str(e)}")
        print(f"[ConsumptionHistoryEndpoint] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get consumption history: {str(e)}")

async def get_consumption_analytics_endpoint(days: int = 30, current_user: Dict = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get consumption analytics endpoint - completely rebuilt
    """
    try:
        print(f"[ConsumptionAnalyticsEndpoint] Getting analytics for user {current_user['id']} for {days} days")
        
        # Get consumption analytics
        analytics = await consumption_tracker.get_consumption_analytics(
            user_id=current_user["id"],
            days=days
        )
        
        print(f"[ConsumptionAnalyticsEndpoint] Generated analytics successfully")
        
        return analytics
        
    except Exception as e:
        print(f"[ConsumptionAnalyticsEndpoint] Error: {str(e)}")
        print(f"[ConsumptionAnalyticsEndpoint] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get consumption analytics: {str(e)}")

async def get_daily_insights_endpoint(current_user: Dict = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get daily insights endpoint - integrated with consumption data
    """
    try:
        print(f"[DailyInsightsEndpoint] Getting insights for user {current_user['id']}")
        
        # Get today's consumption data
        today_analytics = await consumption_tracker.get_consumption_analytics(
            user_id=current_user["id"],
            days=1
        )
        
        # Get weekly data for trends
        weekly_analytics = await consumption_tracker.get_consumption_analytics(
            user_id=current_user["id"],
            days=7
        )
        
        # Calculate daily insights
        today_totals = today_analytics["daily_averages"]
        
        # Default daily goals
        goals = {
            "calories": 2000,
            "protein": 100,
            "carbohydrates": 250,
            "fat": 70
        }
        
        # Calculate adherence percentages
        adherence = {
            "calories": min(100, (today_totals["calories"] / goals["calories"]) * 100) if goals["calories"] > 0 else 0,
            "protein": min(100, (today_totals["protein"] / goals["protein"]) * 100) if goals["protein"] > 0 else 0,
            "carbohydrates": min(100, (today_totals["carbohydrates"] / goals["carbohydrates"]) * 100) if goals["carbohydrates"] > 0 else 0,
            "fat": min(100, (today_totals["fat"] / goals["fat"]) * 100) if goals["fat"] > 0 else 0
        }
        
        # Generate recommendations
        recommendations = []
        
        if today_totals["calories"] < goals["calories"] * 0.8:
            recommendations.append({
                "type": "nutrition",
                "priority": "medium",
                "message": "You're below your daily calorie target. Consider adding a healthy snack.",
                "action": "log_meal"
            })
        
        if today_totals["protein"] < goals["protein"] * 0.8:
            recommendations.append({
                "type": "nutrition",
                "priority": "high",
                "message": "Protein intake is low. Include lean proteins in your next meal.",
                "action": "add_protein"
            })
        
        if weekly_analytics["adherence_stats"]["diabetes_suitable_percentage"] < 70:
            recommendations.append({
                "type": "health",
                "priority": "high",
                "message": "Focus on diabetes-friendly food choices this week.",
                "action": "meal_planning"
            })
        
        insights = {
            "date": today_analytics["date_range"]["end_date"][:10],
            "goals": goals,
            "today_totals": today_totals,
            "adherence": adherence,
            "meals_logged_today": today_analytics["total_meals"],
            "weekly_stats": {
                "total_meals": weekly_analytics["total_meals"],
                "diabetes_suitable_percentage": weekly_analytics["adherence_stats"]["diabetes_suitable_percentage"],
                "average_daily_calories": weekly_analytics["daily_averages"]["calories"]
            },
            "recommendations": recommendations,
            "has_meal_plan": False,  # This would be integrated with meal plan system
            "latest_meal_plan_date": None
        }
        
        print(f"[DailyInsightsEndpoint] Generated insights successfully")
        
        return insights
        
    except Exception as e:
        print(f"[DailyInsightsEndpoint] Error: {str(e)}")
        print(f"[DailyInsightsEndpoint] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get daily insights: {str(e)}") 