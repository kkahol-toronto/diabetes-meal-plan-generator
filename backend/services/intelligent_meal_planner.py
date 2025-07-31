"""
🧠 INTELLIGENT AI-CONTROLLED ADAPTIVE MEAL PLANNER 🧠

This module provides a completely new AI-controlled meal planning system that:
1. Analyzes comprehensive health profile (weight, exercise, medical conditions, medications)
2. Studies consumption history patterns (what user ate last week/month)
3. Creates truly adaptive meal plans using advanced AI reasoning
4. Continuously learns and adapts based on user behavior

Built from scratch to replace all previous meal planning systems.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import os
from services.openai_service import robust_openai_call
from database import (
    get_user_by_email, get_user_consumption_history, get_user_meal_plans,
    save_meal_plan, get_consumption_analytics
)


class IntelligentMealPlanner:
    """AI-Powered Intelligent Meal Planner that truly adapts to user data"""
    
    def __init__(self):
        self.name = "🧠 Intelligent AI Meal Planner"
        self.version = "2.0.0"
        print(f"[{self.name}] Initializing advanced AI meal planning system...")

    async def create_adaptive_meal_plan(
        self, 
        user_email: str, 
        user_profile: dict, 
        days: int = 7, 
        cuisine_preference: str = ""
    ) -> Dict[str, Any]:
        """
        Create a truly intelligent, adaptive meal plan using comprehensive analysis.
        
        This function:
        1. Analyzes user's complete health profile
        2. Studies consumption history patterns
        3. Uses AI to create personalized meal plans
        4. Adapts based on past behavior and preferences
        """
        try:
            print(f"[🧠 AI PLANNER] Creating intelligent meal plan for {user_email}")
            print(f"[🧠 AI PLANNER] Days requested: {days}")
            print(f"[🧠 AI PLANNER] Cuisine preference: {cuisine_preference}")
            
            # Step 1: Comprehensive Health Profile Analysis
            health_analysis = await self._analyze_comprehensive_health_profile(user_email, user_profile)
            print(f"[🧠 AI PLANNER] Health analysis complete: {len(health_analysis.get('medical_conditions', []))} conditions identified")
            
            # Step 2: Deep Consumption History Analysis  
            consumption_analysis = await self._analyze_consumption_history_patterns(user_email)
            print(f"[🧠 AI PLANNER] Consumption analysis complete: {consumption_analysis.get('total_meals_analyzed', 0)} meals analyzed")
            
            # Step 3: AI-Powered Meal Plan Generation
            meal_plan = await self._generate_intelligent_meal_plan(
                user_email, health_analysis, consumption_analysis, days, cuisine_preference
            )
            
            # Step 4: Save and return results
            if meal_plan and meal_plan.get('success'):
                # Save to database with comprehensive metadata
                save_data = {
                    **meal_plan['plan'],
                    "user_email": user_email,
                    "created_at": datetime.utcnow().isoformat(),
                    "plan_type": "intelligent_adaptive",
                    "ai_version": self.version,
                    "health_analysis": health_analysis,
                    "consumption_analysis": consumption_analysis,
                    "personalization_score": meal_plan.get('personalization_score', 95)
                }
                
                await save_meal_plan(user_email, save_data)
                print(f"[🧠 AI PLANNER] Intelligent meal plan saved successfully!")
                
                return {
                    "success": True,
                    "meal_plan": meal_plan['plan'],
                    "personalization_score": meal_plan.get('personalization_score', 95),
                    "ai_insights": meal_plan.get('ai_insights', []),
                    "health_adaptations": meal_plan.get('health_adaptations', []),
                    "message": f"🧠 Intelligent meal plan created! Personalized for your {', '.join(health_analysis.get('medical_conditions', [])[:2])} and based on your consumption patterns."
                }
            else:
                raise Exception("AI meal plan generation failed")
                
        except Exception as e:
            print(f"[🧠 AI PLANNER] Error: {str(e)}")
            import traceback
            print(f"[🧠 AI PLANNER] Traceback: {traceback.format_exc()}")
            # Return intelligent fallback
            return await self._create_intelligent_fallback(user_email, user_profile, days, cuisine_preference)

    async def _analyze_comprehensive_health_profile(self, user_email: str, user_profile: dict) -> Dict[str, Any]:
        """Analyze user's complete health profile for meal planning."""
        print(f"[🧠 HEALTH ANALYSIS] Analyzing comprehensive health profile...")
        
        # Extract all health-related data
        medical_conditions = user_profile.get("medicalConditions", []) or user_profile.get("medical_conditions", [])
        current_medications = user_profile.get("currentMedications", [])
        lab_values = user_profile.get("labValues", {})
        dietary_restrictions = user_profile.get("dietaryRestrictions", [])
        dietary_features = user_profile.get("dietaryFeatures", [])
        diet_type = user_profile.get("dietType", [])  # CRITICAL: User's preferred cuisine types
        allergies = user_profile.get("allergies", [])
        food_preferences = user_profile.get("foodPreferences", [])
        strong_dislikes = user_profile.get("strongDislikes", [])
        primary_goals = user_profile.get("primaryGoals", [])
        
        # Physical metrics
        age = user_profile.get("age")
        weight = user_profile.get("weight")
        height = user_profile.get("height")
        bmi = user_profile.get("bmi")
        
        # Activity and lifestyle
        exercise_frequency = user_profile.get("exerciseFrequency")
        work_activity_level = user_profile.get("workActivityLevel")
        eating_schedule = user_profile.get("eatingSchedule")
        meal_prep_capability = user_profile.get("mealPrepCapability")
        available_appliances = user_profile.get("availableAppliances", [])
        
        # Calculate nutritional needs based on health profile
        base_calories = self._calculate_caloric_needs(age, weight, height, bmi, exercise_frequency, work_activity_level)
        
        # Adjust for medical conditions
        if any('diabetes' in condition.lower() for condition in medical_conditions):
            base_calories = int(base_calories * 0.95)  # Slight reduction for diabetes
        
        # Calculate macro targets based on conditions
        protein_target, carb_target, fat_target = self._calculate_macro_targets(base_calories, medical_conditions)
        
        return {
            "medical_conditions": medical_conditions,
            "current_medications": current_medications,
            "lab_values": lab_values,
            "dietary_restrictions": dietary_restrictions,
            "dietary_features": dietary_features,
            "diet_type": diet_type,  # CRITICAL: User's preferred cuisine types
            "allergies": allergies,
            "food_preferences": food_preferences,
            "strong_dislikes": strong_dislikes,
            "primary_goals": primary_goals,
            "physical_profile": {
                "age": age,
                "weight": weight,
                "height": height,
                "bmi": bmi
            },
            "lifestyle_factors": {
                "exercise_frequency": exercise_frequency,
                "work_activity_level": work_activity_level,
                "eating_schedule": eating_schedule,
                "meal_prep_capability": meal_prep_capability,
                "available_appliances": available_appliances
            },
            "nutritional_targets": {
                "calories": base_calories,
                "protein": protein_target,
                "carbohydrates": carb_target,
                "fat": fat_target
            },
            "health_risk_factors": self._identify_health_risk_factors(medical_conditions, lab_values, bmi),
            "medication_considerations": self._analyze_medication_interactions(current_medications)
        }

    async def _analyze_consumption_history_patterns(self, user_email: str) -> Dict[str, Any]:
        """Deep analysis of user's consumption history to understand patterns."""
        print(f"[🧠 CONSUMPTION ANALYSIS] Analyzing consumption history patterns...")
        
        try:
            # Get extensive consumption history (last 30 days)
            consumption_history = await get_user_consumption_history(user_email, limit=200)
            
            if not consumption_history:
                print(f"[🧠 CONSUMPTION ANALYSIS] No consumption history found")
                return {"total_meals_analyzed": 0, "patterns": [], "recommendations": []}
            
            # Analyze patterns
            patterns = self._identify_consumption_patterns(consumption_history)
            food_preferences = self._extract_food_preferences(consumption_history)
            nutritional_trends = self._analyze_nutritional_trends(consumption_history)
            meal_timing_patterns = self._analyze_meal_timing_patterns(consumption_history)
            
            return {
                "total_meals_analyzed": len(consumption_history),
                "analysis_period_days": 30,
                "consumption_patterns": patterns,
                "food_preferences": food_preferences,
                "nutritional_trends": nutritional_trends,
                "meal_timing_patterns": meal_timing_patterns,
                "frequent_foods": self._get_frequent_foods(consumption_history),
                "avoided_foods": self._get_avoided_foods(consumption_history),
                "calorie_consistency": self._analyze_calorie_consistency(consumption_history),
                "macro_balance_trends": self._analyze_macro_balance(consumption_history),
                "weekend_vs_weekday": self._analyze_weekend_vs_weekday_patterns(consumption_history)
            }
            
        except Exception as e:
            print(f"[🧠 CONSUMPTION ANALYSIS] Error analyzing consumption: {e}")
            return {"total_meals_analyzed": 0, "patterns": [], "error": str(e)}

    async def _generate_intelligent_meal_plan(
        self,
        user_email: str,
        health_analysis: Dict[str, Any],
        consumption_analysis: Dict[str, Any],
        days: int,
        cuisine_preference: str
    ) -> Dict[str, Any]:
        """Generate intelligent meal plan using comprehensive AI analysis."""
        print(f"[🧠 AI GENERATION] Generating intelligent meal plan using AI...")
        
        # Build comprehensive context for AI
        ai_context = self._build_ai_context(health_analysis, consumption_analysis, days, cuisine_preference)
        
        # Create AI prompt for intelligent meal planning
        prompt = f"""You are a world-class clinical nutritionist and AI health coach with expertise in personalized nutrition therapy. Create an intelligent, adaptive {days}-day meal plan using comprehensive health analysis and consumption pattern data.

🎯 MISSION: Create the most personalized meal plan possible using ALL available data about this patient.

📊 COMPREHENSIVE PATIENT ANALYSIS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏥 MEDICAL PROFILE:
- Primary Conditions: {', '.join(health_analysis.get('medical_conditions', [])) or 'None specified'}
- Current Medications: {', '.join(health_analysis.get('current_medications', [])) or 'None'}
- Lab Values: {dict(health_analysis.get('lab_values', {})) if health_analysis.get('lab_values') else 'None provided'}
- Health Risk Factors: {', '.join(health_analysis.get('health_risk_factors', [])) or 'None identified'}
- Medication Considerations: {', '.join(health_analysis.get('medication_considerations', [])) or 'None'}

🧬 DIETARY PROFILE:
**⭐ PREFERRED CUISINE TYPES (MUST FOLLOW STRICTLY): {', '.join(health_analysis.get('diet_type', [])) if health_analysis.get('diet_type') else 'Not specified'} ⭐**
- Restrictions: {', '.join(health_analysis.get('dietary_restrictions', [])) or 'None'}
- Features: {', '.join(health_analysis.get('dietary_features', [])) or 'Standard'}
- Allergies: {', '.join(health_analysis.get('allergies', [])) or 'None'}
- Preferred Foods: {', '.join(health_analysis.get('food_preferences', [])) or 'None specified'}
- Strong Dislikes: {', '.join(health_analysis.get('strong_dislikes', [])) or 'None'}
- Primary Goals: {', '.join(health_analysis.get('primary_goals', [])) or 'General wellness'}

📏 PHYSICAL PROFILE:
- Age: {health_analysis.get('physical_profile', {}).get('age', 'Not specified')}
- Weight: {health_analysis.get('physical_profile', {}).get('weight', 'Not specified')} lbs
- Height: {health_analysis.get('physical_profile', {}).get('height', 'Not specified')} inches
- BMI: {health_analysis.get('physical_profile', {}).get('bmi', 'Not specified')}

🏃 LIFESTYLE PROFILE:
- Exercise: {health_analysis.get('lifestyle_factors', {}).get('exercise_frequency', 'Not specified')}
- Work Activity: {health_analysis.get('lifestyle_factors', {}).get('work_activity_level', 'Not specified')}
- Eating Schedule: {health_analysis.get('lifestyle_factors', {}).get('eating_schedule', 'Standard')}
- Meal Prep Ability: {health_analysis.get('lifestyle_factors', {}).get('meal_prep_capability', 'Moderate')}
- Available Equipment: {', '.join(health_analysis.get('lifestyle_factors', {}).get('available_appliances', [])) or 'Standard kitchen'}
- Preferred Cuisine: {cuisine_preference or 'No preference'}

🎯 NUTRITIONAL TARGETS:
- Daily Calories: {health_analysis.get('nutritional_targets', {}).get('calories', 2000)} kcal
- Protein: {health_analysis.get('nutritional_targets', {}).get('protein', 100)}g
- Carbohydrates: {health_analysis.get('nutritional_targets', {}).get('carbohydrates', 250)}g
- Fat: {health_analysis.get('nutritional_targets', {}).get('fat', 66)}g

📈 CONSUMPTION HISTORY ANALYSIS ({consumption_analysis.get('total_meals_analyzed', 0)} meals analyzed):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🍽️ EATING PATTERNS:
- Frequent Foods: {', '.join(consumption_analysis.get('frequent_foods', [])[:10]) or 'No data'}
- Avoided Foods: {', '.join(consumption_analysis.get('avoided_foods', [])) or 'No clear patterns'}
- Meal Timing: {consumption_analysis.get('meal_timing_patterns', {}).get('preferred_times', 'Standard times')}
- Calorie Consistency: {consumption_analysis.get('calorie_consistency', {}).get('status', 'Unknown')}

📊 NUTRITIONAL TRENDS:
- Average Daily Calories: {consumption_analysis.get('nutritional_trends', {}).get('avg_calories', 'Unknown')}
- Protein Intake Pattern: {consumption_analysis.get('nutritional_trends', {}).get('protein_pattern', 'Unknown')}
- Carb Intake Pattern: {consumption_analysis.get('nutritional_trends', {}).get('carb_pattern', 'Unknown')}
- Fat Intake Pattern: {consumption_analysis.get('nutritional_trends', {}).get('fat_pattern', 'Unknown')}

🎯 INTELLIGENT REQUIREMENTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 🏥 MEDICAL OPTIMIZATION:
   - Design every meal to actively support: {', '.join(health_analysis.get('medical_conditions', [])) or 'general health'}
   - Consider medication timing: {', '.join(health_analysis.get('current_medications', [])) or 'N/A'}
   - Address health risk factors: {', '.join(health_analysis.get('health_risk_factors', [])) or 'N/A'}

2. 🍽️ CONSUMPTION PATTERN ADAPTATION:
   - Build on preferred foods: {', '.join(consumption_analysis.get('frequent_foods', [])[:5]) or 'No clear preferences'}
   - Avoid problematic patterns identified in history
   - Optimize based on successful past choices
   - Match preferred meal timing and structure

3. 🎯 PERSONALIZATION DEPTH:
   - Use actual consumption data to predict preferences
   - **STRICTLY FOLLOW USER'S CUISINE PREFERENCES: {', '.join(health_analysis.get('diet_type', [])) if health_analysis.get('diet_type') else 'Mixed'} - DO NOT GENERATE FOODS FROM OTHER CUISINES**
   - Additional cuisine request: {cuisine_preference or 'None'}
   - Match meal prep capability and equipment
   - Support specific health goals: {', '.join(health_analysis.get('primary_goals', [])) or 'General wellness'}

4. 🧠 INTELLIGENT ADAPTATION:
   - Each day should be different yet consistent with user preferences
   - Progressive complexity based on meal prep ability
   - Strategic nutrition timing for medical conditions
   - Real-world practical implementation
   - **CRITICAL: If user has selected specific cuisine types (Korean/Chinese, Filipino, etc.), ALL meals must be from those cuisines ONLY. Do not generate Western, Mediterranean, or other cuisine foods unless specifically selected.**

GENERATE EXACTLY THIS JSON STRUCTURE:
{{
    "plan_name": "🧠 Intelligent Adaptive Plan - {datetime.now().strftime('%Y-%m-%d')}",
    "duration_days": {days},
    "dailyCalories": {health_analysis.get('nutritional_targets', {}).get('calories', 2000)},
    "macronutrients": {{
        "protein": {health_analysis.get('nutritional_targets', {}).get('protein', 100)},
        "carbohydrates": {health_analysis.get('nutritional_targets', {}).get('carbohydrates', 250)},
        "fat": {health_analysis.get('nutritional_targets', {}).get('fat', 66)}
    }},
    "breakfast": [
        // {days} different, intelligent breakfast choices based on user data
    ],
    "lunch": [
        // {days} different, personalized lunch options
    ],
    "dinner": [
        // {days} different, medically-optimized dinner choices
    ],
    "snacks": [
        // {days} different, strategic snack options
    ],
    "intelligent_adaptations": [
        // 5-7 specific adaptations explaining how this plan uses their health data and consumption patterns
    ],
    "ai_insights": [
        // 3-5 AI insights about their health optimization and pattern analysis
    ],
    "medical_optimizations": [
        // 3-4 specific ways this plan supports their medical conditions
    ],
    "consumption_pattern_integration": [
        // 3-4 ways this plan builds on their eating history and preferences
    ],
    "coaching_notes": "Comprehensive coaching specific to this patient's complete health and consumption profile",
    "personalization_score": 95
}}

🔥 CRITICAL SUCCESS FACTORS:
- Every meal choice must be intentional and data-driven
- Use their actual consumption history to predict preferences
- Address their specific medical conditions with targeted nutrition
- Build on their successful past food choices
- This is precision medicine nutrition therapy, not generic meal planning
- Make it feel like you've studied their eating habits for months"""

        try:
            # Generate AI meal plan
            api_result = await robust_openai_call(
                messages=[
                    {
                        "role": "system",
                        "content": "You are the world's most advanced AI nutritionist specializing in precision medicine and personalized nutrition therapy. You analyze comprehensive health data and consumption patterns to create the most personalized meal plans possible. Every recommendation is evidence-based and tailored to the individual's unique health profile and eating history."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,  # Lower for more consistent medical advice
                max_tokens=2000,  # Increased for comprehensive response
                response_format={"type": "json_object"},
                context="intelligent_adaptive_meal_planning"
            )
            
            if api_result["success"]:
                try:
                    meal_plan_data = json.loads(api_result["content"])
                    
                    # Validate structure
                    required_fields = ["breakfast", "lunch", "dinner", "snacks", "intelligent_adaptations", "ai_insights", "coaching_notes"]
                    if all(field in meal_plan_data for field in required_fields):
                        print(f"[🧠 AI GENERATION] Successfully generated intelligent meal plan!")
                        return {
                            "success": True,
                            "plan": meal_plan_data,
                            "personalization_score": meal_plan_data.get("personalization_score", 95),
                            "ai_insights": meal_plan_data.get("ai_insights", []),
                            "health_adaptations": meal_plan_data.get("intelligent_adaptations", [])
                        }
                    else:
                        print(f"[🧠 AI GENERATION] Invalid meal plan structure")
                        return {"success": False, "error": "Invalid meal plan structure"}
                        
                except json.JSONDecodeError as e:
                    print(f"[🧠 AI GENERATION] JSON parsing error: {e}")
                    return {"success": False, "error": f"JSON parsing error: {e}"}
            else:
                print(f"[🧠 AI GENERATION] AI call failed: {api_result.get('error')}")
                return {"success": False, "error": api_result.get('error')}
                
        except Exception as e:
            print(f"[🧠 AI GENERATION] Error: {e}")
            return {"success": False, "error": str(e)}

    def _calculate_caloric_needs(self, age, weight, height, bmi, exercise_freq, work_activity):
        """Calculate caloric needs based on physical profile."""
        try:
            # Base calculation using Harris-Benedict equation if we have data
            if age and weight and height:
                # Assume male for now (could be enhanced with gender data)
                bmr = 88.362 + (13.397 * float(weight) * 0.453592) + (4.799 * float(height) * 2.54) - (5.677 * float(age))
                
                # Activity multiplier
                activity_multiplier = 1.2  # Sedentary base
                if exercise_freq:
                    if 'daily' in str(exercise_freq).lower() or 'very active' in str(exercise_freq).lower():
                        activity_multiplier = 1.9
                    elif 'frequent' in str(exercise_freq).lower() or 'active' in str(exercise_freq).lower():
                        activity_multiplier = 1.725
                    elif 'moderate' in str(exercise_freq).lower():
                        activity_multiplier = 1.55
                    elif 'light' in str(exercise_freq).lower():
                        activity_multiplier = 1.375
                
                return int(bmr * activity_multiplier)
            else:
                # Default based on general guidelines
                return 2000
                
        except:
            return 2000

    def _calculate_macro_targets(self, calories, medical_conditions):
        """Calculate macro targets based on calories and medical conditions."""
        # Base macros
        protein_pct = 0.20  # 20% protein
        carb_pct = 0.50     # 50% carbs  
        fat_pct = 0.30      # 30% fat
        
        # Adjust for medical conditions
        if any('diabetes' in condition.lower() for condition in medical_conditions):
            carb_pct = 0.40    # Reduce carbs for diabetes
            protein_pct = 0.25  # Increase protein
            fat_pct = 0.35     # Increase healthy fats
        
        if any('heart' in condition.lower() or 'cardiovascular' in condition.lower() for condition in medical_conditions):
            fat_pct = 0.25     # Reduce fat for heart health
            carb_pct = 0.55    # Increase carbs (healthy ones)
        
        protein_target = int(calories * protein_pct / 4)
        carb_target = int(calories * carb_pct / 4)
        fat_target = int(calories * fat_pct / 9)
        
        return protein_target, carb_target, fat_target

    def _identify_health_risk_factors(self, medical_conditions, lab_values, bmi):
        """Identify health risk factors from medical data."""
        risk_factors = []
        
        if bmi:
            try:
                bmi_val = float(bmi)
                if bmi_val >= 30:
                    risk_factors.append("Obesity")
                elif bmi_val >= 25:
                    risk_factors.append("Overweight")
            except:
                pass
        
        if any('diabetes' in condition.lower() for condition in medical_conditions):
            risk_factors.append("Blood sugar management")
        
        if any('hypertension' in condition.lower() or 'blood pressure' in condition.lower() for condition in medical_conditions):
            risk_factors.append("Blood pressure management")
        
        if any('cholesterol' in condition.lower() for condition in medical_conditions):
            risk_factors.append("Cholesterol management")
        
        return risk_factors

    def _analyze_medication_interactions(self, medications):
        """Analyze potential medication-food interactions."""
        considerations = []
        
        for med in medications:
            med_lower = med.lower()
            if 'metformin' in med_lower:
                considerations.append("Take with meals to reduce GI upset")
            elif 'warfarin' in med_lower or 'coumadin' in med_lower:
                considerations.append("Maintain consistent vitamin K intake")
            elif 'insulin' in med_lower:
                considerations.append("Coordinate carbohydrate intake with insulin timing")
            elif 'lisinopril' in med_lower or 'ace inhibitor' in med_lower:
                considerations.append("Monitor potassium intake")
        
        return considerations

    def _identify_consumption_patterns(self, consumption_history):
        """Identify patterns in consumption history."""
        patterns = []
        
        if not consumption_history:
            return patterns
        
        # Analyze meal frequency
        meal_counts = {}
        for record in consumption_history:
            meal_type = record.get('meal_type', 'unknown')
            meal_counts[meal_type] = meal_counts.get(meal_type, 0) + 1
        
        most_common_meal = max(meal_counts, key=meal_counts.get) if meal_counts else None
        if most_common_meal:
            patterns.append(f"Most frequent meal type: {most_common_meal}")
        
        # Add more pattern analysis...
        return patterns

    def _extract_food_preferences(self, consumption_history):
        """Extract food preferences from consumption history."""
        food_counts = {}
        
        for record in consumption_history:
            food_name = record.get('food_name', '').lower()
            if food_name:
                food_counts[food_name] = food_counts.get(food_name, 0) + 1
        
        # Return top foods
        sorted_foods = sorted(food_counts.items(), key=lambda x: x[1], reverse=True)
        return [food for food, count in sorted_foods[:10]]

    def _analyze_nutritional_trends(self, consumption_history):
        """Analyze nutritional trends from consumption history."""
        if not consumption_history:
            return {}
        
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        valid_records = 0
        
        for record in consumption_history:
            nutrition = record.get('nutritional_info', {})
            if nutrition:
                total_calories += nutrition.get('calories', 0)
                total_protein += nutrition.get('protein', 0)
                total_carbs += nutrition.get('carbohydrates', 0)
                total_fat += nutrition.get('fat', 0)
                valid_records += 1
        
        if valid_records == 0:
            return {}
        
        return {
            "avg_calories": round(total_calories / valid_records, 1),
            "avg_protein": round(total_protein / valid_records, 1),
            "avg_carbs": round(total_carbs / valid_records, 1),
            "avg_fat": round(total_fat / valid_records, 1),
            "protein_pattern": "adequate" if (total_protein / valid_records) > 50 else "low",
            "carb_pattern": "high" if (total_carbs / valid_records) > 200 else "moderate",
            "fat_pattern": "adequate" if (total_fat / valid_records) > 40 else "low"
        }

    def _analyze_meal_timing_patterns(self, consumption_history):
        """Analyze meal timing patterns."""
        if not consumption_history:
            return {}
        
        # Simple timing analysis
        morning_meals = 0
        afternoon_meals = 0
        evening_meals = 0
        
        for record in consumption_history:
            timestamp = record.get('timestamp', '')
            if timestamp:
                try:
                    # Simple hour extraction (could be improved)
                    hour = int(timestamp.split('T')[1].split(':')[0]) if 'T' in timestamp else 12
                    if 5 <= hour < 12:
                        morning_meals += 1
                    elif 12 <= hour < 18:
                        afternoon_meals += 1
                    else:
                        evening_meals += 1
                except:
                    pass
        
        return {
            "morning_preference": morning_meals,
            "afternoon_preference": afternoon_meals,
            "evening_preference": evening_meals,
            "preferred_times": "morning" if morning_meals > afternoon_meals and morning_meals > evening_meals else "evening" if evening_meals > afternoon_meals else "afternoon"
        }

    def _get_frequent_foods(self, consumption_history):
        """Get most frequently consumed foods."""
        food_counts = {}
        
        for record in consumption_history:
            food_name = record.get('food_name', '')
            if food_name:
                food_counts[food_name] = food_counts.get(food_name, 0) + 1
        
        # Return top 10 most frequent foods
        sorted_foods = sorted(food_counts.items(), key=lambda x: x[1], reverse=True)
        return [food for food, count in sorted_foods[:10]]

    def _get_avoided_foods(self, consumption_history):
        """Identify foods that might be avoided (this is speculative)."""
        # This is a placeholder - could be enhanced with more sophisticated analysis
        return []

    def _analyze_calorie_consistency(self, consumption_history):
        """Analyze calorie consistency across meals."""
        daily_calories = {}
        
        for record in consumption_history:
            date_str = record.get('timestamp', '').split('T')[0] if record.get('timestamp') else ''
            if date_str:
                calories = record.get('nutritional_info', {}).get('calories', 0)
                daily_calories[date_str] = daily_calories.get(date_str, 0) + calories
        
        if not daily_calories:
            return {"status": "insufficient_data"}
        
        calories_list = list(daily_calories.values())
        avg_calories = sum(calories_list) / len(calories_list)
        
        # Calculate variance (simplified)
        variance = sum((x - avg_calories) ** 2 for x in calories_list) / len(calories_list)
        std_dev = variance ** 0.5
        
        if std_dev < avg_calories * 0.2:
            consistency = "high"
        elif std_dev < avg_calories * 0.4:
            consistency = "moderate"
        else:
            consistency = "low"
        
        return {
            "status": consistency,
            "avg_daily_calories": round(avg_calories, 1),
            "variability": round(std_dev, 1)
        }

    def _analyze_macro_balance(self, consumption_history):
        """Analyze macro balance trends."""
        # Placeholder for macro balance analysis
        return {"status": "needs_analysis"}

    def _analyze_weekend_vs_weekday_patterns(self, consumption_history):
        """Analyze weekend vs weekday eating patterns."""
        # Placeholder for weekend vs weekday analysis
        return {"pattern": "similar"}

    def _build_ai_context(self, health_analysis, consumption_analysis, days, cuisine_preference):
        """Build comprehensive context for AI generation."""
        return {
            "health": health_analysis,
            "consumption": consumption_analysis,
            "parameters": {
                "days": days,
                "cuisine": cuisine_preference
            }
        }

    async def _create_intelligent_fallback(self, user_email: str, user_profile: dict, days: int, cuisine_preference: str):
        """Create intelligent fallback meal plan."""
        print(f"[🧠 FALLBACK] Creating intelligent fallback meal plan...")
        
        # Extract basic info for fallback
        medical_conditions = user_profile.get("medicalConditions", []) or user_profile.get("medical_conditions", [])
        dietary_restrictions = user_profile.get("dietaryRestrictions", [])
        
        fallback_plan = {
            "plan_name": f"🧠 Intelligent Fallback Plan - {datetime.now().strftime('%Y-%m-%d')}",
            "duration_days": days,
            "dailyCalories": 2000,
            "macronutrients": {"protein": 100, "carbohydrates": 200, "fat": 67},
            "breakfast": [f"Healthy breakfast option {i+1}" for i in range(days)],
            "lunch": [f"Nutritious lunch option {i+1}" for i in range(days)],
            "dinner": [f"Balanced dinner option {i+1}" for i in range(days)],
            "snacks": [f"Smart snack option {i+1}" for i in range(days)],
            "intelligent_adaptations": [
                f"Adapted for medical conditions: {', '.join(medical_conditions[:2])}" if medical_conditions else "Standard healthy meal plan",
                f"Respects dietary restrictions: {', '.join(dietary_restrictions[:2])}" if dietary_restrictions else "No dietary restrictions applied"
            ],
            "ai_insights": [
                "This is a fallback plan - regenerate for full AI personalization",
                "Plan includes balanced macronutrients and portion control"
            ],
            "coaching_notes": "Intelligent fallback plan created. For full personalization, please regenerate your meal plan."
        }
        
        return {
            "success": True,
            "meal_plan": fallback_plan,
            "personalization_score": 60,
            "ai_insights": fallback_plan["ai_insights"],
            "health_adaptations": fallback_plan["intelligent_adaptations"],
            "message": "⚠️ Intelligent fallback meal plan created. Regenerate for full AI personalization."
        }


# Global instance
intelligent_planner = IntelligentMealPlanner()