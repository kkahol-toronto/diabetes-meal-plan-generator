import asyncio
import logging
from database import get_user_by_email, user_container

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def set_user_goals(user_id: str):
    """
    Check if user has goals set, if not set default goals.
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
            logger.info(f"Created profile for user {user_id}")

        # Check if goals exist
        if "goals" not in user_doc["profile"]:
            # Set default goals
            user_doc["profile"]["goals"] = {
                "calorieTarget": "2500",
                "macroGoals": {
                    "protein": 140,
                    "carbs": 300,
                    "fat": 80
                }
            }
            logger.info(f"Set default goals for user {user_id}")
        else:
            logger.info(f"User {user_id} already has goals set: {user_doc['profile']['goals']}")
            return True

        # Save updated document
        await user_container.replace_item(item=user_doc["id"], body=user_doc)
        logger.info(f"Successfully saved goals for user {user_id}")
        return True

    except Exception as e:
        logger.error(f"Error setting goals for user {user_id}: {str(e)}")
        return False

async def main():
    user_id = "faizanrahmanrox@gmail.com"
    success = await set_user_goals(user_id)
    if success:
        logger.info("Successfully set/verified user goals")
    else:
        logger.error("Failed to set user goals")

if __name__ == "__main__":
    asyncio.run(main()) 