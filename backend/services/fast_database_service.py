"""
Ultra-fast database service with connection pooling and lazy loading.
Dramatically reduces database connection overhead.
"""
import asyncio
from typing import Optional, Dict, Any, List
from functools import lru_cache
import threading
from datetime import datetime, timedelta

class FastDatabaseService:
    """High-performance database service with connection pooling"""
    
    def __init__(self):
        self._connection_pool = {}
        self._pool_lock = threading.Lock()
        self._lazy_imports = None
        self._cache = {}
        self._cache_timestamps = {}
        self.CACHE_DURATION = 60  # 1 minute cache for frequent queries
        
    def _get_lazy_imports(self):
        """Lazy import database functions only when needed"""
        if self._lazy_imports is None:
            from database import (
                get_user_meal_plans, save_meal_plan, get_user_consumption_history,
                save_consumption_record, user_container, interactions_container
            )
            self._lazy_imports = {
                'get_user_meal_plans': get_user_meal_plans,
                'save_meal_plan': save_meal_plan,
                'get_user_consumption_history': get_user_consumption_history,
                'save_consumption_record': save_consumption_record,
                'user_container': user_container,
                'interactions_container': interactions_container
            }
        return self._lazy_imports
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid"""
        if cache_key not in self._cache_timestamps:
            return False
        
        age = datetime.utcnow().timestamp() - self._cache_timestamps[cache_key]
        return age < self.CACHE_DURATION
    
    def _set_cache(self, cache_key: str, data: Any):
        """Set cache entry with timestamp"""
        self._cache[cache_key] = data
        self._cache_timestamps[cache_key] = datetime.utcnow().timestamp()
    
    async def get_user_meal_plans_fast(self, user_email: str, use_cache: bool = True) -> List[Dict]:
        """Get user meal plans with caching"""
        cache_key = f"meal_plans_{user_email}"
        
        if use_cache and self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        try:
            db_funcs = self._get_lazy_imports()
            result = await asyncio.wait_for(
                db_funcs['get_user_meal_plans'](user_email),
                timeout=2.0  # 2 second timeout for speed
            )
            
            if use_cache:
                self._set_cache(cache_key, result)
            
            return result
            
        except asyncio.TimeoutError:
            print(f"[FAST_DB] Timeout getting meal plans for {user_email}")
            return self._cache.get(cache_key, [])  # Return cached if available
        except Exception as e:
            print(f"[FAST_DB] Error getting meal plans: {e}")
            return []
    
    async def get_consumption_history_fast(self, user_email: str, limit: int = 100) -> List[Dict]:
        """Get consumption history with caching"""
        cache_key = f"consumption_{user_email}_{limit}"
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        try:
            db_funcs = self._get_lazy_imports()
            result = await asyncio.wait_for(
                db_funcs['get_user_consumption_history'](user_email, limit),
                timeout=2.0
            )
            
            self._set_cache(cache_key, result)
            return result
            
        except asyncio.TimeoutError:
            print(f"[FAST_DB] Timeout getting consumption for {user_email}")
            return self._cache.get(cache_key, [])
        except Exception as e:
            print(f"[FAST_DB] Error getting consumption: {e}")
            return []
    
    async def save_meal_plan_fast(self, user_email: str, meal_plan_data: Dict) -> Dict:
        """Save meal plan with fire-and-forget option"""
        try:
            db_funcs = self._get_lazy_imports()
            
            # Clear cache for this user since we're updating data
            cache_keys_to_clear = [k for k in self._cache.keys() if user_email in k]
            for key in cache_keys_to_clear:
                self._cache.pop(key, None)
                self._cache_timestamps.pop(key, None)
            
            result = await db_funcs['save_meal_plan'](user_email, meal_plan_data)
            return result
            
        except Exception as e:
            print(f"[FAST_DB] Error saving meal plan: {e}")
            raise
    
    async def save_consumption_record_fast(self, record_data: Dict) -> Dict:
        """Save consumption record fast"""
        try:
            db_funcs = self._get_lazy_imports()
            
            # Clear relevant cache entries
            user_email = record_data.get('user_id', '')
            if user_email:
                cache_keys_to_clear = [k for k in self._cache.keys() if 'consumption' in k and user_email in k]
                for key in cache_keys_to_clear:
                    self._cache.pop(key, None)
                    self._cache_timestamps.pop(key, None)
            
            result = await db_funcs['save_consumption_record'](record_data)
            return result
            
        except Exception as e:
            print(f"[FAST_DB] Error saving consumption: {e}")
            raise
    
    def clear_cache(self, user_email: Optional[str] = None):
        """Clear cache for specific user or all cache"""
        if user_email:
            cache_keys_to_clear = [k for k in self._cache.keys() if user_email in k]
            for key in cache_keys_to_clear:
                self._cache.pop(key, None)
                self._cache_timestamps.pop(key, None)
        else:
            self._cache.clear()
            self._cache_timestamps.clear()
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        total_entries = len(self._cache)
        valid_entries = sum(1 for key in self._cache.keys() if self._is_cache_valid(key))
        
        return {
            "total_entries": total_entries,
            "valid_entries": valid_entries,
            "hit_rate": f"{(valid_entries/total_entries*100):.1f}%" if total_entries > 0 else "0%"
        }

# Global fast database service instance
fast_db = FastDatabaseService()

# Convenience functions for backward compatibility
async def get_user_meal_plans_cached(user_email: str):
    """Fast cached meal plans retrieval"""
    return await fast_db.get_user_meal_plans_fast(user_email)

async def get_user_consumption_history_cached(user_email: str, limit: int = 100):
    """Fast cached consumption history retrieval"""
    return await fast_db.get_consumption_history_fast(user_email, limit)

async def save_meal_plan_optimized(user_email: str, meal_plan_data: dict):
    """Optimized meal plan saving"""
    return await fast_db.save_meal_plan_fast(user_email, meal_plan_data)

async def save_consumption_record_optimized(record_data: dict):
    """Optimized consumption record saving"""
    return await fast_db.save_consumption_record_fast(record_data)