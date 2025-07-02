from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, List
import sys
import os

# Add the backend directory to the path so we can import consumption_endpoints
backend_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from consumption_endpoints import (
    quick_log_food_endpoint,
    get_consumption_history_endpoint,
    get_consumption_analytics_endpoint,
    get_daily_insights_endpoint
)
from ..services.auth import get_current_user
from ..models.user import User

router = APIRouter()

@router.post("/quick-log")
async def quick_log_food(
    food_data: dict,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Log food quickly with AI analysis"""
    # Ensure user has id field for consumption endpoints
    user_dict = dict(current_user)
    if 'id' not in user_dict and 'email' in user_dict:
        user_dict['id'] = user_dict['email']
    
    return await quick_log_food_endpoint(food_data, user_dict)

@router.get("/history")
async def get_consumption_history(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get user's consumption history"""
    # Ensure user has id field for consumption endpoints
    user_dict = dict(current_user)
    if 'id' not in user_dict and 'email' in user_dict:
        user_dict['id'] = user_dict['email']
    
    return await get_consumption_history_endpoint(limit, user_dict)

@router.get("/analytics")
async def get_consumption_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get consumption analytics for specified number of days"""
    # Ensure user has id field for consumption endpoints
    user_dict = dict(current_user)
    if 'id' not in user_dict and 'email' in user_dict:
        user_dict['id'] = user_dict['email']
    
    return await get_consumption_analytics_endpoint(days, user_dict) 