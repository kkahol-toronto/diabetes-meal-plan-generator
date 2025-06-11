from datetime import datetime, timedelta
from typing import Dict, Any
import logging
from database import (
    interactions_container,
    user_container,
    get_user_by_email,
    get_consumption_analytics
)
import traceback

logger = logging.getLogger(__name__)

async def calculate_adjusted_goals(user_id: str, current_goals: Dict[str, Any], yesterday_consumption: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate adjusted goals based on yesterday's consumption.
    Returns a dictionary with adjusted goals for calories and macros.
    """
    # Get current goals
    current_calories = int(current_goals.get("calorieTarget", 2000))
    current_macros = current_goals.get("macroGoals", {
        "protein": 100,
        "carbs": 250,
        "fat": 66
    })

    # Get yesterday's totals
    yesterday_calories = yesterday_consumption.get("total_calories", 0)
    yesterday_macros = yesterday_consumption.get("total_macronutrients", {
        "protein": 0,
        "carbohydrates": 0,
        "fat": 0
    })

    # Calculate adjustments (simple percentage-based adjustment)
    # If over/under by more than 10%, adjust by 5%
    calorie_diff_percent = (yesterday_calories - current_calories) / current_calories
    adjustment_factor = 0.05 if abs(calorie_diff_percent) > 0.1 else 0

    # Calculate new goals
    new_calories = int(current_calories * (1 - adjustment_factor if calorie_diff_percent > 0 else 1 + adjustment_factor))
    
    # Adjust macros proportionally
    new_macros = {
        "protein": int(current_macros["protein"] * (1 - adjustment_factor if calorie_diff_percent > 0 else 1 + adjustment_factor)),
        "carbs": int(current_macros["carbs"] * (1 - adjustment_factor if calorie_diff_percent > 0 else 1 + adjustment_factor)),
        "fat": int(current_macros["fat"] * (1 - adjustment_factor if calorie_diff_percent > 0 else 1 + adjustment_factor))
    }

    return {
        "calorieTarget": str(new_calories),
        "macroGoals": new_macros
    }

async def save_adjusted_goals(user_id: str, adjusted_goals: Dict[str, Any]):
    """
    Save adjusted goals to the user's profile.
    """
    try:
        # Get user document
        user_doc = await get_user_by_email(user_id)
        if not user_doc:
            logger.error(f"User {user_id} not found")
            return False

        # Ensure profile exists
        if "profile" not in user_doc:
            user_doc["profile"] = {}

        # Update goals
        user_doc["profile"]["calorieTarget"] = adjusted_goals["calorieTarget"]
        user_doc["profile"]["macroGoals"] = adjusted_goals["macroGoals"]

        # Add adjusted goals history
        if "adjusted_goals" not in user_doc["profile"]:
            user_doc["profile"]["adjusted_goals"] = {}

        # Store today's adjusted goals
        today = datetime.utcnow().date().isoformat()
        user_doc["profile"]["adjusted_goals"][today] = adjusted_goals

        # Save updated document
        user_container.replace_item(item=user_doc["id"], body=user_doc)
        logger.info(f"Successfully saved adjusted goals for user {user_id}")
        return True

    except Exception as e:
        logger.error(f"Error saving adjusted goals for user {user_id}: {str(e)}")
        return False

async def recalibrate_user_goals(user_id: str) -> bool:
    """
    Recalibrate goals for a single user based on their consumption data.
    Returns True if successful, False otherwise.
    """
    try:
        # Get user document
        user_doc = await get_user_by_email(user_id)
        if not user_doc or "profile" not in user_doc:
            print(f"User profile not found for user_id: {user_id}")
            return False

        # Get current goals
        current_goals = user_doc["profile"].get("goals", {})
        if not current_goals:
            print(f"No current goals found for user_id: {user_id}")
            return False

        # Get yesterday's consumption data
        yesterday = datetime.utcnow().date() - timedelta(days=1)
        consumption_data = await get_consumption_analytics(user_id, yesterday)
        
        if not consumption_data:
            print(f"No consumption data found for user_id: {user_id} on {yesterday}")
            return False

        # Calculate adjusted goals
        adjusted_goals = await calculate_adjusted_goals(user_id, current_goals, consumption_data)
        if not adjusted_goals:
            print(f"Failed to calculate adjusted goals for user_id: {user_id}")
            return False

        # Save adjusted goals
        success = await save_adjusted_goals(user_id, adjusted_goals)
        if not success:
            print(f"Failed to save adjusted goals for user_id: {user_id}")
            return False

        # Store adjusted goals under tomorrow's date
        tomorrow = datetime.utcnow().date() + timedelta(days=1)
        if "adjusted_goals" not in user_doc["profile"]:
            user_doc["profile"]["adjusted_goals"] = {}
        user_doc["profile"]["adjusted_goals"][str(tomorrow)] = adjusted_goals
        
        # Update user document
        await user_container.replace_item(item=user_doc["id"], body=user_doc)
        print(f"Successfully recalibrated goals for user_id: {user_id}")
        return True

    except Exception as e:
        print(f"Error recalibrating goals for user_id {user_id}: {str(e)}")
        return False

async def recalibrate_all_users_goals():
    """
    Recalibrate goals for all users.
    """
    try:
        # Get all users
        query = "SELECT c.id, c.email FROM c WHERE c.type = 'user'"
        users = list(user_container.query_items(query=query, enable_cross_partition_query=True))

        success_count = 0
        for user in users:
            if await recalibrate_user_goals(user["email"]):
                success_count += 1

        logger.info(f"Successfully recalibrated goals for {success_count} out of {len(users)} users")
        return success_count

    except Exception as e:
        logger.error(f"Error in recalibrate_all_users_goals: {str(e)}")
        return 0 