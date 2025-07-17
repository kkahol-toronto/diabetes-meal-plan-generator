#!/usr/bin/env python3
"""
Script to clean up meal plan data that contains duplicated "Recommended: " text.
This script will find and fix all meal plans in the database that have repetitive text.
"""

import os
import sys
import asyncio
from datetime import datetime
import json

# Add the current directory to the path so we can import from main.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_user_meal_plans, save_meal_plan, interactions_container

def clean_meal_text(meal_text: str) -> str:
    """
    Clean up meal text by removing duplicated "Recommended: " prefixes and other repetitive patterns.
    """
    if not meal_text:
        return meal_text
    
    # Remove multiple "Recommended: " prefixes
    while "Recommended: Recommended: " in meal_text:
        meal_text = meal_text.replace("Recommended: Recommended: ", "Recommended: ")
    
    # Also handle case variations
    while "recommended: recommended: " in meal_text.lower():
        meal_text = meal_text.replace("recommended: recommended: ", "Recommended: ", 1)
        # Fix the case of the remaining "recommended:"
        meal_text = meal_text.replace("recommended:", "Recommended:", 1)
    
    # Remove repetitive "light" text patterns
    while "light light light" in meal_text.lower():
        meal_text = meal_text.replace("light light light", "light", 1)
    while "light light" in meal_text.lower():
        meal_text = meal_text.replace("light light", "light", 1)
    
    # Remove any word that repeats more than 2 times consecutively
    words = meal_text.split()
    cleaned_words = []
    last_word = ''
    repeat_count = 0
    
    for word in words:
        if word.lower() == last_word.lower():
            repeat_count += 1
            if repeat_count <= 2:  # Keep up to 2 repetitions
                cleaned_words.append(word)
            # Skip additional repetitions
        else:
            last_word = word
            repeat_count = 1
            cleaned_words.append(word)
    
    cleaned_text = ' '.join(cleaned_words)
    
    # Additional cleanup for corrupted patterns
    if ('lightlightlight' in cleaned_text.lower() or 
        'lightlight' in cleaned_text.lower() or
        'light light light' in cleaned_text.lower() or
        'light light' in cleaned_text.lower()):
        # Extract only the meaningful part before the repetitive text
        meaningful_part = cleaned_text.split('light')[0]
        cleaned_text = meaningful_part.strip()
    
    # If the cleaned text is too short or empty, provide a fallback
    if len(cleaned_text.strip()) < 3:
        # Try to extract a reasonable meal name
        original_words = meal_text.split()
        meaningful_words = [word for word in original_words 
                          if len(word) > 2 and 
                          not word.isdigit() and 
                          word.lower() not in ['with', 'and', 'or', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'from', 'for', 'of', 'by', 'light', 'recommended']]
        cleaned_text = ' '.join(meaningful_words[:4])
    
    # Final fallback for corrupted descriptions
    if len(cleaned_text.strip()) < 3:
        return "Healthy meal option"
    
    return cleaned_text.strip()

async def cleanup_meal_plans():
    """
    Clean up all meal plans in the database that contain duplicated text.
    """
    try:
        print("Starting meal plan cleanup...")
        
        # Query all meal plans
        query = "SELECT * FROM c WHERE c.type = 'meal_plan'"
        items = interactions_container.query_items(query=query, enable_cross_partition_query=True)
        
        cleaned_count = 0
        total_count = 0
        
        async for item in items:
            total_count += 1
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
                        else:
                            cleaned_meals[meal_type] = meal_text
                    else:
                        cleaned_meals[meal_type] = meal_text
            
            # If any meals needed cleaning, update the item
            if needs_cleaning:
                item['meals'] = cleaned_meals
                item['cleaned_at'] = datetime.utcnow().isoformat()
                item['cleaned_by'] = 'cleanup_script'
                
                # Update the item in the database
                try:
                    interactions_container.replace_item(item=item['id'], body=item)
                    cleaned_count += 1
                    print(f"Cleaned meal plan {item.get('id', 'unknown')} - {list(cleaned_meals.keys())}")
                except Exception as e:
                    print(f"Error updating meal plan {item.get('id', 'unknown')}: {e}")
        
        print(f"\nCleanup completed!")
        print(f"Total meal plans processed: {total_count}")
        print(f"Meal plans cleaned: {cleaned_count}")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        import traceback
        traceback.print_exc()

async def cleanup_user_meal_plans(user_email: str):
    """
    Clean up meal plans for a specific user.
    """
    try:
        print(f"Cleaning meal plans for user: {user_email}")
        
        # Get user's meal plans
        meal_plans = await get_user_meal_plans(user_email)
        
        if not meal_plans:
            print("No meal plans found for this user")
            return
        
        cleaned_count = 0
        
        for meal_plan in meal_plans:
            needs_cleaning = False
            cleaned_meals = {}
            
            # Check if meals exist and need cleaning
            if 'meals' in meal_plan and isinstance(meal_plan['meals'], dict):
                for meal_type, meal_text in meal_plan['meals'].items():
                    if isinstance(meal_text, str):
                        cleaned_text = clean_meal_text(meal_text)
                        if cleaned_text != meal_text:
                            needs_cleaning = True
                            cleaned_meals[meal_type] = cleaned_text
                        else:
                            cleaned_meals[meal_type] = meal_text
                    else:
                        cleaned_meals[meal_type] = meal_text
            
            # If any meals needed cleaning, update the meal plan
            if needs_cleaning:
                meal_plan['meals'] = cleaned_meals
                meal_plan['cleaned_at'] = datetime.utcnow().isoformat()
                meal_plan['cleaned_by'] = 'cleanup_script'
                
                # Save the updated meal plan
                try:
                    await save_meal_plan(user_email, meal_plan)
                    cleaned_count += 1
                    print(f"Cleaned meal plan {meal_plan.get('id', 'unknown')} - {list(cleaned_meals.keys())}")
                except Exception as e:
                    print(f"Error updating meal plan {meal_plan.get('id', 'unknown')}: {e}")
        
        print(f"\nCleanup completed for user {user_email}!")
        print(f"Total meal plans processed: {len(meal_plans)}")
        print(f"Meal plans cleaned: {cleaned_count}")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up meal plan data with duplicated text')
    parser.add_argument('--user', type=str, help='Clean up meal plans for a specific user email')
    parser.add_argument('--all', action='store_true', help='Clean up all meal plans in the database')
    
    args = parser.parse_args()
    
    if args.user:
        asyncio.run(cleanup_user_meal_plans(args.user))
    elif args.all:
        asyncio.run(cleanup_meal_plans())
    else:
        print("Please specify --user <email> or --all")
        print("Example: python cleanup_meal_plans.py --user kanavtoronto@gmail.com")
        print("Example: python cleanup_meal_plans.py --all")