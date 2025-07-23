import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from openai import AzureOpenAI
import logging
import os
import json

class MealExtractionService:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.meal_keywords = {
            'breakfast': ['breakfast', 'morning', 'cereal', 'toast', 'coffee', 'brunch'],
            'lunch': ['lunch', 'noon', 'sandwich', 'salad', 'midday'],
            'dinner': ['dinner', 'evening', 'supper', 'night'],
            'snack': ['snack', 'snacking', 'quick bite', 'between meals']
        }

    async def extract_meals_from_message(
        self, 
        message: str, 
        user_context: Dict,
        conversation_history: List[Dict]
    ) -> List[Dict]:
        """
        Extract meal information from a chat message using AI
        
        Args:
            message: The user's chat message
            user_context: User profile and dietary information
            conversation_history: Recent conversation context
            
        Returns:
            List of extracted meal records with confidence scores
        """
        try:
            context = self._prepare_extraction_context(message, user_context, conversation_history)
            extraction_prompt = self._build_extraction_prompt(message, context)
            
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self._get_meal_extraction_system_prompt()},
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            extracted_meals = self._parse_extraction_response(response.choices[0].message.content)
            enhanced_meals = await self._enhance_with_temporal_analysis(extracted_meals, message, user_context)
            
            return enhanced_meals
            
        except Exception as e:
            logging.error(f"Meal extraction failed: {str(e)}")
            return []

    def _prepare_extraction_context(self, message: str, user_context: Dict, conversation_history: List[Dict]) -> Dict:
        """Prepare context for meal extraction"""
        return {
            "dietary_restrictions": user_context.get("dietaryRestrictions", []),
            "allergies": user_context.get("allergies", []),
            "medical_conditions": user_context.get("medicalConditions", []),
            "recent_conversation": conversation_history[-5:] if conversation_history else [],
            "current_time": datetime.utcnow().isoformat(),
            "user_timezone": user_context.get("timezone", "UTC")
        }

    def _build_extraction_prompt(self, message: str, context: Dict) -> str:
        """Build the extraction prompt for AI"""
        return f"""
        Analyze this message for food/meal mentions and extract structured data:
        
        MESSAGE: "{message}"
        
        CONTEXT:
        - User dietary restrictions: {context.get('dietary_restrictions', [])}
        - User allergies: {context.get('allergies', [])}
        - Medical conditions: {context.get('medical_conditions', [])}
        - Current time: {context.get('current_time')}
        
        Extract any meals mentioned and return JSON:
        {{
            "meals_found": [
                {{
                    "food_name": "specific food item",
                    "estimated_portion": "portion size",
                    "meal_type": "breakfast/lunch/dinner/snack", 
                    "confidence": 0.0-1.0,
                    "estimated_time": "when was this eaten",
                    "nutritional_estimate": {{
                        "calories": estimated_calories,
                        "protein": grams,
                        "carbohydrates": grams,
                        "fat": grams
                    }},
                    "diabetes_impact": "low/medium/high",
                    "extraction_reasoning": "why this was identified as a meal"
                }}
            ],
            "overall_confidence": 0.0-1.0
        }}
        
        Only extract actual food consumption, not planning or hypothetical mentions.
        """

    def _get_meal_extraction_system_prompt(self) -> str:
        """Get the system prompt for meal extraction"""
        return """You are an expert nutritionist AI that specializes in extracting meal information from natural language. 

        Your task is to:
        1. Identify actual food consumption (not planning or hypothetical)
        2. Estimate nutritional information based on typical portions
        3. Assess diabetes impact based on glycemic index and carb content
        4. Determine meal timing and type
        5. Provide confidence scores for your extractions

        Be conservative - only extract meals you're confident about. 
        Consider context clues for portion sizes and meal timing.
        Factor in dietary restrictions when making assessments."""

    def _parse_extraction_response(self, response_content: str) -> List[Dict]:
        """Parse the AI response into structured meal data"""
        try:
            # Extract JSON from response
            start_idx = response_content.find('{')
            end_idx = response_content.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_content[start_idx:end_idx]
                parsed_data = json.loads(json_str)
                return parsed_data.get("meals_found", [])
            
            return []
            
        except Exception as e:
            logging.error(f"Failed to parse extraction response: {str(e)}")
            return []

    async def _enhance_with_temporal_analysis(self, meals: List[Dict], message: str, user_context: Dict) -> List[Dict]:
        """Enhance meal data with temporal analysis"""
        current_time = datetime.utcnow()
        
        for meal in meals:
            # Analyze temporal indicators in the message
            time_indicators = self._extract_time_indicators(message)
            
            if time_indicators:
                meal["estimated_time"] = time_indicators
            else:
                # Default to current time if no indicators found
                meal["estimated_time"] = current_time.isoformat()
            
            # Enhance with diabetes-specific analysis
            meal = await self._add_diabetes_analysis(meal, user_context)
            
        return meals

    def _extract_time_indicators(self, message: str) -> Optional[str]:
        """Extract time indicators from the message"""
        message_lower = message.lower()
        current_time = datetime.utcnow()
        
        # Look for specific time indicators
        if any(word in message_lower for word in ["just ate", "just had", "just finished"]):
            return (current_time - timedelta(minutes=15)).isoformat()
        elif any(word in message_lower for word in ["earlier", "this morning"]):
            return current_time.replace(hour=8, minute=0).isoformat()
        elif any(word in message_lower for word in ["lunch", "noon"]):
            return current_time.replace(hour=12, minute=0).isoformat()
        elif any(word in message_lower for word in ["dinner", "evening"]):
            return current_time.replace(hour=18, minute=0).isoformat()
        
        return None

    async def _add_diabetes_analysis(self, meal: Dict, user_context: Dict) -> Dict:
        """Add diabetes-specific analysis to meal data"""
        # Enhance with medical rating
        meal["medical_rating"] = {
            "diabetes_suitability": self._assess_diabetes_suitability(meal),
            "glycemic_impact": meal.get("diabetes_impact", "medium"),
            "recommendations": self._generate_recommendations(meal, user_context)
        }
        
        return meal

    def _assess_diabetes_suitability(self, meal: Dict) -> str:
        """Assess how suitable a meal is for diabetes management"""
        food_name = meal.get("food_name", "").lower()
        nutrition = meal.get("nutritional_estimate", {})
        
        # High sugar/carb foods
        if any(word in food_name for word in ["candy", "cake", "soda", "ice cream", "donut"]):
            return "low"
        
        # Healthy foods
        if any(word in food_name for word in ["salad", "vegetables", "lean protein", "fish", "chicken"]):
            return "high"
        
        # Moderate carb foods
        if any(word in food_name for word in ["bread", "rice", "pasta", "potato"]):
            return "medium"
        
        return "medium"

    def _generate_recommendations(self, meal: Dict, user_context: Dict) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []
        
        diabetes_suitability = meal.get("medical_rating", {}).get("diabetes_suitability", "medium")
        
        if diabetes_suitability == "low":
            recommendations.append("Consider pairing with protein or fiber to slow glucose absorption")
            recommendations.append("Monitor blood glucose levels after this meal")
        elif diabetes_suitability == "high":
            recommendations.append("Great choice for diabetes management")
        
        return recommendations

    async def smart_log_decision(self, extracted_meals: List[Dict], confidence_threshold: float = 0.85) -> Dict:
        """
        Make smart decisions about whether to auto-log or request confirmation
        
        Args:
            extracted_meals: List of extracted meal data
            confidence_threshold: Minimum confidence for auto-logging
            
        Returns:
            Decision data with recommendations
        """
        try:
            if not extracted_meals:
                return {
                    "action": "no_meals_found",
                    "message": "I didn't detect any meal mentions in your message."
                }
            
            high_confidence_meals = [
                meal for meal in extracted_meals 
                if meal.get("confidence", 0) >= confidence_threshold
            ]
            
            low_confidence_meals = [
                meal for meal in extracted_meals 
                if meal.get("confidence", 0) < confidence_threshold
            ]
            
            if high_confidence_meals and not low_confidence_meals:
                # Auto-log high confidence meals
                return {
                    "action": "auto_log",
                    "meals": high_confidence_meals,
                    "message": f"I detected {len(high_confidence_meals)} meal(s) and logged them automatically."
                }
            elif extracted_meals:
                # Request confirmation for uncertain extractions
                return {
                    "action": "request_confirmation",
                    "meals": extracted_meals,
                    "message": f"I think I detected {len(extracted_meals)} meal(s). Please confirm if this is correct."
                }
            else:
                return {
                    "action": "no_meals_found",
                    "message": "I didn't detect any clear meal mentions."
                }
                
        except Exception as e:
            logging.error(f"Smart log decision failed: {str(e)}")
            return {
                "action": "error",
                "message": "I had trouble analyzing your message. Please try rephrasing or log manually."
            } 