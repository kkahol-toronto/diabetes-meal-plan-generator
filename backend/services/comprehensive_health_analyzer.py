"""
Comprehensive Health Profile Analyzer Service
Provides intelligent meal planning based on complete health profile analysis.
This service analyzes medical conditions, medications, lab values, consumption patterns,
and meal plan history to provide personalized meal recommendations.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import traceback
import json

from database import (
    get_user_by_email, get_user_consumption_history, get_user_meal_plans
)
from services.openai_service import robust_openai_call


class ComprehensiveHealthAnalyzer:
    """
    Comprehensive health profile analyzer for intelligent meal planning.
    Analyzes all aspects of user health data to provide personalized recommendations.
    """
    
    def __init__(self):
        self.medical_condition_mappings = {
            "diabetes": {
                "dietary_focus": ["low_glycemic_index", "balanced_carbohydrates", "high_fiber"],
                "avoid": ["high_sugar", "refined_carbs", "processed_foods"],
                "monitoring": ["blood_glucose", "carbohydrate_counting"]
            },
            "hypertension": {
                "dietary_focus": ["low_sodium", "dash_diet", "potassium_rich"],
                "avoid": ["high_sodium", "processed_meats", "canned_foods"],
                "monitoring": ["sodium_intake", "blood_pressure"]
            },
            "high_cholesterol": {
                "dietary_focus": ["low_saturated_fat", "omega_3", "plant_sterols"],
                "avoid": ["trans_fats", "saturated_fats", "fried_foods"],
                "monitoring": ["cholesterol_levels", "fat_intake"]
            },
            "kidney_disease": {
                "dietary_focus": ["controlled_protein", "phosphorus_limit", "potassium_control"],
                "avoid": ["high_phosphorus", "excessive_protein", "high_potassium"],
                "monitoring": ["protein_intake", "phosphorus", "potassium"]
            },
            "heart_disease": {
                "dietary_focus": ["heart_healthy", "omega_3", "antioxidants"],
                "avoid": ["trans_fats", "excessive_sodium", "processed_foods"],
                "monitoring": ["cardiovascular_health", "cholesterol"]
            }
        }
        
        self.medication_considerations = {
            "metformin": {"timing": "with_meals", "considerations": ["vitamin_b12_absorption"]},
            "insulin": {"timing": "meal_coordination", "considerations": ["carb_counting", "timing_critical"]},
            "warfarin": {"interactions": ["vitamin_k_foods"], "monitoring": ["consistent_intake"]},
            "statins": {"timing": "evening", "considerations": ["grapefruit_interaction"]},
            "ace_inhibitors": {"considerations": ["potassium_monitoring"]},
            "diuretics": {"considerations": ["electrolyte_balance", "hydration"]}
        }

    async def analyze_comprehensive_health_profile(
        self, 
        user_email: str,
        user_profile: Dict[str, Any],
        consumption_history: Optional[List[Dict]] = None,
        meal_plan_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive health profile analysis for meal planning.
        
        Args:
            user_email: User's email identifier
            user_profile: Complete user profile data
            consumption_history: Optional consumption data (will fetch if not provided)
            meal_plan_history: Optional meal plan data (will fetch if not provided)
            
        Returns:
            Comprehensive health analysis for meal planning
        """
        try:
            print(f"[ComprehensiveHealthAnalyzer] Starting analysis for {user_email}")
            
            # Fetch data if not provided
            if consumption_history is None:
                consumption_history = await get_user_consumption_history(user_email, limit=100)
            if meal_plan_history is None:
                meal_plan_history = await get_user_meal_plans(user_email)
            
            # Analyze each component
            medical_analysis = self._analyze_medical_conditions(user_profile)
            medication_analysis = self._analyze_medications(user_profile)
            lab_analysis = self._analyze_lab_values(user_profile)
            physical_analysis = self._analyze_physical_metrics(user_profile)
            consumption_patterns = self._analyze_consumption_patterns(consumption_history)
            meal_plan_patterns = self._analyze_meal_plan_history(meal_plan_history)
            lifestyle_analysis = self._analyze_lifestyle_factors(user_profile)
            
            # Calculate nutritional goals
            nutritional_goals = self._calculate_personalized_nutritional_goals(
                user_profile, medical_analysis, physical_analysis
            )
            
            # Generate comprehensive recommendations
            recommendations = await self._generate_ai_health_recommendations(
                medical_analysis,
                medication_analysis,
                lab_analysis,
                physical_analysis,
                consumption_patterns,
                meal_plan_patterns,
                lifestyle_analysis,
                nutritional_goals,
                user_profile
            )
            
            analysis_result = {
                "user_email": user_email,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "medical_analysis": medical_analysis,
                "medication_analysis": medication_analysis,
                "lab_analysis": lab_analysis,
                "physical_analysis": physical_analysis,
                "consumption_patterns": consumption_patterns,
                "meal_plan_patterns": meal_plan_patterns,
                "lifestyle_analysis": lifestyle_analysis,
                "nutritional_goals": nutritional_goals,
                "ai_recommendations": recommendations,
                "priority_considerations": self._extract_priority_considerations(
                    medical_analysis, medication_analysis, lab_analysis
                )
            }
            
            print(f"[ComprehensiveHealthAnalyzer] Analysis completed successfully")
            return analysis_result
            
        except Exception as e:
            print(f"[ComprehensiveHealthAnalyzer] Error in analysis: {str(e)}")
            print(f"[ComprehensiveHealthAnalyzer] Traceback: {traceback.format_exc()}")
            return self._create_fallback_analysis(user_email, user_profile)

    def _analyze_medical_conditions(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze medical conditions and their dietary implications."""
        conditions = user_profile.get("medicalConditions", []) or user_profile.get("medical_conditions", [])
        
        analysis = {
            "conditions": conditions,
            "dietary_restrictions": [],
            "nutritional_focus": [],
            "foods_to_avoid": [],
            "monitoring_requirements": [],
            "risk_level": "low"
        }
        
        if not conditions:
            return analysis
        
        for condition in conditions:
            condition_lower = condition.lower()
            for key_condition, mappings in self.medical_condition_mappings.items():
                if key_condition in condition_lower:
                    analysis["dietary_restrictions"].extend(mappings.get("dietary_focus", []))
                    analysis["foods_to_avoid"].extend(mappings.get("avoid", []))
                    analysis["monitoring_requirements"].extend(mappings.get("monitoring", []))
        
        # Determine risk level based on conditions
        high_risk_conditions = ["diabetes", "heart disease", "kidney disease"]
        if any(condition.lower() in " ".join(conditions).lower() for condition in high_risk_conditions):
            analysis["risk_level"] = "high"
        elif len(conditions) > 2:
            analysis["risk_level"] = "medium"
        
        return analysis

    def _analyze_medications(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze medications and their dietary interactions."""
        medications = user_profile.get("currentMedications", [])
        
        analysis = {
            "medications": medications,
            "food_interactions": [],
            "timing_considerations": [],
            "nutrient_interactions": [],
            "special_monitoring": []
        }
        
        if not medications:
            return analysis
        
        for medication in medications:
            med_lower = medication.lower()
            for key_med, considerations in self.medication_considerations.items():
                if key_med in med_lower:
                    if "interactions" in considerations:
                        analysis["food_interactions"].extend(considerations["interactions"])
                    if "timing" in considerations:
                        analysis["timing_considerations"].append(considerations["timing"])
                    if "considerations" in considerations:
                        analysis["special_monitoring"].extend(considerations["considerations"])
        
        return analysis

    def _analyze_lab_values(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze lab values and their dietary implications."""
        lab_values = user_profile.get("labValues", {})
        
        analysis = {
            "lab_values": lab_values,
            "concerns": [],
            "dietary_adjustments": [],
            "monitoring_focus": []
        }
        
        if not lab_values:
            return analysis
        
        # Analyze key lab values
        if lab_values.get("a1c"):
            try:
                a1c_value = float(lab_values["a1c"])
                if a1c_value > 7.0:
                    analysis["concerns"].append("elevated_a1c")
                    analysis["dietary_adjustments"].append("strict_carb_control")
                    analysis["monitoring_focus"].append("glucose_management")
            except (ValueError, TypeError):
                pass
        
        if lab_values.get("ldlCholesterol"):
            try:
                ldl_value = float(lab_values["ldlCholesterol"])
                if ldl_value > 100:
                    analysis["concerns"].append("elevated_ldl")
                    analysis["dietary_adjustments"].append("low_saturated_fat")
                    analysis["monitoring_focus"].append("cholesterol_management")
            except (ValueError, TypeError):
                pass
        
        if lab_values.get("egfr"):
            try:
                egfr_value = float(lab_values["egfr"])
                if egfr_value < 60:
                    analysis["concerns"].append("reduced_kidney_function")
                    analysis["dietary_adjustments"].append("protein_restriction")
                    analysis["monitoring_focus"].append("kidney_protection")
            except (ValueError, TypeError):
                pass
        
        return analysis

    def _analyze_physical_metrics(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze physical metrics for nutritional planning."""
        analysis = {
            "bmi_category": "normal",
            "weight_status": "maintain",
            "caloric_needs": 2000,
            "activity_level": "moderate",
            "physical_considerations": []
        }
        
        # BMI Analysis
        height = user_profile.get("height")
        weight = user_profile.get("weight")
        
        if height and weight:
            try:
                height_m = float(height) / 100  # Convert cm to meters
                weight_kg = float(weight)
                bmi = weight_kg / (height_m ** 2)
                
                if bmi < 18.5:
                    analysis["bmi_category"] = "underweight"
                    analysis["weight_status"] = "gain"
                elif bmi >= 25 and bmi < 30:
                    analysis["bmi_category"] = "overweight"
                    analysis["weight_status"] = "lose"
                elif bmi >= 30:
                    analysis["bmi_category"] = "obese"
                    analysis["weight_status"] = "lose"
                
                # Calculate caloric needs based on BMI and activity
                analysis["caloric_needs"] = self._calculate_caloric_needs(
                    weight_kg, height_m, user_profile.get("age", 35), 
                    user_profile.get("gender", "female"),
                    user_profile.get("exerciseFrequency", "moderate")
                )
                
            except (ValueError, TypeError):
                pass
        
        # Activity Level Analysis
        exercise_freq = user_profile.get("exerciseFrequency", "").lower()
        if "daily" in exercise_freq or "very active" in exercise_freq:
            analysis["activity_level"] = "high"
        elif "sedentary" in exercise_freq or "none" in exercise_freq:
            analysis["activity_level"] = "low"
        
        return analysis

    def _analyze_consumption_patterns(self, consumption_history: List[Dict]) -> Dict[str, Any]:
        """Analyze consumption patterns to identify trends and preferences."""
        if not consumption_history:
            return {
                "total_records": 0,
                "avg_daily_calories": 0,
                "meal_timing_patterns": {},
                "food_preferences": [],
                "adherence_patterns": {},
                "nutritional_trends": {}
            }
        
        # Calculate averages and patterns
        total_calories = sum(
            record.get("nutritional_info", {}).get("calories", 0) 
            for record in consumption_history
        )
        avg_calories = total_calories / len(consumption_history) if consumption_history else 0
        
        # Analyze meal timing
        meal_timing = {}
        for record in consumption_history:
            meal_type = record.get("meal_type", "unknown")
            if meal_type not in meal_timing:
                meal_timing[meal_type] = 0
            meal_timing[meal_type] += 1
        
        # Extract food preferences
        food_counts = {}
        for record in consumption_history:
            food_name = record.get("food_name", "").lower()
            if food_name:
                food_counts[food_name] = food_counts.get(food_name, 0) + 1
        
        preferred_foods = sorted(food_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_records": len(consumption_history),
            "avg_daily_calories": round(avg_calories, 2),
            "meal_timing_patterns": meal_timing,
            "food_preferences": [food[0] for food in preferred_foods],
            "adherence_patterns": self._calculate_adherence_patterns(consumption_history),
            "nutritional_trends": self._calculate_nutritional_trends(consumption_history)
        }

    def _analyze_meal_plan_history(self, meal_plan_history: List[Dict]) -> Dict[str, Any]:
        """Analyze meal plan history to understand successful patterns."""
        if not meal_plan_history:
            return {
                "total_plans": 0,
                "successful_patterns": [],
                "preferred_cuisines": [],
                "effective_strategies": []
            }
        
        successful_patterns = []
        cuisines = []
        
        for plan in meal_plan_history:
            # Extract successful elements from past plans
            if plan.get("user_adherence_rate", 0) > 0.7:  # 70% adherence considered successful
                plan_type = plan.get("plan_type", "standard")
                successful_patterns.append(plan_type)
            
            # Extract cuisine preferences
            plan_data = plan.get("meal_plan", {})
            if isinstance(plan_data, dict):
                for day_data in plan_data.values():
                    if isinstance(day_data, dict):
                        for meal_data in day_data.values():
                            if isinstance(meal_data, dict) and "cuisine" in meal_data:
                                cuisines.append(meal_data["cuisine"])
        
        return {
            "total_plans": len(meal_plan_history),
            "successful_patterns": list(set(successful_patterns)),
            "preferred_cuisines": list(set(cuisines)),
            "effective_strategies": self._identify_effective_strategies(meal_plan_history)
        }

    def _analyze_lifestyle_factors(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze lifestyle factors affecting meal planning."""
        return {
            "work_activity": user_profile.get("workActivityLevel", "moderate"),
            "meal_prep_capability": user_profile.get("mealPrepCapability", "moderate"),
            "available_appliances": user_profile.get("availableAppliances", []),
            "eating_schedule": user_profile.get("eatingSchedule", "regular"),
            "primary_goals": user_profile.get("primaryGoals", []),
            "readiness_to_change": user_profile.get("readinessToChange", "moderate"),
            "time_constraints": self._assess_time_constraints(user_profile),
            "cooking_skill_level": self._assess_cooking_skill(user_profile)
        }

    def _calculate_personalized_nutritional_goals(
        self, 
        user_profile: Dict[str, Any],
        medical_analysis: Dict[str, Any],
        physical_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate personalized nutritional goals based on comprehensive analysis."""
        
        # Base caloric needs from physical analysis
        base_calories = physical_analysis.get("caloric_needs", 2000)
        
        # Adjust for medical conditions
        calorie_adjustment = 1.0
        if medical_analysis.get("risk_level") == "high":
            calorie_adjustment = 0.9  # Slightly reduce for high-risk conditions
        elif physical_analysis.get("weight_status") == "lose":
            calorie_adjustment = 0.85  # Reduce for weight loss
        elif physical_analysis.get("weight_status") == "gain":
            calorie_adjustment = 1.1  # Increase for weight gain
        
        target_calories = int(base_calories * calorie_adjustment)
        
        # Override with user preference if provided
        user_calorie_goal = user_profile.get("calorieTarget")
        if user_calorie_goal:
            try:
                target_calories = int(user_calorie_goal)
            except (ValueError, TypeError):
                pass
        
        # Calculate macro goals
        protein_ratio = 0.2  # 20% of calories from protein (default)
        carb_ratio = 0.45    # 45% of calories from carbs (default)
        fat_ratio = 0.35     # 35% of calories from fat (default)
        
        # Adjust ratios for medical conditions
        if "diabetes" in " ".join(medical_analysis.get("conditions", [])).lower():
            carb_ratio = 0.35  # Lower carbs for diabetes
            protein_ratio = 0.25
            fat_ratio = 0.4
        
        if "kidney_disease" in " ".join(medical_analysis.get("conditions", [])).lower():
            protein_ratio = 0.15  # Lower protein for kidney disease
            carb_ratio = 0.5
            fat_ratio = 0.35
        
        protein_grams = int((target_calories * protein_ratio) / 4)  # 4 calories per gram
        carb_grams = int((target_calories * carb_ratio) / 4)       # 4 calories per gram
        fat_grams = int((target_calories * fat_ratio) / 9)         # 9 calories per gram
        
        # Override with user macro goals if provided
        user_macro_goals = user_profile.get("macroGoals", {})
        if user_macro_goals.get("protein"):
            protein_grams = user_macro_goals["protein"]
        if user_macro_goals.get("carbs"):
            carb_grams = user_macro_goals["carbs"]
        if user_macro_goals.get("fat"):
            fat_grams = user_macro_goals["fat"]
        
        return {
            "calories": target_calories,
            "protein": protein_grams,
            "carbs": carb_grams,
            "fat": fat_grams,
            "fiber": max(25, int(target_calories / 100)),  # Minimum 25g fiber
            "sodium": 2300 if "hypertension" not in " ".join(medical_analysis.get("conditions", [])).lower() else 1500,
            "adjustment_reasoning": {
                "calorie_adjustment": calorie_adjustment,
                "medical_considerations": medical_analysis.get("conditions", []),
                "weight_goal": physical_analysis.get("weight_status", "maintain")
            }
        }

    async def _generate_ai_health_recommendations(
        self,
        medical_analysis: Dict,
        medication_analysis: Dict,
        lab_analysis: Dict,
        physical_analysis: Dict,
        consumption_patterns: Dict,
        meal_plan_patterns: Dict,
        lifestyle_analysis: Dict,
        nutritional_goals: Dict,
        user_profile: Dict
    ) -> Dict[str, Any]:
        """Generate AI-powered health recommendations based on comprehensive analysis."""
        
        prompt = f"""
        As a comprehensive health and nutrition AI, analyze this patient's complete health profile and provide personalized meal planning recommendations.

        MEDICAL PROFILE:
        - Medical Conditions: {medical_analysis.get('conditions', [])}
        - Risk Level: {medical_analysis.get('risk_level', 'low')}
        - Current Medications: {medication_analysis.get('medications', [])}
        - Lab Value Concerns: {lab_analysis.get('concerns', [])}

        PHYSICAL PROFILE:
        - BMI Category: {physical_analysis.get('bmi_category', 'normal')}
        - Weight Goal: {physical_analysis.get('weight_status', 'maintain')}
        - Activity Level: {physical_analysis.get('activity_level', 'moderate')}

        CONSUMPTION PATTERNS:
        - Average Daily Calories: {consumption_patterns.get('avg_daily_calories', 0)}
        - Food Preferences: {consumption_patterns.get('food_preferences', [])[:5]}
        - Meal Timing: {consumption_patterns.get('meal_timing_patterns', {})}

        MEAL PLAN HISTORY:
        - Successful Patterns: {meal_plan_patterns.get('successful_patterns', [])}
        - Preferred Cuisines: {meal_plan_patterns.get('preferred_cuisines', [])[:3]}

        LIFESTYLE FACTORS:
        - Meal Prep Capability: {lifestyle_analysis.get('meal_prep_capability', 'moderate')}
        - Primary Goals: {lifestyle_analysis.get('primary_goals', [])}
        - Available Appliances: {lifestyle_analysis.get('available_appliances', [])}

        NUTRITIONAL GOALS:
        - Target Calories: {nutritional_goals.get('calories', 2000)}
        - Protein Goal: {nutritional_goals.get('protein', 100)}g
        - Carb Goal: {nutritional_goals.get('carbs', 250)}g
        - Fat Goal: {nutritional_goals.get('fat', 66)}g

        DIETARY PREFERENCES:
        - Dietary Restrictions: {user_profile.get('dietaryRestrictions', [])}
        - Allergies: {user_profile.get('allergies', [])}
        - Strong Dislikes: {user_profile.get('strongDislikes', [])}

        Provide comprehensive recommendations in JSON format:
        {{
            "meal_timing_strategy": "optimal meal timing for this patient",
            "key_nutritional_focuses": [],
            "foods_to_emphasize": ["food1", "food2", "food3"],
            "foods_to_limit": ["food1", "food2", "food3"],
            "portion_control_strategy": "strategy for portion management",
            "meal_prep_recommendations": ["tip1", "tip2", "tip3"],
            "medical_considerations": ["consideration1", "consideration2"],
            "hydration_guidance": "hydration recommendations",
            "supplement_considerations": ["consideration1", "consideration2"],
            "monitoring_priorities": ["priority1", "priority2"],
            "personalized_tips": []
        }}
        """
        
        try:
            ai_response = await robust_openai_call(
                [{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1200
            )
            
            if ai_response and ai_response.get("success") and ai_response.get("content"):
                content = ai_response["content"].strip()
                return json.loads(content)
        
        except Exception as e:
            print(f"[ComprehensiveHealthAnalyzer] AI recommendation generation failed: {e}")
        
        # Fallback recommendations
        return {
            "meal_timing_strategy": "Regular meals every 3-4 hours with balanced portions",
            "key_nutritional_focuses": [],  # DISABLED: User requested removal of Health Focus section
            "foods_to_emphasize": ["lean_proteins", "vegetables", "whole_grains"],
            "foods_to_limit": ["processed_foods", "added_sugars", "excessive_sodium"],
            "portion_control_strategy": "Use plate method: 1/2 vegetables, 1/4 protein, 1/4 starch",
            "meal_prep_recommendations": ["prepare_proteins_in_advance", "pre_cut_vegetables", "batch_cook_grains"],
            "medical_considerations": ["monitor_blood_glucose", "track_symptoms"],
            "hydration_guidance": "Aim for 8-10 glasses of water daily",
            "supplement_considerations": ["consult_healthcare_provider"],
            "monitoring_priorities": ["weight_trends", "energy_levels"],
            "personalized_tips": []  # DISABLED: User requested removal of Smart Tips section
        }

    def _calculate_caloric_needs(self, weight_kg: float, height_m: float, age: int, gender: str, activity: str) -> int:
        """Calculate caloric needs using Mifflin-St Jeor equation."""
        # Base metabolic rate
        if gender.lower() == "male":
            bmr = 10 * weight_kg + 6.25 * (height_m * 100) - 5 * age + 5
        else:
            bmr = 10 * weight_kg + 6.25 * (height_m * 100) - 5 * age - 161
        
        # Activity multiplier
        activity_multipliers = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very_active": 1.9
        }
        
        activity_key = "moderate"  # default
        for key in activity_multipliers:
            if key in activity.lower():
                activity_key = key
                break
        
        return int(bmr * activity_multipliers[activity_key])

    def _calculate_adherence_patterns(self, consumption_history: List[Dict]) -> Dict[str, Any]:
        """Calculate adherence patterns from consumption history."""
        # This is a simplified version - in practice, you'd compare against meal plans
        return {
            "consistency_score": 0.8,  # Placeholder
            "meal_skipping_frequency": 0.1,  # Placeholder
            "portion_accuracy": 0.75  # Placeholder
        }

    def _calculate_nutritional_trends(self, consumption_history: List[Dict]) -> Dict[str, Any]:
        """Calculate nutritional trends from consumption history."""
        total_protein = sum(
            record.get("nutritional_info", {}).get("protein", 0) 
            for record in consumption_history
        )
        total_carbs = sum(
            record.get("nutritional_info", {}).get("carbs", 0) 
            for record in consumption_history
        )
        total_fat = sum(
            record.get("nutritional_info", {}).get("fat", 0) 
            for record in consumption_history
        )
        
        record_count = len(consumption_history) or 1
        
        return {
            "avg_protein": round(total_protein / record_count, 2),
            "avg_carbs": round(total_carbs / record_count, 2),
            "avg_fat": round(total_fat / record_count, 2)
        }

    def _identify_effective_strategies(self, meal_plan_history: List[Dict]) -> List[str]:
        """Identify effective strategies from meal plan history."""
        # Placeholder - would analyze successful meal plans for common patterns
        return ["consistent_meal_timing", "balanced_macros", "variety_in_foods"]

    def _assess_time_constraints(self, user_profile: Dict[str, Any]) -> str:
        """Assess time constraints for meal preparation."""
        work_level = user_profile.get("workActivityLevel", "").lower()
        meal_prep = user_profile.get("mealPrepCapability", "").lower()
        
        if "very_busy" in work_level or "minimal" in meal_prep:
            return "high_constraints"
        elif "busy" in work_level or "limited" in meal_prep:
            return "moderate_constraints"
        else:
            return "low_constraints"

    def _assess_cooking_skill(self, user_profile: Dict[str, Any]) -> str:
        """Assess cooking skill level."""
        meal_prep = user_profile.get("mealPrepCapability", "").lower()
        appliances = user_profile.get("availableAppliances", [])
        
        if "expert" in meal_prep or len(appliances) > 5:
            return "advanced"
        elif "good" in meal_prep or len(appliances) > 2:
            return "intermediate"
        else:
            return "beginner"

    def _extract_priority_considerations(
        self, 
        medical_analysis: Dict, 
        medication_analysis: Dict, 
        lab_analysis: Dict
    ) -> List[str]:
        """Extract top priority considerations for meal planning."""
        priorities = []
        
        if medical_analysis.get("risk_level") == "high":
            priorities.append("high_risk_medical_conditions")
        
        if medication_analysis.get("food_interactions"):
            priorities.append("medication_food_interactions")
        
        if lab_analysis.get("concerns"):
            priorities.extend([f"lab_concern_{concern}" for concern in lab_analysis["concerns"]])
        
        return priorities[:5]  # Top 5 priorities

    def _create_fallback_analysis(self, user_email: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback analysis when main analysis fails."""
        return {
            "user_email": user_email,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "status": "fallback",
            "nutritional_goals": {
                "calories": int(user_profile.get("calorieTarget", 2000)) if user_profile.get("calorieTarget") else 2000,
                "protein": 100,
                "carbs": 250,
                "fat": 66
            },
            "ai_recommendations": {
                "meal_timing_strategy": "Regular balanced meals",
                "key_nutritional_focuses": [],  # DISABLED: User requested removal of Health Focus section
                "foods_to_emphasize": ["vegetables", "lean_proteins", "whole_grains"],
                "foods_to_limit": ["processed_foods", "added_sugars"],
                "personalized_tips": []  # DISABLED: User requested removal of Smart Tips section
            }
        }


# Global analyzer instance
health_analyzer = ComprehensiveHealthAnalyzer()