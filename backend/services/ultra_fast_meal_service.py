"""
Ultra-fast meal plan service with aggressive caching and optimizations.
Extracted from main.py for performance.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
from functools import lru_cache
import json

# Import only when needed to reduce startup time
def get_dependencies():
    """Lazy import of heavy dependencies"""
    from services.fast_database_service import get_user_meal_plans_cached, save_meal_plan_optimized
    from services.openai_service import robust_openai_call
    from services.preload_service import get_quick_meal_templates
    return {
        'get_user_meal_plans': get_user_meal_plans_cached,
        'save_meal_plan': save_meal_plan_optimized,
        'robust_openai_call': robust_openai_call,
        'get_quick_meal_templates': get_quick_meal_templates
    }

# Cache for frequently accessed meal plans
_meal_plan_cache = {}
_cache_timestamps = {}
CACHE_DURATION = 300  # 5 minutes cache

@lru_cache(maxsize=128)
def get_fallback_meals(cuisine_type: str = "international", is_vegetarian: bool = False):
    """Fast fallback meals with caching"""
    if 'vegetarian' in cuisine_type.lower() or is_vegetarian:
        return {
            "breakfast": "Steel-cut oats with almond milk and fresh berries",
            "lunch": "Quinoa Buddha bowl with roasted vegetables and tahini",
            "dinner": "Lentil curry with brown rice and steamed broccoli", 
            "snack": "Apple slices with almond butter"
        }
    else:
        return {
            "breakfast": "Greek yogurt with berries and nuts",
            "lunch": "Grilled chicken salad with mixed vegetables",
            "dinner": "Baked salmon with sweet potato and steamed vegetables",
            "snack": "Hummus with cucumber slices"
        }

async def get_todays_meal_plan_ultra_fast(user_email: str, user_profile: dict) -> dict:
    """⚡ Ultra-fast today's meal plan with aggressive caching and preloaded data"""
    
    # Check cache first
    cache_key = f"{user_email}_{datetime.utcnow().date().isoformat()}"
    current_time = datetime.utcnow().timestamp()
    
    if (cache_key in _meal_plan_cache and 
        cache_key in _cache_timestamps and
        current_time - _cache_timestamps[cache_key] < CACHE_DURATION):
        return _meal_plan_cache[cache_key]
    
    try:
        deps = get_dependencies()
        
        # Get meal plans with ultra-fast cached database service
        meal_plans = await deps['get_user_meal_plans'](user_email)
        
        today = datetime.utcnow().date()
        todays_plan = None
        
        # Quick search for today's plan (limit to 3 for speed)
        for plan in meal_plans[:3]:
            plan_date = plan.get("date")
            if plan_date:
                try:
                    if datetime.fromisoformat(plan_date).date() == today:
                        todays_plan = plan
                        break
                except:
                    continue
        
        # If no today's plan, use preloaded templates for speed
        if not todays_plan:
            dietary_features = user_profile.get('dietaryFeatures', [])
            is_vegetarian = any('vegetarian' in str(f).lower() for f in dietary_features)
            
            # Use preloaded templates for maximum speed
            template_type = 'vegetarian' if is_vegetarian else 'standard'
            templates = deps['get_quick_meal_templates'](template_type)
            
            if not templates:  # Fallback to cached templates
                templates = get_fallback_meals(is_vegetarian=is_vegetarian) 
            
            todays_plan = {
                "id": f"template_{user_email}_{today.isoformat()}",
                "date": today.isoformat(),
                "type": "preloaded_template",
                "meals": {
                    "breakfast": templates.get('breakfast', ['Oatmeal with berries'])[0],
                    "lunch": templates.get('lunch', ['Healthy salad'])[0],
                    "dinner": templates.get('dinner', ['Balanced dinner'])[0],
                    "snack": templates.get('snacks', ['Healthy snack'])[0]
                },
                "dailyCalories": int(user_profile.get('calorieTarget', '2000')),
                "created_at": datetime.utcnow().isoformat(),
                "optimization_note": "⚡ Generated with preloaded templates for maximum speed"
            }
        
        # Cache the result
        _meal_plan_cache[cache_key] = todays_plan
        _cache_timestamps[cache_key] = current_time
        
        return todays_plan
        
    except Exception as e:
        print(f"[ULTRA_FAST] Error: {e}, using emergency fallback")
        # Emergency fallback with minimal processing
        return {
            "id": f"emergency_{datetime.utcnow().timestamp()}",
            "date": datetime.utcnow().date().isoformat(),
            "type": "emergency_fallback",
            "meals": {
                "breakfast": "Quick oats with fruit",
                "lunch": "Simple salad",
                "dinner": "Light protein with vegetables", 
                "snack": "Fresh fruit"
            },
            "dailyCalories": 2000,
            "created_at": datetime.utcnow().isoformat()
        }

async def create_adaptive_meal_plan_ultra_fast(user_email: str, user_profile: dict, payload: dict) -> dict:
    """Ultra-fast adaptive meal plan creation"""
    
    try:
        deps = get_dependencies()
        
        # Get basic parameters quickly
        days = min(int(payload.get("days", 3)), 7)  # Cap at 7 days for speed
        target_calories = int(user_profile.get("calorieTarget", "2000"))
        
        # Fast dietary analysis
        dietary_features = user_profile.get("dietaryFeatures", [])
        dietary_restrictions = user_profile.get("dietaryRestrictions", [])
        allergies = user_profile.get("allergies", [])
        
        is_vegetarian = any('vegetarian' in str(f).lower() for f in dietary_features + dietary_restrictions)
        
        # Quick meal generation
        fallback_meals = get_fallback_meals(is_vegetarian=is_vegetarian)
        
        # Generate plan data
        meal_plan_data = {
            "plan_name": f"Ultra Fast Plan - {datetime.now().strftime('%Y-%m-%d')}",
            "duration_days": days,
            "dailyCalories": target_calories,
            "breakfast": [fallback_meals["breakfast"]] * days,
            "lunch": [fallback_meals["lunch"]] * days,
            "dinner": [fallback_meals["dinner"]] * days,
            "snacks": [fallback_meals["snack"]] * days,
            "macronutrients": {
                "protein": int(target_calories * 0.2 / 4),
                "carbs": int(target_calories * 0.45 / 4), 
                "fats": int(target_calories * 0.35 / 9)
            },
            "user_id": user_email,
            "created_at": datetime.utcnow().isoformat(),
            "type": "ultra_fast_adaptive",
            "plan_type": "adaptive_speed_optimized"
        }
        
        # Save in background to not block response
        async def save_in_background():
            try:
                await deps['save_meal_plan'](user_email, meal_plan_data)
            except Exception as e:
                print(f"[ULTRA_FAST] Background save error: {e}")
        
        asyncio.create_task(save_in_background())
        
        return {
            "success": True,
            "message": "Ultra-fast adaptive meal plan created!",
            "meal_plan": meal_plan_data
        }
        
    except Exception as e:
        print(f"[ULTRA_FAST] Adaptive plan error: {e}")
        raise Exception(f"Failed to create ultra-fast meal plan: {str(e)}")

def clear_meal_plan_cache():
    """Clear meal plan cache"""
    global _meal_plan_cache, _cache_timestamps
    _meal_plan_cache.clear()
    _cache_timestamps.clear()