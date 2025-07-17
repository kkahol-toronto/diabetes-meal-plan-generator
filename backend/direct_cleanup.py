#!/usr/bin/env python3
"""
Direct cleanup script that bypasses authentication to fix meal plan issues.
"""

import os
import sys
import asyncio
from datetime import datetime

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import interactions_container, delete_all_user_meal_plans, save_meal_plan
from main import generate_fresh_adaptive_meal_plan, get_today_consumption_records_async

async def direct_cleanup_user_meal_plans(user_email: str):
    """
    Directly clean up meal plans for a specific user without authentication.
    """
    try:
        print(f"Directly cleaning meal plans for user: {user_email}")
        
        # Delete all existing meal plans for this user
        await delete_all_user_meal_plans(user_email)
        print(f"Deleted all existing meal plans for user: {user_email}")
        
        # Create a basic profile for meal plan generation
        profile = {
            "timezone": "America/Toronto",
            "calorieTarget": "1800",
            "dietaryRestrictions": [],
            "allergies": [],
            "dietType": ["Western", "South Asian – North Indian"],
            "foodPreferences": [],
            "strongDislikes": []
        }
        
        # Get today's consumption
        today_consumption = await get_today_consumption_records_async(user_email, profile.get("timezone", "UTC"))
        calories_consumed = sum(r.get("nutritional_info", {}).get("calories", 0) for r in today_consumption)
        target_calories = int(profile.get('calorieTarget', '2000'))
        remaining_calories = max(0, target_calories - calories_consumed)
        
        print(f"Calories consumed: {calories_consumed}, Target: {target_calories}, Remaining: {remaining_calories}")
        
        # Get dietary restrictions
        dietary_restrictions = profile.get('dietaryRestrictions', [])
        allergies = profile.get('allergies', [])
        diet_type = profile.get('dietType', [])
        
        # Check if user is vegetarian or has restrictions
        is_vegetarian = 'vegetarian' in [r.lower() for r in dietary_restrictions] or 'vegetarian' in [d.lower() for d in diet_type]
        no_eggs = any('egg' in r.lower() for r in dietary_restrictions) or any('egg' in a.lower() for a in allergies)
        
        print(f"Vegetarian: {is_vegetarian}, No eggs: {no_eggs}")
        
        # Generate fresh adaptive meal plan
        fresh_plan = await generate_fresh_adaptive_meal_plan(
            user_email,
            today_consumption,
            remaining_calories,
            is_vegetarian,
            no_eggs,
            dietary_restrictions,
            allergies,
            profile.get('dietType', []),
            profile.get('foodPreferences', []),
            profile.get('strongDislikes', [])
        )
        
        if fresh_plan:
            await save_meal_plan(user_email, fresh_plan)
            print(f"Generated and saved fresh meal plan for user: {user_email}")
            print(f"Plan ID: {fresh_plan.get('id')}")
            print(f"Meals: {fresh_plan.get('meals', {})}")
            
            return {
                "success": True,
                "message": "Meal plans cleaned and fresh plan generated",
                "plan_id": fresh_plan.get("id"),
                "meals": fresh_plan.get("meals", {})
            }
        else:
            print("Failed to generate fresh meal plan")
            return {"success": False, "message": "Failed to generate fresh meal plan"}
            
    except Exception as e:
        print(f"Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Cleanup failed: {str(e)}"}

if __name__ == "__main__":
    user_email = "kanavtoronto@gmail.com"
    result = asyncio.run(direct_cleanup_user_meal_plans(user_email))
    print(f"\nResult: {result}") 