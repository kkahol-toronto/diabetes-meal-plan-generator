import asyncio
from datetime import datetime, timedelta
import random
import traceback
from uuid import uuid4
from database import interactions_container, get_user_by_email

async def create_test_records(user_id: str):
    """
    Create test consumption records for the past 7 days.
    Each day will have 2-3 meals with varying calorie and macro values.
    """
    try:
        print(f"Starting to create test records for user {user_id}")
        
        # Get user document to verify user exists
        print("Fetching user document...")
        user_doc = await get_user_by_email(user_id)
        if not user_doc:
            print(f"User {user_id} not found")
            return False
        
        print(f"Found user document: {user_doc.get('id', 'No ID')}")

        # Generate records for past 7 days
        for day_offset in range(7, 0, -1):  # 7 days ago to yesterday
            date = datetime.utcnow().date() - timedelta(days=day_offset)
            print(f"\nProcessing records for date: {date.isoformat()}")
            
            # Create 2-3 meals per day
            num_meals = random.randint(2, 3)
            for meal_num in range(num_meals):
                # Generate random nutritional values
                calories = random.randint(400, 800)
                protein = random.randint(20, 40)
                carbs = random.randint(40, 80)
                fat = random.randint(10, 30)

                # Create record with unique ID
                record_id = f"test_record_{date.isoformat()}_{meal_num}_{uuid4().hex}"
                record = {
                    "id": record_id,
                    "type": "consumption_record",
                    "user_id": user_id,
                    "timestamp": date.isoformat(),
                    "meal_type": random.choice(["breakfast", "lunch", "dinner", "snack"]),
                    "nutritional_info": {
                        "calories": calories,
                        "protein": protein,
                        "carbohydrates": carbs,
                        "fat": fat
                    }
                }

                print(f"Creating record {record_id}...")
                try:
                    # Save record using synchronous create_item
                    interactions_container.create_item(body=record)
                    print(f"Successfully created record for {date.isoformat()}, meal {meal_num + 1}: {calories} kcal")
                except Exception as e:
                    print(f"Error creating individual record: {str(e)}")
                    traceback.print_exc()
                    continue

        print("\nSuccessfully created all test records")
        return True

    except Exception as e:
        print(f"Error creating test records: {str(e)}")
        traceback.print_exc()
        return False

async def main():
    user_id = "faizanrahmanrox@gmail.com"
    print("Starting test record creation process...")
    success = await create_test_records(user_id)
    if success:
        print("Test records created successfully")
    else:
        print("Failed to create test records")

if __name__ == "__main__":
    asyncio.run(main()) 