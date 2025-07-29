from fastapi import APIRouter, HTTPException, Depends, status, Request, Body, Form
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
from datetime import datetime
from models import User
from routers.auth import get_current_user
from database import (
    save_meal_plan, get_user_meal_plans, get_meal_plan_by_id,
    delete_meal_plan_by_id, delete_all_user_meal_plans, view_meal_plans,
    interactions_container
)
import traceback

router = APIRouter()

@router.post("/generate_plan")
async def generate_plan(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Save a generated meal plan to history"""
    try:
        data = await request.json()
        
        # Validate required fields
        required_fields = ["user_profile", "recipes", "shopping_list"]
        for field in required_fields:
            if field not in data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Save the meal plan using Cosmos DB
        meal_plan = await save_meal_plan(current_user["email"], data)
        
        return {
            "status": "success",
            "message": "Meal plan saved successfully",
            "meal_plan": meal_plan
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/meal_plans")
async def get_meal_plans(
    current_user: User = Depends(get_current_user)
):
    """Get all meal plans for the current user"""
    try:
        meal_plans = await get_user_meal_plans(current_user["email"])
        return {"meal_plans": meal_plans}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve meal plans: {str(e)}"
        )

@router.get("/meal_plans/{plan_id}")
async def get_meal_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific meal plan by ID"""
    try:
        # Query Cosmos DB for the specific meal plan
        query = f"SELECT * FROM c WHERE (c.type = 'meal_plan' OR c.type = 'full_meal_plan') AND c.id = '{plan_id}' AND c.user_id = '{current_user['email']}'"
        items = list(interactions_container.query_items(query=query, enable_cross_partition_query=True))
        
        if not items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meal plan not found"
            )
            
        return {"meal_plan": items[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve meal plan: {str(e)}"
        )

@router.delete("/meal_plans/all")
async def delete_all_meal_plans_endpoint(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Deletes all meal plans for the current user."""
    try:
        user_id = current_user.get("email")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in token. Please log in again.")

        deleted_count = await delete_all_user_meal_plans(user_id)

        if deleted_count == 0:
            return {"message": "No meal plans were found to delete. Your history is already empty."}
        else:
            return {"message": f"Successfully deleted all {deleted_count} meal plan(s) for user {user_id}."}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in DELETE /meal_plans/all: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to delete all meal plans: {str(e)}")

@router.delete("/meal_plans/{plan_id}")
async def delete_meal_plan(
    plan_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Deletes a specific meal plan by ID for the current user."""
    try:
        user_id = current_user.get("email")
        if not user_id:
             raise HTTPException(status_code=400, detail="User ID not found in token.")
        deleted = await delete_meal_plan_by_id(plan_id, user_id)
        if not deleted:
             raise HTTPException(status_code=404, detail="Meal plan not found or does not belong to user.")
        return {"message": f"Meal plan '{plan_id}' deleted successfully"}
    except Exception as e:
        print(f"Error in DELETE /meal_plans/{{plan_id}}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to delete meal plan: {str(e)}")

@router.post("/meal_plans/bulk_delete")
async def bulk_delete_meal_plans(
    plan_ids: List[str] = Body(..., embed=True),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Deletes a list of specific meal plans by ID for the current user."""
    if not plan_ids:
        raise HTTPException(status_code=400, detail="No meal plan IDs provided for deletion.")
        
    user_id = current_user.get("email")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found in token.")

    deleted_count = 0
    failed_deletions = []
    corrupted_plans = []
    
    for plan_id in plan_ids:
        try:
            if not plan_id:
                failed_deletions.append("Empty ID provided")
                continue

            # Ensure plan_id has the correct prefix
            if not plan_id.startswith('meal_plan_'):
                plan_id = f'meal_plan_{plan_id}'

            deleted = await delete_meal_plan_by_id(plan_id, user_id)
            
            if deleted:
                deleted_count += 1
            else:
                # Check if the plan exists but is corrupted
                query = f"SELECT c.id, c.created_at, c.dailyCalories, c.macronutrients FROM c WHERE c.type = 'meal_plan' AND c.id = '{plan_id}' AND c.user_id = '{user_id}'"
                items = list(interactions_container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                ))
                
                if items:
                    # Plan exists but might be corrupted
                    plan = items[0]
                    required_fields = ['created_at', 'dailyCalories', 'macronutrients']
                    missing_fields = [field for field in required_fields if field not in plan]
                    if missing_fields:
                        corrupted_plans.append(f"{plan_id} (missing: {', '.join(missing_fields)})")
                    else:
                        failed_deletions.append(f"{plan_id} (not found or access denied)")
                else:
                    failed_deletions.append(f"{plan_id} (not found or access denied)")

        except Exception as e:
            print(f"Error deleting meal plan {plan_id} during bulk delete: {e}")
            failed_deletions.append(f"{plan_id} (error: {str(e)})")

    if deleted_count == 0 and not failed_deletions and not corrupted_plans:
        raise HTTPException(status_code=404, detail="No meal plans were found to delete.")
    
    response = {
        "message": f"Successfully deleted {deleted_count} meal plan(s).",
        "deleted_count": deleted_count
    }
    
    if failed_deletions:
        response["failed_deletions"] = failed_deletions
    
    if corrupted_plans:
        response["corrupted_plans"] = corrupted_plans
    
    return response

@router.get("/view-meal-plans")
async def view_meal_plans_endpoint(current_user: Dict[str, Any] = Depends(get_current_user)):
    """View all meal plans for the current user"""
    try:
        meal_plans = await view_meal_plans(current_user["email"])
        return {"meal_plans": meal_plans}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# NOTE: save-full-meal-plan endpoint moved to meal_plans.py to handle PDF info properly
# and prevent route conflicts. The unified endpoint handles both regular meal plans
# and meal plans with PDF attachments correctly.

@router.get("/debug/meal_plans")
async def debug_meal_plans(current_user: User = Depends(get_current_user)):
    """Return all meal plans for the current user, including IDs and partition keys, for debugging."""
    try:
        user_id = current_user.get("email")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in token.")
        query = f"SELECT * FROM c WHERE c.type = 'meal_plan' AND c.user_id = '{user_id}'"
        print(f"[DEBUG] Querying all meal plans for user_id: {user_id}")
        items = list(interactions_container.query_items(query=query, enable_cross_partition_query=True))
        print(f"[DEBUG] Found {len(items)} meal plans for user_id: {user_id}")
        return {"meal_plans": items}
    except Exception as e:
        print(f"[DEBUG] Error in /debug/meal_plans: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/debug/cleanup-meal-plans")
async def cleanup_meal_plans(current_user: User = Depends(get_current_user)):
    """Clean up meal plans with duplicated text and regenerate fresh ones"""
    try:
        user_email = current_user["email"]
        print(f"[CLEANUP] Starting meal plan cleanup for user: {user_email}")
        
        # Delete all existing meal plans for this user
        from database import delete_all_user_meal_plans
        await delete_all_user_meal_plans(user_email)
        print(f"[CLEANUP] Deleted all existing meal plans for user: {user_email}")
        
        # Generate a fresh meal plan
        profile = current_user.get("profile", {})
        
        # Get today's consumption
        from services.consumption_analysis import get_today_consumption_records_async
        today_consumption = await get_today_consumption_records_async(user_email, profile.get("timezone", "UTC"))
        calories_consumed = sum(r.get("nutritional_info", {}).get("calories", 0) for r in today_consumption)
        target_calories = int(profile.get('calorieTarget', '2000'))
        remaining_calories = max(0, target_calories - calories_consumed)
        
        # Get dietary restrictions
        dietary_restrictions = profile.get('dietaryRestrictions', [])
        allergies = profile.get('allergies', [])
        diet_type = profile.get('dietType', [])
        
        # Check if user is vegetarian or has restrictions
        is_vegetarian = 'vegetarian' in [r.lower() for r in dietary_restrictions] or 'vegetarian' in [d.lower() for d in diet_type]
        no_eggs = any('egg' in r.lower() for r in dietary_restrictions) or any('egg' in a.lower() for a in allergies)
        
        # Generate fresh adaptive meal plan
        from services.consumption_analysis import generate_fresh_adaptive_meal_plan
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
            from database import save_meal_plan
            await save_meal_plan(user_email, fresh_plan)
            print(f"[CLEANUP] Generated and saved fresh meal plan for user: {user_email}")
            
            return {
                "success": True,
                "message": "Meal plans cleaned and fresh plan generated",
                "plan_id": fresh_plan.get("id"),
                "meals": fresh_plan.get("meals", {})
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to generate fresh meal plan")
            
    except Exception as e:
        print(f"[CLEANUP] Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

@router.get("/meal_plans/history")
async def get_meal_plans_history_alias(current_user: User = Depends(get_current_user)):
    """Alias for /meal_plans to maintain frontend backward compatibility"""
    try:
        meal_plans = await get_user_meal_plans(current_user["email"])
        return {"meal_plans": meal_plans}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve meal plans: {str(e)}"
        ) 