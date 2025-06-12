import asyncio
import logging
from goal_recalibration import seed_weekly_goals
from database import get_user_by_email

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    user_id = "faizanrahmanrox@gmail.com"
    
    # First check if user exists and has goals
    user_doc = await get_user_by_email(user_id)
    if not user_doc:
        logger.error(f"User {user_id} not found")
        return
    if "profile" not in user_doc:
        logger.error(f"User {user_id} has no profile")
        return
    if "goals" not in user_doc["profile"]:
        logger.error(f"User {user_id} has no goals set")
        return
    
    logger.info(f"Found user profile with goals: {user_doc['profile']['goals']}")
    
    # Try to seed weekly goals
    success = await seed_weekly_goals(user_id)
    if success:
        logger.info("Successfully seeded weekly goals")
    else:
        logger.error("Failed to seed weekly goals")

if __name__ == "__main__":
    asyncio.run(main()) 