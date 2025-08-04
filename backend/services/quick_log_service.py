"""
Quick Log Service
Optimized service for fast food logging with minimal overhead.
Extracted from main.py to improve performance and reduce response times.
"""

import json
import traceback
from datetime import datetime
from typing import Dict, Any, Optional

from services.openai_service import robust_openai_call
# Dynamic calibration service will be imported when needed to avoid circular imports
from services.database_service import save_consumption_record_with_cache_invalidation
from utils import filter_today_records


async def quick_log_food_optimized(
    food_data: dict,
    user_email: str,
    user_profile: dict
) -> Dict[str, Any]:
    """
    Optimized quick food logging with streamlined AI analysis and meal plan updates.
    
    Args:
        food_data: Food information from user
        user_email: User's email identifier  
        user_profile: User's profile data
        
    Returns:
        Dict containing success status and relevant data
    """
    try:
        food_name = food_data.get("food_name", "").strip()
        portion = food_data.get("portion", "medium portion").strip()
        
        if not food_name:
            return {"success": False, "error": "Food name is required"}
        
        print(f"[quick_log_optimized] Processing {food_name} for {user_email}")
        
        # Streamlined AI nutritional analysis
        analysis_data = await _get_nutrition_analysis(food_name, portion)
        
        # Determine meal type efficiently
        meal_type = _determine_meal_type(food_data, user_profile)
        
        # Prepare consumption data
        consumption_data = {
            "food_name": analysis_data.get("food_name", food_name),
            "estimated_portion": analysis_data.get("estimated_portion", portion),
            "nutritional_info": analysis_data.get("nutritional_info", {}),
            "medical_rating": analysis_data.get("medical_rating", {}),
            "image_analysis": analysis_data.get("analysis_notes", f"Quick log entry for {food_name}"),
            "image_url": None,
            "meal_type": meal_type
        }
        
        # Save consumption record with cache invalidation
        consumption_record = await save_consumption_record_with_cache_invalidation(user_email, consumption_data, meal_type=meal_type)
        print(f"[quick_log_optimized] Saved record: {consumption_record['id']}")
        
        # Trigger enhanced dynamic meal plan calibration
        try:
            from services.dynamic_meal_calibration_service import dynamic_calibration_service
            
            # Prepare newly logged food data for calibration analysis
            newly_logged_food = {
                "food_name": analysis_data.get("food_name", food_name),
                "nutritional_info": analysis_data.get("nutritional_info", {}),
                "meal_type": meal_type,
                "logged_at": datetime.utcnow().isoformat()
            }
            
            calibration_result = await dynamic_calibration_service.trigger_dynamic_calibration(
                user_email, user_profile, newly_logged_food
            )
            
            meal_plan_updated = calibration_result.get("calibration_performed", False)
            remaining_calories = calibration_result.get("remaining_targets", {}).get("calories", 0)
            calibration_insights = calibration_result.get("calibration_insights", {})
            
            print(f"[quick_log_optimized] Dynamic calibration result: {calibration_result.get('calibration_reason', 'no_calibration')}")
            
        except Exception as e:
            print(f"[quick_log_optimized] Dynamic calibration failed: {e}")
            meal_plan_updated = False
            remaining_calories = 0
            calibration_insights = {}
        
        return {
            "success": True,
            "message": f"Successfully logged {analysis_data.get('food_name', food_name)}",
            "consumption_record_id": consumption_record["id"],
            "analysis": analysis_data,
            "nutritional_summary": {
                "calories": analysis_data.get("nutritional_info", {}).get("calories", 0),
                "carbohydrates": analysis_data.get("nutritional_info", {}).get("carbohydrates", 0),
                "protein": analysis_data.get("nutritional_info", {}).get("protein", 0),
                "fat": analysis_data.get("nutritional_info", {}).get("fat", 0)
            },
            "diabetes_rating": analysis_data.get("medical_rating", {}).get("diabetes_suitability", "medium"),
            "meal_plan_updated": meal_plan_updated,
            "remaining_calories": remaining_calories,
            "dynamic_calibration": {
                "calibration_performed": meal_plan_updated,
                "calibration_insights": calibration_insights.get("calibration_summary", "") if 'calibration_insights' in locals() else "",
                "next_meal_guidance": calibration_insights.get("next_meal_guidance", "") if 'calibration_insights' in locals() else "",
                "health_recommendations": calibration_insights.get("health_recommendations", []) if 'calibration_insights' in locals() else []
            }
        }
        
    except Exception as e:
        print(f"[quick_log_optimized] Error: {str(e)}")
        return {"success": False, "error": f"Failed to log food: {str(e)}"}


async def _get_nutrition_analysis(food_name: str, portion: str) -> Dict[str, Any]:
    """Get AI nutritional analysis with optimized prompt and error handling."""
    
    # Streamlined prompt for faster processing
    prompt = f"""Analyze: {food_name} ({portion})

Return JSON with this structure:
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
        "recommended_frequency": "daily/weekly/occasional"
    }},
    "analysis_notes": "Brief diabetes assessment"
}}

Be fast and accurate. Only return valid JSON."""

    # Fallback data for API failures
    fallback_data = {
        "food_name": food_name,
        "estimated_portion": portion,
        "nutritional_info": {
            "calories": 200, "carbohydrates": 25, "protein": 10,
            "fat": 8, "fiber": 3, "sugar": 5, "sodium": 300
        },
        "medical_rating": {
            "diabetes_suitability": "medium",
            "glycemic_impact": "medium", 
            "recommended_frequency": "weekly"
        },
        "analysis_notes": f"Nutritional estimate for {food_name}"
    }
    
    try:
        api_result = await robust_openai_call(
            messages=[
                {"role": "system", "content": "You are a nutrition analysis expert. Provide fast, accurate nutritional estimates."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,  # Reduced for faster response
            temperature=0.3,
            max_retries=2,   # Reduced retries for faster response
            timeout=20,      # Shorter timeout
            context="quick_log_nutrition"
        )
        
        if api_result["success"]:
            # Quick JSON extraction
            content = api_result["content"]
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx]
                return json.loads(json_str)
                
    except Exception as e:
        print(f"[nutrition_analysis] API error: {e}")
    
    return fallback_data


def _determine_meal_type(food_data: dict, user_profile: dict) -> str:
    """Efficiently determine meal type based on time and user input."""
    
    # Check if explicitly provided
    provided_meal_type = food_data.get("meal_type", "").strip().lower()
    if provided_meal_type in ["breakfast", "lunch", "dinner", "snack"]:
        return provided_meal_type
    
    # Determine from current time
    current_hour = datetime.utcnow().hour
    
    # Simple time-based logic (can be enhanced with timezone later)
    if 5 <= current_hour < 11:
        return "breakfast"
    elif 11 <= current_hour < 16:
        return "lunch" 
    elif 16 <= current_hour < 22:
        return "dinner"
    else:
        return "snack"