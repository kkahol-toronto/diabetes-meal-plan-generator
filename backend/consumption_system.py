"""
AI Diabetes Coach - Consumption Tracking System
Complete rebuild with consistent data structures and full integration
"""

import os
import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict
import asyncio

# Database imports
from database import interactions_container

# OpenAI client
from openai import AzureOpenAI

# Initialize OpenAI client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

class ConsumptionTracker:
    """Complete consumption tracking system with AI integration"""
    
    def __init__(self):
        self.container = interactions_container
    
    async def quick_log_food(self, user_id: str, food_name: str, portion: str = "medium portion") -> Dict[str, Any]:
        """
        Quick log food with AI nutritional analysis
        Returns: Complete consumption record with analysis
        """
        try:
            print(f"[ConsumptionTracker] Quick logging food for user {user_id}: {food_name} ({portion})")
            
            # Get AI nutritional analysis
            analysis = await self._get_ai_nutrition_analysis(food_name, portion)
            
            # Create consumption record
            record = await self._create_consumption_record(user_id, analysis)
            
            print(f"[ConsumptionTracker] Successfully logged food with record ID: {record['id']}")
            
            return {
                "success": True,
                "record_id": record["id"],
                "food_name": analysis["food_name"],
                "nutritional_summary": {
                    "calories": analysis["nutritional_info"]["calories"],
                    "carbohydrates": analysis["nutritional_info"]["carbohydrates"],
                    "protein": analysis["nutritional_info"]["protein"],
                    "fat": analysis["nutritional_info"]["fat"]
                },
                "diabetes_rating": analysis["medical_rating"]["diabetes_suitability"],
                "message": f"Successfully logged {analysis['food_name']}"
            }
            
        except Exception as e:
            print(f"[ConsumptionTracker] Error in quick_log_food: {str(e)}")
            print(f"[ConsumptionTracker] Traceback: {traceback.format_exc()}")
            raise Exception(f"Failed to log food: {str(e)}")
    
    async def _get_ai_nutrition_analysis(self, food_name: str, portion: str) -> Dict[str, Any]:
        """Get comprehensive AI nutritional analysis"""
        
        prompt = f"""
        Analyze the food item: {food_name} ({portion})
        
        Provide a comprehensive JSON response with this EXACT structure:
        {{
            "food_name": "{food_name}",
            "estimated_portion": "{portion}",
            "nutritional_info": {{
                "calories": <number>,
                "carbohydrates": <number>,
                "protein": <number>,
                "fat": <number>,
                "fiber": <number>,
                "sugar": <number>,
                "sodium": <number>
            }},
            "medical_rating": {{
                "diabetes_suitability": "high/medium/low",
                "glycemic_impact": "low/medium/high",
                "recommended_frequency": "daily/weekly/occasional/avoid",
                "portion_recommendation": "appropriate/reduce/increase"
            }},
            "analysis_notes": "Brief explanation of nutritional value and diabetes considerations"
        }}
        
        Base estimates on standard nutritional databases. Be accurate and conservative with diabetes ratings.
        Only return valid JSON, no other text.
        """
        
        # Fallback data
        fallback_data = {
            "food_name": food_name,
            "estimated_portion": portion,
            "nutritional_info": {
                "calories": 200,
                "carbohydrates": 25,
                "protein": 10,
                "fat": 8,
                "fiber": 3,
                "sugar": 5,
                "sodium": 300
            },
            "medical_rating": {
                "diabetes_suitability": "medium",
                "glycemic_impact": "medium",
                "recommended_frequency": "weekly",
                "portion_recommendation": "appropriate"
            },
            "analysis_notes": f"Nutritional estimate for {food_name}. Consult healthcare provider for personalized advice."
        }
        
        try:
            print(f"[ConsumptionTracker] Getting AI analysis for {food_name}")
            
            # Import the robust wrapper from main
            from main import robust_openai_call
            
            api_result = await robust_openai_call(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a nutrition analysis expert specializing in diabetes management. Provide accurate nutritional estimates and diabetes-appropriate recommendations."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=500,
                temperature=0.3,
                max_retries=3,
                timeout=30,
                context="consumption_analysis"
            )
            
            if api_result["success"]:
                analysis_text = api_result["content"]
                print(f"[ConsumptionTracker] AI response: {analysis_text}")
            else:
                print(f"[ConsumptionTracker] OpenAI failed: {api_result['error']}. Using fallback.")
                return fallback_data
            
            # Parse JSON response
            try:
                start_idx = analysis_text.find('{')
                end_idx = analysis_text.rfind('}') + 1
                json_str = analysis_text[start_idx:end_idx]
                analysis_data = json.loads(json_str)
                
                # Validate required fields
                required_fields = ["food_name", "estimated_portion", "nutritional_info", "medical_rating"]
                if all(field in analysis_data for field in required_fields):
                    print(f"[ConsumptionTracker] Successfully parsed AI analysis")
                    return analysis_data
                else:
                    print(f"[ConsumptionTracker] Missing required fields, using fallback")
                    return fallback_data
                    
            except (json.JSONDecodeError, ValueError) as parse_error:
                print(f"[ConsumptionTracker] JSON parsing error: {str(parse_error)}")
                return fallback_data
                
        except Exception as ai_error:
            print(f"[ConsumptionTracker] AI API error: {str(ai_error)}")
            return fallback_data
    
    async def _create_consumption_record(self, user_id: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create and save consumption record to database"""
        
        # Generate unique record ID
        timestamp = datetime.utcnow()
        record_id = f"consumption_{user_id}_{int(timestamp.timestamp() * 1000)}"
        
        # Create standardized consumption record
        record = {
            "type": "consumption_record",
            "id": record_id,
            "session_id": record_id,  # Partition key
            "user_id": user_id,
            "timestamp": timestamp.isoformat(),
            "logged_at": timestamp,
            
            # Food information
            "food_name": analysis["food_name"],
            "estimated_portion": analysis["estimated_portion"],
            
            # Nutritional information (standardized structure)
            "nutritional_info": {
                "calories": float(analysis["nutritional_info"].get("calories", 0)),
                "carbohydrates": float(analysis["nutritional_info"].get("carbohydrates", 0)),
                "protein": float(analysis["nutritional_info"].get("protein", 0)),
                "fat": float(analysis["nutritional_info"].get("fat", 0)),
                "fiber": float(analysis["nutritional_info"].get("fiber", 0)),
                "sugar": float(analysis["nutritional_info"].get("sugar", 0)),
                "sodium": float(analysis["nutritional_info"].get("sodium", 0))
            },
            
            # Medical rating
            "medical_rating": analysis["medical_rating"],
            
            # Analysis notes
            "image_analysis": analysis["analysis_notes"],
            "image_url": None,  # No image for quick log
            
            # Meal type determination
            "meal_type": self._determine_meal_type(timestamp)
        }
        
        print(f"[ConsumptionTracker] Creating record: {record}")
        
        # Save to database
        result = self.container.upsert_item(body=record)
        print(f"[ConsumptionTracker] Saved record with ID: {result['id']}")
        
        return result
    
    def _determine_meal_type(self, timestamp: datetime) -> str:
        """Determine meal type based on time"""
        try:
            # Use local time for meal type determination
            # Default to US Eastern timezone as a reasonable assumption
            import pytz
            eastern = pytz.timezone('America/New_York')
            utc_time = timestamp.replace(tzinfo=pytz.utc)
            local_time = utc_time.astimezone(eastern)
            hour = local_time.hour
        except:
            # Fallback to UTC if timezone conversion fails
            hour = timestamp.hour
        
        if 5 <= hour < 11:
            return "breakfast"
        elif 11 <= hour < 16:
            return "lunch"
        elif 16 <= hour < 22:
            return "dinner"
        else:
            return "snack"
    
    async def get_consumption_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's consumption history with standardized format"""
        try:
            print(f"[ConsumptionTracker] Getting consumption history for user {user_id}")
            
            query = f"""
            SELECT * FROM c 
            WHERE c.type = 'consumption_record' 
            AND c.user_id = '{user_id}' 
            ORDER BY c.timestamp DESC
            """
            
            records = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            # Apply limit
            limited_records = records[:limit] if limit else records
            
            print(f"[ConsumptionTracker] Retrieved {len(limited_records)} consumption records")
            
            return limited_records
            
        except Exception as e:
            print(f"[ConsumptionTracker] Error getting consumption history: {str(e)}")
            print(f"[ConsumptionTracker] Traceback: {traceback.format_exc()}")
            raise Exception(f"Failed to get consumption history: {str(e)}")
    
    async def get_consumption_analytics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive consumption analytics"""
        try:
            print(f"[ConsumptionTracker] Getting analytics for user {user_id} for {days} days")
            
            # Get consumption records for the period
            threshold_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            query = f"""
            SELECT * FROM c 
            WHERE c.type = 'consumption_record' 
            AND c.user_id = '{user_id}' 
            AND c.timestamp >= '{threshold_date}' 
            ORDER BY c.timestamp DESC
            """
            
            records = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            if not records:
                return self._empty_analytics_response(threshold_date)
            
            # Process analytics
            analytics = self._process_consumption_analytics(records, days, threshold_date)
            
            print(f"[ConsumptionTracker] Generated analytics for {len(records)} records")
            
            return analytics
            
        except Exception as e:
            print(f"[ConsumptionTracker] Error getting analytics: {str(e)}")
            print(f"[ConsumptionTracker] Traceback: {traceback.format_exc()}")
            raise Exception(f"Failed to get consumption analytics: {str(e)}")
    
    def _empty_analytics_response(self, start_date: str) -> Dict[str, Any]:
        """Return empty analytics structure"""
        return {
            "total_meals": 0,
            "date_range": {
                "start_date": start_date,
                "end_date": datetime.utcnow().isoformat()
            },
            "daily_averages": {
                "calories": 0,
                "protein": 0,
                "carbohydrates": 0,
                "fat": 0,
                "fiber": 0,
                "sugar": 0,
                "sodium": 0
            },
            "weekly_trends": {
                "calories": [0] * 7,
                "protein": [0] * 7,
                "carbohydrates": [0] * 7,
                "fat": [0] * 7
            },
            "meal_distribution": {
                "breakfast": 0,
                "lunch": 0,
                "dinner": 0,
                "snack": 0
            },
            "top_foods": [],
            "adherence_stats": {
                "diabetes_suitable_percentage": 0,
                "calorie_goal_adherence": 0,
                "protein_goal_adherence": 0,
                "carb_goal_adherence": 0
            },
            "daily_nutrition_history": []
        }
    
    def _process_consumption_analytics(self, records: List[Dict], days: int, start_date: str) -> Dict[str, Any]:
        """Process consumption records into comprehensive analytics"""
        
        # Initialize tracking
        daily_totals = defaultdict(lambda: {
            "calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0,
            "fiber": 0, "sugar": 0, "sodium": 0, "meals_count": 0
        })
        food_frequency = defaultdict(lambda: {"frequency": 0, "total_calories": 0})
        meal_type_counts = {"breakfast": 0, "lunch": 0, "dinner": 0, "snack": 0}
        diabetes_suitable_count = 0
        
        # Daily goals
        daily_goals = {
            "calories": 2000,
            "protein": 100,
            "carbohydrates": 250,
            "fat": 70
        }
        
        # Process each record
        for record in records:
            nutritional_info = record.get("nutritional_info", {})
            medical_rating = record.get("medical_rating", {})
            food_name = record.get("food_name", "Unknown Food")
            timestamp = record.get("timestamp", "")
            meal_type = record.get("meal_type", "snack")
            
            # Extract date
            try:
                record_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).date().isoformat()
            except:
                record_date = datetime.utcnow().date().isoformat()
            
            # Extract nutrition values (standardized)
            calories = nutritional_info.get("calories", 0)
            protein = nutritional_info.get("protein", 0)
            carbohydrates = nutritional_info.get("carbohydrates", 0)
            fat = nutritional_info.get("fat", 0)
            fiber = nutritional_info.get("fiber", 0)
            sugar = nutritional_info.get("sugar", 0)
            sodium = nutritional_info.get("sodium", 0)
            
            # Update daily totals
            daily_totals[record_date]["calories"] += calories
            daily_totals[record_date]["protein"] += protein
            daily_totals[record_date]["carbohydrates"] += carbohydrates
            daily_totals[record_date]["fat"] += fat
            daily_totals[record_date]["fiber"] += fiber
            daily_totals[record_date]["sugar"] += sugar
            daily_totals[record_date]["sodium"] += sodium
            daily_totals[record_date]["meals_count"] += 1
            
            # Track food frequency
            food_frequency[food_name]["frequency"] += 1
            food_frequency[food_name]["total_calories"] += calories
            
            # Count meal types
            meal_type_counts[meal_type] += 1
            
            # Check diabetes suitability
            diabetes_suitability = medical_rating.get("diabetes_suitability", "").lower()
            if diabetes_suitability in ["high", "good", "suitable", "excellent"]:
                diabetes_suitable_count += 1
        
        # Calculate totals and averages
        total_records = len(records)
        total_calories = sum(day["calories"] for day in daily_totals.values())
        total_protein = sum(day["protein"] for day in daily_totals.values())
        total_carbohydrates = sum(day["carbohydrates"] for day in daily_totals.values())
        total_fat = sum(day["fat"] for day in daily_totals.values())
        total_fiber = sum(day["fiber"] for day in daily_totals.values())
        total_sugar = sum(day["sugar"] for day in daily_totals.values())
        total_sodium = sum(day["sodium"] for day in daily_totals.values())
        
        avg_daily_calories = total_calories / days if days > 0 else 0
        avg_daily_protein = total_protein / days if days > 0 else 0
        avg_daily_carbohydrates = total_carbohydrates / days if days > 0 else 0
        avg_daily_fat = total_fat / days if days > 0 else 0
        
        # Calculate adherence
        calorie_adherence = min(100, (avg_daily_calories / daily_goals["calories"]) * 100) if daily_goals["calories"] > 0 else 0
        protein_adherence = min(100, (avg_daily_protein / daily_goals["protein"]) * 100) if daily_goals["protein"] > 0 else 0
        carb_adherence = min(100, (avg_daily_carbohydrates / daily_goals["carbohydrates"]) * 100) if daily_goals["carbohydrates"] > 0 else 0
        
        # Prepare top foods
        top_foods = [
            {
                "food": food,
                "frequency": data["frequency"],
                "total_calories": data["total_calories"]
            }
            for food, data in sorted(food_frequency.items(), key=lambda x: x[1]["frequency"], reverse=True)
        ][:10]
        
        # Prepare daily nutrition history
        daily_nutrition_history = []
        for date_str, totals in sorted(daily_totals.items()):
            daily_nutrition_history.append({
                "date": date_str,
                "calories": totals["calories"],
                "protein": totals["protein"],
                "carbohydrates": totals["carbohydrates"],
                "fat": totals["fat"],
                "meals_count": totals["meals_count"]
            })
        
        # Calculate weekly trends (last 7 days)
        recent_days = sorted(daily_totals.items())[-7:]
        weekly_trends = {
            "calories": [day[1]["calories"] for day in recent_days] + [0] * (7 - len(recent_days)),
            "protein": [day[1]["protein"] for day in recent_days] + [0] * (7 - len(recent_days)),
            "carbohydrates": [day[1]["carbohydrates"] for day in recent_days] + [0] * (7 - len(recent_days)),
            "fat": [day[1]["fat"] for day in recent_days] + [0] * (7 - len(recent_days))
        }
        
        return {
            "total_meals": total_records,
            "date_range": {
                "start_date": start_date,
                "end_date": datetime.utcnow().isoformat()
            },
            "daily_averages": {
                "calories": avg_daily_calories,
                "protein": avg_daily_protein,
                "carbohydrates": avg_daily_carbohydrates,
                "fat": avg_daily_fat,
                "fiber": total_fiber / days if days > 0 else 0,
                "sugar": total_sugar / days if days > 0 else 0,
                "sodium": total_sodium / days if days > 0 else 0
            },
            "weekly_trends": weekly_trends,
            "meal_distribution": meal_type_counts,
            "top_foods": top_foods,
            "adherence_stats": {
                "diabetes_suitable_percentage": (diabetes_suitable_count / total_records * 100) if total_records > 0 else 0,
                "calorie_goal_adherence": calorie_adherence,
                "protein_goal_adherence": protein_adherence,
                "carb_goal_adherence": carb_adherence
            },
            "daily_nutrition_history": daily_nutrition_history
        }

# Global instance
consumption_tracker = ConsumptionTracker() 