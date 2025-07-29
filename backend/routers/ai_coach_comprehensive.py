from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from models import User
from routers.auth import get_current_user
from database import (
    get_user_consumption_history, get_user_meal_plans, get_consumption_analytics,
    log_meal_suggestion, user_container, interactions_container
)
from services.openai_service import robust_openai_call, get_openai_client
from services.coaching_system import calculate_consistency_streak
from utils import filter_today_records
from datetime import datetime, timedelta
import os
import json
import re
import logging

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/coach/meal-suggestion")
async def get_meal_suggestion(
    request: dict,
    current_user: User = Depends(get_current_user)
):
    """
    🧠 COMPREHENSIVE AI COACH - Central intelligence with full access to user data
    Provides intelligent responses based on consumption history, meal plans, progress, and health data
    """
    try:
        print(f"[AI_COACH] Processing query for user: {current_user['email']}")
        
        # Handle both simple query format and detailed format
        query = request.get("query", "").strip()
        if not query:
            return {
                "success": False,
                "error": "Please provide a question or query"
            }
        
        # 🔍 COMPREHENSIVE DATA GATHERING - Get ALL user context
        print("[AI_COACH] Gathering comprehensive user data...")
        
        # 1. Get user profile with all health information
        try:
            user_profile_query = f"SELECT * FROM c WHERE c.type = 'user' AND c.id = '{current_user['email']}'"
            user_profiles = list(user_container.query_items(query=user_profile_query, enable_cross_partition_query=True))
            user_profile = user_profiles[0].get("profile", {}) if user_profiles else {}
        except Exception as e:
            print(f"[AI_COACH] Error fetching user profile: {e}")
            user_profile = {}
        
        # 2. Get comprehensive consumption history (last 30 days) - INCREASED LIMIT to ensure we get ALL today's meals
        try:
            consumption_history = await get_user_consumption_history(current_user["email"], limit=300)
            # Filter to last 30 days for comprehensive analysis
            from datetime import datetime, timedelta
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_consumption = [
                record for record in consumption_history 
                if datetime.fromisoformat(record.get("timestamp", "").replace("Z", "+00:00")) > thirty_days_ago
            ]
        except Exception as e:
            print(f"[AI_COACH] Error fetching consumption history: {e}")
            recent_consumption = []
        
        # 3. Get today's consumption for daily analysis - USE PROPER TIMEZONE-AWARE FILTERING
        try:
            # Use the new timezone-aware filtering function that resets at midnight
            user_timezone = user_profile.get("timezone", "UTC")
            today_consumption = filter_today_records(recent_consumption, user_timezone=user_timezone)
            
            print(f"[AI_COACH] Found {len(today_consumption)} meals for today using timezone-aware filtering")
            
        except Exception as e:
            print(f"[AI_COACH] Error filtering today's consumption: {e}")
            today_consumption = []
        
        # 4. Get meal plans history
        try:
            meal_plans = await get_user_meal_plans(current_user["email"])
            latest_meal_plan = meal_plans[0] if meal_plans else None
        except Exception as e:
            print(f"[AI_COACH] Error fetching meal plans: {e}")
            meal_plans = []
            latest_meal_plan = None
        
        # 5. Get consumption analytics for trends
        try:
            # Get user's timezone for analytics
            user_timezone = current_user.get("profile", {}).get("timezone", "UTC")
            weekly_analytics = await get_consumption_analytics(current_user["email"], 7, user_timezone)
            monthly_analytics = await get_consumption_analytics(current_user["email"], 30, user_timezone)
        except Exception as e:
            print(f"[AI_COACH] Error fetching analytics: {e}")
            weekly_analytics = {}
            monthly_analytics = {}
        
        # 6. Get progress data - import here to avoid circular imports
        try:
            from services.coaching_system import get_consumption_progress_data
            progress_data = await get_consumption_progress_data(current_user)
        except Exception as e:
            print(f"[AI_COACH] Error fetching progress data: {e}")
            progress_data = {}
        
        # 📊 COMPREHENSIVE DATA ANALYSIS
        print("[AI_COACH] Analyzing comprehensive user data...")
        
        # Calculate today's nutritional totals
        today_totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0, "sugar": 0, "sodium": 0}
        for record in today_consumption:
            nutritional_info = record.get("nutritional_info", {})
            today_totals["calories"] += nutritional_info.get("calories", 0)
            today_totals["protein"] += nutritional_info.get("protein", 0)
            today_totals["carbs"] += nutritional_info.get("carbohydrates", 0)
            today_totals["fat"] += nutritional_info.get("fat", 0)
            today_totals["fiber"] += nutritional_info.get("fiber", 0)
            today_totals["sugar"] += nutritional_info.get("sugar", 0)
            today_totals["sodium"] += nutritional_info.get("sodium", 0)
        
        # Debug logging for today's consumption
        print(f"[AI_COACH_DEBUG] Found {len(today_consumption)} meals for today")
        print(f"[AI_COACH_DEBUG] Today's totals: {today_totals}")
        if today_consumption:
            print(f"[AI_COACH_DEBUG] Today's meals: {[record.get('food_name') for record in today_consumption]}")
        else:
            print(f"[AI_COACH_DEBUG] No meals found for today - recent_consumption had {len(recent_consumption)} records")
        
        # Calculate weekly averages
        weekly_totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "meals": 0}
        for record in recent_consumption[-21:]:  # Last 3 weeks for better average
            nutritional_info = record.get("nutritional_info", {})
            weekly_totals["calories"] += nutritional_info.get("calories", 0)
            weekly_totals["protein"] += nutritional_info.get("protein", 0)
            weekly_totals["carbs"] += nutritional_info.get("carbohydrates", 0)
            weekly_totals["fat"] += nutritional_info.get("fat", 0)
            weekly_totals["meals"] += 1
        
        weekly_averages = {}
        if weekly_totals["meals"] > 0:
            days_logged = max(1, weekly_totals["meals"] / 3)  # Estimate days
            weekly_averages = {
                "calories": weekly_totals["calories"] / days_logged,
                "protein": weekly_totals["protein"] / days_logged,
                "carbs": weekly_totals["carbs"] / days_logged,
                "fat": weekly_totals["fat"] / days_logged
            }
        
        # Get user's goals and health info
        calorie_goal = 2000  # Default
        macro_goals = {"protein": 100, "carbs": 250, "fat": 70}
        
        if user_profile.get("calorieTarget"):
            try:
                calorie_goal = int(user_profile["calorieTarget"])
            except:
                pass
        elif latest_meal_plan and latest_meal_plan.get("dailyCalories"):
            calorie_goal = latest_meal_plan["dailyCalories"]
        
        # Health conditions and dietary info
        health_conditions = user_profile.get("medicalConditions", []) or user_profile.get("medical_conditions", [])
        dietary_restrictions = user_profile.get("dietaryRestrictions", []) or user_profile.get("dietary_restrictions", [])
        allergies = user_profile.get("allergies", [])
        medications = user_profile.get("currentMedications", [])
        
        # Calculate diabetes adherence and health metrics
        diabetes_suitable_count = 0
        high_carb_meals = 0
        high_sugar_meals = 0
        high_sodium_meals = 0
        
        for record in recent_consumption:
            medical_rating = record.get("medical_rating", {})
            nutritional_info = record.get("nutritional_info", {})
            
            # Diabetes suitability
            diabetes_suitability = medical_rating.get("diabetes_suitability", "").lower()
            if diabetes_suitability in ["high", "good", "suitable"]:
                diabetes_suitable_count += 1
            
            # Track concerning patterns
            if nutritional_info.get("carbohydrates", 0) > 45:
                high_carb_meals += 1
            if nutritional_info.get("sugar", 0) > 15:
                high_sugar_meals += 1
            if nutritional_info.get("sodium", 0) > 800:
                high_sodium_meals += 1
        
        total_recent_meals = len(recent_consumption)
        diabetes_adherence = (diabetes_suitable_count / total_recent_meals * 100) if total_recent_meals > 0 else 0
        
        # Calculate consistency streak
        consistency_streak = calculate_consistency_streak(recent_consumption, user_profile.get("timezone", "UTC"))
        
        # Analyze meal timing patterns
        meal_times = {}
        for record in recent_consumption:
            meal_type = record.get("meal_type", "unknown")
            timestamp = record.get("timestamp", "")
            try:
                hour = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).hour
                if meal_type not in meal_times:
                    meal_times[meal_type] = []
                meal_times[meal_type].append(hour)
            except:
                pass
        
        # Get recent meal names for pattern analysis
        recent_meals = [record.get("food_name", "Unknown") for record in recent_consumption[:10]]
        today_meals = [record.get("food_name", "Unknown") for record in today_consumption]
        
        # 🤖 BUILD COMPREHENSIVE AI COACH SYSTEM PROMPT
        print("[AI_COACH] Building comprehensive AI response...")
        
        system_prompt = f"""You are an advanced AI Diet Coach and Diabetes Management Specialist with FULL ACCESS to the user's comprehensive health data. You are their personal nutrition expert, meal planner, and health companion.

🎯 **YOUR ROLE**: You are the central intelligence of their diabetes management system with complete visibility into their eating patterns, progress, and health journey.

👤 **USER PROFILE**:
- Name: {user_profile.get('name', 'Not specified')}
- Age: {user_profile.get('age', 'Not specified')} | Gender: {user_profile.get('gender', 'Not specified')}
- Weight: {user_profile.get('weight', 'Not specified')} kg | Height: {user_profile.get('height', 'Not specified')} cm
- BMI: {user_profile.get('bmi', 'Not calculated')}
- Blood Pressure: {user_profile.get('systolicBP', 'Not specified')}/{user_profile.get('diastolicBP', 'Not specified')} mmHg

🏥 **HEALTH CONDITIONS & MEDICATIONS**:
- Medical Conditions: {', '.join(health_conditions) if health_conditions else 'None specified'}
- Current Medications: {', '.join(medications) if medications else 'None specified'}
- Allergies: {', '.join(allergies) if allergies else 'None specified'}
- Dietary Features: {', '.join(user_profile.get('dietaryFeatures', []) or user_profile.get('diet_features', [])) if user_profile.get('dietaryFeatures') or user_profile.get('diet_features') else 'None specified'}
- Dietary Restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None specified'}

🎯 **DAILY GOALS & TODAY'S PROGRESS** ({datetime.utcnow().strftime('%B %d, %Y')}):
- Calorie Goal: {calorie_goal} kcal | Today: {today_totals['calories']:.0f} kcal ({today_totals['calories']/calorie_goal*100:.1f}%)
- Protein Goal: {macro_goals['protein']}g | Today: {today_totals['protein']:.1f}g ({today_totals['protein']/macro_goals['protein']*100:.1f}%)
- Carbs: {today_totals['carbs']:.1f}g | Fat: {today_totals['fat']:.1f}g
- Fiber: {today_totals['fiber']:.1f}g | Sugar: {today_totals['sugar']:.1f}g | Sodium: {today_totals['sodium']:.0f}mg
- Meals logged today: {len(today_consumption)}

📊 **RECENT PERFORMANCE ANALYSIS** (Last 30 days):
- Total meals logged: {total_recent_meals}
- Diabetes-suitable meals: {diabetes_suitable_count}/{total_recent_meals} ({diabetes_adherence:.1f}%)
- High-carb meals (>45g): {high_carb_meals} | High-sugar meals (>15g): {high_sugar_meals}
- High-sodium meals (>800mg): {high_sodium_meals}
- Consistency streak: {consistency_streak} days
- Weekly averages: {weekly_averages.get('calories', 0):.0f} cal, {weekly_averages.get('protein', 0):.1f}g protein

🍽️ **MEAL PATTERNS & HISTORY**:
- Today's meals: {', '.join(today_meals) if today_meals else 'No meals logged today'}
- Recent meals: {', '.join(recent_meals[:5]) if recent_meals else 'No recent meals'}
- Meal timing patterns: {meal_times}

📋 **CURRENT MEAL PLAN STATUS**:
- Has active meal plan: {'Yes' if latest_meal_plan else 'No'}
- Latest meal plan date: {latest_meal_plan.get('created_at', 'None')[:10] if latest_meal_plan else 'None'}
- Total meal plans created: {len(meal_plans)}

🎯 **HEALTH INSIGHTS**:
- Diabetes adherence trend: {diabetes_adherence:.1f}% (Target: >80%)
- Carb management: {'Good' if high_carb_meals < total_recent_meals * 0.3 else 'Needs attention'}
- Sugar control: {'Good' if high_sugar_meals < total_recent_meals * 0.2 else 'Needs attention'}
- Sodium management: {'Good' if high_sodium_meals < total_recent_meals * 0.3 else 'Needs attention'}

**CRITICAL FORMATTING INSTRUCTIONS**:
1. **NO MARKDOWN**: Do not use any markdown formatting (no #, ##, ###, *, **, _, __, ---, etc.)
2. **PLAIN TEXT ONLY**: Return clean, readable plain text that displays well in a web interface
3. **USE EMOJIS**: Use emojis for visual appeal instead of markdown headers
4. **LINE BREAKS**: Use simple line breaks for structure, not markdown syntax
5. **LISTS**: Use simple bullet points (•) or numbers, not markdown list syntax
6. **EMPHASIS**: Use CAPITAL LETTERS or emojis for emphasis, not markdown bold/italic

**RESPONSE INSTRUCTIONS**:
1. **Be Comprehensive**: Use ALL the data above to provide intelligent, personalized responses
2. **Be Specific**: Reference actual numbers, patterns, and trends from their data
3. **Be Actionable**: Provide specific recommendations based on their current status
4. **Be Encouraging**: Acknowledge their progress and efforts
5. **Be Health-Focused**: Always consider their medical conditions in recommendations
6. **Be Contextual**: Consider their meal timing, recent choices, and patterns
7. **Be Readable**: Format for easy reading in a web interface without markdown

Answer their question with the full context of their health journey, current progress, and specific data patterns. Use plain text formatting that will display beautifully in a web interface."""

        user_prompt = f"""User's Question: "{query}"
Please provide a comprehensive, personalized response that:
- Uses their specific consumption data and patterns
- References their actual progress numbers
- Considers their health conditions and goals
- Provides actionable recommendations
- Acknowledges their current status and trends

Be conversational but informative, like a knowledgeable nutrition coach who knows them well."""

        # 🚀 GET AI RESPONSE FROM AZURE OPENAI
        try:
            api_result = await robust_openai_call(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
                max_retries=3,
                timeout=60,
                context="meal_suggestion"
            )
            
            if api_result["success"]:
                ai_response = api_result["content"].strip()
            else:
                print(f"[AI_COACH] OpenAI failed: {api_result['error']}")
                ai_response = f"I'm having trouble accessing my AI capabilities right now, but I can see you have {len(today_consumption)} meals logged today with {today_totals['calories']:.0f} calories. Your diabetes adherence is at {diabetes_adherence:.1f}%. Please try your question again in a moment."
            
            # 🧹 CLEAN MARKDOWN FORMATTING for better frontend display
            import re
            # Remove markdown headers
            ai_response = re.sub(r'^#{1,6}\s+', '', ai_response, flags=re.MULTILINE)
            # Remove markdown bold/italic
            ai_response = re.sub(r'\*\*(.*?)\*\*', r'\1', ai_response)
            ai_response = re.sub(r'\*(.*?)\*', r'\1', ai_response)
            ai_response = re.sub(r'__(.*?)__', r'\1', ai_response)
            ai_response = re.sub(r'_(.*?)_', r'\1', ai_response)
            # Remove markdown horizontal rules
            ai_response = re.sub(r'^---+$', '', ai_response, flags=re.MULTILINE)
            # Clean up multiple line breaks
            ai_response = re.sub(r'\n{3,}', '\n\n', ai_response)
            
        except Exception as e:
            print(f"[AI_COACH] Error getting AI response: {e}")
            ai_response = f"I'm having trouble accessing my AI capabilities right now, but I can see you have {len(today_consumption)} meals logged today with {today_totals['calories']:.0f} calories. Your diabetes adherence is at {diabetes_adherence:.1f}%. Please try your question again in a moment."
        
        # 📝 LOG THE INTERACTION
        try:
            await log_meal_suggestion(
                user_id=current_user["email"],
                meal_type="ai_coach_query",
                suggestion=ai_response,
                context={
                    "query": query,
                    "today_totals": today_totals,
                    "diabetes_adherence": diabetes_adherence,
                    "meals_logged": len(today_consumption),
                    "consistency_streak": consistency_streak
                }
            )
        except Exception as e:
            print(f"[AI_COACH] Error logging interaction: {e}")
        
        print(f"[AI_COACH] Successfully generated comprehensive response for user")
        
        return {
            "success": True,
            "suggestion": ai_response,
            "response": ai_response,  # Frontend compatibility
            "context": {
                "comprehensive_analysis": True,
                "data_sources": [
                    "user_profile", "consumption_history", "meal_plans", 
                    "progress_tracking", "health_conditions", "dietary_patterns"
                ],
                "today_meals": len(today_consumption),
                "total_calories_today": today_totals["calories"],
                "diabetes_adherence": diabetes_adherence,
                "consistency_streak": consistency_streak,
                "has_meal_plan": latest_meal_plan is not None,
                "analysis_period": "30_days",
                "personalized": True,
                "health_focused": True
            }
        }
        
    except Exception as e:
        print(f"[AI_COACH] Critical error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": "I'm experiencing technical difficulties. Please try again in a moment.",
            "suggestion": "I'm currently unable to access your comprehensive health data. Please try again.",
            "response": "I'm currently unable to access your comprehensive health data. Please try again."
        }

