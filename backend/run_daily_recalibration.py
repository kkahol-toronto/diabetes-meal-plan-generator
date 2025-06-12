import asyncio
import logging
from goal_recalibration import recalibrate_user_goals

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run():
    user_id = "faizanrahmanrox@gmail.com"
    logger.info("Starting daily recalibration for user: %s", user_id)
    success = await recalibrate_user_goals(user_id)
    if success:
        logger.info("Daily recalibration completed successfully.")
    else:
        logger.error("Daily recalibration failed.")

if __name__ == "__main__":
    asyncio.run(run()) 