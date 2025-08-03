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
        print(f"[QuickLogEndpoint] Processing request for user {current_user['email']}")
        print(f"[QuickLogEndpoint] Food data: {food_data}")
        
        # Validate input
        food_name = food_data.get("food_name", "").strip()
        portion = food_data.get("portion", "medium portion").strip()
        
        if not food_name:
            raise HTTPException(status_code=400, detail="Food name is required")
        
        # Use the consumption tracker with EMAIL (consistent with how data is saved)
        result = await consumption_tracker.quick_log_food(
            user_id=current_user["email"],
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
        print(f"[ConsumptionHistoryEndpoint] Getting history for user {current_user['email']}")
        
        # Get consumption history using EMAIL (consistent with how data is saved)
        history = await consumption_tracker.get_consumption_history(
            user_id=current_user["email"],
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
        print(f"[ConsumptionAnalyticsEndpoint] Getting analytics for user {current_user['email']} for {days} days")
        
        # Get consumption analytics using EMAIL (consistent with how data is saved)
        analytics = await consumption_tracker.get_consumption_analytics(
            user_id=current_user["email"],
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
    Get daily insights endpoint - NOW USING SMART AI RECOMMENDATIONS
    """
    try:
        print(f"[DailyInsightsEndpoint] Getting SMART AI insights for user {current_user['email']}")
        
        # Import the smart coaching system
        from services.coaching_system import get_daily_coaching_insights_data
        from database import get_user_by_email
        
        # Get user's complete profile for smart recommendations
        user_data = await get_user_by_email(current_user["email"])
        user_profile = user_data.get("profile", {})
        
        print(f"[DailyInsightsEndpoint] User profile loaded with medical conditions: {user_profile.get('medicalConditions', [])}")
        print(f"[DailyInsightsEndpoint] User medications: {user_profile.get('currentMedications', [])}")
        
        # Use the SMART coaching system that considers full health profile
        smart_insights = await get_daily_coaching_insights_data(current_user["email"], user_profile)
        
        print(f"[DailyInsightsEndpoint] Generated smart insights with {len(smart_insights.get('recommendations', []))} personalized recommendations")
        
        return smart_insights
        
    except Exception as e:
        print(f"[DailyInsightsEndpoint] Smart insights failed, falling back to basic system: {str(e)}")
        
        # Fallback to basic system if smart system fails
        try:
            # Get today's consumption data for fallback using EMAIL (consistent with how data is saved)
            today_analytics = await consumption_tracker.get_consumption_analytics(
                user_id=current_user["email"],
                days=1
            )
            
            today_totals = today_analytics["daily_averages"]
            
            # Basic fallback insights
            fallback_insights = {
                "date": today_analytics["date_range"]["end_date"][:10],
                "goals": {"calories": 2000, "protein": 100, "carbohydrates": 250, "fat": 70},
                "today_totals": today_totals,
                "adherence": {
                    "calories": min(100, (today_totals["calories"] / 2000) * 100),
                    "protein": min(100, (today_totals["protein"] / 100) * 100),
                    "carbohydrates": min(100, (today_totals["carbohydrates"] / 250) * 100),
                    "fat": min(100, (today_totals["fat"] / 70) * 100)
                },
                "meals_logged_today": today_analytics["total_meals"],
                "recommendations": [{
                    "type": "system",
                    "priority": "medium", 
                    "message": "Keep logging your meals for personalized recommendations!",
                    "action": "log_meal"
                }],
                "has_meal_plan": False,
                "latest_meal_plan_date": None
            }
            
            return fallback_insights
            
        except Exception as fallback_error:
            print(f"[DailyInsightsEndpoint] Even fallback failed: {str(fallback_error)}")
            raise HTTPException(status_code=500, detail=f"Failed to get daily insights: {str(fallback_error)}") 