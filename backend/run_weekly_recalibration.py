import asyncio
import logging
from goal_recalibration import recalibrate_weekly_goals

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    user_id = "faizanrahmanrox@gmail.com"
    logger.info("Starting weekly recalibration for user: %s", user_id)
    success = await recalibrate_weekly_goals(user_id)
    if success:
        logger.info("Weekly recalibration completed successfully.")
    else:
        logger.error("Weekly recalibration failed.")

if __name__ == "__main__":
    asyncio.run(main())