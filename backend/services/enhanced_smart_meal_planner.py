"""
Enhanced Smart Daily Meal Planner Service
Provides comprehensive AI-powered daily meal planning with full health profile integration,
meal plan history analysis, and real-time dynamic calibration.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import traceback
import json

from database import (
    get_user_by_email, get_user_consumption_history, get_user_meal_plans
)
from services.comprehensive_health_analyzer import health_analyzer
from services.meal_plan_history_analyzer import meal_plan_history_analyzer
from services.openai_service import robust_openai_call
from utils import filter_today_records


class EnhancedSmartMealPlanner:
    """
    Enhanced Smart Daily Meal Planner that provides comprehensive AI-powered meal planning
    with full health profile integration and dynamic calibration.
    """
    
    def __init__(self):
        self.health_analyzer = health_analyzer
        self.history_analyzer = meal_plan_history_analyzer
        
    async def generate_comprehensive_smart_meal_plan(
        self,
        user_email: str,
        user_profile: Dict[str, Any],
        current_consumption: Optional[List[Dict]] = None,
        target_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive smart daily meal plan using full health profile analysis.
        
        Args:
            user_email: User's email identifier
            user_profile: Complete user profile data
            current_consumption: Optional today's consumption data
            target_date: Optional target date (defaults to today)
            
        Returns:
            Comprehensive smart meal plan with dynamic calibration
        """
        try:
            print(f"[EnhancedSmartMealPlanner] Starting comprehensive meal planning for {user_email}")
            
            # Set target date
            if not target_date:
                target_date = datetime.utcnow().strftime("%Y-%m-%d")
            
            # Get timezone
            user_timezone = user_profile.get("timezone", "UTC")
            
            # Fetch consumption data if not provided
            if current_consumption is None:
                current_consumption = await self._get_today_consumption(user_email, user_timezone)
            
            # Perform comprehensive health analysis
            print(f"[EnhancedSmartMealPlanner] Performing comprehensive health analysis...")
            health_analysis = await self.health_analyzer.analyze_comprehensive_health_profile(
                user_email, user_profile
            )
            
            # Perform meal plan history analysis
            print(f"[EnhancedSmartMealPlanner] Analyzing meal plan history...")
            history_analysis = await self.history_analyzer.analyze_meal_plan_history(user_email)
            
            # Analyze current consumption and determine remaining meals
            consumption_analysis = self._analyze_current_consumption(
                current_consumption, health_analysis["nutritional_goals"], user_timezone
            )
            
            # Generate dynamic meal recommendations
            print(f"[EnhancedSmartMealPlanner] Generating AI-powered meal recommendations...")
            meal_recommendations = await self._generate_comprehensive_meal_recommendations(
                health_analysis,
                history_analysis,
                consumption_analysis,
                user_profile,
                user_timezone
            )
            
            # Apply real-time calibration
            calibrated_plan = self._apply_dynamic_calibration(
                meal_recommendations,
                consumption_analysis,
                health_analysis["nutritional_goals"]
            )
            
            # Generate smart nutrition insights
            nutrition_insights = self._generate_nutrition_insights(
                health_analysis,
                consumption_analysis,
                calibrated_plan
            )
            
            # Create comprehensive response
            response = {
                "user_email": user_email,
                "target_date": target_date,
                "generated_at": datetime.utcnow().isoformat(),
                "user_timezone": user_timezone,
                
                # Nutritional Goals & Progress
                "nutritional_goals": health_analysis["nutritional_goals"],
                "daily_progress": consumption_analysis["daily_progress"],
                "remaining_targets": consumption_analysis["remaining_targets"],
                
                # Current Status (with backward compatibility)
                "current_consumption": consumption_analysis["consumption_summary"],
                "consumption_summary": consumption_analysis["consumption_summary"],  # For backward compatibility
                "remaining_meals": consumption_analysis["remaining_meals"],
                "meal_timing_status": consumption_analysis["meal_timing_status"],
                
                # Legacy fields for backward compatibility
                "calories_consumed": consumption_analysis["daily_progress"]["calories"]["consumed"],
                "target_calories": consumption_analysis["daily_progress"]["calories"]["target"],
                "remaining_calories": consumption_analysis["remaining_targets"]["calories"],
                
                # Smart Meal Plan (with backward compatibility)
                "smart_meal_plan": calibrated_plan,
                "meal_recommendations": meal_recommendations,
                "smart_suggestions": calibrated_plan,  # For backward compatibility
                
                # AI Insights
                "health_insights": health_analysis["ai_recommendations"],
                "nutrition_insights": nutrition_insights,
                "personalization_factors": self._extract_personalization_factors(
                    health_analysis, history_analysis
                ),
                
                # History Integration
                "historical_insights": history_analysis.get("predictive_recommendations", {}),
                "success_patterns": history_analysis.get("success_patterns", {}),
                
                # Dynamic Calibration Info
                "calibration_applied": consumption_analysis["requires_calibration"],
                "calibration_reason": consumption_analysis.get("calibration_reason", ""),
                
                # Confidence & Quality Metrics
                "recommendation_confidence": self._calculate_recommendation_confidence(
                    health_analysis, history_analysis, consumption_analysis
                ),
                "data_completeness": self._assess_data_completeness(
                    user_profile, health_analysis, history_analysis
                )
            }
            
            print(f"[EnhancedSmartMealPlanner] Comprehensive meal planning completed successfully")
            return response
            
        except Exception as e:
            print(f"[EnhancedSmartMealPlanner] Error in comprehensive meal planning: {str(e)}")
            print(f"[EnhancedSmartMealPlanner] Traceback: {traceback.format_exc()}")
            return self._create_fallback_meal_plan(user_email, user_profile, target_date)

    async def _get_today_consumption(self, user_email: str, user_timezone: str) -> List[Dict]:
        """Get today's consumption records with timezone awareness."""
        try:
            # Get consumption history
            consumption_history = await get_user_consumption_history(user_email, limit=100)
            
            # Filter for today's records
            today_consumption = filter_today_records(consumption_history, user_timezone)
            
            print(f"[EnhancedSmartMealPlanner] Found {len(today_consumption)} consumption records for today")
            return today_consumption
            
        except Exception as e:
            print(f"[EnhancedSmartMealPlanner] Error getting today's consumption: {str(e)}")
            return []

    def _analyze_current_consumption(
        self,
        current_consumption: List[Dict],
        nutritional_goals: Dict[str, Any],
        user_timezone: str
    ) -> Dict[str, Any]:
        """Analyze current consumption against nutritional goals."""
        
        # Calculate consumed nutrients
        consumed_calories = 0
        consumed_protein = 0
        consumed_carbs = 0
        consumed_fat = 0
        
        consumption_by_meal = {}
        
        for record in current_consumption:
            nutrition_info = record.get("nutritional_info", {})
            
            consumed_calories += nutrition_info.get("calories", 0)
            consumed_protein += nutrition_info.get("protein", 0)
            consumed_carbs += nutrition_info.get("carbohydrates", nutrition_info.get("carbs", 0))
            consumed_fat += nutrition_info.get("fat", 0)
            
            # Group by meal type
            meal_type = record.get("meal_type", "snack").lower()
            if meal_type not in consumption_by_meal:
                consumption_by_meal[meal_type] = []
            
            consumption_by_meal[meal_type].append({
                "food_name": record.get("food_name", ""),
                "calories": nutrition_info.get("calories", 0),
                "protein": nutrition_info.get("protein", 0),
                "carbs": nutrition_info.get("carbohydrates", nutrition_info.get("carbs", 0)),
                "fat": nutrition_info.get("fat", 0),
                "timestamp": record.get("timestamp", "")
            })
        
        # Calculate remaining targets
        target_calories = nutritional_goals.get("calories", 2000)
        target_protein = nutritional_goals.get("protein", 100)
        target_carbs = nutritional_goals.get("carbs", 250)
        target_fat = nutritional_goals.get("fat", 66)
        
        # SMART LOGIC: Allow negative values when over goals for intelligent recommendations
        remaining_calories = target_calories - consumed_calories
        remaining_protein = target_protein - consumed_protein
        remaining_carbs = target_carbs - consumed_carbs
        remaining_fat = target_fat - consumed_fat
        
        # Determine remaining meals based on time
        remaining_meals = self._determine_remaining_meals(user_timezone)
        
        # Check if calibration is needed
        requires_calibration = self._check_calibration_needed(
            consumed_calories, target_calories, remaining_meals, consumption_by_meal
        )
        
        return {
            "daily_progress": {
                "calories": {"consumed": consumed_calories, "target": target_calories, "percentage": min(100, (consumed_calories / target_calories) * 100)},
                "protein": {"consumed": round(consumed_protein, 1), "target": target_protein, "percentage": min(100, (consumed_protein / target_protein) * 100)},
                "carbs": {"consumed": round(consumed_carbs, 1), "target": target_carbs, "percentage": min(100, (consumed_carbs / target_carbs) * 100)},
                "fat": {"consumed": round(consumed_fat, 1), "target": target_fat, "percentage": min(100, (consumed_fat / target_fat) * 100)}
            },
            "remaining_targets": {
                "calories": remaining_calories,
                "protein": round(remaining_protein, 1),
                "carbs": round(remaining_carbs, 1),
                "fat": round(remaining_fat, 1)
            },
            "consumption_summary": consumption_by_meal,
            "remaining_meals": remaining_meals,
            "meal_timing_status": self._analyze_meal_timing(consumption_by_meal, user_timezone),
            "requires_calibration": requires_calibration,
            "calibration_reason": self._get_calibration_reason(
                consumed_calories, target_calories, remaining_meals, consumption_by_meal
            ) if requires_calibration else ""
        }

    def _determine_remaining_meals(self, user_timezone: str) -> List[str]:
        """Determine which meals are still remaining based on current time."""
        try:
            import pytz
            user_tz = pytz.timezone(user_timezone)
            current_time = datetime.now(user_tz)
            current_hour = current_time.hour
        except Exception:
            current_hour = datetime.utcnow().hour
        
        remaining_meals = []
        
        if current_hour < 10:  # Before 10 AM
            remaining_meals = ['breakfast', 'lunch', 'dinner', 'snack']
        elif current_hour < 14:  # Before 2 PM
            remaining_meals = ['lunch', 'dinner', 'snack']
        elif current_hour < 18:  # Before 6 PM
            remaining_meals = ['dinner', 'snack']
        elif current_hour < 22:  # Before 10 PM
            remaining_meals = ['snack']
        
        return remaining_meals

    def _analyze_meal_timing(self, consumption_by_meal: Dict, user_timezone: str) -> Dict[str, Any]:
        """Analyze meal timing patterns."""
        timing_analysis = {
            "on_schedule": True,
            "late_meals": [],
            "missed_meals": [],
            "timing_score": 100
        }
        
        try:
            import pytz
            user_tz = pytz.timezone(user_timezone)
            current_time = datetime.now(user_tz)
            current_hour = current_time.hour
        except Exception:
            current_hour = datetime.utcnow().hour
        
        # Check for missed meals based on time
        if current_hour >= 11 and 'breakfast' not in consumption_by_meal:
            timing_analysis["missed_meals"].append("breakfast")
            timing_analysis["timing_score"] -= 20
        
        if current_hour >= 15 and 'lunch' not in consumption_by_meal:
            timing_analysis["missed_meals"].append("lunch")
            timing_analysis["timing_score"] -= 25
        
        if current_hour >= 20 and 'dinner' not in consumption_by_meal:
            timing_analysis["missed_meals"].append("dinner")
            timing_analysis["timing_score"] -= 30
        
        timing_analysis["on_schedule"] = len(timing_analysis["missed_meals"]) == 0
        timing_analysis["timing_score"] = max(0, timing_analysis["timing_score"])
        
        return timing_analysis

    def _check_calibration_needed(
        self,
        consumed_calories: float,
        target_calories: int,
        remaining_meals: List[str],
        consumption_by_meal: Dict
    ) -> bool:
        """Check if meal plan calibration is needed."""
        
        # Calibration needed if significantly over or under target
        calorie_deviation = abs(consumed_calories - target_calories) / target_calories
        
        # If over 30% deviation and meals remaining, calibration needed
        if calorie_deviation > 0.3 and remaining_meals:
            return True
        
        # If consumed more than 80% of calories but still have major meals remaining
        if consumed_calories > (target_calories * 0.8) and any(meal in remaining_meals for meal in ['lunch', 'dinner']):
            return True
        
        # If very low consumption and it's late in the day
        if consumed_calories < (target_calories * 0.3) and len(remaining_meals) <= 2:
            return True
        
        return False

    def _get_calibration_reason(
        self,
        consumed_calories: float,
        target_calories: int,
        remaining_meals: List[str],
        consumption_by_meal: Dict
    ) -> str:
        """Get reason for calibration."""
        calorie_percentage = (consumed_calories / target_calories) * 100
        
        if calorie_percentage > 120:
            return f"consumed_excess_calories_{calorie_percentage:.0f}%"
        elif calorie_percentage < 30 and len(remaining_meals) <= 2:
            return f"low_consumption_late_day_{calorie_percentage:.0f}%"
        elif calorie_percentage > 80 and any(meal in remaining_meals for meal in ['lunch', 'dinner']):
            return f"high_consumption_major_meals_remaining_{calorie_percentage:.0f}%"
        else:
            return "significant_deviation_from_target"

    async def _generate_comprehensive_meal_recommendations(
        self,
        health_analysis: Dict[str, Any],
        history_analysis: Dict[str, Any],
        consumption_analysis: Dict[str, Any],
        user_profile: Dict[str, Any],
        user_timezone: str
    ) -> Dict[str, Any]:
        """Generate comprehensive AI-powered meal recommendations."""
        
        # Extract key information for AI prompt
        medical_conditions = health_analysis.get("medical_analysis", {}).get("conditions", [])
        medications = health_analysis.get("medication_analysis", {}).get("medications", [])
        nutritional_goals = health_analysis["nutritional_goals"]
        remaining_targets = consumption_analysis["remaining_targets"]
        remaining_meals = consumption_analysis["remaining_meals"]
        consumed_foods_today = self._extract_consumed_foods(consumption_analysis["consumption_summary"])
        
        # Historical preferences
        preferred_foods = history_analysis.get("food_preferences", {}).get("most_frequent_foods", [])[:5]
        successful_recipes = history_analysis.get("recipe_success_rates", {}).get("top_successful_recipes", [])[:3]
        
        # User preferences - CHECK BOTH dietaryRestrictions AND dietaryFeatures
        dietary_restrictions = user_profile.get("dietaryRestrictions", [])
        dietary_features = user_profile.get("dietaryFeatures", [])  # This is where vegetarian info is stored!
        food_preferences = user_profile.get("foodPreferences", [])
        allergies = user_profile.get("allergies", [])
        strong_dislikes = user_profile.get("strongDislikes", [])
        
        # 🚨 COMBINE dietary restrictions and features for complete dietary info
        all_dietary_info = dietary_restrictions + dietary_features
        
        # 🚨 ENHANCED DEBUG LOGGING
        print(f"[MEAL_GEN_DEBUG] ============== DIETARY ANALYSIS DEBUG ==============")
        print(f"[MEAL_GEN_DEBUG] dietaryRestrictions from profile: {dietary_restrictions}")
        print(f"[MEAL_GEN_DEBUG] dietaryFeatures from profile: {dietary_features}")
        print(f"[MEAL_GEN_DEBUG] Combined all_dietary_info: {all_dietary_info}")
        print(f"[MEAL_GEN_DEBUG] allergies: {allergies}")
        print(f"[MEAL_GEN_DEBUG] strong_dislikes: {strong_dislikes}")
        print(f"[MEAL_GEN_DEBUG] ==================================================")
        
        # Create diverse meal options based on different cuisines and cooking methods
        import random
        from datetime import datetime
        
        # Use current time as seed for variety
        random.seed(int(datetime.now().timestamp()) % 1000)
        
        # 🥩🥗 FILTER PROTEIN SOURCES BY DIETARY RESTRICTIONS
        all_proteins = {
            "vegetarian": ["pan-seared tofu", "lentil patties", "chickpea fritters", "tempeh", "black bean patties", "quinoa-veggie patties", "marinated portobello mushrooms", "hemp seed tofu", "seitan strips"],
            "vegan": ["pan-seared tofu", "lentil patties", "chickpea fritters", "tempeh", "black bean patties", "quinoa-veggie patties", "hemp seed tofu", "seitan strips", "walnut meat"],
            "pescatarian": ["baked salmon", "grilled shrimp", "baked cod", "pan-seared tofu", "lentil patties", "chickpea fritters", "tempeh", "tuna steaks", "sea bass"],
            "omnivore": ["grilled chicken breast", "baked salmon", "pan-seared tofu", "turkey meatballs", "lentil patties", "grilled shrimp", "baked cod", "chickpea fritters", "lean beef strips", "tempeh"]
        }
        
        # Determine user's dietary category - check BOTH restrictions and features
        dietary_category = "omnivore"  # default
        diet_info = [str(d).lower().strip() for d in all_dietary_info if d]
        
        # 🚨 ENHANCED VEGETARIAN DETECTION - Check multiple fields and formats
        vegetarian_indicators = []
        
        # Check in all possible profile fields for vegetarian indicators
        profile_fields_to_check = [
            dietary_restrictions, dietary_features, user_profile.get('dietType', []), 
            user_profile.get('diet_type', []), user_profile.get('diet_features', [])
        ]
        
        for field in profile_fields_to_check:
            if isinstance(field, list):
                vegetarian_indicators.extend([str(item).lower().strip() for item in field if item])
            elif field:
                vegetarian_indicators.append(str(field).lower().strip())
        
        # Comprehensive vegetarian detection
        is_vegetarian = any(
            "vegetarian" in indicator or 
            "veg" in indicator or
            "no meat" in indicator or
            "plant-based" in indicator
            for indicator in vegetarian_indicators
        )
        
        # Check for dietary patterns in BOTH fields - handle various formats
        if is_vegetarian or any("vegetarian" in d for d in diet_info):
            dietary_category = "vegetarian"
            # Check if eggs are allowed for vegetarians
            has_eggs = any("with eggs" in d or "with egg" in d for d in diet_info + vegetarian_indicators)
            no_eggs = any("no eggs" in d or "no egg" in d or "vegetarian (no eggs)" in d for d in diet_info + vegetarian_indicators)
            print(f"[EnhancedSmartMealPlanner] Vegetarian detected - eggs allowed: {has_eggs}, no eggs: {no_eggs}")
        elif any("vegan" in d for d in diet_info):
            dietary_category = "vegan"  
        elif any("pescatarian" in d for d in diet_info):
            dietary_category = "pescatarian"
        
        print(f"[EnhancedSmartMealPlanner] Dietary category: {dietary_category} (from {all_dietary_info})")
        
        # 🚨 ADDITIONAL DEBUG - Show exactly what we're checking
        print(f"[MEAL_GEN_DEBUG] ============== DIETARY CATEGORY DETECTION ==============")
        print(f"[MEAL_GEN_DEBUG] diet_info (lowercased): {diet_info}")
        print(f"[MEAL_GEN_DEBUG] Checking for 'vegetarian' in diet_info...")
        vegetarian_found = [d for d in diet_info if "vegetarian" in d]
        print(f"[MEAL_GEN_DEBUG] Vegetarian matches found: {vegetarian_found}")
        print(f"[MEAL_GEN_DEBUG] Final dietary_category determined: {dietary_category}")
        print(f"[MEAL_GEN_DEBUG] =====================================================")
        
        # Get appropriate proteins for user's diet - ENHANCED with safety check
        if dietary_category == "vegetarian" or is_vegetarian:
            proteins = all_proteins["vegetarian"]
        elif dietary_category == "vegan":
            proteins = all_proteins["vegan"]
        elif dietary_category == "pescatarian":
            proteins = all_proteins["pescatarian"]
        else:
            proteins = all_proteins["omnivore"]
            
        print(f"[MEAL_GEN_DEBUG] Selected proteins for {dietary_category} (is_vegetarian: {is_vegetarian}): {proteins}")
        
        # Diverse carb sources (diabetes-friendly)
        carbs = ["quinoa", "brown rice", "sweet potato", "cauliflower rice", "whole grain pasta", "barley", "bulgur wheat", "wild rice", "buckwheat", "steel-cut oats"]
        
        # Diverse vegetables
        vegetables = ["steamed broccoli", "roasted Brussels sprouts", "sautéed spinach", "grilled zucchini", "roasted bell peppers", "steamed asparagus", "roasted cauliflower", "sautéed kale", "grilled eggplant", "steamed green beans"]
        
        # Cooking methods for variety
        cooking_methods = ["grilled", "baked", "pan-seared", "roasted", "steamed", "sautéed", "braised", "stir-fried"]
        
        # Different cuisine inspirations
        cuisines = ["Mediterranean", "Asian-inspired", "Mexican-style", "Italian-style", "Middle Eastern", "Indian-spiced", "Thai-inspired", "Greek-style"]
        
        prompt = f"""You are a creative AI chef specializing in diabetes-friendly meal planning. Generate UNIQUE, SPECIFIC meals that are different every time.

NUTRITIONAL TARGETS (distribute across {len(remaining_meals)} meals):
- Total Calories Remaining: {remaining_targets['calories']}
- Total Protein Remaining: {remaining_targets['protein']}g 
- Total Carbs Remaining: {remaining_targets['carbs']}g
- Total Fat Remaining: {remaining_targets['fat']}g

MEALS TO CREATE: {remaining_meals}

USER PROFILE:
- Medical Conditions: {medical_conditions}
- Dietary Restrictions: {dietary_restrictions}  
- Allergies: {allergies}
- Dislikes: {strong_dislikes}
- Preferences: {food_preferences}

ALREADY CONSUMED TODAY: {consumed_foods_today}

CREATIVITY GUIDELINES:
- Use different cuisines: {random.sample(cuisines, min(3, len(cuisines)))}
- Vary cooking methods: {random.sample(cooking_methods, min(4, len(cooking_methods)))}
- Mix protein sources: {random.sample(proteins, min(5, len(proteins)))}
- Rotate vegetables: {random.sample(vegetables, min(5, len(vegetables)))}
- Use diverse grains: {random.sample(carbs, min(4, len(carbs)))}

🚨🚨🚨 CRITICAL DIETARY RESTRICTIONS - READ CAREFULLY 🚨🚨🚨
USER IS: {dietary_category.upper()}
DIETARY INFO: {all_dietary_info}
DIETARY FEATURES: {dietary_features}
VEGETARIAN INDICATORS: {vegetarian_indicators}

🛑 ABSOLUTELY FORBIDDEN - DO NOT INCLUDE ANY OF THESE:
{"- NO MEAT: chicken, beef, pork, lamb, turkey, duck, venison" if dietary_category == "vegetarian" or is_vegetarian else ""}
{"- NO SEAFOOD: fish, salmon, tuna, shrimp, crab, lobster, mussels, oysters" if dietary_category == "vegetarian" or is_vegetarian else ""}
{"- NO POULTRY: chicken, turkey, duck, goose" if dietary_category == "vegetarian" or is_vegetarian else ""}
{"- NO ANIMAL FLESH OF ANY KIND" if dietary_category == "vegetarian" or is_vegetarian else ""}
{"- ONLY PLANT-BASED PROTEINS ALLOWED" if dietary_category == "vegetarian" or is_vegetarian else ""}

🌱 ONLY USE THESE PROTEINS FOR {dietary_category.upper()}: {proteins}

EXAMPLES of creative meal names for {dietary_category.upper()} diet:
{self._get_dietary_examples(dietary_category)}

Create DIVERSE, SPECIFIC meals in JSON format. Make each meal unique and interesting:

🚨 ABSOLUTE REQUIREMENT: If user is VEGETARIAN, you MUST NOT include ANY animal flesh, fish, seafood, chicken, turkey, beef, pork, or any meat products. ONLY plant-based proteins like tofu, lentils, tempeh, chickpeas are allowed.
{"🥚 EGG RESTRICTION: User is vegetarian with NO EGGS - do not include eggs, omelets, quiche, egg-based dishes" if (dietary_category == "vegetarian" or is_vegetarian) and any("no egg" in d for d in diet_info + vegetarian_indicators) else ""}

⚠️ MANDATORY: All meals MUST comply with {dietary_category} dietary restrictions! Any meal containing forbidden ingredients will be REJECTED!

🚨 TRIPLE CHECK: User profile indicates vegetarian preferences: {is_vegetarian}. If TRUE, meals MUST be 100% vegetarian!

{{"""
        
        # 🎯 SMART PROTEIN DISTRIBUTION - Calculate nutrition per meal based on remaining needs
        total_remaining_calories = remaining_targets.get('calories', 0)
        total_remaining_protein = remaining_targets.get('protein', 0) 
        total_remaining_carbs = remaining_targets.get('carbs', 0)
        total_remaining_fat = remaining_targets.get('fat', 0)
        
        print(f"[EnhancedSmartMealPlanner] 🎯 REMAINING TARGETS: {total_remaining_calories} cal, {total_remaining_protein}g protein, {total_remaining_carbs}g carbs, {total_remaining_fat}g fat")
        print(f"[EnhancedSmartMealPlanner] 🎯 DISTRIBUTING ACROSS: {remaining_meals} ({len(remaining_meals)} meals)")
        
        if len(remaining_meals) == 0:
            # No meals to plan
            calories_per_meal = 350
            protein_per_meal = 25
            carbs_per_meal = 35
            fat_per_meal = 15
        else:
            # Smart distribution based on meal type priorities
            calories_per_meal = max(200, total_remaining_calories // len(remaining_meals))
            
            # Protein priority: Ensure we meet protein goals
            base_protein_per_meal = max(15, total_remaining_protein // len(remaining_meals))
            
            # Give extra protein to dinner and snacks if needed
            protein_per_meal = base_protein_per_meal
            if total_remaining_protein > (base_protein_per_meal * len(remaining_meals)):
                # Add extra protein to prioritize protein goals
                extra_protein = (total_remaining_protein - (base_protein_per_meal * len(remaining_meals))) // len(remaining_meals)
                protein_per_meal = base_protein_per_meal + extra_protein
            
            carbs_per_meal = max(20, total_remaining_carbs // len(remaining_meals))
            fat_per_meal = max(10, total_remaining_fat // len(remaining_meals))
        
        print(f"[EnhancedSmartMealPlanner] 🎯 PER MEAL TARGETS: {calories_per_meal} cal, {protein_per_meal}g protein, {carbs_per_meal}g carbs, {fat_per_meal}g fat")
        
        # Create JSON structure
        json_structure = {}
        for meal_type in remaining_meals:
            json_structure[meal_type] = {
                "meal_name": f"Creative {meal_type} with specific ingredients and cooking method",
                "description": "Detailed description highlighting flavors and cooking technique",
                "estimated_calories": calories_per_meal,
                "estimated_protein": protein_per_meal,
                "estimated_carbs": carbs_per_meal,
                "estimated_fat": fat_per_meal,
                "prep_time": "15-25 minutes",
                "health_benefits": ["diabetes_friendly", "heart_healthy", "high_protein"],
                "ingredients": ["specific ingredient 1", "specific ingredient 2", "specific ingredient 3", "herbs/spices"],
                "preparation_tips": "Step-by-step cooking instructions"
            }
        
        prompt += f"""
{json.dumps(json_structure, indent=2)}
}}

CRITICAL REQUIREMENTS:
1. Each meal must be COMPLETELY DIFFERENT and creative
2. Use specific ingredients and cooking methods
3. Include cuisine inspiration in meal names
4. Vary protein sources across meals
5. Make it diabetes-friendly (low glycemic index)
6. Respect allergies: {allergies}
7. Avoid dislikes: {strong_dislikes}
8. Return ONLY valid JSON without any other text

BE CREATIVE! Make each meal sound delicious and unique!"""
        
        # Try AI generation with multiple attempts for reliability
        for attempt in range(3):
            try:
                print(f"[EnhancedSmartMealPlanner] AI meal generation attempt {attempt + 1}/3...")
                
                # Adjust temperature based on attempt for variety
                temperature = 0.7 if attempt == 0 else 0.5 if attempt == 1 else 0.3
                
                ai_response = await robust_openai_call(
                    [{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=1500  # Increased for more detailed responses
                )
                
                if not ai_response or not ai_response.get("success") or not ai_response.get("content"):
                    print(f"[EnhancedSmartMealPlanner] Attempt {attempt + 1}: No valid AI response")
                    continue
                
                content = ai_response["content"].strip()
                print(f"[EnhancedSmartMealPlanner] Attempt {attempt + 1}: Received content ({len(content)} chars)")
                
                # Clean up formatting more thoroughly
                content = content.replace("```json", "").replace("```", "").strip()
                
                # Remove any text before the first {
                if "{" in content:
                    content = content[content.find("{"):]
                
                # Remove any text after the last }
                if "}" in content:
                    content = content[:content.rfind("}") + 1]
                
                try:
                    recommendations = json.loads(content)
                    print(f"[EnhancedSmartMealPlanner] Attempt {attempt + 1}: Successfully parsed JSON")
                    
                    # 🚨 DEBUG: Log generated meals for dietary compliance check
                    print(f"[MEAL_GEN_DEBUG] ============== GENERATED MEALS DEBUG ==============")
                    for meal_type, meal_data in recommendations.items():
                        if isinstance(meal_data, dict):
                            meal_name = meal_data.get('meal_name', 'No name')
                            ingredients = meal_data.get('ingredients', [])
                            print(f"[MEAL_GEN_DEBUG] {meal_type.upper()}: {meal_name}")
                            print(f"[MEAL_GEN_DEBUG] {meal_type.upper()} ingredients: {ingredients}")
                            
                            # Check for problematic ingredients
                            problematic = []
                            for ingredient in ingredients:
                                ingredient_lower = str(ingredient).lower()
                                if any(meat in ingredient_lower for meat in ['chicken', 'beef', 'pork', 'turkey', 'salmon', 'fish', 'meat', 'bacon', 'ham', 'sausage', 'tuna', 'duck', 'lamb']):
                                    problematic.append(ingredient)
                            if problematic:
                                print(f"[MEAL_GEN_DEBUG] ⚠️  {meal_type.upper()} CONTAINS PROBLEMATIC INGREDIENTS: {problematic}")
                            
                            # Check meal name for problematic terms too
                            meal_name_lower = meal_name.lower()
                            if any(meat in meal_name_lower for meat in ['chicken', 'beef', 'pork', 'turkey', 'salmon', 'fish', 'meat', 'bacon', 'ham', 'sausage', 'tuna', 'duck', 'lamb']):
                                print(f"[MEAL_GEN_DEBUG] ⚠️  {meal_type.upper()} MEAL NAME CONTAINS MEAT: {meal_name}")
                    print(f"[MEAL_GEN_DEBUG] ================================================")
                    
                    # Validate that we got actual meal recommendations
                    valid_meals = 0
                    for meal_type in remaining_meals:
                        if meal_type in recommendations and isinstance(recommendations[meal_type], dict):
                            meal_name = recommendations[meal_type].get('meal_name', '')
                            if meal_name and len(meal_name) > 10 and 'specific' not in meal_name.lower():
                                valid_meals += 1
                    
                    if valid_meals >= len(remaining_meals):
                        print(f"[EnhancedSmartMealPlanner] SUCCESS! Generated {valid_meals} valid meals")
                        
                        # 🚨 CRITICAL VALIDATION: Check for forbidden animal products
                        if dietary_category == "vegetarian" or is_vegetarian:
                            validation_result = self._validate_vegetarian_meals(recommendations, remaining_meals, all_dietary_info + vegetarian_indicators)
                            if not validation_result["is_valid"]:
                                print(f"🚨 [DIETARY_VIOLATION] Rejected meals containing: {validation_result['violations']}")
                                print(f"🚨 [DIETARY_VIOLATION] Attempting new generation...")
                                continue  # Try again with different generation
                            else:
                                print(f"✅ [DIETARY_VALIDATION] All meals are vegetarian-compliant!")
                        
                        # Filter and return successful recommendations
                        filtered_recommendations = {}
                        for meal_type in remaining_meals:
                            if meal_type in recommendations:
                                filtered_recommendations[meal_type] = recommendations[meal_type]
                                print(f"[EnhancedSmartMealPlanner] ✅ {meal_type}: {recommendations[meal_type].get('meal_name', 'Unknown')}")
                        
                        return filtered_recommendations
                    else:
                        print(f"[EnhancedSmartMealPlanner] Attempt {attempt + 1}: Only {valid_meals}/{len(remaining_meals)} valid meals generated")
                        
                except json.JSONDecodeError as json_error:
                    print(f"[EnhancedSmartMealPlanner] Attempt {attempt + 1}: JSON parsing failed - {json_error}")
                    print(f"[EnhancedSmartMealPlanner] Content preview: {content[:300]}...")
                    continue
                    
            except Exception as e:
                print(f"[EnhancedSmartMealPlanner] Attempt {attempt + 1}: Generation failed - {e}")
                continue
        
        print(f"[EnhancedSmartMealPlanner] All AI attempts failed, using AI-generated fallback...")
        
        # Use AI for fallback too, but with simpler prompt
        return await self._create_ai_fallback_recommendations(remaining_meals, remaining_targets)

    def _apply_dynamic_calibration(
        self,
        meal_recommendations: Dict[str, Any],
        consumption_analysis: Dict[str, Any],
        nutritional_goals: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply dynamic calibration to meal recommendations with intelligent macro handling."""
        
        if not consumption_analysis.get("requires_calibration", False):
            return meal_recommendations
        
        print(f"[EnhancedSmartMealPlanner] Applying dynamic calibration...")
        
        calibrated_plan = meal_recommendations.copy()
        remaining_targets = consumption_analysis["remaining_targets"]
        remaining_meals = consumption_analysis["remaining_meals"]
        
        if not remaining_meals:
            return calibrated_plan
        
        # SMART CALIBRATION: Handle macro overages intelligently
        remaining_calories = remaining_targets["calories"]
        remaining_protein = remaining_targets["protein"]
        remaining_carbs = remaining_targets["carbs"] 
        remaining_fat = remaining_targets["fat"]
        
        # Check if user is over their macro goals
        calories_over = remaining_calories < 0
        protein_over = remaining_protein < 0
        carbs_over = remaining_carbs < 0
        fat_over = remaining_fat < 0
        
        print(f"[EnhancedSmartMealPlanner] Macro status - Calories: {remaining_calories}, Protein: {remaining_protein}, Carbs: {remaining_carbs}, Fat: {remaining_fat}")
        
        # Apply calibration to each remaining meal
        for meal_type in remaining_meals:
            if meal_type in calibrated_plan and isinstance(calibrated_plan[meal_type], dict):
                meal_data = calibrated_plan[meal_type]
                
                # INTELLIGENT SNACK HANDLING
                if meal_type == "snack":
                    if calories_over:
                        # User is over calorie goal - suggest no snack or pure protein only
                        if remaining_protein > 0:
                            # Still need protein - suggest pure protein snack
                            meal_data["meal_name"] = "Optional pure protein snack (only if genuinely hungry)"
                            meal_data["description"] = "Since you've exceeded your calorie goal, only pure protein is recommended if needed"
                            meal_data["estimated_calories"] = 50
                            meal_data["estimated_protein"] = max(10, min(20, int(remaining_protein)))
                            meal_data["estimated_carbs"] = 0
                            meal_data["estimated_fat"] = 2
                            meal_data["ingredients"] = ["Greek yogurt (plain, non-fat)", "or protein powder with water", "or small handful of almonds"]
                            meal_data["personalization_notes"] = ["You've exceeded your calorie goal", "Only consume if genuinely hungry", "Focus on pure protein to meet protein targets"]
                        else:
                            # Over all macros - no snack needed
                            meal_data["meal_name"] = "No additional snacks needed"
                            meal_data["description"] = "You've met or exceeded your daily nutritional goals. Focus on hydration and rest."
                            meal_data["estimated_calories"] = 0
                            meal_data["estimated_protein"] = 0
                            meal_data["estimated_carbs"] = 0
                            meal_data["estimated_fat"] = 0
                            meal_data["ingredients"] = ["Water", "herbal tea", "or sparkling water with lemon"]
                            meal_data["personalization_notes"] = ["Goals achieved for today", "Stay hydrated", "No additional food needed"]
                    elif remaining_calories <= 100:
                        # Close to calorie goal - very light snack only if needed
                        meal_data["meal_name"] = "Optional light snack (only if genuinely hungry)"
                        meal_data["description"] = "You're close to your calorie goal. Only eat if genuinely hungry."
                        meal_data["estimated_calories"] = min(50, max(0, int(remaining_calories)))
                        meal_data["estimated_protein"] = max(5, min(10, int(remaining_protein / len(remaining_meals)) if remaining_protein > 0 else 0))
                        meal_data["estimated_carbs"] = 5
                        meal_data["estimated_fat"] = 1
                        meal_data["ingredients"] = ["1 small apple", "or cucumber slices", "or herbal tea"]
                        meal_data["personalization_notes"] = ["Close to calorie goal", "Only if genuinely hungry", "Keep portions very small"]
                    else:
                        # Normal distribution for snacks under calorie goal
                        calories_per_meal = max(100, remaining_calories / len(remaining_meals))
                        protein_per_meal = max(10, remaining_protein / len(remaining_meals)) if remaining_protein > 0 else 10
                        carbs_per_meal = max(15, remaining_carbs / len(remaining_meals)) if remaining_carbs > 0 else 15
                        fat_per_meal = max(5, remaining_fat / len(remaining_meals)) if remaining_fat > 0 else 5
                        
                        meal_data["estimated_calories"] = int(calories_per_meal)
                        meal_data["estimated_protein"] = int(protein_per_meal)
                        meal_data["estimated_carbs"] = int(carbs_per_meal)
                        meal_data["estimated_fat"] = int(fat_per_meal)
                else:
                    # For main meals (breakfast, lunch, dinner)
                    if calories_over:
                        # Over calorie goal - suggest very light versions
                        meal_data["meal_name"] = f"Light {meal_type} (modified portion)"
                        meal_data["description"] = f"Reduced portion {meal_type} as you've exceeded your calorie goal"
                        meal_data["estimated_calories"] = 150
                        meal_data["estimated_protein"] = max(15, min(25, int(remaining_protein / len(remaining_meals)) if remaining_protein > 0 else 15))
                        meal_data["estimated_carbs"] = 10
                        meal_data["estimated_fat"] = 5
                        meal_data["personalization_notes"] = ["Reduced portion due to calorie overage", "Focus on protein and vegetables", "Minimize carbs and fats"]
                    else:
                        # Normal distribution
                        calories_per_meal = max(200, remaining_calories / len(remaining_meals))
                        protein_per_meal = max(15, remaining_protein / len(remaining_meals)) if remaining_protein > 0 else 20
                        carbs_per_meal = max(20, remaining_carbs / len(remaining_meals)) if remaining_carbs > 0 else 25
                        fat_per_meal = max(10, remaining_fat / len(remaining_meals)) if remaining_fat > 0 else 12
                        
                        meal_data["estimated_calories"] = int(calories_per_meal)
                        meal_data["estimated_protein"] = int(protein_per_meal)
                        meal_data["estimated_carbs"] = int(carbs_per_meal)
                        meal_data["estimated_fat"] = int(fat_per_meal)
                
                # Add calibration note
                if "personalization_notes" not in meal_data:
                    meal_data["personalization_notes"] = []
                
                meal_data["personalization_notes"].append(
                    f"Intelligently calibrated based on current macro status"
                )
        
        return calibrated_plan

    def _generate_nutrition_insights(
        self,
        health_analysis: Dict[str, Any],
        consumption_analysis: Dict[str, Any],
        meal_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate intelligent nutrition insights."""
        
        daily_progress = consumption_analysis["daily_progress"]
        remaining_targets = consumption_analysis["remaining_targets"]
        
        insights = {
            "progress_assessment": [],
            "nutritional_alerts": [],  # DISABLED: User requested removal
            "optimization_tips": [],   # DISABLED: User requested removal  
            "health_focus_areas": []   # DISABLED: User requested removal
        }
        
        # Progress assessment (keep this for internal use)
        for nutrient, data in daily_progress.items():
            percentage = data["percentage"]
            if percentage >= 90:
                insights["progress_assessment"].append(f"excellent_{nutrient}_progress")
            elif percentage >= 70:
                insights["progress_assessment"].append(f"good_{nutrient}_progress")
            elif percentage >= 50:
                insights["progress_assessment"].append(f"moderate_{nutrient}_progress")
            else:
                insights["progress_assessment"].append(f"low_{nutrient}_progress")
        
        # 🚫 DISABLED: Nutritional alerts (removed per user request)
        # if daily_progress["calories"]["percentage"] > 120:
        #     insights["nutritional_alerts"].append("calorie_excess_alert")
        # elif daily_progress["calories"]["percentage"] < 50:
        #     insights["nutritional_alerts"].append("calorie_deficit_alert")
        # 
        # if daily_progress["protein"]["percentage"] < 60:
        #     insights["nutritional_alerts"].append("protein_insufficient_alert")
        
        # 🚫 DISABLED: Optimization tips and health focus (removed per user request)
        # ai_recommendations = health_analysis.get("ai_recommendations", {})
        # insights["optimization_tips"] = ai_recommendations.get("personalized_tips", [])
        # insights["health_focus_areas"] = ai_recommendations.get("key_nutritional_focuses", [])
        
        # Medical considerations (keep this as it's different from the UI sections)
        medical_considerations = health_analysis.get("ai_recommendations", {}).get("medical_considerations", [])
        if medical_considerations:
            insights["medical_reminders"] = medical_considerations
        
        return insights

    def _extract_personalization_factors(
        self,
        health_analysis: Dict[str, Any],
        history_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract key personalization factors."""
        
        return {
            "health_risk_level": health_analysis.get("medical_analysis", {}).get("risk_level", "low"),
            "dietary_complexity": health_analysis.get("medical_analysis", {}).get("dietary_restrictions", []),
            "medication_interactions": len(health_analysis.get("medication_analysis", {}).get("food_interactions", [])),
            "historical_success_rate": history_analysis.get("success_patterns", {}).get("success_rate", 0.0),
            "food_diversity_score": history_analysis.get("food_preferences", {}).get("dietary_diversity_score", 0.5),
            "adherence_level": history_analysis.get("adherence_analysis", {}).get("overall_adherence_rate", 0.0),
            "confidence_level": history_analysis.get("confidence_score", 0.0)
        }

    def _calculate_recommendation_confidence(
        self,
        health_analysis: Dict[str, Any],
        history_analysis: Dict[str, Any],
        consumption_analysis: Dict[str, Any]
    ) -> float:
        """Calculate overall recommendation confidence score."""
        
        # Health data completeness (0-1)
        health_completeness = 0.8 if health_analysis.get("medical_analysis", {}).get("conditions") else 0.3
        
        # Historical data confidence
        history_confidence = history_analysis.get("confidence_score", 0.0)
        
        # Current consumption data quality
        consumption_quality = 0.9 if len(consumption_analysis.get("consumption_summary", {})) > 0 else 0.5
        
        # Medical risk factor (higher risk = higher confidence needed, so slight penalty)
        risk_level = health_analysis.get("medical_analysis", {}).get("risk_level", "low")
        risk_adjustment = 1.0 if risk_level == "high" else 0.95 if risk_level == "medium" else 0.9
        
        # Calculate weighted average
        confidence = (
            health_completeness * 0.4 +
            history_confidence * 0.3 +
            consumption_quality * 0.3
        ) * risk_adjustment
        
        return round(min(1.0, confidence), 3)

    def _assess_data_completeness(
        self,
        user_profile: Dict[str, Any],
        health_analysis: Dict[str, Any],
        history_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess completeness of available data for meal planning."""
        
        profile_score = 0.0
        profile_fields = ["medicalConditions", "currentMedications", "dietaryRestrictions", "allergies", "age", "weight", "height"]
        filled_fields = sum(1 for field in profile_fields if user_profile.get(field))
        profile_score = filled_fields / len(profile_fields)
        
        health_score = 0.5  # Base score for health analysis completion
        if health_analysis.get("medical_analysis", {}).get("conditions"):
            health_score += 0.3
        if health_analysis.get("lab_analysis", {}).get("lab_values"):
            health_score += 0.2
        
        history_score = min(1.0, history_analysis.get("total_meal_plans", 0) / 5)  # Full score at 5+ plans
        
        return {
            "profile_completeness": round(profile_score, 2),
            "health_analysis_completeness": round(min(1.0, health_score), 2),
            "history_completeness": round(history_score, 2),
            "overall_completeness": round((profile_score + health_score + history_score) / 3, 2),
            "missing_critical_data": self._identify_missing_critical_data(user_profile)
        }

    def _identify_missing_critical_data(self, user_profile: Dict[str, Any]) -> List[str]:
        """Identify missing critical data for meal planning."""
        missing = []
        
        critical_fields = {
            "calorieTarget": "calorie_goal",
            "medicalConditions": "medical_conditions",
            "dietaryRestrictions": "dietary_restrictions",
            "allergies": "allergies"
        }
        
        for field, description in critical_fields.items():
            if not user_profile.get(field):
                missing.append(description)
        
        return missing

    def _extract_consumed_foods(self, consumption_summary: Dict[str, List]) -> List[str]:
        """Extract list of consumed foods from consumption summary."""
        consumed_foods = []
        
        for meal_type, foods in consumption_summary.items():
            for food_record in foods:
                food_name = food_record.get("food_name", "")
                if food_name:
                    consumed_foods.append(f"{meal_type}: {food_name}")
        
        return consumed_foods[:10]  # Limit to prevent prompt overflow

    def _create_fallback_recommendations(
        self,
        remaining_meals: List[str],
        remaining_targets: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create fallback recommendations when AI generation fails."""
        
        # SMART FALLBACK: Calculate calories per meal with overage handling
        remaining_calories = remaining_targets.get("calories", 400)
        calories_over = remaining_calories < 0
        
        if calories_over:
            calories_per_meal = 150  # Very conservative when over goal
            protein_per_meal = max(15, remaining_targets.get("protein", 25) // max(len(remaining_meals), 1)) if remaining_targets.get("protein", 25) > 0 else 15
        else:
            calories_per_meal = remaining_calories // max(len(remaining_meals), 1)
            protein_per_meal = remaining_targets.get("protein", 25) // max(len(remaining_meals), 1)
        
        fallback_meals = {
            "breakfast": {
                "meal_name": "Scrambled eggs with avocado toast and spinach",
                "description": "High-protein breakfast with healthy fats and fiber",
                "estimated_calories": min(400, calories_per_meal),
                "estimated_protein": max(20, protein_per_meal),
                "estimated_carbs": 25,
                "estimated_fat": 15,
                "prep_time": "10 minutes",
                "health_benefits": ["blood_sugar_control", "sustained_energy", "high_protein"],
                "ingredients": ["2 eggs", "1 slice whole grain bread", "½ avocado", "handful spinach", "olive oil"],
                "preparation_tips": "Scramble eggs with spinach, toast bread, mash avocado on top"
            },
            "lunch": {
                "meal_name": "Grilled chicken salad with quinoa and chickpeas",
                "description": "Protein-rich salad with complete amino acids and fiber",
                "estimated_calories": min(500, calories_per_meal),
                "estimated_protein": max(30, protein_per_meal),
                "estimated_carbs": 35,
                "estimated_fat": 18,
                "prep_time": "15 minutes",
                "health_benefits": ["complete_protein", "fiber_rich", "diabetes_friendly"],
                "ingredients": ["4oz grilled chicken breast", "½ cup cooked quinoa", "⅓ cup chickpeas", "mixed greens", "olive oil vinaigrette"],
                "preparation_tips": "Combine all ingredients, drizzle with olive oil and lemon"
            },
            "dinner": {
                "meal_name": "Baked salmon with roasted sweet potato and steamed broccoli",
                "description": "Omega-3 rich dinner with complex carbs and vegetables",
                "estimated_calories": min(550, calories_per_meal),
                "estimated_protein": max(35, protein_per_meal),
                "estimated_carbs": 40,
                "estimated_fat": 20,
                "prep_time": "25 minutes",
                "health_benefits": ["omega_3_fatty_acids", "anti_inflammatory", "heart_healthy"],
                "ingredients": ["5oz salmon fillet", "1 medium roasted sweet potato", "1 cup steamed broccoli", "olive oil", "herbs"],
                "preparation_tips": "Bake salmon at 400°F for 15 mins, roast sweet potato, steam broccoli"
            },
            "snack": {
                "meal_name": "No additional snacks needed" if calories_over else "Greek yogurt with mixed berries and chopped almonds",
                "description": "You've exceeded your calorie goal - focus on hydration" if calories_over else "High-protein snack with antioxidants and healthy fats",
                "estimated_calories": 0 if calories_over else min(200, calories_per_meal),
                "estimated_protein": 0 if calories_over else max(15, protein_per_meal),
                "estimated_carbs": 0 if calories_over else 18,
                "estimated_fat": 0 if calories_over else 8,
                "prep_time": "0 minutes" if calories_over else "2 minutes",
                "health_benefits": ["hydration", "goal_achievement"] if calories_over else ["probiotics", "antioxidants", "protein_rich"],
                "ingredients": ["Water", "herbal tea"] if calories_over else ["¾ cup Greek yogurt", "½ cup mixed berries", "1 tbsp chopped almonds", "dash of cinnamon"],
                "preparation_tips": "Stay hydrated and rest" if calories_over else "Mix yogurt with berries, top with almonds and cinnamon",
                "personalization_notes": ["Calorie goal exceeded - no snack recommended"] if calories_over else []
            }
        }
        
        # Filter to only remaining meals
        recommendations = {}
        for meal_type in remaining_meals:
            if meal_type in fallback_meals:
                recommendations[meal_type] = fallback_meals[meal_type]
        
        # Add general recommendations
        recommendations.update({
            "daily_hydration_plan": {
                "total_water_target": "8-10 glasses",
                "timing_suggestions": ["with_meals", "between_meals"]
            },
            "personalization_notes": [
                "Fallback recommendations due to AI processing issue",
                "Based on general healthy eating principles and current macro status",
                "Intelligently adjusted to remaining nutritional needs"
            ] + (["Portions reduced due to calorie goal achievement"] if calories_over else [])
        })
        
        return recommendations

    async def _create_ai_fallback_recommendations(
        self,
        remaining_meals: List[str],
        remaining_targets: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create AI-generated fallback recommendations with a simpler prompt."""
        
        try:
            calories_per_meal = remaining_targets.get("calories", 400) // max(len(remaining_meals), 1)
            protein_per_meal = remaining_targets.get("protein", 25) // max(len(remaining_meals), 1)
            
            simple_prompt = f"""Create {len(remaining_meals)} specific diabetes-friendly meals.

MEALS NEEDED: {remaining_meals}
NUTRITION PER MEAL: ~{calories_per_meal} calories, ~{protein_per_meal}g protein

Generate simple JSON format:
{{"""
            
            for i, meal_type in enumerate(remaining_meals):
                simple_prompt += f"""
  "{meal_type}": {{
    "meal_name": "specific {meal_type} dish name",
    "estimated_calories": {calories_per_meal},
    "estimated_protein": {protein_per_meal}
  }}{"," if i < len(remaining_meals) - 1 else ""}"""
            
            simple_prompt += "\n}\n\nMake each meal name specific and different (e.g., 'Grilled chicken with quinoa and broccoli')."
            
            print(f"[EnhancedSmartMealPlanner] Trying AI fallback generation...")
            
            ai_response = await robust_openai_call(
                [{"role": "user", "content": simple_prompt}],
                temperature=0.8,  # Higher temperature for creativity
                max_tokens=800
            )
            
            if ai_response and ai_response.get("success") and ai_response.get("content"):
                content = ai_response["content"].strip()
                content = content.replace("```json", "").replace("```", "").strip()
                
                if "{" in content:
                    content = content[content.find("{"):]
                if "}" in content:
                    content = content[:content.rfind("}") + 1]
                
                fallback_meals = json.loads(content)
                print(f"[EnhancedSmartMealPlanner] AI fallback successful!")
                
                # Add missing fields to make it complete
                for meal_type in fallback_meals:
                    if isinstance(fallback_meals[meal_type], dict):
                        meal = fallback_meals[meal_type]
                        meal.setdefault("description", f"Nutritious {meal_type} option")
                        meal.setdefault("estimated_carbs", 30)
                        meal.setdefault("estimated_fat", 15)
                        meal.setdefault("prep_time", "15-20 minutes")
                        meal.setdefault("health_benefits", ["diabetes_friendly", "balanced_nutrition"])
                        meal.setdefault("ingredients", ["main protein", "healthy carb", "vegetables"])
                        meal.setdefault("preparation_tips", "Follow standard cooking methods")
                
                return fallback_meals
                
        except Exception as e:
            print(f"[EnhancedSmartMealPlanner] AI fallback failed: {e}")
        
        # Only use hardcoded fallback as absolute last resort
        print(f"[EnhancedSmartMealPlanner] Using hardcoded emergency fallback")
        return self._create_hardcoded_fallback_recommendations(remaining_meals, remaining_targets)

    def _create_hardcoded_fallback_recommendations(
        self,
        remaining_meals: List[str],
        remaining_targets: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Emergency hardcoded fallback - only used when AI completely fails."""
        
        # SMART HARDCODED FALLBACK: Handle calorie overages 
        remaining_calories = remaining_targets.get("calories", 400)
        calories_over = remaining_calories < 0
        
        if calories_over:
            calories_per_meal = 150  # Very conservative when over goal
            protein_per_meal = max(15, remaining_targets.get("protein", 25) // max(len(remaining_meals), 1)) if remaining_targets.get("protein", 25) > 0 else 15
        else:
            calories_per_meal = remaining_calories // max(len(remaining_meals), 1)
            protein_per_meal = remaining_targets.get("protein", 25) // max(len(remaining_meals), 1)
        
        fallback_meals = {
            "breakfast": {
                "meal_name": "Scrambled eggs with avocado toast and spinach",
                "description": "High-protein breakfast with healthy fats and fiber",
                "estimated_calories": min(400, calories_per_meal),
                "estimated_protein": max(20, protein_per_meal),
                "estimated_carbs": 25,
                "estimated_fat": 15,
                "prep_time": "10 minutes",
                "health_benefits": ["blood_sugar_control", "sustained_energy", "high_protein"],
                "ingredients": ["2 eggs", "1 slice whole grain bread", "½ avocado", "handful spinach", "olive oil"],
                "preparation_tips": "Scramble eggs with spinach, toast bread, mash avocado on top"
            },
            "lunch": {
                "meal_name": "Grilled chicken salad with quinoa and chickpeas",
                "description": "Protein-rich salad with complete amino acids and fiber",
                "estimated_calories": min(500, calories_per_meal),
                "estimated_protein": max(30, protein_per_meal),
                "estimated_carbs": 35,
                "estimated_fat": 18,
                "prep_time": "15 minutes",
                "health_benefits": ["complete_protein", "fiber_rich", "diabetes_friendly"],
                "ingredients": ["4oz grilled chicken breast", "½ cup cooked quinoa", "⅓ cup chickpeas", "mixed greens", "olive oil vinaigrette"],
                "preparation_tips": "Combine all ingredients, drizzle with olive oil and lemon"
            },
            "dinner": {
                "meal_name": "Baked salmon with roasted sweet potato and steamed broccoli",
                "description": "Omega-3 rich dinner with complex carbs and vegetables",
                "estimated_calories": min(550, calories_per_meal),
                "estimated_protein": max(35, protein_per_meal),
                "estimated_carbs": 40,
                "estimated_fat": 20,
                "prep_time": "25 minutes",
                "health_benefits": ["omega_3_fatty_acids", "anti_inflammatory", "heart_healthy"],
                "ingredients": ["5oz salmon fillet", "1 medium roasted sweet potato", "1 cup steamed broccoli", "olive oil", "herbs"],
                "preparation_tips": "Bake salmon at 400°F for 15 mins, roast sweet potato, steam broccoli"
            },
            "snack": {
                "meal_name": "No additional snacks needed" if calories_over else "Greek yogurt with mixed berries and chopped almonds",
                "description": "You've exceeded your calorie goal - focus on hydration" if calories_over else "High-protein snack with antioxidants and healthy fats",
                "estimated_calories": 0 if calories_over else min(200, calories_per_meal),  
                "estimated_protein": 0 if calories_over else max(15, protein_per_meal),
                "estimated_carbs": 0 if calories_over else 18,
                "estimated_fat": 0 if calories_over else 8,
                "prep_time": "0 minutes" if calories_over else "2 minutes",
                "health_benefits": ["hydration", "goal_achievement"] if calories_over else ["probiotics", "antioxidants", "protein_rich"],
                "ingredients": ["Water", "herbal tea"] if calories_over else ["¾ cup Greek yogurt", "½ cup mixed berries", "1 tbsp chopped almonds", "dash of cinnamon"],
                "preparation_tips": "Stay hydrated and rest" if calories_over else "Mix yogurt with berries, top with almonds and cinnamon",
                "personalization_notes": ["Hardcoded fallback - calorie goal exceeded"] if calories_over else []
            }
        }
        
        # Filter to only remaining meals
        recommendations = {}
        for meal_type in remaining_meals:
            if meal_type in fallback_meals:
                recommendations[meal_type] = fallback_meals[meal_type]
        
        # Add general recommendations
        recommendations.update({
            "daily_hydration_plan": {
                "total_water_target": "8-10 glasses",
                "timing_suggestions": ["with_meals", "between_meals"]
            },
            "personalization_notes": [
                "Emergency fallback recommendations due to AI processing issue",
                "Based on general healthy eating principles and current macro status",
                "Intelligently adjusted to remaining nutritional needs"
            ] + (["Emergency mode - portions reduced due to calorie overage"] if calories_over else [])
        })
        
        return recommendations

    def _get_dietary_examples(self, dietary_category: str) -> str:
        """Get appropriate meal examples based on dietary restrictions."""
        examples = {
            "vegetarian": [
                "- 'Mediterranean lentil patties with herb quinoa and roasted eggplant'",
                "- 'Asian-inspired tofu stir-fry with brown rice and snap peas'", 
                "- 'Mexican-style black bean bowl with cilantro-lime cauliflower rice'",
                "- 'Indian-spiced chickpea curry with bulgur and sautéed spinach'"
            ],
            "vegan": [
                "- 'Mediterranean hemp tofu with lemon quinoa and roasted zucchini'",
                "- 'Asian-inspired tempeh stir-fry with brown rice and bok choy'",
                "- 'Mexican-style walnut meat tacos with cilantro-lime cauliflower rice'", 
                "- 'Thai-spiced seitan with coconut bulgur and steamed vegetables'"
            ],
            "pescatarian": [
                "- 'Mediterranean baked cod with lemon quinoa and roasted zucchini'",
                "- 'Asian-inspired tofu and shrimp stir-fry with brown rice'",
                "- 'Mexican-style fish bowl with cilantro-lime cauliflower rice'",
                "- 'Thai-spiced salmon with coconut bulgur and steamed bok choy'"
            ],
            "omnivore": [
                "- 'Mediterranean baked cod with lemon quinoa and roasted zucchini'",
                "- 'Asian-inspired chicken stir-fry with brown rice and snap peas'",
                "- 'Mexican-style turkey bowl with cilantro-lime cauliflower rice'",
                "- 'Thai-spiced salmon with coconut bulgur and steamed bok choy'"
            ]
        }
        
        return "\n".join(examples.get(dietary_category, examples["omnivore"]))

    async def _apply_real_time_calibration(
        self, 
        existing_plan: Dict[str, Any], 
        today_consumption: List[Dict], 
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply real-time calibration to existing meal plan based on current consumption."""
        try:
            print(f"[EnhancedSmartMealPlanner] Applying real-time calibration with {len(today_consumption)} consumed items")
            
            # Get the smart meal plan from existing plan
            smart_meal_plan = existing_plan.get('smart_meal_plan', {})
            if not smart_meal_plan:
                print(f"[EnhancedSmartMealPlanner] No smart_meal_plan found in existing plan")
                return existing_plan
            
            # Check if user consumed exactly what was planned - if so, no changes needed
            consumed_matches_plan = self._check_consumption_matches_plan(smart_meal_plan, today_consumption)
            if consumed_matches_plan:
                print(f"[EnhancedSmartMealPlanner] ✅ User consumed exactly what was planned - no changes needed")
                return existing_plan
            
            print(f"[EnhancedSmartMealPlanner] ⚠️ User consumed different food from plan - recalibrating remaining meals")
            
            # Calculate new remaining targets based on actual consumption
            from services.consumption_analysis import consumption_analyzer
            
            consumption_analysis = await consumption_analyzer.analyze_consumption(
                user_email=user_profile.get('email', ''),
                user_profile=user_profile,
                consumption_records=today_consumption
            )
            
            # Get remaining meals that haven't been consumed yet
            remaining_meals = self._get_remaining_meals(smart_meal_plan, today_consumption)
            print(f"[EnhancedSmartMealPlanner] Remaining meals to recalibrate: {remaining_meals}")
            
            if not remaining_meals:
                print(f"[EnhancedSmartMealPlanner] No remaining meals to calibrate")
                return existing_plan
            
            # Generate new recommendations for remaining meals only
            new_meal_recommendations = await self._generate_comprehensive_meal_recommendations(
                health_analysis=existing_plan.get('health_analysis', {}),
                history_analysis=existing_plan.get('history_analysis', {}),
                consumption_analysis=consumption_analysis,
                user_profile=user_profile,
                user_timezone=user_profile.get('timezone', 'UTC')
            )
            
            # Update only the remaining meals in the plan
            calibrated_plan = existing_plan.copy()
            smart_meal_plan_updated = smart_meal_plan.copy()
            
            for meal_type in remaining_meals:
                if meal_type in new_meal_recommendations:
                    smart_meal_plan_updated[meal_type] = new_meal_recommendations[meal_type]
                    print(f"[EnhancedSmartMealPlanner] ✅ Updated {meal_type}: {new_meal_recommendations[meal_type].get('meal_name', 'Unknown')}")
            
            calibrated_plan['smart_meal_plan'] = smart_meal_plan_updated
            calibrated_plan['meal_recommendations'] = smart_meal_plan_updated
            calibrated_plan['calibration_applied'] = True
            calibrated_plan['calibration_timestamp'] = datetime.utcnow().isoformat()
            
            return calibrated_plan
            
        except Exception as e:
            print(f"[EnhancedSmartMealPlanner] Error in real-time calibration: {e}")
            return existing_plan

    def _check_consumption_matches_plan(self, smart_meal_plan: Dict, today_consumption: List[Dict]) -> bool:
        """Check if user consumed exactly what was planned."""
        try:
            # Group consumption by meal type
            consumed_by_meal = {}
            for item in today_consumption:
                meal_type = item.get('meal_type', '').lower()
                if meal_type not in consumed_by_meal:
                    consumed_by_meal[meal_type] = []
                consumed_by_meal[meal_type].append(item.get('food_name', '').lower())
            
            # Check each planned meal
            matches = 0
            total_planned = 0
            
            for meal_type, meal_data in smart_meal_plan.items():
                if isinstance(meal_data, dict) and 'meal_name' in meal_data:
                    total_planned += 1
                    planned_meal = meal_data['meal_name'].lower()
                    consumed_foods = consumed_by_meal.get(meal_type, [])
                    
                    # Check if any consumed food closely matches the planned meal
                    for consumed_food in consumed_foods:
                        if self._meals_match(planned_meal, consumed_food):
                            matches += 1
                            break
            
            # Consider it a match if at least 80% of planned meals were consumed as planned
            match_rate = matches / total_planned if total_planned > 0 else 0
            print(f"[EnhancedSmartMealPlanner] Meal match rate: {matches}/{total_planned} = {match_rate:.1%}")
            
            return match_rate >= 0.8
            
        except Exception as e:
            print(f"[EnhancedSmartMealPlanner] Error checking meal matches: {e}")
            return False

    def _meals_match(self, planned_meal: str, consumed_food: str) -> bool:
        """Check if consumed food matches planned meal."""
        # Simple keyword matching - could be enhanced with ML
        planned_words = set(planned_meal.split())
        consumed_words = set(consumed_food.split())
        
        # Find common significant words (excluding common words)
        common_words = ['with', 'and', 'in', 'on', 'the', 'a', 'an']
        planned_significant = {w for w in planned_words if w not in common_words and len(w) > 3}
        consumed_significant = {w for w in consumed_words if w not in common_words and len(w) > 3}
        
        # Check for overlap
        overlap = len(planned_significant.intersection(consumed_significant))
        match_threshold = max(1, len(planned_significant) * 0.3)  # At least 30% overlap
        
        return overlap >= match_threshold

    def _get_remaining_meals(self, smart_meal_plan: Dict, today_consumption: List[Dict]) -> List[str]:
        """Get list of meals that haven't been consumed yet today."""
        # Group consumption by meal type
        consumed_meal_types = set()
        for item in today_consumption:
            meal_type = item.get('meal_type', '').lower()
            if meal_type:
                consumed_meal_types.add(meal_type)
        
        # Find planned meals that haven't been consumed
        remaining_meals = []
        for meal_type, meal_data in smart_meal_plan.items():
            if isinstance(meal_data, dict) and 'meal_name' in meal_data:
                if meal_type.lower() not in consumed_meal_types:
                    remaining_meals.append(meal_type)
        
        return remaining_meals

    def _create_fallback_meal_plan(
        self,
        user_email: str,
        user_profile: Dict[str, Any],
        target_date: str
    ) -> Dict[str, Any]:
        """Create fallback meal plan when comprehensive analysis fails."""
        
        calorie_target = 2000
        try:
            if user_profile.get("calorieTarget"):
                calorie_target = int(user_profile["calorieTarget"])
        except (ValueError, TypeError):
            pass
        
        return {
            "user_email": user_email,
            "target_date": target_date,
            "generated_at": datetime.utcnow().isoformat(),
            "status": "fallback_mode",
            "nutritional_goals": {
                "calories": calorie_target,
                "protein": 100,
                "carbs": 250,
                "fat": 66
            },
            "smart_meal_plan": self._create_fallback_recommendations(
                ["breakfast", "lunch", "dinner", "snack"],
                {"calories": calorie_target}
            ),
            "nutrition_insights": {
                "progress_assessment": ["fallback_recommendations_provided"],
                "optimization_tips": ["track_consumption", "update_profile", "try_again_later"]
            },
            "recommendation_confidence": 0.3,
            "error_message": "Comprehensive analysis failed, using basic recommendations"
        }

    def _validate_vegetarian_meals(self, recommendations: Dict[str, Any], remaining_meals: List[str], dietary_info: List[str] = None) -> Dict[str, Any]:
        """
        Validate that all generated meals are vegetarian-compliant.
        Returns: {"is_valid": bool, "violations": List[str]}
        """
        if dietary_info is None:
            dietary_info = []
            
        # List of forbidden animal products for vegetarians
        forbidden_items = [
            # Meat
            "chicken", "beef", "pork", "lamb", "turkey", "duck", "venison", "goose", 
            "ham", "bacon", "sausage", "meatball", "burger", "steak",
            # Seafood  
            "fish", "salmon", "tuna", "cod", "shrimp", "crab", "lobster", "mussels", 
            "oysters", "scallops", "clams", "sardines", "mackerel", "halibut", "sea bass",
            # Poultry
            "wing", "drumstick", "breast", "thigh"
        ]
        
        # Add eggs to forbidden list if user is vegetarian with no eggs
        if any("no egg" in str(d).lower() for d in dietary_info):
            forbidden_items.extend(["egg", "omelet", "omelette", "quiche", "scrambled"])
        
        # Items to exclude from violation checking (to avoid false positives)
        allowed_items = [
            "roasted", "roasting", "breast milk", "chicken of the sea", "sea salt", "eggplant"
        ]
        
        violations = []
        
        for meal_type in remaining_meals:
            if meal_type in recommendations:
                meal_data = recommendations[meal_type]
                meal_name = meal_data.get('meal_name', '').lower()
                description = meal_data.get('description', '').lower()
                ingredients = meal_data.get('ingredients', [])
                ingredients_text = ' '.join([str(ing).lower() for ing in ingredients])
                
                # Check meal name, description, and ingredients for forbidden items
                full_text = f"{meal_name} {description} {ingredients_text}"
                
                for forbidden_item in forbidden_items:
                    if forbidden_item in full_text:
                        # Check if this is a false positive (e.g., "roasted vegetables")
                        is_false_positive = False
                        for allowed_item in allowed_items:
                            if allowed_item in full_text and forbidden_item in allowed_item:
                                is_false_positive = True
                                break
                        
                        if not is_false_positive:
                            violations.append(f"{meal_type}: contains '{forbidden_item}' in '{meal_name}'")
        
        return {
            "is_valid": len(violations) == 0,
            "violations": violations
        }


# Global planner instance
enhanced_smart_meal_planner = EnhancedSmartMealPlanner()