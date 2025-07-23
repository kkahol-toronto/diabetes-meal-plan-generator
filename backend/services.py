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
        Extract meal information from user message using AI
        Returns list of detected meals with confidence scores
        """
        try:
            # Prepare context for AI
            context = self._prepare_extraction_context(
                message, 
                user_context, 
                conversation_history
            )
            
            # Use GPT-4 for meal extraction
            extraction_prompt = self._build_extraction_prompt(message, context)
            
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system", 
                        "content": self._get_meal_extraction_system_prompt()
                    },
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent extraction
                max_tokens=500
            )
            
            # Parse AI response
            extracted_meals = self._parse_extraction_response(
                response.choices[0].message.content
            )
            
            # Enhance with temporal analysis
            enhanced_meals = await self._enhance_with_temporal_analysis(
                extracted_meals, 
                message,
                user_context
            )
            
            return enhanced_meals
            
        except Exception as e:
            logging.error(f"Meal extraction failed: {str(e)}")
            return []

    def _get_meal_extraction_system_prompt(self) -> str:
        return """
        You are a diabetes nutrition expert tasked with extracting meal information from user messages.
        
        Your job is to identify:
        1. Food items mentioned
        2. Quantities (portions, servings, amounts)
        3. Meal type (breakfast, lunch, dinner, snack)
        4. Timing information
        5. Preparation methods
        6. Confidence level (0-100)
        
        Return ONLY valid JSON in this format:
        {
          "meals": [
            {
              "food_name": "grilled chicken breast",
              "quantity": "6 oz",
              "meal_type": "lunch",
              "estimated_time": "12:30 PM",
              "preparation": "grilled",
              "confidence": 85,
              "raw_mention": "had some grilled chicken for lunch"
            }
          ]
        }
        
        Rules:
        - Only extract actual food items, not cooking ingredients
        - If no specific quantity is mentioned, use "1 serving"
        - Confidence should be 70+ for clear food mentions, 50-69 for uncertain
        - Don't extract vague mentions like "something to eat"
        - Include preparation method if mentioned (grilled, baked, fried, etc.)
        """

    def _build_extraction_prompt(self, message: str, context: Dict) -> str:
        """Build the extraction prompt with context"""
        
        prompt = f"""
        User Context:
        - Dietary restrictions: {context.get('dietary_restrictions', [])}
        - Medical conditions: {context.get('medical_conditions', [])}
        - Typical meal times: {context.get('meal_schedule', 'standard')}
        - Current time: {datetime.now().strftime('%H:%M')}
        
        Recent conversation context:
        {context.get('recent_messages', '')}
        
        Message to analyze:
        "{message}"
        
        Extract any food or meal mentions from this message. Be specific about food items and portions.
        """
        
        return prompt

    def _prepare_extraction_context(
        self, 
        message: str, 
        user_context: Dict,
        conversation_history: List[Dict]
    ) -> Dict:
        """Prepare context for meal extraction"""
        
        context = {
            'dietary_restrictions': user_context.get('dietaryRestrictions', []),
            'medical_conditions': user_context.get('medicalConditions', []),
            'meal_schedule': user_context.get('eatingSchedule', 'standard'),
            'recent_messages': ''
        }
        
        # Add recent conversation context (last 3 messages)
        if conversation_history:
            recent_messages = conversation_history[-3:]
            context['recent_messages'] = '\n'.join([
                f"{'User' if msg.get('is_user') else 'Assistant'}: {msg.get('message_content', '')}"
                for msg in recent_messages
            ])
        
        return context

    def _parse_extraction_response(self, response_content: str) -> List[Dict]:
        """Parse the AI response and extract meal data"""
        try:
            # Clean up the response
            cleaned_response = response_content.strip()
            
            # Find JSON content
            json_start = cleaned_response.find('{')
            json_end = cleaned_response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_content = cleaned_response[json_start:json_end]
                parsed_data = json.loads(json_content)
                
                return parsed_data.get('meals', [])
            else:
                logging.warning("No valid JSON found in extraction response")
                return []
                
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse extraction response: {str(e)}")
            return []
        except Exception as e:
            logging.error(f"Error parsing extraction response: {str(e)}")
            return []

    async def _enhance_with_temporal_analysis(
        self, 
        extracted_meals: List[Dict],
        original_message: str,
        user_context: Dict
    ) -> List[Dict]:
        """
        Enhance extracted meals with temporal analysis and context
        """
        enhanced_meals = []
        current_time = datetime.now()
        
        for meal in extracted_meals:
            enhanced_meal = meal.copy()
            
            # Analyze temporal cues
            temporal_cues = self._extract_temporal_cues(original_message)
            
            if temporal_cues:
                enhanced_meal['timing_cues'] = temporal_cues
                enhanced_meal['estimated_consumption_time'] = (
                    await self._estimate_consumption_time(
                        temporal_cues, 
                        meal.get('meal_type', 'snack'),
                        current_time
                    )
                )
            
            # Add nutritional estimates
            enhanced_meal['estimated_nutrition'] = (
                await self._estimate_nutrition(meal.get('food_name', ''), meal.get('quantity', '1 serving'))
            )
            
            # Diabetes impact assessment
            enhanced_meal['diabetes_impact'] = (
                await self._assess_diabetes_impact(enhanced_meal)
            )
            
            enhanced_meals.append(enhanced_meal)
        
        return enhanced_meals

    def _extract_temporal_cues(self, message: str) -> List[str]:
        """Extract temporal cues from the message"""
        temporal_patterns = [
            r'(\d{1,2}:\d{2}\s*(?:am|pm|AM|PM)?)',  # Time patterns
            r'(this morning|this afternoon|this evening|tonight)',
            r'(yesterday|today|earlier|just now|a while ago)',
            r'(breakfast|lunch|dinner|snack) time',
            r'(before|after) (work|gym|meeting)',
            r'(\d+) (minutes?|hours?) ago'
        ]
        
        cues = []
        for pattern in temporal_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            cues.extend([match if isinstance(match, str) else ' '.join(match) for match in matches])
        
        return cues

    async def _estimate_consumption_time(
        self, 
        temporal_cues: List[str],
        meal_type: str,
        current_time: datetime
    ) -> datetime:
        """Estimate when the meal was consumed based on cues"""
        
        # Default meal times
        default_times = {
            'breakfast': 8,  # 8 AM
            'lunch': 12,     # 12 PM
            'dinner': 18,    # 6 PM
            'snack': current_time.hour  # Current time for snacks
        }
        
        # Check for specific time mentions
        for cue in temporal_cues:
            time_match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm|AM|PM)?', cue)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                period = time_match.group(3)
                
                if period and period.lower() == 'pm' and hour != 12:
                    hour += 12
                elif period and period.lower() == 'am' and hour == 12:
                    hour = 0
                
                return current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # Check for relative time mentions
        for cue in temporal_cues:
            if 'ago' in cue:
                ago_match = re.search(r'(\d+)\s*(minutes?|hours?)\s*ago', cue, re.IGNORECASE)
                if ago_match:
                    amount = int(ago_match.group(1))
                    unit = ago_match.group(2).lower()
                    
                    if 'hour' in unit:
                        return current_time - timedelta(hours=amount)
                    elif 'minute' in unit:
                        return current_time - timedelta(minutes=amount)
        
        # Use default time for meal type
        default_hour = default_times.get(meal_type, current_time.hour)
        return current_time.replace(hour=default_hour, minute=0, second=0, microsecond=0)

    async def _estimate_nutrition(self, food_name: str, quantity: str) -> Dict:
        """Estimate nutritional information for the food item"""
        try:
            # Use AI to estimate nutrition
            nutrition_prompt = f"""
            Estimate the nutritional information for: {food_name} ({quantity})
            
            Return ONLY a JSON object with these fields:
            {{
              "calories": number,
              "protein": number,
              "carbohydrates": number,
              "fat": number,
              "fiber": number,
              "sugar": number,
              "sodium": number
            }}
            
            Use standard nutritional values. If quantity is unclear, assume "1 serving".
            """
            
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a nutrition expert. Return only valid JSON."},
                    {"role": "user", "content": nutrition_prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            nutrition_content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            json_start = nutrition_content.find('{')
            json_end = nutrition_content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_content = nutrition_content[json_start:json_end]
                nutrition_data = json.loads(json_content)
                return nutrition_data
            else:
                logging.warning(f"No valid JSON in nutrition response for {food_name}")
                return self._get_default_nutrition()
                
        except Exception as e:
            logging.error(f"Nutrition estimation failed for {food_name}: {str(e)}")
            return self._get_default_nutrition()

    def _get_default_nutrition(self) -> Dict:
        """Return default nutrition values"""
        return {
            "calories": 200,
            "protein": 10,
            "carbohydrates": 25,
            "fat": 8,
            "fiber": 3,
            "sugar": 5,
            "sodium": 300
        }

    async def _assess_diabetes_impact(self, meal_data: Dict) -> Dict:
        """Assess the diabetes impact of the meal"""
        try:
            nutrition = meal_data.get('estimated_nutrition', {})
            food_name = meal_data.get('food_name', '')
            
            # Calculate glycemic load estimate
            carbs = nutrition.get('carbohydrates', 0)
            fiber = nutrition.get('fiber', 0)
            
            # Simple diabetes impact assessment
            net_carbs = max(0, carbs - fiber)
            
            if net_carbs <= 15:
                impact_level = "low"
            elif net_carbs <= 30:
                impact_level = "moderate"
            else:
                impact_level = "high"
            
            # Additional considerations
            considerations = []
            if net_carbs > 45:
                considerations.append("High carbohydrate content - monitor blood glucose")
            if nutrition.get('sugar', 0) > 20:
                considerations.append("High sugar content - consider portion control")
            if nutrition.get('sodium', 0) > 500:
                considerations.append("High sodium content")
            
            return {
                "impact_level": impact_level,
                "net_carbs": net_carbs,
                "considerations": considerations,
                "recommendation": self._get_diabetes_recommendation(impact_level, considerations)
            }
            
        except Exception as e:
            logging.error(f"Diabetes impact assessment failed: {str(e)}")
            return {
                "impact_level": "unknown",
                "net_carbs": 0,
                "considerations": [],
                "recommendation": "Monitor blood glucose as usual"
            }

    def _get_diabetes_recommendation(self, impact_level: str, considerations: List[str]) -> str:
        """Get diabetes management recommendation"""
        
        if impact_level == "low":
            return "Good choice for blood glucose management"
        elif impact_level == "moderate":
            return "Monitor blood glucose and consider insulin adjustment if needed"
        else:
            return "High impact food - monitor blood glucose closely and adjust insulin as prescribed" 