async def get_ai_suggestion(prompt: str) -> str:
    """Get meal suggestion from Azure OpenAI"""
    try:
        # Call Azure OpenAI API
        response = get_openai_client().chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            messages=[
                {"role": "system", "content": "You are a knowledgeable nutritionist and meal planner. Provide specific, healthy meal suggestions that consider dietary restrictions and nutritional needs."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error getting AI suggestion: {str(e)}")
        return None

async def log_meal_suggestion(user_id: str, meal_type: str, suggestion: str, context: dict):
    """Log meal suggestion for future reference"""
    try:
        suggestion_log = {
            "user_id": user_id,
            "meal_type": meal_type,
            "suggestion": suggestion,
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Save to database - use interactions_container for consistency
        interactions_container.create_item(body=suggestion_log)
    except Exception as e:
        logger.error(f"Error logging meal suggestion: {str(e)}")
        # Non-critical error, don't raise

def build_meal_suggestion_prompt(
    meal_type: str,
    remaining_calories: int,
    meal_patterns: dict,
    dietary_restrictions: list,
    health_conditions: list,
    context: dict,
    preferences: str
) -> str:
    """
    Build a context-aware prompt for meal suggestions.
    """
    query_context = context.get("query_context", "")
    current_hour = context.get("current_hour", 0)
    is_late_meal = context.get("is_late_meal", False)
    todays_meals = context.get("todays_meals", [])
    
    prompt = f"""Based on the user's query "{query_context}", suggest a {meal_type} that:
    1. Fits within {remaining_calories} remaining calories
    2. Considers their dietary restrictions: {', '.join(dietary_restrictions)}
    3. Is appropriate for their health conditions: {', '.join(health_conditions)}
    4. Avoids repetition with today's meals: {', '.join([m['name'] for m in todays_meals])}
    5. {"Provides a lighter option since it's a late meal" if is_late_meal else "Provides a satisfying portion"}
    6. Matches their usual meal patterns for {meal_type}
    7. {preferences if preferences else ""}
    
    Include:
    - Specific ingredients and portions
    - Brief preparation instructions
    - Nutritional breakdown
    - Health benefits
    - Any relevant tips or modifications
    """
    
    return prompt

def analyze_meal_patterns(meal_history: list) -> dict:
    """
    Analyze user's meal patterns to provide more personalized suggestions.
    """
    patterns = {
        "breakfast": [],
        "lunch": [],
        "dinner": [],
        "snack": []
    }
    
    for meal in meal_history:
        if meal["meal_type"] in patterns:
            patterns[meal["meal_type"]].append({
                "name": meal["food_name"],
                "frequency": 1,  # Can be updated for repeated meals
                "calories": meal["nutritional_info"]["calories"]
            })
    
    return patterns 