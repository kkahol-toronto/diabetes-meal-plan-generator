"""
Cache Service
Simple in-memory caching for frequently accessed data to improve performance.
Reduces database queries for user profiles, meal plans, and other commonly accessed data.
"""

import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta


class SimpleCache:
    """Simple in-memory cache with TTL (Time To Live) support."""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if it exists and hasn't expired."""
        if key not in self.cache:
            return None
            
        item = self.cache[key]
        if time.time() > item['expires_at']:
            # Item has expired, remove it
            del self.cache[key]
            return None
            
        return item['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL."""
        expires_at = time.time() + (ttl or self.default_ttl)
        self.cache[key] = {
            'value': value,
            'expires_at': expires_at,
            'created_at': time.time()
        }
    
    def delete(self, key: str) -> None:
        """Remove key from cache."""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        current_time = time.time()
        valid_items = sum(1 for item in self.cache.values() if current_time <= item['expires_at'])
        
        return {
            'total_keys': len(self.cache),
            'valid_keys': valid_items,
            'expired_keys': len(self.cache) - valid_items
        }


# Global cache instances
user_profile_cache = SimpleCache(default_ttl=600)  # 10 minutes for user profiles
meal_plan_cache = SimpleCache(default_ttl=300)     # 5 minutes for meal plans  
consumption_cache = SimpleCache(default_ttl=180)   # 3 minutes for consumption data


async def get_cached_user_profile(user_email: str, fetch_function: Callable) -> Optional[Dict[str, Any]]:
    """
    Get user profile from cache or fetch and cache it.
    
    Args:
        user_email: User's email identifier
        fetch_function: Async function to fetch profile from database
        
    Returns:
        User profile dict or None
    """
    cache_key = f"user_profile:{user_email}"
    
    # Try to get from cache first
    cached_profile = user_profile_cache.get(cache_key)
    if cached_profile is not None:
        print(f"[cache] User profile cache HIT for {user_email}")
        return cached_profile
    
    # Cache miss - fetch from database
    print(f"[cache] User profile cache MISS for {user_email}")
    try:
        profile = await fetch_function(user_email)
        if profile:
            user_profile_cache.set(cache_key, profile)
        return profile
    except Exception as e:
        print(f"[cache] Error fetching user profile: {e}")
        return None


async def get_cached_user_meal_plans(user_email: str, fetch_function: Callable) -> list:
    """
    Get user meal plans from cache or fetch and cache them.
    
    Args:
        user_email: User's email identifier
        fetch_function: Async function to fetch meal plans from database
        
    Returns:
        List of meal plans
    """
    cache_key = f"meal_plans:{user_email}"
    
    # Try to get from cache first
    cached_plans = meal_plan_cache.get(cache_key)
    if cached_plans is not None:
        print(f"[cache] Meal plans cache HIT for {user_email}")
        return cached_plans
    
    # Cache miss - fetch from database
    print(f"[cache] Meal plans cache MISS for {user_email}")
    try:
        plans = await fetch_function(user_email)
        if plans:
            meal_plan_cache.set(cache_key, plans)
        return plans or []
    except Exception as e:
        print(f"[cache] Error fetching meal plans: {e}")
        return []


async def get_cached_consumption_history(user_email: str, limit: int, fetch_function: Callable) -> list:
    """
    Get consumption history from cache or fetch and cache it.
    
    Args:
        user_email: User's email identifier
        limit: Number of records to fetch
        fetch_function: Async function to fetch consumption from database
        
    Returns:
        List of consumption records
    """
    cache_key = f"consumption:{user_email}:{limit}"
    
    # Try to get from cache first
    cached_consumption = consumption_cache.get(cache_key)
    if cached_consumption is not None:
        print(f"[cache] Consumption cache HIT for {user_email}")
        return cached_consumption
    
    # Cache miss - fetch from database
    print(f"[cache] Consumption cache MISS for {user_email}")
    try:
        consumption = await fetch_function(user_email, limit)
        if consumption:
            consumption_cache.set(cache_key, consumption)
        return consumption or []
    except Exception as e:
        print(f"[cache] Error fetching consumption history: {e}")
        return []


def invalidate_user_cache(user_email: str) -> None:
    """
    Invalidate all cache entries for a specific user.
    Call this when user data changes.
    
    Args:
        user_email: User's email identifier
    """
    # Clear user profile cache
    user_profile_cache.delete(f"user_profile:{user_email}")
    
    # Clear meal plans cache
    meal_plan_cache.delete(f"meal_plans:{user_email}")
    
    # Clear consumption cache (multiple keys possible due to different limits)
    keys_to_delete = []
    for key in consumption_cache.cache.keys():
        if key.startswith(f"consumption:{user_email}:"):
            keys_to_delete.append(key)
    
    for key in keys_to_delete:
        consumption_cache.delete(key)
    
    print(f"[cache] Invalidated all cache entries for {user_email}")


def invalidate_consumption_cache(user_email: str) -> None:
    """
    Invalidate consumption cache for a user (when new consumption is logged).
    
    Args:
        user_email: User's email identifier
    """
    keys_to_delete = []
    for key in consumption_cache.cache.keys():
        if key.startswith(f"consumption:{user_email}:"):
            keys_to_delete.append(key)
    
    for key in keys_to_delete:
        consumption_cache.delete(key)
    
    print(f"[cache] Invalidated consumption cache for {user_email}")


def invalidate_meal_plan_cache(user_email: str) -> None:
    """
    Invalidate meal plan cache for a user (when meal plan is updated).
    
    Args:
        user_email: User's email identifier
    """
    meal_plan_cache.delete(f"meal_plans:{user_email}")
    print(f"[cache] Invalidated meal plan cache for {user_email}")


def invalidate_all_meal_plan_caches(user_email: str) -> None:
    """
    ROBUST cache invalidation - clears ALL possible cached meal plan data.
    This function ensures deleted meal plans don't reappear from any cache layer.
    
    Args:
        user_email: User's email identifier
    """
    # Clear primary meal plan cache
    meal_plan_cache.delete(f"meal_plans:{user_email}")
    
    # Clear any date-specific meal plan caches (today's plan, etc.)
    from datetime import datetime, timedelta
    
    # Clear caches for the last 30 days to be thorough
    today = datetime.utcnow().date()
    for i in range(30):
        date_key = (today - timedelta(days=i)).isoformat()
        meal_plan_cache.delete(f"{user_email}_{date_key}")
        
    # Clear fast database service cache if it exists
    try:
        from services.fast_database_service import fast_db
        if hasattr(fast_db, '_cache'):
            cache_key = f"meal_plans_{user_email}"
            if cache_key in fast_db._cache:
                del fast_db._cache[cache_key]
                if hasattr(fast_db, '_cache_timestamps') and cache_key in fast_db._cache_timestamps:
                    del fast_db._cache_timestamps[cache_key]
                print(f"[cache] Cleared fast_db meal plan cache for {user_email}")
    except Exception as e:
        print(f"[cache] Warning: Could not clear fast_db cache: {e}")
    
    # Clear ultra-fast meal service cache if it exists
    try:
        from services.ultra_fast_meal_service import _meal_plan_cache, _cache_timestamps
        keys_to_remove = [key for key in _meal_plan_cache.keys() if key.startswith(user_email)]
        for key in keys_to_remove:
            del _meal_plan_cache[key]
            if key in _cache_timestamps:
                del _cache_timestamps[key]
        if keys_to_remove:
            print(f"[cache] Cleared ultra_fast_meal_service cache for {user_email}: {len(keys_to_remove)} entries")
    except Exception as e:
        print(f"[cache] Warning: Could not clear ultra_fast_meal_service cache: {e}")
    
    print(f"[cache] COMPREHENSIVE meal plan cache invalidation completed for {user_email}")


def get_cache_stats() -> Dict[str, Any]:
    """Get statistics for all cache instances."""
    return {
        'user_profiles': user_profile_cache.get_stats(),
        'meal_plans': meal_plan_cache.get_stats(),
        'consumption': consumption_cache.get_stats()
    }


def clear_all_caches() -> None:
    """Clear all caches - useful for debugging or maintenance."""
    user_profile_cache.clear()
    meal_plan_cache.clear()
    consumption_cache.clear()
    print("[cache] All caches cleared")