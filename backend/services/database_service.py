"""
Database Service
Cached wrapper functions for database operations to improve performance.
Provides caching layer on top of existing database functions.
"""

from typing import Dict, Any, List, Optional
from database import (
    get_user_by_email as db_get_user_by_email,
    get_user_meal_plans as db_get_user_meal_plans,
    get_user_consumption_history as db_get_user_consumption_history,
    save_meal_plan as db_save_meal_plan,
    save_consumption_record as db_save_consumption_record
)
from services.cache_service import (
    get_cached_user_profile,
    get_cached_user_meal_plans,
    get_cached_consumption_history,
    invalidate_user_cache,
    invalidate_consumption_cache,
    invalidate_meal_plan_cache
)


async def get_user_profile_cached(user_email: str) -> Optional[Dict[str, Any]]:
    """
    Get user profile with caching.
    
    Args:
        user_email: User's email identifier
        
    Returns:
        User profile dict or None
    """
    async def fetch_from_db(email: str):
        try:
            user_data = await db_get_user_by_email(email)
            return user_data.get("profile", {}) if user_data else None
        except Exception as e:
            print(f"[db_service] Error fetching user profile: {e}")
            return None
    
    return await get_cached_user_profile(user_email, fetch_from_db)


async def get_user_meal_plans_cached(user_email: str) -> List[Dict[str, Any]]:
    """
    Get user meal plans with caching.
    
    Args:
        user_email: User's email identifier
        
    Returns:
        List of meal plans
    """
    async def fetch_from_db(email: str):
        return await db_get_user_meal_plans(email)
    
    return await get_cached_user_meal_plans(user_email, fetch_from_db)


async def get_user_consumption_history_cached(user_email: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get user consumption history with caching.
    
    Args:
        user_email: User's email identifier
        limit: Number of records to fetch
        
    Returns:
        List of consumption records
    """
    async def fetch_from_db(email: str, limit: int):
        return await db_get_user_consumption_history(email, limit)
    
    return await get_cached_consumption_history(user_email, limit, fetch_from_db)


async def save_meal_plan_with_cache_invalidation(user_email: str, meal_plan_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save meal plan and invalidate relevant caches.
    
    Args:
        user_email: User's email identifier
        meal_plan_data: Meal plan data to save
        
    Returns:
        Saved meal plan data
    """
    print(f"[save_meal_plan_cache] Saving meal plan for {user_email}")
    print(f"[save_meal_plan_cache] Meal plan data: {meal_plan_data}")
    
    # Save to database
    result = await db_save_meal_plan(user_email, meal_plan_data)
    print(f"[save_meal_plan_cache] Database save result: {result}")
    
    # Invalidate meal plan cache for this user
    invalidate_meal_plan_cache(user_email)
    print(f"[save_meal_plan_cache] Cache invalidated for {user_email}")
    
    return result


async def save_consumption_record_with_cache_invalidation(
    user_email: str, 
    consumption_data: Dict[str, Any], 
    meal_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Save consumption record and invalidate relevant caches.
    
    Args:
        user_email: User's email identifier
        consumption_data: Consumption data to save
        meal_type: Optional meal type
        
    Returns:
        Saved consumption record
    """
    # Get user timezone from profile if available
    user_timezone = "UTC"  # Default fallback
    try:
        from database import get_user_by_email
        user_doc = await get_user_by_email(user_email)
        if user_doc and "profile" in user_doc:
            user_timezone = user_doc["profile"].get("timezone", "UTC")
    except Exception as e:
        print(f"[database_service] Could not get user timezone: {e}")
    
    # Save to database
    result = await db_save_consumption_record(user_email, consumption_data, meal_type, user_timezone)
    
    # Invalidate consumption cache for this user (but keep other caches)
    invalidate_consumption_cache(user_email)
    
    return result


# Convenience functions for common operations
async def get_user_context_cached(user_email: str) -> Dict[str, Any]:
    """
    Get comprehensive user context with caching.
    
    Args:
        user_email: User's email identifier
        
    Returns:
        Dict containing profile, meal plans, and recent consumption
    """
    # Fetch all data in parallel for better performance
    import asyncio
    
    profile_task = get_user_profile_cached(user_email)
    meal_plans_task = get_user_meal_plans_cached(user_email)
    consumption_task = get_user_consumption_history_cached(user_email, limit=50)
    
    profile, meal_plans, consumption = await asyncio.gather(
        profile_task, meal_plans_task, consumption_task, return_exceptions=True
    )
    
    # Handle any exceptions gracefully
    if isinstance(profile, Exception):
        print(f"[db_service] Error fetching profile: {profile}")
        profile = {}
        
    if isinstance(meal_plans, Exception):
        print(f"[db_service] Error fetching meal plans: {meal_plans}")
        meal_plans = []
        
    if isinstance(consumption, Exception):
        print(f"[db_service] Error fetching consumption: {consumption}")
        consumption = []
    
    return {
        'profile': profile or {},
        'meal_plans': meal_plans or [],
        'consumption_history': consumption or []
    }