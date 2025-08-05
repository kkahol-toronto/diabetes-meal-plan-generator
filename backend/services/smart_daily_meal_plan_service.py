"""
Comprehensive Smart Daily Meal Plan Service

This service provides an interconnected meal planning system that integrates:
1. User's comprehensive health profile (goals, preferences, medical conditions)
2. User's past consumption history 
3. User's past meal plans from meal history
4. Real-time recalibration based on actual consumption vs planned meals

Features:
- Persistent daily meal plans (same plan all day until midnight reset)
- Dynamic recalibration when user eats different foods than planned
- Multiple food logging display with proper separation
- Macro goal adherence through intelligent meal adjustments
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import traceback
from database import (
    interactions_container, 
    get_user_consumption_history,
    get_user_meal_plans,
    get_user_by_email
)
# Note: We generate basic meal templates within this service to avoid complex dependencies


class SmartDailyMealPlanService:
    """Comprehensive Smart Daily Meal Plan Service"""
    
    def __init__(self):
        self.meal_types = ["breakfast", "lunch", "dinner", "snack"]
    
    async def get_smart_daily_meal_plan(self, user_email: str, user_profile: Dict) -> Dict[str, Any]:
        """
        Main entry point for Smart Daily Meal Plan generation.
        
        Returns comprehensive meal plan with:
        - Today's planned meals based on health profile + meal history
        - User's actual consumption for each meal type
        - Recalibrated remaining meals if needed
        - Macro progress tracking
        """
        try:
            print(f"[SmartDailyMealPlan] Getting smart meal plan for {user_email}")
            
            today_date = datetime.utcnow().strftime("%Y-%m-%d")
            user_timezone = user_profile.get("timezone", "UTC")
            
            # Check for existing plan first (persistent throughout the day)
            existing_plan = await self._get_existing_daily_plan(user_email, today_date)
            
            if existing_plan:
                print(f"[SmartDailyMealPlan] Found existing plan for {today_date}")
                
                # Get today's consumption to check if recalibration is needed
                today_consumption = await self._get_today_consumption(user_email, user_timezone)
                
                # Check if recalibration is needed
                if await self._needs_recalibration(existing_plan, today_consumption):
                    print(f"[SmartDailyMealPlan] Recalibration needed based on consumption changes")
                    recalibrated_plan = await self._recalibrate_meal_plan(
                        existing_plan, today_consumption, user_profile
                    )
                    
                    # Update the stored plan
                    await self._update_daily_plan(user_email, today_date, recalibrated_plan)
                    return recalibrated_plan
                else:
                    # Add consumption data to existing plan
                    return await self._add_consumption_to_plan(existing_plan, today_consumption)
            
            # Generate new plan for today
            print(f"[SmartDailyMealPlan] Generating new plan for {today_date}")
            new_plan = await self._generate_new_daily_plan(user_email, user_profile, today_date)
            
            # Save the new plan
            await self._save_daily_plan(user_email, today_date, new_plan)
            
            return new_plan
            
        except Exception as e:
            print(f"[SmartDailyMealPlan] Error: {str(e)}")
            print(f"[SmartDailyMealPlan] Traceback: {traceback.format_exc()}")
            raise Exception(f"Failed to get smart daily meal plan: {str(e)}")
    
    async def _generate_new_daily_plan(self, user_email: str, user_profile: Dict, date: str) -> Dict[str, Any]:
        """Generate a new daily meal plan from scratch"""
        try:
            print(f"[SmartDailyMealPlan] Generating new daily plan for {user_email}")
            
            # Get the three key data sources
            health_profile = user_profile
            consumption_history = await get_user_consumption_history(user_email, limit=100)
            meal_plan_history = await get_user_meal_plans(user_email)
            
            # Determine meal configuration from health profile
            meal_config = self._get_meal_configuration(health_profile)
            
            # Check if we have a recent meal plan to use as base
            base_meal_plan = None
            if meal_plan_history:
                # Look for meal plans from the last 7 days
                recent_plans = self._filter_recent_meal_plans(meal_plan_history, days=7)
                if recent_plans:
                    base_meal_plan = recent_plans[0]  # Most recent
                    print(f"[SmartDailyMealPlan] Using recent meal plan as base")
            
            # Generate or adapt meal plan
            if base_meal_plan:
                daily_meals = await self._adapt_from_existing_plan(base_meal_plan, health_profile, meal_config)
            else:
                daily_meals = await self._generate_from_health_profile(health_profile, meal_config)
            
            # Get today's consumption
            user_timezone = health_profile.get("timezone", "UTC")
            today_consumption = await self._get_today_consumption(user_email, user_timezone)
            
            # Calculate macro progress
            macro_progress = self._calculate_macro_progress(daily_meals, today_consumption, health_profile)
            
            # Build comprehensive plan
            plan = {
                "date": date,
                "user_email": user_email,
                "meals": daily_meals,
                "consumption": self._format_consumption_by_meal_type(today_consumption),
                "macro_progress": macro_progress,
                "meal_configuration": meal_config,
                "recalibration_history": [],
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat()
            }
            
            return plan
            
        except Exception as e:
            print(f"[SmartDailyMealPlan] Error generating new plan: {str(e)}")
            raise
    
    def _get_meal_configuration(self, health_profile: Dict) -> Dict[str, Any]:
        """Extract meal configuration from health profile"""
        try:
            # Default configuration
            config = {
                "meal_count": 4,  # breakfast, lunch, dinner, snack
                "active_meals": ["breakfast", "lunch", "dinner", "snack"],
                "calorie_goal": 2000,
                "protein_goal": 150,
                "carb_goal": 250,
                "fat_goal": 67
            }
            
            # Extract goals from health profile
            if health_profile.get("calorieTarget"):
                try:
                    config["calorie_goal"] = int(health_profile["calorieTarget"])
                except:
                    pass
            
            if health_profile.get("proteinTarget"):
                try:
                    config["protein_goal"] = int(health_profile["proteinTarget"])
                except:
                    pass
            
            # Check macro goals
            macro_goals = health_profile.get("macroGoals", {})
            if macro_goals.get("protein"):
                config["protein_goal"] = macro_goals["protein"]
            if macro_goals.get("carbs"):
                config["carb_goal"] = macro_goals["carbs"]
            if macro_goals.get("fat"):
                config["fat_goal"] = macro_goals["fat"]
            
            # Check eating schedule for meal count/timing
            eating_schedule = health_profile.get("eatingSchedule", "")
            if "3" in eating_schedule or "three" in eating_schedule.lower():
                config["meal_count"] = 3
                config["active_meals"] = ["breakfast", "lunch", "dinner"]
            elif "5" in eating_schedule or "five" in eating_schedule.lower():
                config["meal_count"] = 5
                config["active_meals"] = ["breakfast", "snack1", "lunch", "snack2", "dinner"]
            
            print(f"[SmartDailyMealPlan] Meal configuration: {config}")
            return config
            
        except Exception as e:
            print(f"[SmartDailyMealPlan] Error getting meal config: {str(e)}")
            # Return default config
            return {
                "meal_count": 4,
                "active_meals": ["breakfast", "lunch", "dinner", "snack"],
                "calorie_goal": 2000,
                "protein_goal": 150,
                "carb_goal": 250,
                "fat_goal": 67
            }
    
    async def _adapt_from_existing_plan(self, base_plan: Dict, health_profile: Dict, meal_config: Dict) -> Dict[str, Any]:
        """Adapt meals from existing meal plan to today's needs"""
        try:
            print(f"[SmartDailyMealPlan] Adapting from existing meal plan")
            
            adapted_meals = {}
            
            # Extract meals from base plan
            base_meals = base_plan.get("meal_plan", {})
            
            for meal_type in meal_config["active_meals"]:
                if meal_type in base_meals and base_meals[meal_type]:
                    # Use the meal from base plan
                    base_meal = base_meals[meal_type]
                    adapted_meals[meal_type] = {
                        "meal_name": base_meal.get("meal_name", ""),
                        "description": base_meal.get("description", ""),
                        "ingredients": base_meal.get("ingredients", []),
                        "nutritional_info": base_meal.get("nutritional_info", {}),
                        "preparation_time": base_meal.get("preparation_time", "15 minutes"),
                        "source": "adapted_from_history"
                    }
                else:
                    # Generate new meal for this slot
                    adapted_meals[meal_type] = await self._generate_single_meal(meal_type, health_profile)
            
            return adapted_meals
            
        except Exception as e:
            print(f"[SmartDailyMealPlan] Error adapting from existing plan: {str(e)}")
            # Fallback to generating from health profile
            return await self._generate_from_health_profile(health_profile, meal_config)
    
    async def _generate_from_health_profile(self, health_profile: Dict, meal_config: Dict) -> Dict[str, Any]:
        """Generate meals based on health profile when no meal history available"""
        try:
            print(f"[SmartDailyMealPlan] Generating meals from health profile")
            
            meals = {}
            
            # Calculate calories per meal
            total_calories = meal_config["calorie_goal"]
            calories_per_meal = total_calories // len(meal_config["active_meals"])
            
            for meal_type in meal_config["active_meals"]:
                meals[meal_type] = await self._generate_single_meal(meal_type, health_profile, calories_per_meal)
            
            return meals
            
        except Exception as e:
            print(f"[SmartDailyMealPlan] Error generating from health profile: {str(e)}")
            raise
    
    async def _generate_single_meal(self, meal_type: str, health_profile: Dict, target_calories: int = 500) -> Dict[str, Any]:
        """Generate a single meal based on health profile"""
        try:
            # Extract dietary preferences
            dietary_restrictions = health_profile.get("dietaryRestrictions", [])
            dietary_features = health_profile.get("dietaryFeatures", [])
            allergies = health_profile.get("allergies", [])
            strong_dislikes = health_profile.get("strongDislikes", [])
            diet_type = health_profile.get("dietType", [])
            
            # Simple meal generation based on meal type and preferences
            meal_templates = {
                "breakfast": {
                    "default": {
                        "meal_name": "Balanced Breakfast Bowl",
                        "description": "Nutritious breakfast with protein, healthy carbs, and vegetables",
                        "ingredients": ["oats", "berries", "greek yogurt", "nuts", "honey"],
                        "preparation_time": "10 minutes"
                    },
                    "vegetarian": {
                        "meal_name": "Vegetarian Breakfast Scramble",
                        "description": "Protein-rich vegetarian breakfast with eggs and vegetables",
                        "ingredients": ["eggs", "spinach", "mushrooms", "bell peppers", "whole grain toast"],
                        "preparation_time": "15 minutes"
                    }
                },
                "lunch": {
                    "default": {
                        "meal_name": "Mediterranean Chicken Salad",
                        "description": "Fresh salad with lean protein and healthy fats",
                        "ingredients": ["chicken breast", "mixed greens", "cucumber", "tomatoes", "olive oil", "feta cheese"],
                        "preparation_time": "20 minutes"
                    },
                    "vegetarian": {
                        "meal_name": "Quinoa Power Bowl",
                        "description": "Protein-packed vegetarian bowl with quinoa and legumes",
                        "ingredients": ["quinoa", "chickpeas", "roasted vegetables", "avocado", "tahini dressing"],
                        "preparation_time": "25 minutes"
                    }
                },
                "dinner": {
                    "default": {
                        "meal_name": "Grilled Salmon with Vegetables",
                        "description": "Omega-3 rich salmon with fiber-rich vegetables",
                        "ingredients": ["salmon fillet", "broccoli", "sweet potato", "asparagus", "lemon"],
                        "preparation_time": "30 minutes"
                    },
                    "vegetarian": {
                        "meal_name": "Lentil and Vegetable Curry",
                        "description": "Protein-rich vegetarian curry with complex carbohydrates",
                        "ingredients": ["red lentils", "coconut milk", "mixed vegetables", "brown rice", "curry spices"],
                        "preparation_time": "35 minutes"
                    }
                },
                "snack": {
                    "default": {
                        "meal_name": "Greek Yogurt with Berries",
                        "description": "High-protein snack with antioxidants",
                        "ingredients": ["greek yogurt", "mixed berries", "almonds", "chia seeds"],
                        "preparation_time": "5 minutes"
                    },
                    "vegetarian": {
                        "meal_name": "Hummus and Veggie Sticks",
                        "description": "Plant-based protein with fresh vegetables",
                        "ingredients": ["hummus", "carrots", "celery", "bell peppers", "cucumber"],
                        "preparation_time": "5 minutes"
                    }
                }
            }
            
            # Select template based on dietary preferences
            template_type = "vegetarian" if any(d.lower() in ["vegetarian", "vegan"] for d in dietary_features + diet_type) else "default"
            
            if meal_type in meal_templates and template_type in meal_templates[meal_type]:
                template = meal_templates[meal_type][template_type]
            else:
                template = meal_templates["snack"]["default"]  # Fallback
            
            # Calculate nutritional info based on target calories
            protein_ratio = 0.25  # 25% protein
            carb_ratio = 0.45     # 45% carbs  
            fat_ratio = 0.30      # 30% fat
            
            nutritional_info = {
                "calories": target_calories,
                "protein": round((target_calories * protein_ratio) / 4),  # 4 cal/g protein
                "carbohydrates": round((target_calories * carb_ratio) / 4),  # 4 cal/g carbs
                "fat": round((target_calories * fat_ratio) / 9),  # 9 cal/g fat
                "fiber": round(target_calories / 100),  # Rough estimate
                "sugar": round(target_calories / 200)   # Rough estimate
            }
            
            return {
                "meal_name": template["meal_name"],
                "description": template["description"],
                "ingredients": template["ingredients"],
                "nutritional_info": nutritional_info,
                "preparation_time": template["preparation_time"],
                "source": "generated_from_profile"
            }
            
        except Exception as e:
            print(f"[SmartDailyMealPlan] Error generating single meal: {str(e)}")
            # Return basic fallback meal
            return {
                "meal_name": f"Healthy {meal_type.title()}",
                "description": f"Balanced {meal_type} meal",
                "ingredients": ["balanced ingredients"],
                "nutritional_info": {"calories": target_calories, "protein": 25, "carbohydrates": 50, "fat": 15},
                "preparation_time": "15 minutes",
                "source": "fallback"
            }
    
    async def _get_today_consumption(self, user_email: str, user_timezone: str = "UTC") -> List[Dict]:
        """Get today's consumption records for the user"""
        try:
            print(f"[SmartDailyMealPlan] Getting today's consumption for {user_email}")
            
            # Calculate today's date range in user's timezone
            import pytz
            from datetime import datetime, timezone
            
            try:
                user_tz = pytz.timezone(user_timezone)
                utc_now = datetime.now(timezone.utc)
                local_now = utc_now.astimezone(user_tz)
                
                # Get start and end of today in user's timezone
                local_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
                local_end = local_now.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                # Convert back to UTC for database query
                start_utc = local_start.astimezone(timezone.utc)
                end_utc = local_end.astimezone(timezone.utc)
                
            except Exception as tz_error:
                print(f"[SmartDailyMealPlan] Timezone error, using UTC: {tz_error}")
                utc_now = datetime.now(timezone.utc)
                start_utc = utc_now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_utc = utc_now.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # Query consumption records for today
            query = """
            SELECT * FROM c 
            WHERE c.type = 'consumption_record' 
            AND c.user_id = @user_id
            AND c.timestamp >= @start_time
            AND c.timestamp <= @end_time
            ORDER BY c.timestamp ASC
            """
            
            parameters = [
                {"name": "@user_id", "value": user_email},
                {"name": "@start_time", "value": start_utc.isoformat()},
                {"name": "@end_time", "value": end_utc.isoformat()}
            ]
            
            consumption_records = list(interactions_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            print(f"[SmartDailyMealPlan] Found {len(consumption_records)} consumption records for today")
            return consumption_records
            
        except Exception as e:
            print(f"[SmartDailyMealPlan] Error getting today's consumption: {str(e)}")
            return []
    
    def _format_consumption_by_meal_type(self, consumption_records: List[Dict]) -> Dict[str, List[Dict]]:
        """Format consumption records grouped by meal type with multiple food support"""
        try:
            consumption_by_meal = {
                "breakfast": [],
                "lunch": [], 
                "dinner": [],
                "snack": []
            }
            
            for record in consumption_records:
                meal_type = record.get("meal_type", "snack")
                if meal_type not in consumption_by_meal:
                    meal_type = "snack"  # Default fallback
                
                consumption_by_meal[meal_type].append({
                    "food_name": record.get("food_name", ""),
                    "estimated_portion": record.get("estimated_portion", ""),
                    "nutritional_info": record.get("nutritional_info", {}),
                    "timestamp": record.get("timestamp", ""),
                    "id": record.get("id", "")
                })
            
            return consumption_by_meal
            
        except Exception as e:
            print(f"[SmartDailyMealPlan] Error formatting consumption: {str(e)}")
            return {"breakfast": [], "lunch": [], "dinner": [], "snack": []}
    
    def _calculate_macro_progress(self, daily_meals: Dict, today_consumption: List[Dict], health_profile: Dict) -> Dict[str, Any]:
        """Calculate macro progress based on planned meals and actual consumption"""
        try:
            meal_config = self._get_meal_configuration(health_profile)
            
            # Calculate total planned macros
            planned_totals = {"calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0}
            for meal_type, meal_data in daily_meals.items():
                nutrition = meal_data.get("nutritional_info", {})
                planned_totals["calories"] += nutrition.get("calories", 0)
                planned_totals["protein"] += nutrition.get("protein", 0)
                planned_totals["carbohydrates"] += nutrition.get("carbohydrates", 0)
                planned_totals["fat"] += nutrition.get("fat", 0)
            
            # Calculate actual consumed macros
            consumed_totals = {"calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0}
            for record in today_consumption:
                nutrition = record.get("nutritional_info", {})
                consumed_totals["calories"] += nutrition.get("calories", 0)
                consumed_totals["protein"] += nutrition.get("protein", 0)
                consumed_totals["carbohydrates"] += nutrition.get("carbohydrates", 0)
                consumed_totals["fat"] += nutrition.get("fat", 0)
            
            # Calculate remaining macros
            remaining_totals = {}
            for macro in ["calories", "protein", "carbohydrates", "fat"]:
                remaining_totals[macro] = max(0, planned_totals[macro] - consumed_totals[macro])
            
            # Progress percentages based on goals
            goals = {
                "calories": meal_config["calorie_goal"],
                "protein": meal_config["protein_goal"],
                "carbohydrates": meal_config["carb_goal"],
                "fat": meal_config["fat_goal"]
            }
            
            progress_percentages = {}
            for macro, goal in goals.items():
                if goal > 0:
                    progress_percentages[macro] = min(100, round((consumed_totals[macro] / goal) * 100, 1))
                else:
                    progress_percentages[macro] = 0
            
            return {
                "planned": planned_totals,
                "consumed": consumed_totals,
                "remaining": remaining_totals,
                "goals": goals,
                "progress_percentages": progress_percentages
            }
            
        except Exception as e:
            print(f"[SmartDailyMealPlan] Error calculating macro progress: {str(e)}")
            return {
                "planned": {"calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0},
                "consumed": {"calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0},
                "remaining": {"calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0},
                "goals": {"calories": 2000, "protein": 150, "carbohydrates": 250, "fat": 67},
                "progress_percentages": {"calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0}
            }
    
    def _filter_recent_meal_plans(self, meal_plans: List[Dict], days: int = 7) -> List[Dict]:
        """Filter meal plans from the last N days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            recent_plans = []
            for plan in meal_plans:
                created_at = plan.get("created_at", "")
                if created_at:
                    try:
                        plan_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        if plan_date >= cutoff_date:
                            recent_plans.append(plan)
                    except:
                        continue
            
            # Sort by creation date (newest first)
            recent_plans.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return recent_plans
            
        except Exception as e:
            print(f"[SmartDailyMealPlan] Error filtering recent plans: {str(e)}")
            return []
    
    async def _needs_recalibration(self, existing_plan: Dict, today_consumption: List[Dict]) -> bool:
        """Check if the meal plan needs recalibration based on consumption changes"""
        try:
            # Get the last consumption timestamp from the plan
            last_consumption_check = existing_plan.get("last_consumption_check", "")
            
            if not today_consumption:
                return False
            
            # Check if there are new consumption records since last check
            if not last_consumption_check:
                return len(today_consumption) > 0
            
            # Parse last check timestamp
            try:
                last_check_dt = datetime.fromisoformat(last_consumption_check.replace('Z', '+00:00'))
            except:
                return True  # If we can't parse, assume recalibration needed
            
            # Check if any consumption records are newer than last check
            for record in today_consumption:
                record_timestamp = record.get("timestamp", "")
                if record_timestamp:
                    try:
                        record_dt = datetime.fromisoformat(record_timestamp.replace('Z', '+00:00'))
                        if record_dt > last_check_dt:
                            return True
                    except:
                        continue
            
            return False
            
        except Exception as e:
            print(f"[SmartDailyMealPlan] Error checking recalibration need: {str(e)}")
            return False
    
    async def _recalibrate_meal_plan(self, existing_plan: Dict, today_consumption: List[Dict], health_profile: Dict) -> Dict[str, Any]:
        """Recalibrate meal plan based on actual consumption vs planned meals"""
        try:
            print(f"[SmartDailyMealPlan] Recalibrating meal plan based on consumption")
            
            # Start with existing plan
            recalibrated_plan = existing_plan.copy()
            
            # Update consumption data
            consumption_by_meal = self._format_consumption_by_meal_type(today_consumption)
            recalibrated_plan["consumption"] = consumption_by_meal
            
            # Get meal configuration
            meal_config = self._get_meal_configuration(health_profile)
            
            # Calculate what was actually consumed vs planned for each meal
            consumed_macros_by_meal = {}
            planned_macros_by_meal = {}
            
            for meal_type in meal_config["active_meals"]:
                # Calculate consumed macros for this meal type
                consumed_macros = {"calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0}
                for consumption in consumption_by_meal.get(meal_type, []):
                    nutrition = consumption.get("nutritional_info", {})
                    consumed_macros["calories"] += nutrition.get("calories", 0)
                    consumed_macros["protein"] += nutrition.get("protein", 0)
                    consumed_macros["carbohydrates"] += nutrition.get("carbohydrates", 0)
                    consumed_macros["fat"] += nutrition.get("fat", 0)
                
                consumed_macros_by_meal[meal_type] = consumed_macros
                
                # Get planned macros for this meal type
                planned_meal = recalibrated_plan["meals"].get(meal_type, {})
                planned_nutrition = planned_meal.get("nutritional_info", {})
                planned_macros_by_meal[meal_type] = {
                    "calories": planned_nutrition.get("calories", 0),
                    "protein": planned_nutrition.get("protein", 0),
                    "carbohydrates": planned_nutrition.get("carbohydrates", 0),
                    "fat": planned_nutrition.get("fat", 0)
                }
            
            # Determine current time to know which meals are remaining
            current_hour = datetime.utcnow().hour  # Simplified - could use user timezone
            remaining_meals = self._get_remaining_meals(current_hour, meal_config["active_meals"])
            
            if remaining_meals:
                print(f"[SmartDailyMealPlan] Remaining meals to recalibrate: {remaining_meals}")
                
                # Calculate total macro deviation (consumed vs planned so far)
                total_deviation = {"calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0}
                
                for meal_type in meal_config["active_meals"]:
                    if meal_type not in remaining_meals:  # Only count meals that should have been eaten
                        consumed = consumed_macros_by_meal[meal_type]
                        planned = planned_macros_by_meal[meal_type]
                        
                        for macro in total_deviation.keys():
                            total_deviation[macro] += consumed[macro] - planned[macro]
                
                # Redistribute the deviation across remaining meals
                if len(remaining_meals) > 0:
                    deviation_per_meal = {}
                    for macro in total_deviation.keys():
                        deviation_per_meal[macro] = -total_deviation[macro] / len(remaining_meals)
                    
                    # Update remaining meals with recalibrated nutrition
                    for meal_type in remaining_meals:
                        if meal_type in recalibrated_plan["meals"]:
                            original_nutrition = recalibrated_plan["meals"][meal_type]["nutritional_info"]
                            
                            # Apply recalibration
                            recalibrated_nutrition = {}
                            for macro in deviation_per_meal.keys():
                                original_value = original_nutrition.get(macro, 0)
                                adjustment = deviation_per_meal[macro]
                                recalibrated_nutrition[macro] = max(0, round(original_value + adjustment))
                            
                            recalibrated_plan["meals"][meal_type]["nutritional_info"] = recalibrated_nutrition
                            
                            # Update meal description to indicate recalibration
                            original_desc = recalibrated_plan["meals"][meal_type].get("description", "")
                            recalibrated_plan["meals"][meal_type]["description"] = f"{original_desc} (Recalibrated based on your consumption)"
            
            # Update macro progress
            recalibrated_plan["macro_progress"] = self._calculate_macro_progress(
                recalibrated_plan["meals"], today_consumption, health_profile
            )
            
            # Add recalibration record
            recalibration_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "reason": "consumption_deviation",
                "remaining_meals": remaining_meals,
                "total_deviation": total_deviation
            }
            
            if "recalibration_history" not in recalibrated_plan:
                recalibrated_plan["recalibration_history"] = []
            
            recalibrated_plan["recalibration_history"].append(recalibration_record)
            recalibrated_plan["last_consumption_check"] = datetime.utcnow().isoformat()
            recalibrated_plan["last_updated"] = datetime.utcnow().isoformat()
            
            return recalibrated_plan
            
        except Exception as e:
            print(f"[SmartDailyMealPlan] Error recalibrating meal plan: {str(e)}")
            # Return plan with updated consumption at minimum
            existing_plan["consumption"] = self._format_consumption_by_meal_type(today_consumption)
            existing_plan["last_consumption_check"] = datetime.utcnow().isoformat()
            return existing_plan
    
    def _get_remaining_meals(self, current_hour: int, active_meals: List[str]) -> List[str]:
        """Determine which meals are remaining based on current time"""
        try:
            # Simple time-based logic (could be enhanced with user preferences)
            meal_times = {
                "breakfast": (5, 11),
                "lunch": (11, 16), 
                "dinner": (16, 22),
                "snack": (0, 24)  # Snacks can be anytime
            }
            
            remaining = []
            
            for meal in active_meals:
                if meal in meal_times:
                    start_hour, end_hour = meal_times[meal]
                    
                    # Check if current time is before the meal time window ends
                    if current_hour < end_hour:
                        remaining.append(meal)
                    elif meal == "snack":  # Snacks are always available
                        remaining.append(meal)
            
            return remaining
            
        except Exception as e:
            print(f"[SmartDailyMealPlan] Error getting remaining meals: {str(e)}")
            return active_meals  # Return all meals as fallback
    
    async def _add_consumption_to_plan(self, existing_plan: Dict, today_consumption: List[Dict]) -> Dict[str, Any]:
        """Add consumption data to existing plan without recalibration"""
        try:
            plan_with_consumption = existing_plan.copy()
            plan_with_consumption["consumption"] = self._format_consumption_by_meal_type(today_consumption)
            plan_with_consumption["last_consumption_check"] = datetime.utcnow().isoformat()
            return plan_with_consumption
            
        except Exception as e:
            print(f"[SmartDailyMealPlan] Error adding consumption to plan: {str(e)}")
            return existing_plan
    
    # Database operations
    async def _get_existing_daily_plan(self, user_email: str, date: str) -> Optional[Dict]:
        """Get existing daily plan from database"""
        try:
            daily_key = f"smart_daily_{user_email}_{date}"
            
            query = """
            SELECT * FROM c
            WHERE c.id = @daily_key
            AND c.type = 'smart_daily_meal_plan'
            """
            
            parameters = [{"name": "@daily_key", "value": daily_key}]
            
            items = list(interactions_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            if items:
                return items[0]
            
            return None
            
        except Exception as e:
            print(f"[SmartDailyMealPlan] Error getting existing plan: {str(e)}")
            return None
    
    async def _save_daily_plan(self, user_email: str, date: str, plan_data: Dict) -> bool:
        """Save daily plan to database"""
        try:
            daily_key = f"smart_daily_{user_email}_{date}"
            
            document = {
                "id": daily_key,
                "type": "smart_daily_meal_plan",
                "user_email": user_email,
                "date": date,
                "plan_data": plan_data,
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat()
            }
            
            interactions_container.upsert_item(document)
            print(f"[SmartDailyMealPlan] Saved daily plan for {user_email} on {date}")
            return True
            
        except Exception as e:
            print(f"[SmartDailyMealPlan] Error saving daily plan: {str(e)}")
            return False
    
    async def _update_daily_plan(self, user_email: str, date: str, updated_plan_data: Dict) -> bool:
        """Update existing daily plan in database"""
        try:
            daily_key = f"smart_daily_{user_email}_{date}"
            
            # Get existing document
            existing_doc = await self._get_existing_daily_plan(user_email, date)
            if not existing_doc:
                return await self._save_daily_plan(user_email, date, updated_plan_data)
            
            # Update the document
            existing_doc["plan_data"] = updated_plan_data
            existing_doc["last_updated"] = datetime.utcnow().isoformat()
            
            interactions_container.replace_item(
                item=existing_doc["id"],
                body=existing_doc
            )
            
            print(f"[SmartDailyMealPlan] Updated daily plan for {user_email} on {date}")
            return True
            
        except Exception as e:
            print(f"[SmartDailyMealPlan] Error updating daily plan: {str(e)}")
            return False


# Global service instance
smart_daily_meal_plan_service = SmartDailyMealPlanService()