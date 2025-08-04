"""
Meal Plan History Integration System
Analyzes user's meal plan history to identify successful patterns, preferences,
and strategies for future meal plan recommendations.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
import traceback
import json

from database import get_user_meal_plans, get_user_consumption_history
from services.openai_service import robust_openai_call


class MealPlanHistoryAnalyzer:
    """
    Analyzes meal plan history to extract successful patterns and preferences
    for intelligent meal plan generation.
    """
    
    def __init__(self):
        self.success_threshold = 0.7  # 70% adherence considered successful
        self.recency_weight = 0.3     # Weight given to more recent plans
        
    async def analyze_meal_plan_history(
        self, 
        user_email: str,
        meal_plan_history: Optional[List[Dict]] = None,
        consumption_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive analysis of user's meal plan history.
        
        Args:
            user_email: User's email identifier
            meal_plan_history: Optional meal plan data (will fetch if not provided)
            consumption_history: Optional consumption data (will fetch if not provided)
            
        Returns:
            Detailed analysis of meal plan patterns and preferences
        """
        try:
            print(f"[MealPlanHistoryAnalyzer] Starting analysis for {user_email}")
            
            # Fetch data if not provided
            if meal_plan_history is None:
                meal_plan_history = await get_user_meal_plans(user_email)
            if consumption_history is None:
                consumption_history = await get_user_consumption_history(user_email, limit=200)
            
            if not meal_plan_history:
                print(f"[MealPlanHistoryAnalyzer] No meal plan history found for {user_email}")
                return self._create_empty_analysis(user_email)
            
            # Core analyses
            success_patterns = self._analyze_success_patterns(meal_plan_history)
            food_preferences = self._extract_food_preferences(meal_plan_history)
            timing_patterns = self._analyze_timing_patterns(meal_plan_history)
            adherence_analysis = await self._analyze_adherence_patterns(
                meal_plan_history, consumption_history, user_email
            )
            nutritional_patterns = self._analyze_nutritional_patterns(meal_plan_history)
            seasonal_preferences = self._analyze_seasonal_preferences(meal_plan_history)
            
            # Advanced pattern recognition
            recipe_success_rates = self._calculate_recipe_success_rates(
                meal_plan_history, consumption_history
            )
            meal_combination_preferences = self._analyze_meal_combinations(meal_plan_history)
            
            # Generate predictive insights
            recommendations = await self._generate_history_based_recommendations(
                success_patterns,
                food_preferences,
                adherence_analysis,
                nutritional_patterns,
                user_email
            )
            
            analysis_result = {
                "user_email": user_email,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "total_meal_plans": len(meal_plan_history),
                "analysis_period_days": self._calculate_analysis_period(meal_plan_history),
                "success_patterns": success_patterns,
                "food_preferences": food_preferences,
                "timing_patterns": timing_patterns,
                "adherence_analysis": adherence_analysis,
                "nutritional_patterns": nutritional_patterns,
                "seasonal_preferences": seasonal_preferences,
                "recipe_success_rates": recipe_success_rates,
                "meal_combination_preferences": meal_combination_preferences,
                "predictive_recommendations": recommendations,
                "confidence_score": self._calculate_confidence_score(
                    len(meal_plan_history), adherence_analysis
                )
            }
            
            print(f"[MealPlanHistoryAnalyzer] Analysis completed successfully")
            return analysis_result
            
        except Exception as e:
            print(f"[MealPlanHistoryAnalyzer] Error in analysis: {str(e)}")
            print(f"[MealPlanHistoryAnalyzer] Traceback: {traceback.format_exc()}")
            return self._create_empty_analysis(user_email)

    def _analyze_success_patterns(self, meal_plan_history: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns in successful meal plans."""
        successful_plans = [
            plan for plan in meal_plan_history 
            if plan.get("user_adherence_rate", 0) >= self.success_threshold
        ]
        
        if not successful_plans:
            return {
                "successful_plan_count": 0,
                "success_rate": 0.0,
                "successful_plan_types": [],
                "successful_duration_patterns": [],
                "successful_calorie_ranges": []
            }
        
        # Analyze successful plan characteristics
        plan_types = Counter([plan.get("plan_type", "standard") for plan in successful_plans])
        
        # Extract calorie patterns from successful plans
        calorie_ranges = []
        for plan in successful_plans:
            daily_calories = plan.get("dailyCalories")
            if daily_calories:
                try:
                    calorie_ranges.append(int(daily_calories))
                except (ValueError, TypeError):
                    pass
        
        avg_successful_calories = sum(calorie_ranges) / len(calorie_ranges) if calorie_ranges else 0
        
        return {
            "successful_plan_count": len(successful_plans),
            "success_rate": len(successful_plans) / len(meal_plan_history),
            "successful_plan_types": list(plan_types.keys()),
            "most_successful_type": plan_types.most_common(1)[0][0] if plan_types else None,
            "successful_calorie_ranges": {
                "average": round(avg_successful_calories, 0),
                "range": [min(calorie_ranges), max(calorie_ranges)] if calorie_ranges else [0, 0]
            },
            "success_characteristics": self._extract_success_characteristics(successful_plans)
        }

    def _extract_food_preferences(self, meal_plan_history: List[Dict]) -> Dict[str, Any]:
        """Extract food preferences from meal plan history."""
        all_foods = []
        cuisine_preferences = Counter()
        ingredient_frequency = Counter()
        
        for plan in meal_plan_history:
            meal_plan_data = plan.get("meal_plan", {})
            if not isinstance(meal_plan_data, dict):
                continue
                
            # Extract foods from each day and meal
            for day_key, day_data in meal_plan_data.items():
                if not isinstance(day_data, dict):
                    continue
                    
                for meal_type, meal_data in day_data.items():
                    if not isinstance(meal_data, dict):
                        continue
                    
                    # Extract meal name/title
                    meal_name = meal_data.get("meal", meal_data.get("name", ""))
                    if meal_name:
                        all_foods.append(meal_name.lower())
                    
                    # Extract cuisine type
                    cuisine = meal_data.get("cuisine", "")
                    if cuisine:
                        cuisine_preferences[cuisine.lower()] += 1
                    
                    # Extract ingredients
                    ingredients = meal_data.get("ingredients", [])
                    if isinstance(ingredients, list):
                        for ingredient in ingredients:
                            if isinstance(ingredient, str):
                                ingredient_frequency[ingredient.lower()] += 1
                            elif isinstance(ingredient, dict):
                                ingredient_name = ingredient.get("ingredient", ingredient.get("name", ""))
                                if ingredient_name:
                                    ingredient_frequency[ingredient_name.lower()] += 1
        
        # Analyze food patterns
        food_frequency = Counter(all_foods)
        
        return {
            "total_unique_foods": len(set(all_foods)),
            "most_frequent_foods": [
                {"food": food, "frequency": freq} 
                for food, freq in food_frequency.most_common(10)
            ],
            "preferred_cuisines": [
                {"cuisine": cuisine, "frequency": freq}
                for cuisine, freq in cuisine_preferences.most_common(5)
            ],
            "common_ingredients": [
                {"ingredient": ingredient, "frequency": freq}
                for ingredient, freq in ingredient_frequency.most_common(15)
            ],
            "dietary_diversity_score": self._calculate_diversity_score(all_foods)
        }

    def _analyze_timing_patterns(self, meal_plan_history: List[Dict]) -> Dict[str, Any]:
        """Analyze meal timing patterns from meal plan history."""
        meal_type_preferences = Counter()
        meal_complexity_by_time = defaultdict(list)
        
        for plan in meal_plan_history:
            meal_plan_data = plan.get("meal_plan", {})
            if not isinstance(meal_plan_data, dict):
                continue
            
            for day_key, day_data in meal_plan_data.items():
                if not isinstance(day_data, dict):
                    continue
                
                for meal_type, meal_data in day_data.items():
                    if not isinstance(meal_data, dict):
                        continue
                    
                    meal_type_preferences[meal_type.lower()] += 1
                    
                    # Estimate meal complexity (number of ingredients or preparation steps)
                    complexity = 0
                    ingredients = meal_data.get("ingredients", [])
                    if isinstance(ingredients, list):
                        complexity = len(ingredients)
                    
                    meal_complexity_by_time[meal_type.lower()].append(complexity)
        
        # Calculate average complexity by meal type
        avg_complexity = {}
        for meal_type, complexities in meal_complexity_by_time.items():
            if complexities:
                avg_complexity[meal_type] = sum(complexities) / len(complexities)
        
        return {
            "meal_type_frequency": dict(meal_type_preferences),
            "preferred_meal_types": [
                meal_type for meal_type, _ in meal_type_preferences.most_common(4)
            ],
            "average_meal_complexity": avg_complexity,
            "complexity_preferences": self._analyze_complexity_preferences(avg_complexity)
        }

    async def _analyze_adherence_patterns(
        self, 
        meal_plan_history: List[Dict],
        consumption_history: List[Dict],
        user_email: str
    ) -> Dict[str, Any]:
        """Analyze adherence patterns by comparing meal plans with actual consumption."""
        if not consumption_history:
            return {
                "overall_adherence_rate": 0.0,
                "adherence_by_meal_type": {},
                "adherence_trends": [],
                "adherence_factors": []
            }
        
        # Group consumption by date and meal type
        consumption_by_date = defaultdict(lambda: defaultdict(list))
        for record in consumption_history:
            try:
                timestamp = record.get("timestamp", "")
                if timestamp:
                    date_str = timestamp.split("T")[0]  # Extract date part
                    meal_type = record.get("meal_type", "snack").lower()
                    consumption_by_date[date_str][meal_type].append(record)
            except Exception:
                continue
        
        # Calculate adherence rates
        total_adherence_scores = []
        adherence_by_meal_type = defaultdict(list)
        
        for plan in meal_plan_history:
            plan_date = plan.get("created_at", "").split("T")[0]
            meal_plan_data = plan.get("meal_plan", {})
            
            if not isinstance(meal_plan_data, dict) or not plan_date:
                continue
            
            # Check adherence for each day in the plan
            for day_key, day_data in meal_plan_data.items():
                if not isinstance(day_data, dict):
                    continue
                
                # For simplicity, assume day_key relates to plan_date + offset
                # In practice, you'd need more sophisticated date matching
                actual_consumption = consumption_by_date.get(plan_date, {})
                
                for meal_type, planned_meal in day_data.items():
                    if not isinstance(planned_meal, dict):
                        continue
                    
                    actual_meals = actual_consumption.get(meal_type.lower(), [])
                    
                    # Simple adherence calculation (presence of meal)
                    adherence_score = 1.0 if actual_meals else 0.0
                    
                    # More sophisticated matching could compare meal content
                    if actual_meals and isinstance(planned_meal, dict):
                        planned_name = planned_meal.get("meal", "").lower()
                        actual_names = [meal.get("food_name", "").lower() for meal in actual_meals]
                        
                        # Check for partial matches
                        if any(planned_name in actual_name or actual_name in planned_name 
                               for actual_name in actual_names):
                            adherence_score = 1.0
                        elif actual_names:  # Had some food, just not exactly what was planned
                            adherence_score = 0.5
                    
                    total_adherence_scores.append(adherence_score)
                    adherence_by_meal_type[meal_type.lower()].append(adherence_score)
        
        # Calculate summary statistics
        overall_adherence = sum(total_adherence_scores) / len(total_adherence_scores) if total_adherence_scores else 0.0
        
        meal_type_adherence = {}
        for meal_type, scores in adherence_by_meal_type.items():
            meal_type_adherence[meal_type] = sum(scores) / len(scores) if scores else 0.0
        
        return {
            "overall_adherence_rate": round(overall_adherence, 3),
            "adherence_by_meal_type": meal_type_adherence,
            "adherence_sample_size": len(total_adherence_scores),
            "high_adherence_threshold_met": overall_adherence >= self.success_threshold,
            "adherence_insights": self._generate_adherence_insights(
                overall_adherence, meal_type_adherence
            )
        }

    def _analyze_nutritional_patterns(self, meal_plan_history: List[Dict]) -> Dict[str, Any]:
        """Analyze nutritional patterns from meal plan history."""
        calorie_trends = []
        macro_patterns = defaultdict(list)
        
        for plan in meal_plan_history:
            # Extract daily calories
            daily_calories = plan.get("dailyCalories")
            if daily_calories:
                try:
                    calorie_trends.append(int(daily_calories))
                except (ValueError, TypeError):
                    pass
            
            # Extract macro goals if available
            macros = plan.get("macronutrients", {})
            if isinstance(macros, dict):
                for macro, value in macros.items():
                    if value is not None:
                        try:
                            macro_patterns[macro].append(float(value))
                        except (ValueError, TypeError):
                            pass
        
        # Calculate trends
        calorie_analysis = {}
        if calorie_trends:
            calorie_analysis = {
                "average": round(sum(calorie_trends) / len(calorie_trends), 0),
                "range": [min(calorie_trends), max(calorie_trends)],
                "trend": "stable"  # Could implement trend analysis
            }
        
        macro_analysis = {}
        for macro, values in macro_patterns.items():
            if values:
                macro_analysis[macro] = {
                    "average": round(sum(values) / len(values), 1),
                    "range": [min(values), max(values)]
                }
        
        return {
            "calorie_patterns": calorie_analysis,
            "macro_patterns": macro_analysis,
            "nutritional_consistency": self._calculate_nutritional_consistency(
                calorie_trends, macro_patterns
            )
        }

    def _analyze_seasonal_preferences(self, meal_plan_history: List[Dict]) -> Dict[str, Any]:
        """Analyze seasonal preferences from meal plan timing."""
        seasonal_foods = defaultdict(list)
        seasonal_plan_counts = defaultdict(int)
        
        for plan in meal_plan_history:
            created_at = plan.get("created_at", "")
            if not created_at:
                continue
            
            try:
                date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                month = date_obj.month
                
                # Determine season
                if month in [12, 1, 2]:
                    season = "winter"
                elif month in [3, 4, 5]:
                    season = "spring"
                elif month in [6, 7, 8]:
                    season = "summer"
                else:
                    season = "fall"
                
                seasonal_plan_counts[season] += 1
                
                # Extract foods from this seasonal plan
                meal_plan_data = plan.get("meal_plan", {})
                if isinstance(meal_plan_data, dict):
                    for day_data in meal_plan_data.values():
                        if isinstance(day_data, dict):
                            for meal_data in day_data.values():
                                if isinstance(meal_data, dict):
                                    meal_name = meal_data.get("meal", "")
                                    if meal_name:
                                        seasonal_foods[season].append(meal_name.lower())
                                        
            except Exception:
                continue
        
        # Identify unique seasonal preferences
        seasonal_preferences = {}
        for season, foods in seasonal_foods.items():
            if foods:
                food_counter = Counter(foods)
                seasonal_preferences[season] = [
                    food for food, _ in food_counter.most_common(5)
                ]
        
        return {
            "seasonal_plan_distribution": dict(seasonal_plan_counts),
            "seasonal_food_preferences": seasonal_preferences,
            "most_active_season": max(seasonal_plan_counts.items(), key=lambda x: x[1])[0] if seasonal_plan_counts else None
        }

    def _calculate_recipe_success_rates(
        self, 
        meal_plan_history: List[Dict],
        consumption_history: List[Dict]
    ) -> Dict[str, Any]:
        """Calculate success rates for specific recipes/meals."""
        recipe_appearances = Counter()
        recipe_success = Counter()
        
        # Extract all planned recipes
        for plan in meal_plan_history:
            meal_plan_data = plan.get("meal_plan", {})
            adherence_rate = plan.get("user_adherence_rate", 0)
            
            if not isinstance(meal_plan_data, dict):
                continue
            
            for day_data in meal_plan_data.values():
                if isinstance(day_data, dict):
                    for meal_data in day_data.values():
                        if isinstance(meal_data, dict):
                            meal_name = meal_data.get("meal", "")
                            if meal_name:
                                recipe_name = meal_name.lower()
                                recipe_appearances[recipe_name] += 1
                                
                                # Consider successful if overall plan adherence was good
                                if adherence_rate >= self.success_threshold:
                                    recipe_success[recipe_name] += 1
        
        # Calculate success rates
        recipe_success_rates = {}
        for recipe, appearances in recipe_appearances.items():
            if appearances > 0:
                success_rate = recipe_success[recipe] / appearances
                recipe_success_rates[recipe] = {
                    "success_rate": round(success_rate, 3),
                    "appearances": appearances,
                    "successes": recipe_success[recipe]
                }
        
        # Sort by success rate and appearances
        top_recipes = sorted(
            recipe_success_rates.items(),
            key=lambda x: (x[1]["success_rate"], x[1]["appearances"]),
            reverse=True
        )[:10]
        
        return {
            "total_unique_recipes": len(recipe_success_rates),
            "top_successful_recipes": [
                {"recipe": recipe, **data} for recipe, data in top_recipes
            ],
            "average_recipe_success_rate": round(
                sum(data["success_rate"] for data in recipe_success_rates.values()) / 
                len(recipe_success_rates) if recipe_success_rates else 0, 3
            )
        }

    def _analyze_meal_combinations(self, meal_plan_history: List[Dict]) -> Dict[str, Any]:
        """Analyze successful meal combinations within days."""
        daily_combinations = []
        
        for plan in meal_plan_history:
            meal_plan_data = plan.get("meal_plan", {})
            adherence_rate = plan.get("user_adherence_rate", 0)
            
            if not isinstance(meal_plan_data, dict):
                continue
            
            for day_data in meal_plan_data.values():
                if isinstance(day_data, dict):
                    day_meals = []
                    for meal_type, meal_data in day_data.items():
                        if isinstance(meal_data, dict):
                            meal_name = meal_data.get("meal", "")
                            if meal_name:
                                day_meals.append((meal_type.lower(), meal_name.lower()))
                    
                    if len(day_meals) >= 2:  # At least 2 meals to form a combination
                        daily_combinations.append({
                            "meals": day_meals,
                            "successful": adherence_rate >= self.success_threshold
                        })
        
        # Analyze patterns
        successful_combinations = [
            combo for combo in daily_combinations if combo["successful"]
        ]
        
        return {
            "total_daily_combinations": len(daily_combinations),
            "successful_combinations": len(successful_combinations),
            "combination_success_rate": len(successful_combinations) / len(daily_combinations) if daily_combinations else 0,
            "common_successful_patterns": self._extract_combination_patterns(successful_combinations)
        }

    async def _generate_history_based_recommendations(
        self,
        success_patterns: Dict,
        food_preferences: Dict,
        adherence_analysis: Dict,
        nutritional_patterns: Dict,
        user_email: str
    ) -> Dict[str, Any]:
        """Generate recommendations based on historical analysis."""
        
        # Defensive programming for data types - FIXED!
        
        if not isinstance(success_patterns, dict):
            print(f"[MealPlanHistoryAnalyzer] WARNING: success_patterns is {type(success_patterns)}, converting to dict")
            success_patterns = {"success_rate": 0.0, "most_successful_type": "N/A", "successful_calorie_ranges": {"range": [0, 0]}}
        if not isinstance(food_preferences, dict):
            print(f"[MealPlanHistoryAnalyzer] WARNING: food_preferences is {type(food_preferences)}, converting to dict")
            food_preferences = {"most_frequent_foods": [], "preferred_cuisines": [], "dietary_diversity_score": 0.5}
        if not isinstance(adherence_analysis, dict):
            print(f"[MealPlanHistoryAnalyzer] WARNING: adherence_analysis is {type(adherence_analysis)}, converting to dict")
            adherence_analysis = {"overall_adherence_rate": 0.0, "adherence_by_meal_type": {}}
        if not isinstance(nutritional_patterns, dict):
            print(f"[MealPlanHistoryAnalyzer] WARNING: nutritional_patterns is {type(nutritional_patterns)}, converting to dict")
            nutritional_patterns = {"calorie_patterns": {"average": 2000}, "nutritional_consistency": "moderate"}
        
        # Extra safety for nested dictionary access
        if not isinstance(success_patterns.get('successful_calorie_ranges'), dict):
            success_patterns['successful_calorie_ranges'] = {"range": [0, 0]}
        if not isinstance(adherence_analysis.get('adherence_by_meal_type'), dict):
            adherence_analysis['adherence_by_meal_type'] = {}

        try:
            # Safely build prompt with defensive access
            success_rate = success_patterns.get('success_rate', 0.0) if isinstance(success_patterns, dict) else 0.0
            successful_type = success_patterns.get('most_successful_type', 'N/A') if isinstance(success_patterns, dict) else 'N/A'
            
            calorie_ranges = success_patterns.get('successful_calorie_ranges', {}) if isinstance(success_patterns, dict) else {}
            calorie_range = calorie_ranges.get('range', [0, 0]) if isinstance(calorie_ranges, dict) else [0, 0]
            
            # Safe list comprehensions
            top_foods = []
            preferred_cuisines = []
            try:
                foods_list = food_preferences.get('most_frequent_foods', []) if isinstance(food_preferences, dict) else []
                if isinstance(foods_list, list):
                    top_foods = [item.get('food', '') for item in foods_list[:5] if isinstance(item, dict) and 'food' in item]
                
                cuisines_list = food_preferences.get('preferred_cuisines', []) if isinstance(food_preferences, dict) else []
                if isinstance(cuisines_list, list):
                    preferred_cuisines = [item.get('cuisine', '') for item in cuisines_list[:3] if isinstance(item, dict) and 'cuisine' in item]
            except Exception as e:
                print(f"[MealPlanHistoryAnalyzer] Error processing food preferences: {e}")
                top_foods = []
                preferred_cuisines = []
            
            dietary_diversity = food_preferences.get('dietary_diversity_score', 0.5) if isinstance(food_preferences, dict) else 0.5
            overall_adherence = adherence_analysis.get('overall_adherence_rate', 0.0) if isinstance(adherence_analysis, dict) else 0.0
            
            # Safe max operation
            best_meal_type = 'N/A'
            try:
                meal_types = adherence_analysis.get('adherence_by_meal_type', {}) if isinstance(adherence_analysis, dict) else {}
                if isinstance(meal_types, dict) and meal_types:
                    best_meal_type = max(meal_types.items(), key=lambda x: x[1], default=('N/A', 0))[0]
            except Exception as e:
                print(f"[MealPlanHistoryAnalyzer] Error processing adherence by meal type: {e}")
                best_meal_type = 'N/A'
            
            avg_calories = 2000
            consistency = 'moderate'
            try:
                calorie_patterns = nutritional_patterns.get('calorie_patterns', {}) if isinstance(nutritional_patterns, dict) else {}
                avg_calories = calorie_patterns.get('average', 2000) if isinstance(calorie_patterns, dict) else 2000
                consistency = nutritional_patterns.get('nutritional_consistency', 'moderate') if isinstance(nutritional_patterns, dict) else 'moderate'
            except Exception as e:
                print(f"[MealPlanHistoryAnalyzer] Error processing nutritional patterns: {e}")
            
            prompt = f"""Based on this user's meal plan history analysis, provide personalized recommendations for future meal planning.

SUCCESS PATTERNS:
- Success Rate: {success_rate:.1%}
- Most Successful Plan Type: {successful_type}
- Successful Calorie Range: {calorie_range}

FOOD PREFERENCES:
- Top Foods: {top_foods}
- Preferred Cuisines: {preferred_cuisines}
- Dietary Diversity Score: {dietary_diversity}

ADHERENCE PATTERNS:
- Overall Adherence: {overall_adherence:.1%}
- Best Adherence Meal Type: {best_meal_type}

NUTRITIONAL PATTERNS:
- Average Calories: {avg_calories}
- Macro Consistency: {consistency}

Provide recommendations in JSON format:
{{
    "optimal_plan_characteristics": {{
        "recommended_plan_type": "type",
        "optimal_calorie_target": 2000,
        "recommended_duration": "7_days"
    }},
    "food_recommendations": {{
        "foods_to_include_more": ["food1", "food2", "food3"],
        "foods_to_reduce": ["food1", "food2"],
        "new_foods_to_try": ["food1", "food2", "food3"]
    }},
    "timing_recommendations": {{
        "best_meal_types_to_focus": ["breakfast", "lunch"],
        "meal_prep_suggestions": ["tip1", "tip2"],
        "timing_optimization": "advice"
    }},
    "adherence_improvement_tips": ["tip1", "tip2", "tip3"],
    "personalization_insights": ["insight1", "insight2", "insight3"]
}}
"""
            
        except Exception as prompt_error:
            print(f"[MealPlanHistoryAnalyzer] Critical error building prompt: {prompt_error}")
            # Fallback prompt if all else fails
            prompt = """Based on meal plan history analysis, provide basic recommendations in JSON format:
{
    "optimal_plan_characteristics": {
        "recommended_plan_type": "balanced",
        "optimal_calorie_target": 2000,
        "recommended_duration": "7_days"
    },
    "food_recommendations": {
        "foods_to_include_more": ["vegetables", "lean_proteins", "whole_grains"],
        "foods_to_reduce": ["processed_foods", "sugary_snacks"],
        "new_foods_to_try": ["quinoa", "lentils", "salmon"]
    },
    "timing_recommendations": {
        "best_meal_types_to_focus": ["breakfast", "lunch"],
        "meal_prep_suggestions": ["batch_cooking", "portion_control"],
        "timing_optimization": "eat_regularly"
    },
    "adherence_improvement_tips": ["meal_prep", "variety", "moderation"],
    "personalization_insights": ["focus_on_consistency", "gradual_changes", "track_progress"]
}
"""
        
        try:
            ai_response = await robust_openai_call(
                [{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800
            )
            
            if ai_response and ai_response.get("success") and ai_response.get("content"):
                content = ai_response["content"].strip()
                return json.loads(content)
        
        except Exception as e:
            print(f"[MealPlanHistoryAnalyzer] AI recommendation generation failed: {e}")
        
        # Fallback recommendations
        return {
            "optimal_plan_characteristics": {
                "recommended_plan_type": success_patterns.get('most_successful_type', 'adaptive'),
                "optimal_calorie_target": nutritional_patterns.get('calorie_patterns', {}).get('average', 2000),
                "recommended_duration": "7_days"
            },
            "food_recommendations": {
                "foods_to_include_more": [item['food'] for item in food_preferences.get('most_frequent_foods', [])[:3]],
                "foods_to_reduce": [],
                "new_foods_to_try": ["variety_proteins", "seasonal_vegetables", "whole_grains"]
            },
            "timing_recommendations": {
                "best_meal_types_to_focus": ["breakfast", "lunch"],
                "meal_prep_suggestions": ["prepare_proteins_ahead", "pre_cut_vegetables"],
                "timing_optimization": "maintain_consistent_meal_times"
            },
            "adherence_improvement_tips": ["plan_ahead", "keep_simple", "allow_flexibility"],
            "personalization_insights": ["focus_on_preferred_foods", "maintain_successful_patterns"]
        }

    def _calculate_analysis_period(self, meal_plan_history: List[Dict]) -> int:
        """Calculate the period covered by the analysis in days."""
        if not meal_plan_history:
            return 0
        
        dates = []
        for plan in meal_plan_history:
            created_at = plan.get("created_at", "")
            if created_at:
                try:
                    date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    dates.append(date_obj)
                except Exception:
                    continue
        
        if len(dates) < 2:
            return 0
        
        return (max(dates) - min(dates)).days

    def _calculate_confidence_score(self, plan_count: int, adherence_analysis: Dict) -> float:
        """Calculate confidence score for the analysis."""
        # Base confidence on number of plans and data quality
        plan_confidence = min(plan_count / 10, 1.0)  # Full confidence at 10+ plans
        adherence_confidence = adherence_analysis.get('overall_adherence_rate', 0)
        sample_size_confidence = min(adherence_analysis.get('adherence_sample_size', 0) / 50, 1.0)
        
        return round((plan_confidence + adherence_confidence + sample_size_confidence) / 3, 3)

    def _extract_success_characteristics(self, successful_plans: List[Dict]) -> List[str]:
        """Extract common characteristics of successful plans."""
        characteristics = []
        
        # Analyze plan types
        plan_types = [plan.get("plan_type", "") for plan in successful_plans]
        if plan_types:
            most_common_type = Counter(plan_types).most_common(1)[0][0]
            if most_common_type:
                characteristics.append(f"effective_plan_type_{most_common_type}")
        
        # Analyze calorie ranges
        calories = []
        for plan in successful_plans:
            daily_calories = plan.get("dailyCalories")
            if daily_calories:
                try:
                    calories.append(int(daily_calories))
                except (ValueError, TypeError):
                    pass
        
        if calories:
            avg_calories = sum(calories) / len(calories)
            if avg_calories < 1800:
                characteristics.append("lower_calorie_success")
            elif avg_calories > 2200:
                characteristics.append("higher_calorie_success")
            else:
                characteristics.append("moderate_calorie_success")
        
        return characteristics

    def _calculate_diversity_score(self, foods: List[str]) -> float:
        """Calculate dietary diversity score."""
        if not foods:
            return 0.0
        
        unique_foods = len(set(foods))
        total_foods = len(foods)
        
        # Simple diversity score: unique foods / total foods
        diversity = unique_foods / total_foods if total_foods > 0 else 0
        return round(diversity, 3)

    def _analyze_complexity_preferences(self, avg_complexity: Dict[str, float]) -> Dict[str, str]:
        """Analyze meal complexity preferences."""
        preferences = {}
        
        for meal_type, complexity in avg_complexity.items():
            if complexity < 3:
                preferences[meal_type] = "simple"
            elif complexity > 6:
                preferences[meal_type] = "complex"
            else:
                preferences[meal_type] = "moderate"
        
        return preferences

    def _generate_adherence_insights(
        self, 
        overall_adherence: float, 
        meal_type_adherence: Dict[str, float]
    ) -> List[str]:
        """Generate insights about adherence patterns."""
        insights = []
        
        if overall_adherence >= 0.8:
            insights.append("excellent_overall_adherence")
        elif overall_adherence >= 0.6:
            insights.append("good_adherence_with_room_for_improvement")
        else:
            insights.append("significant_adherence_challenges")
        
        # Find best and worst meal types
        if meal_type_adherence:
            best_meal = max(meal_type_adherence.items(), key=lambda x: x[1])
            worst_meal = min(meal_type_adherence.items(), key=lambda x: x[1])
            
            insights.append(f"strongest_adherence_{best_meal[0]}")
            if worst_meal[1] < 0.5:
                insights.append(f"needs_improvement_{worst_meal[0]}")
        
        return insights

    def _calculate_nutritional_consistency(
        self, 
        calorie_trends: List[int], 
        macro_patterns: Dict[str, List[float]]
    ) -> str:
        """Calculate nutritional consistency rating."""
        if not calorie_trends:
            return "insufficient_data"
        
        # Calculate coefficient of variation for calories
        if len(calorie_trends) > 1:
            mean_calories = sum(calorie_trends) / len(calorie_trends)
            variance = sum((x - mean_calories) ** 2 for x in calorie_trends) / len(calorie_trends)
            std_dev = variance ** 0.5
            cv = std_dev / mean_calories if mean_calories > 0 else 0
            
            if cv < 0.1:
                return "very_consistent"
            elif cv < 0.2:
                return "consistent"
            elif cv < 0.3:
                return "moderately_consistent"
            else:
                return "inconsistent"
        
        return "single_data_point"

    def _extract_combination_patterns(self, successful_combinations: List[Dict]) -> List[str]:
        """Extract common patterns from successful meal combinations."""
        patterns = []
        
        # Analyze meal type combinations
        combination_types = []
        for combo in successful_combinations:
            meal_types = [meal[0] for meal in combo["meals"]]
            meal_types.sort()  # Normalize order
            combination_types.append(tuple(meal_types))
        
        if combination_types:
            most_common = Counter(combination_types).most_common(3)
            for combo_tuple, count in most_common:
                patterns.append(f"successful_combination_{'_'.join(combo_tuple)}")
        
        return patterns

    def _create_empty_analysis(self, user_email: str) -> Dict[str, Any]:
        """Create empty analysis structure when no meal plan history exists."""
        return {
            "user_email": user_email,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "total_meal_plans": 0,
            "analysis_period_days": 0,
            "success_patterns": {
                "successful_plan_count": 0,
                "success_rate": 0.0,
                "successful_plan_types": [],
                "most_successful_type": None
            },
            "food_preferences": {
                "total_unique_foods": 0,
                "most_frequent_foods": [],
                "preferred_cuisines": [],
                "dietary_diversity_score": 0.0
            },
            "adherence_analysis": {
                "overall_adherence_rate": 0.0,
                "adherence_by_meal_type": {},
                "adherence_sample_size": 0
            },
            "predictive_recommendations": {
                "optimal_plan_characteristics": {
                    "recommended_plan_type": "adaptive",
                    "optimal_calorie_target": 2000,
                    "recommended_duration": "7_days"
                },
                "food_recommendations": {
                    "foods_to_include_more": ["lean_proteins", "vegetables", "whole_grains"],
                    "new_foods_to_try": ["variety_proteins", "seasonal_vegetables"]
                },
                "adherence_improvement_tips": ["start_simple", "plan_ahead", "track_progress"]
            },
            "confidence_score": 0.0,
            "status": "no_history_available"
        }


# Global analyzer instance
meal_plan_history_analyzer = MealPlanHistoryAnalyzer()