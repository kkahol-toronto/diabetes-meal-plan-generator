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
    try:
        # Get user document to check for weekly adjusted goals
        user_doc = await get_user_by_email(user_id)
        if not user_doc or "profile" not in user_doc:
            logger.error(f"User profile not found for user_id: {user_id}")
            return None

        # Get current week's ISO week key
        current_week = get_iso_week_key(datetime.utcnow())
        
        # Check if we have weekly adjusted goals for current week
        weekly_goals = user_doc["profile"].get("weekly_adjusted_goals", {}).get(current_week)
        
        # Use weekly goals as baseline if available, otherwise use current goals
        baseline_goals = weekly_goals if weekly_goals else current_goals

        # Get current goals from baseline
        current_calories = int(baseline_goals.get("calorieTarget", 2000))
        current_macros = baseline_goals.get("macroGoals", {
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

    except Exception as e:
        logger.error(f"Error calculating adjusted goals: {str(e)}")
        return None

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
    """Recalibrate goals for a specific user based on their consumption data."""
    try:
        # Get user document
        user_doc = await get_user_by_email(user_id)
        if not user_doc:
            logging.error(f"User document not found for user_id: {user_id}")
            return False
            
        # Get current goals
        current_goals = user_doc.get("profile", {}).get("goals", {})
        if not current_goals:
            logging.error(f"No current goals found for user_id: {user_id}")
            return False
            
        # Get yesterday's consumption data
        yesterday = datetime.utcnow().date() - timedelta(days=1)
        yesterday_datetime = datetime.combine(yesterday, datetime.min.time())
        consumption_data = await get_consumption_analytics(user_id, 1)
        if not consumption_data:
            logging.error(f"Failed to get consumption analytics for user_id: {user_id}")
            return False
            
        # Map consumption_data keys to expected daily_averages keys
        daily_averages = {
            "calories": consumption_data.get("total_calories", 0),
            "protein": consumption_data.get("total_macronutrients", {}).get("protein", 0),
            "carbs": consumption_data.get("total_macronutrients", {}).get("carbohydrates", 0),
            "fat": consumption_data.get("total_macronutrients", {}).get("fat", 0),
        }
            
        # Calculate adjusted goals using the sync version
        adjusted_goals = calculate_adjusted_goals(user_doc, daily_averages)
        if not adjusted_goals:
            logging.error(f"Failed to calculate adjusted goals for user_id: {user_id}")
            return False
            
        # Save adjusted goals back to user document
        user_doc["profile"]["goals"] = adjusted_goals
        success = await save_adjusted_goals(user_id, adjusted_goals)
        if not success:
            logging.error(f"Failed to save adjusted goals for user_id: {user_id}")
            return False
            
        logging.info(f"Successfully recalibrated goals for user_id: {user_id}")
        return True
        
    except Exception as e:
        logging.error(f"Error recalibrating goals for user_id {user_id}: {str(e)}")
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

def get_iso_week_key(date: datetime) -> str:
    """
    Get ISO week key in format YYYY-W## for a given date.
    """
    return date.strftime("%Y-W%V")

async def get_weekly_consumption_average(user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """
    Calculate weekly average consumption for a user between start_date and end_date.
    """
    try:
        # Get consumption records for the week
        query = (
            "SELECT c.nutritional_info FROM c WHERE c.type = 'consumption_record' "
            f"AND c.user_id = '{user_id}' "
            f"AND c.timestamp >= '{start_date.isoformat()}' AND c.timestamp < '{end_date.isoformat()}'"
        )
        records = list(interactions_container.query_items(query=query, enable_cross_partition_query=True))
        
        if not records:
            return None

        # Calculate totals
        total_calories = 0
        total_macros = {"protein": 0, "carbohydrates": 0, "fat": 0}
        days_with_data = 0

        for rec in records:
            ni = rec.get("nutritional_info", {})
            if ni:
                total_calories += ni.get("calories", 0)
                total_macros["protein"] += ni.get("protein", 0)
                total_macros["carbohydrates"] += ni.get("carbohydrates", 0)
                total_macros["fat"] += ni.get("fat", 0)
                days_with_data += 1

        if days_with_data == 0:
            return None

        # Calculate averages
        return {
            "calories": round(total_calories / days_with_data),
            "macros": {
                "protein": round(total_macros["protein"] / days_with_data),
                "carbs": round(total_macros["carbohydrates"] / days_with_data),
                "fat": round(total_macros["fat"] / days_with_data)
            }
        }

    except Exception as e:
        logger.error(f"Error calculating weekly consumption average: {str(e)}")
        return None

async def calculate_weekly_adjusted_goals(current_goals: Dict[str, Any], weekly_average: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate adjusted goals based on weekly consumption average.
    Returns a dictionary with adjusted goals for calories and macros.
    """
    # Get current goals
    current_calories = int(current_goals.get("calorieTarget", 2000))
    current_macros = current_goals.get("macroGoals", {
        "protein": 100,
        "carbs": 250,
        "fat": 66
    })

    # Calculate adjustments (simple percentage-based adjustment)
    # If over/under by more than 10%, adjust by 5%
    calorie_diff_percent = (weekly_average["calories"] - current_calories) / current_calories
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

async def save_weekly_adjusted_goals(user_id: str, week_key: str, adjusted_goals: Dict[str, Any]):
    """
    Save weekly adjusted goals to the user's profile.
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

        # Ensure weekly_adjusted_goals exists
        if "weekly_adjusted_goals" not in user_doc["profile"]:
            user_doc["profile"]["weekly_adjusted_goals"] = {}

        # Store weekly adjusted goals
        user_doc["profile"]["weekly_adjusted_goals"][week_key] = adjusted_goals

        # Save updated document
        user_container.replace_item(item=user_doc["id"], body=user_doc)
        logger.info(f"Successfully saved weekly adjusted goals for user {user_id} for week {week_key}")
        return True

    except Exception as e:
        logger.error(f"Error saving weekly adjusted goals for user {user_id}: {str(e)}")
        return False

async def recalibrate_weekly_goals(user_id: str) -> bool:
    """
    Recalibrate weekly goals for a single user based on their consumption data.
    Returns True if successful, False otherwise.
    """
    try:
        # Get user document
        user_doc = await get_user_by_email(user_id)
        if not user_doc or "profile" not in user_doc:
            logger.error(f"User profile not found for user_id: {user_id}")
            return False

        # Get current goals
        current_goals = user_doc["profile"].get("goals", {})
        if not current_goals:
            logger.error(f"No current goals found for user_id: {user_id}")
            return False

        # Calculate date range for last week
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=7)

        # Get weekly consumption average
        weekly_average = await get_weekly_consumption_average(user_id, start_date, end_date)
        if not weekly_average:
            logger.error(f"No consumption data found for user_id: {user_id} in the past week")
            return False

        # Calculate adjusted goals
        adjusted_goals = await calculate_weekly_adjusted_goals(current_goals, weekly_average)
        if not adjusted_goals:
            logger.error(f"Failed to calculate adjusted goals for user_id: {user_id}")
            return False

        # Get next week's ISO week key
        next_week = end_date + timedelta(days=1)
        week_key = get_iso_week_key(next_week)

        # Save adjusted goals
        success = await save_weekly_adjusted_goals(user_id, week_key, adjusted_goals)
        if not success:
            logger.error(f"Failed to save adjusted goals for user_id: {user_id}")
            return False

        logger.info(f"Successfully recalibrated weekly goals for user_id: {user_id}")
        return True

    except Exception as e:
        logger.error(f"Error recalibrating weekly goals for user_id {user_id}: {str(e)}")
        return False

async def recalibrate_all_users_weekly():
    """
    Recalibrate weekly goals for all users.
    """
    try:
        # Get all users
        query = "SELECT c.id, c.email FROM c WHERE c.type = 'user'"
        users = list(user_container.query_items(query=query, enable_cross_partition_query=True))

        success_count = 0
        for user in users:
            if await recalibrate_weekly_goals(user["email"]):
                success_count += 1

        logger.info(f"Successfully recalibrated weekly goals for {success_count} out of {len(users)} users")
        return success_count

    except Exception as e:
        logger.error(f"Error in recalibrate_all_users_weekly: {str(e)}")
        return 0

async def seed_weekly_goals(user_id: str) -> bool:
    """
    Initialize weekly goals for a user by copying their current goals.
    Returns True if successful, False otherwise.
    """
    try:
        # Get user document
        user_doc = await get_user_by_email(user_id)
        if not user_doc or "profile" not in user_doc:
            logger.error(f"User profile not found for user_id: {user_id}")
            return False

        # Get current goals
        current_goals = user_doc["profile"].get("goals", {})
        if not current_goals:
            logger.error(f"No current goals found for user_id: {user_id}")
            return False

        # Get current week's ISO week key
        current_week = get_iso_week_key(datetime.utcnow())
        
        # Create weekly goals object
        weekly_goals = {
            "calorieTarget": current_goals.get("calorieTarget", "2000"),
            "macroGoals": current_goals.get("macroGoals", {
                "protein": 100,
                "carbs": 250,
                "fat": 66
            })
        }

        # Ensure weekly_adjusted_goals exists
        if "weekly_adjusted_goals" not in user_doc["profile"]:
            user_doc["profile"]["weekly_adjusted_goals"] = {}

        # Store weekly goals
        user_doc["profile"]["weekly_adjusted_goals"][current_week] = weekly_goals

        # Save updated document
        user_container.replace_item(item=user_doc["id"], body=user_doc)
        logger.info(f"Successfully seeded weekly goals for user {user_id} for week {current_week}")
        return True

    except Exception as e:
        logger.error(f"Error seeding weekly goals for user {user_id}: {str(e)}")
        return False

def calculate_adjusted_goals(user_doc: dict, daily_averages: dict) -> dict:
    """
    Calculate adjusted goals based on daily averages and baseline goals.
    Uses weekly_adjusted_goals as baseline if available, otherwise falls back to profile goals.
    """
    try:
        # Get current week's ISO week key
        current_week = datetime.utcnow().isocalendar()
        week_key = f"{current_week[0]}-W{current_week[1]:02d}"
        
        # Determine which baseline to use
        weekly_goals = user_doc.get("profile", {}).get("weekly_adjusted_goals", {})
        baseline = weekly_goals.get(week_key)
        
        if baseline:
            logger.info(f"Using weekly adjusted goals for week {week_key} as baseline for daily recalibration.")
        else:
            baseline = user_doc.get("profile", {}).get("goals", {})
            logger.info("No weekly adjusted goals found for current week, falling back to profile goals.")
        
        # Log the exact baseline values being used
        logger.info("Baseline values used: %s", baseline)
        
        # Calculate deviations
        calorie_deviation = (daily_averages["calories"] - float(baseline["calorieTarget"])) / float(baseline["calorieTarget"])
        protein_deviation = (daily_averages["protein"] - baseline["macroGoals"]["protein"]) / baseline["macroGoals"]["protein"]
        carbs_deviation = (daily_averages["carbs"] - baseline["macroGoals"]["carbs"]) / baseline["macroGoals"]["carbs"]
        fat_deviation = (daily_averages["fat"] - baseline["macroGoals"]["fat"]) / baseline["macroGoals"]["fat"]

        # Adjust goals if deviation exceeds threshold
        adjusted_goals = {
            "calorieTarget": baseline["calorieTarget"],
            "macroGoals": {
                "protein": baseline["macroGoals"]["protein"],
                "carbs": baseline["macroGoals"]["carbs"],
                "fat": baseline["macroGoals"]["fat"]
            }
        }

        if abs(calorie_deviation) > 0.1:
            adjusted_goals["calorieTarget"] = str(int(float(baseline["calorieTarget"]) * (1 + calorie_deviation * 0.5)))
        if abs(protein_deviation) > 0.1:
            adjusted_goals["macroGoals"]["protein"] = int(baseline["macroGoals"]["protein"] * (1 + protein_deviation * 0.5))
        if abs(carbs_deviation) > 0.1:
            adjusted_goals["macroGoals"]["carbs"] = int(baseline["macroGoals"]["carbs"] * (1 + carbs_deviation * 0.5))
        if abs(fat_deviation) > 0.1:
            adjusted_goals["macroGoals"]["fat"] = int(baseline["macroGoals"]["fat"] * (1 + fat_deviation * 0.5))

        return adjusted_goals
    except Exception as e:
        logger.error(f"Error calculating adjusted goals: {str(e)}")
        return None 