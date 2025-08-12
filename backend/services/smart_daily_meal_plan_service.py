"""
Smart Daily Meal Plan Service

This service provides a comprehensive Smart Daily Meal Plan functionality that:
1. Uses user's comprehensive health profile
2. Leverages past consumption history 
3. Adapts from past meal plans in meal plan history
4. Implements real-time recalibration based on consumption vs planned meals
5. Maintains daily persistence (stays same until midnight reset)
6. Formats consumption display with comma and & separators
7. Properly handles snacks from meal plan history
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import json


class SmartDailyMealPlanService:
    def __init__(self):
        self.service_name = "SmartDailyMealPlanService"
    
    async def get_smart_daily_meal_plan(self, user_email: str, user_profile: Dict) -> Dict:
        """
        Generate comprehensive Smart Daily Meal Plan based on:
        - User's comprehensive health profile
        - Past consumption history
        - Past meal plans from meal plan history
        - Real-time recalibration based on actual vs planned consumption
        """
        print(f"[{self.service_name}] Starting Smart Daily Meal Plan generation for {user_email}")
        
        try:
            # Get today's date for consistency
            today_date = datetime.utcnow().date().isoformat()
            
            # Check if we have an existing plan for today (persistence requirement)
            existing_plan = await self._get_existing_daily_plan(user_email, today_date)
            if existing_plan:
                print(f"[{self.service_name}] Found existing plan for today, applying real-time updates")
                return await self._apply_real_time_updates(existing_plan, user_email, user_profile)
            
            # Generate new plan for today
            print(f"[{self.service_name}] Generating new plan for today")
            
            # Step 1: Get meal configuration from user profile
            meal_config = self._get_meal_configuration(user_profile)
            
            # Step 2: Get consumption history for context
            consumption_history = await self._get_consumption_history(user_email)
            today_consumption = await self._get_today_consumption(user_email, user_profile.get("timezone", "UTC"))
            
            # Step 3: Get past meal plans from meal plan history  
            meal_plan_history = await self._get_meal_plan_history(user_email)
            
            # Step 4: Generate meals - prioritize history, fallback to health profile
            meals = {}
            if meal_plan_history:
                print(f"[{self.service_name}] Adapting meals from meal plan history")
                meals = await self._adapt_from_meal_history(meal_config["active_meals"], meal_plan_history)
            
            if not meals or len(meals) < len(meal_config["active_meals"]):
                print(f"[{self.service_name}] Generating missing meals from health profile")
                missing_meals = [meal for meal in meal_config["active_meals"] if meal not in meals]
                generated_meals = await self._generate_from_health_profile(missing_meals, user_profile)
                meals.update(generated_meals)
            
            # Step 5: Apply real-time recalibration based on today's consumption
            consumption_by_meal = self._organize_consumption_by_meal(today_consumption)
            recalibration_history = []
            
            if today_consumption:
                print(f"[{self.service_name}] Applying real-time recalibration based on consumption")
                # Recalibrate remaining meals to fit within remaining goals
                meals, recalibrations = await self._apply_recalibration(meals, consumption_by_meal, user_profile)
                recalibration_history.extend(recalibrations)

            # Always perform a final day-level normalization to ensure the sum of
            # planned calories does not exceed the daily target, even when there
            # is no consumption yet or when meals were adapted from history with
            # fixed estimates.
            try:
                calorie_target = int(user_profile.get("calorieTarget", "2000"))
                normalized, normalization_records = self._normalize_meals_to_daily_target(meals, calorie_target)
                if normalization_records:
                    meals = normalized
                    recalibration_history.extend(normalization_records)
            except Exception as _norm_err:
                # Never break plan generation due to normalization errors
                print(f"[{self.service_name}] Warning: normalization skipped due to: {_norm_err}")
            
            # Step 6: Calculate macro progress
            macro_progress = self._calculate_macro_progress(today_consumption, user_profile)
            
            # Step 7: Build comprehensive response
            comprehensive_plan = {
                "meals": meals,
                "consumption": consumption_by_meal,
                "macro_progress": macro_progress,
                "meal_configuration": meal_config,
                "recalibration_history": recalibration_history,
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
                "plan_date": today_date,
                "user_email": user_email
            }
            
            # Step 8: Save plan for persistence
            await self._save_daily_plan(user_email, today_date, comprehensive_plan)
            
            print(f"[{self.service_name}] Successfully generated Smart Daily Meal Plan")
            return comprehensive_plan
            
        except Exception as e:
            print(f"[{self.service_name}] Error generating meal plan: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e
    
    def _get_meal_configuration(self, user_profile: Dict) -> Dict:
        """Get meal configuration from user's comprehensive health profile"""
        try:
            # Check if user has meal preference in profile
            meals_per_day = user_profile.get("mealsPerDay", 4)  # Default to 4 meals
            
            if meals_per_day == 3:
                active_meals = ["breakfast", "lunch", "dinner"]
            elif meals_per_day == 4:
                active_meals = ["breakfast", "lunch", "dinner", "snack"]
            else:
                # Default fallback
                active_meals = ["breakfast", "lunch", "dinner", "snack"]
            
            return {
                "active_meals": active_meals,
                "meals_per_day": len(active_meals)
            }
        except Exception as e:
            print(f"[{self.service_name}] Error getting meal config: {e}")
            return {
                "active_meals": ["breakfast", "lunch", "dinner", "snack"],
                "meals_per_day": 4
            }
    
    async def _get_consumption_history(self, user_email: str) -> List[Dict]:
        """Get user's past consumption history for context"""
        try:
            from database import interactions_container
            
            # Get last 30 days of consumption for pattern analysis
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            
            query = """
            SELECT * FROM c
            WHERE c.user_id = @user_email
            AND c.type = 'consumption_record'
            AND c.timestamp >= @start_date
            AND c.timestamp <= @end_date
            ORDER BY c.timestamp DESC
            """
            
            parameters = [
                {"name": "@user_email", "value": user_email},
                {"name": "@start_date", "value": start_date.isoformat()},
                {"name": "@end_date", "value": end_date.isoformat()}
            ]
            
            items = list(interactions_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            print(f"[{self.service_name}] Found {len(items)} consumption records in last 30 days")
            return items
            
        except Exception as e:
            print(f"[{self.service_name}] Error getting consumption history: {e}")
            return []
    
    async def _get_today_consumption(self, user_email: str, user_timezone: str = "UTC") -> List[Dict]:
        """Get today's consumption records"""
        try:
            from database import interactions_container
            import pytz
            
            # Calculate today's date range in user's timezone
            if user_timezone != "UTC":
                try:
                    tz = pytz.timezone(user_timezone)
                    local_now = datetime.now(tz)
                except:
                    local_now = datetime.utcnow()
            else:
                local_now = datetime.utcnow()
            
            today_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = local_now.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # Convert to UTC for database query if needed
            if user_timezone != "UTC":
                today_start_utc = today_start.astimezone(timezone.utc)
                today_end_utc = today_end.astimezone(timezone.utc)
            else:
                today_start_utc = today_start
                today_end_utc = today_end
            
            query = """
            SELECT * FROM c
            WHERE c.user_id = @user_email
            AND c.type = 'consumption_record'
            AND c.timestamp >= @start_time
            AND c.timestamp <= @end_time
            ORDER BY c.timestamp ASC
            """
            
            parameters = [
                {"name": "@user_email", "value": user_email},
                {"name": "@start_time", "value": today_start_utc.isoformat()},
                {"name": "@end_time", "value": today_end_utc.isoformat()}
            ]
            
            items = list(interactions_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            print(f"[{self.service_name}] Found {len(items)} consumption records for today")
            return items
            
        except Exception as e:
            print(f"[{self.service_name}] Error getting today's consumption: {e}")
            return []
    
    async def _get_meal_plan_history(self, user_email: str) -> List[Dict]:
        """Get user's past meal plans from meal plan history"""
        try:
            from database import interactions_container
            
            # Get recent meal plans (last 30 days) for adaptation
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            
            query = """
            SELECT * FROM c
            WHERE c.user_id = @user_email
            AND c.type = 'meal_plan'
            AND c.created_at >= @start_date
            ORDER BY c.created_at DESC
            """
            
            parameters = [
                {"name": "@user_email", "value": user_email},
                {"name": "@start_date", "value": start_date.isoformat()}
            ]
            
            items = list(interactions_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            print(f"[{self.service_name}] Found {len(items)} meal plans in history for adaptation")
            return items
            
        except Exception as e:
            print(f"[{self.service_name}] Error getting meal plan history: {e}")
            return []
    
    async def _adapt_from_meal_history(self, active_meals: List[str], meal_plan_history: List[Dict]) -> Dict:
        """Adapt meals from past meal plans in history"""
        adapted_meals = {}
        
        try:
            if not meal_plan_history:
                return adapted_meals
            
            # Use the most recent meal plan as base
            latest_plan = meal_plan_history[0]
            plan_data = latest_plan.get("plan_data", latest_plan)
            
            # Extract meals from the plan data
            base_meals = {}
            if "meals" in plan_data:
                base_meals = plan_data["meals"]
            elif "breakfast" in plan_data or "lunch" in plan_data or "dinner" in plan_data:
                # Direct meal structure
                base_meals = plan_data
            
            print(f"[{self.service_name}] Adapting from meal plan with meals: {list(base_meals.keys())}")
            
            for meal_type in active_meals:
                if meal_type in base_meals and base_meals[meal_type]:
                    # Handle different meal data structures
                    meal_data = base_meals[meal_type]
                    
                    if isinstance(meal_data, str):
                        # Simple string meal name
                        adapted_meals[meal_type] = {
                            "meal_name": meal_data,
                            "description": f"Adapted from your meal plan history",
                            "ingredients": [meal_data],
                            "nutritional_info": self._estimate_nutrition(meal_data, meal_type),
                            "preparation_time": "15 minutes",
                            "source": "adapted_from_history"
                        }
                    elif isinstance(meal_data, dict):
                        # Structured meal data
                        adapted_meals[meal_type] = {
                            "meal_name": meal_data.get("meal_name", meal_data.get("name", f"Planned {meal_type}")),
                            "description": meal_data.get("description", f"Adapted from your meal plan history"),
                            "ingredients": meal_data.get("ingredients", []),
                            "nutritional_info": meal_data.get("nutritional_info", self._estimate_nutrition("", meal_type)),
                            "preparation_time": meal_data.get("preparation_time", "15 minutes"),
                            "source": "adapted_from_history"
                        }
                    elif isinstance(meal_data, list) and len(meal_data) > 0:
                        # Array of meals - take the first one
                        first_meal = meal_data[0]
                        if isinstance(first_meal, str):
                            adapted_meals[meal_type] = {
                                "meal_name": first_meal,
                                "description": f"Adapted from your meal plan history",
                                "ingredients": [first_meal],
                                "nutritional_info": self._estimate_nutrition(first_meal, meal_type),
                                "preparation_time": "15 minutes",
                                "source": "adapted_from_history"
                            }
                        elif isinstance(first_meal, dict):
                            adapted_meals[meal_type] = {
                                "meal_name": first_meal.get("meal_name", first_meal.get("name", f"Planned {meal_type}")),
                                "description": first_meal.get("description", f"Adapted from your meal plan history"),
                                "ingredients": first_meal.get("ingredients", []),
                                "nutritional_info": first_meal.get("nutritional_info", self._estimate_nutrition("", meal_type)),
                                "preparation_time": first_meal.get("preparation_time", "15 minutes"),
                                "source": "adapted_from_history"
                            }
                
                # Special handling for snacks - check both "snack" and "snacks" keys
                elif meal_type == "snack":
                    # Check for "snacks" (plural) which is common in meal plan arrays
                    if "snacks" in base_meals and base_meals["snacks"]:
                        snacks_data = base_meals["snacks"]
                        if isinstance(snacks_data, list) and len(snacks_data) > 0:
                            # Take the first snack from the array
                            first_snack = snacks_data[0]
                            if isinstance(first_snack, str):
                                adapted_meals[meal_type] = {
                                    "meal_name": first_snack,
                                    "description": f"Healthy snack from your meal plan",
                                    "ingredients": [first_snack],
                                    "nutritional_info": self._estimate_nutrition(first_snack, "snack"),
                                    "preparation_time": "5 minutes",
                                    "source": "adapted_from_history"
                                }
                                print(f"[{self.service_name}] ✅ Found snack from history (plural): {first_snack}")
                        elif isinstance(snacks_data, str):
                            adapted_meals[meal_type] = {
                                "meal_name": snacks_data,
                                "description": f"Healthy snack from your meal plan",
                                "ingredients": [snacks_data],
                                "nutritional_info": self._estimate_nutrition(snacks_data, "snack"),
                                "preparation_time": "5 minutes",
                                "source": "adapted_from_history"
                            }
                            print(f"[{self.service_name}] ✅ Found snack from history (string): {snacks_data}")
            
            print(f"[{self.service_name}] Successfully adapted {len(adapted_meals)} meals from history")
            return adapted_meals
            
        except Exception as e:
            print(f"[{self.service_name}] Error adapting from meal history: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    async def _generate_from_health_profile(self, missing_meals: List[str], user_profile: Dict) -> Dict:
        """Generate meals based on user's comprehensive health profile"""
        generated_meals = {}
        
        try:
            # Get user's dietary preferences and restrictions from profile
            dietary_restrictions = user_profile.get("dietaryRestrictions", [])
            food_preferences = user_profile.get("foodPreferences", [])
            calorie_target = int(user_profile.get("calorieTarget", "2000"))

            # Calorie distribution that sums to 100% of target
            # breakfast 25%, lunch 35%, dinner 35%, snack 5%
            b_cal = max(200, int(round(calorie_target * 0.25)))
            l_cal = max(250, int(round(calorie_target * 0.35)))
            d_cal = max(250, int(round(calorie_target * 0.35)))
            s_cal = max(50, int(round(calorie_target * 0.05)))
            
            # Basic meal templates based on health profile
            meal_templates = {
                "breakfast": {
                    "meal_name": "Balanced Breakfast",
                    "description": "Protein-rich breakfast with complex carbohydrates for sustained energy",
                    "ingredients": ["oats", "berries", "nuts", "protein source"],
                    "nutritional_info": {"calories": b_cal, "protein": 20, "carbohydrates": 45, "fat": 12},
                    "preparation_time": "10 minutes",
                    "source": "generated_from_profile"
                },
                "lunch": {
                    "meal_name": "Nutritious Lunch",
                    "description": "Balanced lunch with lean protein and vegetables",
                    "ingredients": ["lean protein", "vegetables", "healthy grains"],
                    "nutritional_info": {"calories": l_cal, "protein": 25, "carbohydrates": 40, "fat": 15},
                    "preparation_time": "20 minutes",
                    "source": "generated_from_profile"
                },
                "dinner": {
                    "meal_name": "Healthy Dinner",
                    "description": "Well-balanced dinner with protein, vegetables, and healthy carbs",
                    "ingredients": ["protein", "vegetables", "complex carbs"],
                    "nutritional_info": {"calories": d_cal, "protein": 30, "carbohydrates": 35, "fat": 18},
                    "preparation_time": "25 minutes",
                    "source": "generated_from_profile"
                },
                "snack": {
                    "meal_name": "Healthy Snack",
                    "description": "Nutritious snack to bridge meal gaps",
                    "ingredients": ["nuts", "fruit"],
                    "nutritional_info": {"calories": s_cal, "protein": 5, "carbohydrates": 15, "fat": 8},
                    "preparation_time": "5 minutes",
                    "source": "generated_from_profile"
                }
            }
            
            for meal_type in missing_meals:
                if meal_type in meal_templates:
                    generated_meals[meal_type] = meal_templates[meal_type].copy()
                    
                    # Customize based on dietary restrictions
                    if "vegetarian" in dietary_restrictions:
                        if "protein source" in generated_meals[meal_type]["ingredients"]:
                            generated_meals[meal_type]["ingredients"] = [ing.replace("protein source", "plant protein") for ing in generated_meals[meal_type]["ingredients"]]
                    
                    print(f"[{self.service_name}] Generated {meal_type} from health profile")
            
            return generated_meals
            
        except Exception as e:
            print(f"[{self.service_name}] Error generating from health profile: {e}")
            return {}
    
    def _estimate_nutrition(self, meal_name: str, meal_type: str) -> Dict:
        """Estimate nutritional information for a meal"""
        # Basic nutrition estimates by meal type
        nutrition_estimates = {
            "breakfast": {"calories": 400, "protein": 20, "carbohydrates": 45, "fat": 12},
            "lunch": {"calories": 500, "protein": 25, "carbohydrates": 40, "fat": 15},
            "dinner": {"calories": 600, "protein": 30, "carbohydrates": 35, "fat": 18},
            "snack": {"calories": 150, "protein": 5, "carbohydrates": 15, "fat": 8}
        }
        
        return nutrition_estimates.get(meal_type, {"calories": 300, "protein": 15, "carbohydrates": 30, "fat": 10})
    
    def _organize_consumption_by_meal(self, today_consumption: List[Dict]) -> Dict:
        """Organize today's consumption records by meal type"""
        consumption_by_meal = {
            "breakfast": [],
            "lunch": [],
            "dinner": [],
            "snack": []
        }
        
        try:
            for record in today_consumption:
                meal_type = record.get("meal_type", "snack").lower()
                if meal_type in consumption_by_meal:
                    consumption_by_meal[meal_type].append({
                        "food_name": record.get("food_name", "Unknown food"),
                        "quantity": record.get("quantity", "1 serving"),
                        "calories": record.get("nutritional_info", {}).get("calories", 0),
                        "protein": record.get("nutritional_info", {}).get("protein", 0),
                        "timestamp": record.get("timestamp", ""),
                        "session_id": record.get("session_id", "")
                    })
            
            return consumption_by_meal
            
        except Exception as e:
            print(f"[{self.service_name}] Error organizing consumption by meal: {e}")
            return consumption_by_meal
    
    async def _apply_recalibration(self, meals: Dict, consumption_by_meal: Dict, user_profile: Dict) -> tuple:
        """Apply real-time recalibration based on actual vs planned consumption"""
        recalibrations = []
        
        try:
            calorie_target = int(user_profile.get("calorieTarget", "2000"))
            protein_target = int(user_profile.get("proteinTarget", "150"))
            
            # Calculate total consumed so far
            total_consumed_calories = sum(
                sum(item["calories"] for item in meal_items)
                for meal_items in consumption_by_meal.values()
            )
            
            total_consumed_protein = sum(
                sum(item["protein"] for item in meal_items)
                for meal_items in consumption_by_meal.values()
            )
            
            # Compute remaining goals
            remaining_calories = max(0, calorie_target - total_consumed_calories)
            remaining_protein = max(0, protein_target - total_consumed_protein)

            # Count remaining meals (meals that haven't been consumed)
            remaining_meals = [
                meal_type for meal_type, consumption in consumption_by_meal.items()
                if not consumption and meal_type in meals
            ]

            if remaining_meals:
                # Planned total for the remaining meals
                planned_remaining_total = sum(
                    max(0, meals[m].get("nutritional_info", {}).get("calories", 0))
                    for m in remaining_meals if m in meals
                )

                # If planned calories for remaining meals exceed what is left,
                # scale them down proportionally to fit within the remaining budget.
                if planned_remaining_total > max(0, remaining_calories):
                    scale = (remaining_calories / planned_remaining_total) if planned_remaining_total > 0 else 0
                    for meal_type in remaining_meals:
                        if meal_type in meals and "nutritional_info" in meals[meal_type]:
                            info = meals[meal_type]["nutritional_info"]
                            old_cal = int(info.get("calories", 0))
                            old_pro = int(info.get("protein", 0))
                            # Keep sensible minimums
                            min_cal = 50 if meal_type == "snack" else 120
                            new_cal = max(min_cal, int(round(old_cal * scale)))
                            # Scale protein similarly but keep a small floor
                            new_pro = max(5 if meal_type == "snack" else 12, int(round(old_pro * scale)))
                            info["calories"] = new_cal
                            info["protein"] = new_pro
                            recalibrations.append({
                                "meal_type": meal_type,
                                "reason": "scaled_to_remaining_calories",
                                "old_calories": old_cal,
                                "new_calories": new_cal,
                                "timestamp": datetime.utcnow().isoformat()
                            })
                    print(f"[{self.service_name}] Recalibrated remaining meals to fit within remaining calories ({remaining_calories} kcal)")
            
            return meals, recalibrations
            
        except Exception as e:
            print(f"[{self.service_name}] Error applying recalibration: {e}")
            return meals, []

    def _normalize_meals_to_daily_target(self, meals: Dict, calorie_target: int) -> tuple:
        """Ensure the sum of all planned meal calories does not exceed the daily target.

        Returns (updated_meals, recalibration_records).
        """
        try:
            meal_keys = [k for k in ["breakfast", "lunch", "dinner", "snack"] if k in meals]
            planned_total = sum(
                max(0, meals[k].get("nutritional_info", {}).get("calories", 0)) for k in meal_keys
            )
            if planned_total <= max(0, calorie_target):
                return meals, []

            scale = (calorie_target / planned_total) if planned_total > 0 else 0
            records = []
            for k in meal_keys:
                info = meals[k].get("nutritional_info", {})
                old_cal = int(info.get("calories", 0))
                old_pro = int(info.get("protein", 0))
                min_cal = 50 if k == "snack" else 120
                new_cal = max(min_cal, int(round(old_cal * scale)))
                new_pro = max(5 if k == "snack" else 12, int(round(old_pro * scale)))
                info["calories"] = new_cal
                info["protein"] = new_pro
                records.append({
                    "meal_type": k,
                    "reason": "normalized_to_daily_target",
                    "old_calories": old_cal,
                    "new_calories": new_cal,
                    "timestamp": datetime.utcnow().isoformat()
                })
            return meals, records
        except Exception as _e:
            print(f"[{self.service_name}] Error in daily normalization: {_e}")
            return meals, []
    
    def _calculate_macro_progress(self, today_consumption: List[Dict], user_profile: Dict) -> Dict:
        """Calculate macro progress for today"""
        try:
            calorie_target = int(user_profile.get("calorieTarget", "2000"))
            protein_target = int(user_profile.get("proteinTarget", "150"))
            
            total_calories = sum(
                record.get("nutritional_info", {}).get("calories", 0)
                for record in today_consumption
            )
            
            total_protein = sum(
                record.get("nutritional_info", {}).get("protein", 0)
                for record in today_consumption
            )
            
            return {
                "calories": {
                    "consumed": total_calories,
                    "target": calorie_target,
                    "remaining": max(0, calorie_target - total_calories),
                    "percentage": min(100, (total_calories / calorie_target) * 100)
                },
                "protein": {
                    "consumed": total_protein,
                    "target": protein_target,
                    "remaining": max(0, protein_target - total_protein),
                    "percentage": min(100, (total_protein / protein_target) * 100)
                }
            }
            
        except Exception as e:
            print(f"[{self.service_name}] Error calculating macro progress: {e}")
            return {
                "calories": {"consumed": 0, "target": 2000, "remaining": 2000, "percentage": 0},
                "protein": {"consumed": 0, "target": 150, "remaining": 150, "percentage": 0}
            }
    
    async def _get_existing_daily_plan(self, user_email: str, date: str) -> Optional[Dict]:
        """Check if a Smart Daily Meal Plan exists for today (persistence requirement)"""
        try:
            from database import interactions_container
            
            daily_key = f"smart_daily_{user_email}_{date}"
            
            query = """
            SELECT * FROM c
            WHERE c.id = @daily_key
            AND c.type = 'smart_daily_meal_plan'
            ORDER BY c._ts DESC
            """
            
            parameters = [{"name": "@daily_key", "value": daily_key}]
            
            items = list(interactions_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            if items:
                plan = items[0]
                print(f"[{self.service_name}] Found existing plan for {date}")
                return plan.get("plan_data", plan)
            
            return None
            
        except Exception as e:
            print(f"[{self.service_name}] Error checking existing plan: {e}")
            return None
    
    async def _save_daily_plan(self, user_email: str, date: str, plan_data: Dict) -> bool:
        """Save Smart Daily Meal Plan for persistence"""
        try:
            from database import interactions_container
            
            daily_key = f"smart_daily_{user_email}_{date}"
            
            plan_record = {
                "id": daily_key,
                "type": "smart_daily_meal_plan",
                "user_id": user_email,
                "plan_date": date,
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
                "plan_data": plan_data
            }
            
            interactions_container.upsert_item(body=plan_record)
            print(f"[{self.service_name}] Saved daily plan for {date}")
            return True
            
        except Exception as e:
            print(f"[{self.service_name}] Error saving daily plan: {e}")
            return False
    
    async def _apply_real_time_updates(self, existing_plan: Dict, user_email: str, user_profile: Dict) -> Dict:
        """Apply real-time updates to existing plan based on new consumption"""
        try:
            # Get fresh consumption data
            today_consumption = await self._get_today_consumption(user_email, user_profile.get("timezone", "UTC"))
            consumption_by_meal = self._organize_consumption_by_meal(today_consumption)
            
            # Update consumption data in plan
            existing_plan["consumption"] = consumption_by_meal
            existing_plan["macro_progress"] = self._calculate_macro_progress(today_consumption, user_profile)
            
            # Apply recalibration if needed
            meals = existing_plan.get("meals", {})
            meals, new_recalibrations = await self._apply_recalibration(meals, consumption_by_meal, user_profile)
            
            existing_plan["meals"] = meals
            existing_plan["recalibration_history"].extend(new_recalibrations)
            existing_plan["last_updated"] = datetime.utcnow().isoformat()

            # Final guard: normalize plan to user's calorie target after updates
            try:
                calorie_target = int(user_profile.get("calorieTarget", "2000"))
                normalized, normalization_records = self._normalize_meals_to_daily_target(meals, calorie_target)
                if normalization_records:
                    existing_plan["meals"] = normalized
                    existing_plan["recalibration_history"].extend(normalization_records)
            except Exception as _norm_err:
                print(f"[{self.service_name}] Warning: normalization on update skipped due to: {_norm_err}")
            
            # Save updated plan
            await self._save_daily_plan(user_email, existing_plan["plan_date"], existing_plan)
            
            print(f"[{self.service_name}] Applied real-time updates to existing plan")
            return existing_plan
            
        except Exception as e:
            print(f"[{self.service_name}] Error applying real-time updates: {e}")
            return existing_plan


# Create singleton instance
smart_daily_meal_plan_service = SmartDailyMealPlanService()