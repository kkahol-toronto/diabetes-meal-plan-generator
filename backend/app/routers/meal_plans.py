from fastapi import APIRouter, Depends, HTTPException, Path
from typing import Dict, Any, List
import sys
import os

# Add the backend directory to the path so we can import database functions
backend_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from database import (
    get_user_meal_plans,
    get_meal_plan_by_id,
    delete_all_user_meal_plans,
    delete_meal_plan_by_id
)
from ..services.auth import get_current_user
from ..models.user import User
from ..utils.logger import logger

router = APIRouter()

@router.get("")
async def get_meal_plans(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get all meal plans for the current user"""
    try:
        # User is a dict, get email
        user_email = current_user.get("email")
        if not user_email:
            raise HTTPException(status_code=400, detail="User email not found")
        
        meal_plans = await get_user_meal_plans(user_email)
        return {"meal_plans": meal_plans}
        
    except Exception as e:
        logger.error(f"Error getting meal plans: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get meal plans: {str(e)}")

@router.get("/{plan_id}")
async def get_meal_plan(
    plan_id: str = Path(..., description="The ID of the meal plan to retrieve"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get a specific meal plan by ID"""
    try:
        meal_plan = await get_meal_plan_by_id(plan_id)
        if not meal_plan:
            raise HTTPException(status_code=404, detail="Meal plan not found")
        
        # Verify the meal plan belongs to the current user
        user_email = current_user.get("email")
        if meal_plan.get("user_id") != user_email:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return meal_plan
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting meal plan {plan_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get meal plan: {str(e)}")

@router.delete("/all")
async def delete_all_meal_plans(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Delete all meal plans for the current user"""
    try:
        user_email = current_user.get("email")
        if not user_email:
            raise HTTPException(status_code=400, detail="User email not found")
        
        deleted_count = await delete_all_user_meal_plans(user_email)
        return {
            "message": f"Successfully deleted {deleted_count} meal plans",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error deleting all meal plans: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete meal plans: {str(e)}")

@router.delete("/{plan_id}")
async def delete_meal_plan_endpoint(
    plan_id: str = Path(..., description="The ID of the meal plan to delete"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Delete a specific meal plan by ID"""
    try:
        # First verify the meal plan exists and belongs to the user
        meal_plan = await get_meal_plan_by_id(plan_id)
        if not meal_plan:
            raise HTTPException(status_code=404, detail="Meal plan not found")
        
        user_email = current_user.get("email")
        if meal_plan.get("user_id") != user_email:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete the meal plan
        success = await delete_meal_plan_by_id(plan_id, user_email)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete meal plan")
        
        return {"message": f"Successfully deleted meal plan {plan_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting meal plan {plan_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete meal plan: {str(e)}")

@router.post("/bulk_delete")
async def bulk_delete_meal_plans(
    request: Dict[str, List[str]],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Delete multiple meal plans by their IDs"""
    try:
        plan_ids = request.get("plan_ids", [])
        if not plan_ids:
            raise HTTPException(status_code=400, detail="No plan IDs provided")
        
        user_email = current_user.get("email")
        deleted_count = 0
        failed_deletions = []
        
        for plan_id in plan_ids:
            try:
                # Verify ownership before deletion
                meal_plan = await get_meal_plan_by_id(plan_id)
                if meal_plan and meal_plan.get("user_id") == user_email:
                    success = await delete_meal_plan_by_id(plan_id, user_email)
                    if success:
                        deleted_count += 1
                    else:
                        failed_deletions.append(plan_id)
                else:
                    failed_deletions.append(plan_id)
            except Exception as e:
                logger.error(f"Error deleting meal plan {plan_id}: {str(e)}")
                failed_deletions.append(plan_id)
        
        return {
            "message": f"Successfully deleted {deleted_count} meal plans",
            "deleted_count": deleted_count,
            "failed_deletions": failed_deletions
        }
        
    except Exception as e:
        logger.error(f"Error in bulk delete: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete meal plans: {str(e)}") 