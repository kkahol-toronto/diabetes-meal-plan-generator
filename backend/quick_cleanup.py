#!/usr/bin/env python3
"""
Quick script to clean up meal plan data with duplicated "Recommended: " text.
"""

import os
import sys
import asyncio
from datetime import datetime

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import interactions_container

def clean_meal_text(meal_text: str) -> str:
    """
    Clean up meal text by removing duplicated "Recommended: " prefixes.
    """
    if not meal_text:
        return meal_text
    
    # Remove multiple "Recommended: " prefixes
    while "Recommended: Recommended: " in meal_text:
        meal_text = meal_text.replace("Recommended: Recommended: ", "Recommended: ")
    
    # Also handle case variations
    while "recommended: recommended: " in meal_text.lower():
        meal_text = meal_text.replace("recommended: recommended: ", "Recommended: ", 1)
        meal_text = meal_text.replace("recommended:", "Recommended:", 1)
    
    # Remove repetitive "light" text patterns
    while "light light light" in meal_text.lower():
        meal_text = meal_text.replace("light light light", "light", 1)
    while "light light" in meal_text.lower():
        meal_text = meal_text.replace("light light", "light", 1)
    
    return meal_text.strip()

async def cleanup_user_meal_plans(user_email: str):
    """
    Clean up meal plans for a specific user.
    """
    try:
        print(f"Cleaning meal plans for user: {user_email}")
        
        # Query meal plans for this user
        query = f"SELECT * FROM c WHERE c.type = 'meal_plan' AND c.user_id = '{user_email}'"
        items = list(interactions_container.query_items(query=query, enable_cross_partition_query=True))
        
        if not items:
            print("No meal plans found for this user")
            return
        
        print(f"Found {len(items)} meal plans")
        cleaned_count = 0
        
        for item in items:
            needs_cleaning = False
            cleaned_meals = {}
            
            # Check if meals exist and need cleaning
            if 'meals' in item and isinstance(item['meals'], dict):
                for meal_type, meal_text in item['meals'].items():
                    if isinstance(meal_text, str):
                        cleaned_text = clean_meal_text(meal_text)
                        if cleaned_text != meal_text:
                            needs_cleaning = True
                            cleaned_meals[meal_type] = cleaned_text
                            print(f"  Cleaning {meal_type}: '{meal_text}' -> '{cleaned_text}'")
                        else:
                            cleaned_meals[meal_type] = meal_text
                    else:
                        cleaned_meals[meal_type] = meal_text
            
            # If any meals needed cleaning, update the item
            if needs_cleaning:
                item['meals'] = cleaned_meals
                item['cleaned_at'] = datetime.utcnow().isoformat()
                item['cleaned_by'] = 'quick_cleanup_script'
                
                # Update the item in the database
                try:
                    interactions_container.replace_item(item=item['id'], body=item)
                    cleaned_count += 1
                    print(f"  Updated meal plan {item.get('id', 'unknown')}")
                except Exception as e:
                    print(f"  Error updating meal plan {item.get('id', 'unknown')}: {e}")
        
        print(f"\nCleanup completed for user {user_email}!")
        print(f"Total meal plans processed: {len(items)}")
        print(f"Meal plans cleaned: {cleaned_count}")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    user_email = "kanavtoronto@gmail.com"
    asyncio.run(cleanup_user_meal_plans(user_email)) 