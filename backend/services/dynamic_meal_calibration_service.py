"""
Dynamic Meal Plan Calibration Service
Provides real-time meal plan calibration when users log food consumption.
Integrates with the Enhanced Smart Daily Meal Planner to dynamically adjust
remaining meal recommendations based on actual vs planned consumption.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
import traceback
import json

from database import get_user_by_email, get_user_consumption_history
from services.enhanced_smart_meal_planner import enhanced_smart_meal_planner
from services.comprehensive_health_analyzer import health_analyzer
from services.openai_service import robust_openai_call
from utils import filter_today_records


class DynamicMealCalibrationService:
    """
    Service for real-time dynamic meal plan calibration based on consumption patterns.
    Automatically adjusts remaining meal suggestions when users log food.
    """
    
    def __init__(self):
        self.calibration_threshold = 0.2  # 20% deviation triggers calibration
        self.max_calibration_frequency = 3  # Max calibrations per day per user
        
    async def trigger_dynamic_calibration(
        self,
        user_email: str,
        user_profile: Dict[str, Any],
        newly_logged_food: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Trigger dynamic meal plan calibration after food logging.
        
        Args:
            user_email: User's email identifier
            user_profile: User's complete profile data
            newly_logged_food: Optional data about the food just logged
            
        Returns:
            Calibration result with updated meal recommendations
        """
        try:
            print(f"[DynamicCalibration] Starting calibration for {user_email}")
            
            # Get current consumption and nutritional status
            calibration_analysis = await self._analyze_calibration_need(
                user_email, user_profile, newly_logged_food
            )
            
            if not calibration_analysis["calibration_needed"]:
                print(f"[DynamicCalibration] No calibration needed for {user_email}")
                return {
                    "calibration_performed": False,
                    "reason": calibration_analysis["reason"],
                    "current_status": calibration_analysis["current_status"]
                }
            
            print(f"[DynamicCalibration] Calibration needed: {calibration_analysis['reason']}")
            
            # Generate updated smart meal plan with dynamic calibration
            updated_meal_plan = await self._generate_calibrated_meal_plan(
                user_email, user_profile, calibration_analysis
            )
            
            # Create calibration insights
            calibration_insights = await self._generate_calibration_insights(
                calibration_analysis, updated_meal_plan, newly_logged_food
            )
            
            # Track calibration for user
            await self._track_calibration_event(user_email, calibration_analysis, updated_meal_plan)
            
            result = {
                "calibration_performed": True,
                "calibration_reason": calibration_analysis["reason"],
                "calibration_timestamp": datetime.utcnow().isoformat(),
                "updated_meal_plan": updated_meal_plan.get("smart_meal_plan", {}),
                "nutritional_status": updated_meal_plan.get("daily_progress", {}),
                "remaining_targets": updated_meal_plan.get("remaining_targets", {}),
                "calibration_insights": calibration_insights,
                "confidence_score": updated_meal_plan.get("recommendation_confidence", 0.8),
                "next_meal_focus": self._determine_next_meal_focus(calibration_analysis, updated_meal_plan)
            }
            
            print(f"[DynamicCalibration] Successfully calibrated meal plan for {user_email}")
            return result
            
        except Exception as e:
            print(f"[DynamicCalibration] Error in calibration for {user_email}: {str(e)}")
            print(f"[DynamicCalibration] Traceback: {traceback.format_exc()}")
            return {
                "calibration_performed": False,
                "error": str(e),
                "fallback_recommendation": "Continue with existing meal plan and monitor progress"
            }

    async def _analyze_calibration_need(
        self,
        user_email: str,
        user_profile: Dict[str, Any],
        newly_logged_food: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze whether meal plan calibration is needed."""
        try:
            # Get today's consumption including the newly logged food
            user_timezone = user_profile.get("timezone", "UTC")
            today_consumption = await self._get_today_consumption(user_email, user_timezone)
            
            # Get nutritional goals
            calorie_target = self._extract_calorie_target(user_profile)
            protein_target = self._extract_protein_target(user_profile)
            
            # Calculate current consumption
            consumed_calories = sum(
                record.get("nutritional_info", {}).get("calories", 0) 
                for record in today_consumption
            )
            consumed_protein = sum(
                record.get("nutritional_info", {}).get("protein", 0) 
                for record in today_consumption
            )
            
            # Determine remaining meals
            remaining_meals = self._determine_remaining_meals(user_timezone)
            
            # Calculate deviation from plan
            calorie_deviation = abs(consumed_calories - calorie_target) / calorie_target if calorie_target > 0 else 0
            protein_deviation = abs(consumed_protein - protein_target) / protein_target if protein_target > 0 else 0
            
            # Check calibration conditions
            calibration_needed = False
            reasons = []
            
            # Condition 1: Significant nutritional deviation
            if calorie_deviation > self.calibration_threshold:
                calibration_needed = True
                reasons.append(f"calorie_deviation_{calorie_deviation:.1%}")
            
            if protein_deviation > self.calibration_threshold:
                calibration_needed = True
                reasons.append(f"protein_deviation_{protein_deviation:.1%}")
            
            # Condition 2: Major meals remaining but high consumption
            major_meals_remaining = sum(1 for meal in remaining_meals if meal in ['breakfast', 'lunch', 'dinner'])
            if major_meals_remaining > 0 and consumed_calories > (calorie_target * 0.75):
                calibration_needed = True
                reasons.append("high_consumption_major_meals_remaining")
            
            # Condition 3: Very low consumption late in day
            current_hour = datetime.utcnow().hour
            if current_hour > 14 and consumed_calories < (calorie_target * 0.4):
                calibration_needed = True
                reasons.append("low_consumption_late_day")
            
            # Condition 4: New food significantly different from typical patterns
            if newly_logged_food and self._is_atypical_food_choice(newly_logged_food, today_consumption):
                calibration_needed = True
                reasons.append("atypical_food_choice")
            
            return {
                "calibration_needed": calibration_needed,
                "reason": "; ".join(reasons) if reasons else "no_calibration_needed",
                "current_status": {
                    "consumed_calories": consumed_calories,
                    "target_calories": calorie_target,
                    "consumed_protein": round(consumed_protein, 1),
                    "target_protein": protein_target,
                    "calorie_deviation": round(calorie_deviation * 100, 1),
                    "protein_deviation": round(protein_deviation * 100, 1),
                    "remaining_meals": remaining_meals,
                    "major_meals_remaining": major_meals_remaining
                },
                "deviation_analysis": {
                    "calorie_deviation_percent": round(calorie_deviation * 100, 1),
                    "protein_deviation_percent": round(protein_deviation * 100, 1),
                    "exceeds_threshold": calorie_deviation > self.calibration_threshold or protein_deviation > self.calibration_threshold
                }
            }
            
        except Exception as e:
            print(f"[DynamicCalibration] Error analyzing calibration need: {str(e)}")
            return {
                "calibration_needed": False,
                "reason": f"analysis_error_{str(e)}",
                "current_status": {},
                "error": str(e)
            }

    async def _generate_calibrated_meal_plan(
        self,
        user_email: str,
        user_profile: Dict[str, Any],
        calibration_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate updated meal plan with dynamic calibration applied."""
        try:
            # Get fresh consumption data for calibration
            user_timezone = user_profile.get("timezone", "UTC")
            current_consumption = await self._get_today_consumption(user_email, user_timezone)
            
            # Generate updated comprehensive meal plan
            updated_plan = await enhanced_smart_meal_planner.generate_comprehensive_smart_meal_plan(
                user_email=user_email,
                user_profile=user_profile,
                current_consumption=current_consumption
            )
            
            # Add calibration metadata
            updated_plan["calibration_metadata"] = {
                "calibration_applied": True,
                "calibration_reason": calibration_analysis["reason"],
                "calibration_timestamp": datetime.utcnow().isoformat(),
                "deviation_analysis": calibration_analysis.get("deviation_analysis", {}),
                "pre_calibration_status": calibration_analysis["current_status"]
            }
            
            return updated_plan
            
        except Exception as e:
            print(f"[DynamicCalibration] Error generating calibrated meal plan: {str(e)}")
            raise

    async def _generate_calibration_insights(
        self,
        calibration_analysis: Dict[str, Any],
        updated_meal_plan: Dict[str, Any],
        newly_logged_food: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate AI-powered insights about the calibration."""
        
        # Extract key data for AI analysis
        current_status = calibration_analysis["current_status"]
        remaining_targets = updated_meal_plan.get("remaining_targets", {})
        remaining_meals = current_status.get("remaining_meals", [])
        
        prompt = f"""
        Provide personalized insights about this meal plan calibration for a diabetes management user.

        CALIBRATION CONTEXT:
        - Reason for Calibration: {calibration_analysis['reason']}
        - Calorie Deviation: {current_status.get('calorie_deviation', 0)}%
        - Protein Deviation: {current_status.get('protein_deviation', 0)}%
        - Consumed Calories: {current_status.get('consumed_calories', 0)} / {current_status.get('target_calories', 0)}
        - Consumed Protein: {current_status.get('consumed_protein', 0)}g / {current_status.get('target_protein', 0)}g

        REMAINING PLAN:
        - Remaining Meals: {remaining_meals}
        - Remaining Calories: {remaining_targets.get('calories', 0)}
        - Remaining Protein: {remaining_targets.get('protein', 0)}g

        NEWLY LOGGED FOOD: {newly_logged_food.get('food_name', 'N/A') if newly_logged_food else 'N/A'}

        Provide insights in JSON format:
        {{
            "calibration_summary": "brief explanation of why calibration was needed",
            "nutritional_impact": "how this affects daily nutrition goals",
            "adjustment_strategy": "how remaining meals were adjusted",
            "health_recommendations": ["tip1", "tip2", "tip3"],
            "positive_reinforcement": "encouraging message about progress",
            "next_meal_guidance": "specific guidance for next meal",
            "diabetes_management_focus": "diabetes-specific considerations"
        }}
        """
        
        try:
            ai_response = await robust_openai_call(
                [{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=600
            )
            
            if ai_response and ai_response.get("success") and ai_response.get("content"):
                content = ai_response["content"].strip()
                return json.loads(content)
                
        except Exception as e:
            print(f"[DynamicCalibration] AI insights generation failed: {e}")
        
        # Fallback insights
        return {
            "calibration_summary": f"Meal plan adjusted due to {calibration_analysis['reason'].replace('_', ' ')}",
            "nutritional_impact": "Remaining meals optimized to meet daily nutrition goals",
            "adjustment_strategy": "Portion sizes and meal composition adjusted for balance",
            "health_recommendations": [
                "Stay hydrated throughout the day",
                "Focus on balanced portions in remaining meals",
                "Monitor blood glucose if applicable"
            ],
            "positive_reinforcement": "Great job logging your food! This helps optimize your meal plan.",
            "next_meal_guidance": "Focus on balanced nutrition in your next meal",
            "diabetes_management_focus": "Continue monitoring carbohydrate intake and portion sizes"
        }

    async def _track_calibration_event(
        self,
        user_email: str,
        calibration_analysis: Dict[str, Any],
        updated_meal_plan: Dict[str, Any]
    ) -> None:
        """Track calibration event for analytics and rate limiting."""
        try:
            # This would typically save to a calibration tracking table
            # For now, we'll just log it
            print(f"[DynamicCalibration] Calibration event tracked for {user_email}")
            print(f"[DynamicCalibration] Reason: {calibration_analysis['reason']}")
            print(f"[DynamicCalibration] Confidence: {updated_meal_plan.get('recommendation_confidence', 'N/A')}")
            
        except Exception as e:
            print(f"[DynamicCalibration] Error tracking calibration event: {str(e)}")

    async def _get_today_consumption(self, user_email: str, user_timezone: str) -> List[Dict]:
        """Get today's consumption records with timezone awareness."""
        try:
            consumption_history = await get_user_consumption_history(user_email, limit=50)
            return filter_today_records(consumption_history, user_timezone)
        except Exception as e:
            print(f"[DynamicCalibration] Error getting today's consumption: {str(e)}")
            return []

    def _extract_calorie_target(self, user_profile: Dict[str, Any]) -> int:
        """Extract calorie target from user profile."""
        calorie_target = user_profile.get("calorieTarget", "2000")
        try:
            return int(calorie_target) if calorie_target else 2000
        except (ValueError, TypeError):
            return 2000

    def _extract_protein_target(self, user_profile: Dict[str, Any]) -> int:
        """Extract protein target from user profile."""
        # Try new protein target field first
        protein_target = user_profile.get("proteinTarget")
        if protein_target:
            try:
                return int(protein_target)
            except (ValueError, TypeError):
                pass
        
        # Try macro goals
        macro_goals = user_profile.get("macroGoals", {})
        if macro_goals and macro_goals.get("protein"):
            try:
                return int(macro_goals["protein"])
            except (ValueError, TypeError):
                pass
        
        # Default based on calorie target (20% of calories / 4 = protein grams)
        calorie_target = self._extract_calorie_target(user_profile)
        return int((calorie_target * 0.2) / 4)

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

    def _is_atypical_food_choice(
        self,
        newly_logged_food: Dict[str, Any],
        today_consumption: List[Dict]
    ) -> bool:
        """Determine if newly logged food is atypical compared to user's patterns."""
        # This is a simplified implementation
        # In practice, you'd analyze historical patterns more thoroughly
        
        new_food_calories = newly_logged_food.get("nutritional_info", {}).get("calories", 0)
        
        # Consider atypical if significantly higher calorie than other meals today
        other_meal_calories = [
            record.get("nutritional_info", {}).get("calories", 0)
            for record in today_consumption[:-1]  # Exclude the newest entry
        ]
        
        if other_meal_calories:
            avg_calories = sum(other_meal_calories) / len(other_meal_calories)
            return new_food_calories > (avg_calories * 1.5)  # 50% higher than average
        
        return False  # Not enough data to determine

    def _determine_next_meal_focus(
        self,
        calibration_analysis: Dict[str, Any],
        updated_meal_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine focus areas for the next meal."""
        remaining_targets = updated_meal_plan.get("remaining_targets", {})
        remaining_meals = calibration_analysis["current_status"].get("remaining_meals", [])
        
        if not remaining_meals:
            return {"focus": "day_complete", "message": "All meals completed for today"}
        
        next_meal = remaining_meals[0]
        calories_per_meal = remaining_targets.get("calories", 0) / len(remaining_meals) if remaining_meals else 0
        protein_per_meal = remaining_targets.get("protein", 0) / len(remaining_meals) if remaining_meals else 0
        
        focus_areas = []
        if calories_per_meal > 600:
            focus_areas.append("calorie_control")
        if protein_per_meal > 30:
            focus_areas.append("protein_focus")
        if calories_per_meal < 200:
            focus_areas.append("light_meal")
        
        return {
            "next_meal": next_meal,
            "target_calories": int(calories_per_meal),
            "target_protein": int(protein_per_meal),
            "focus_areas": focus_areas,
            "message": f"Focus on balanced {next_meal} with {int(calories_per_meal)} calories"
        }


# Global service instance
dynamic_calibration_service = DynamicMealCalibrationService()