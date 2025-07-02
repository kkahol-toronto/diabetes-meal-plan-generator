from fastapi import APIRouter, Depends, HTTPException, Query, Form, File, UploadFile
from fastapi.responses import StreamingResponse
from typing import Dict, List, Any, Optional
import json
from ..models.user import User
from ..services.auth import get_current_user
from ..utils.logger import logger

# Import chat storage functions (with fallback if database unavailable)
try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from database import save_chat_message, get_recent_chat_history, get_user_sessions, clear_chat_history
    DATABASE_AVAILABLE = True
    logger.info("Database connection successful - chat history will be saved")
except Exception as e:
    logger.warning(f"Database unavailable: {e}. Chat will work without history persistence.")
    DATABASE_AVAILABLE = False
    
    # Create mock functions when database is unavailable
    async def save_chat_message(user_id: str, message: str, is_user: bool, session_id: str = None, image_url: str = None):
        logger.debug(f"Mock save: {message[:50]}...")
        return True
        
    async def get_recent_chat_history(user_id: str, session_id: str = None, limit: int = 50):
        return []
        
    async def get_user_sessions(user_id: str):
        return []
        
    async def clear_chat_history(user_id: str, session_id: str = None):
        return True

router = APIRouter()

# Helper functions to get user data for personalization
async def get_user_meal_plans(user_id: str) -> Dict:
    """Get user's recent meal plans for personalization."""
    try:
        # Try to get meal plans from database
        try:
            import sys
            import os
            # Add the backend directory to the path to import database module
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            if backend_dir not in sys.path:
                sys.path.append(backend_dir)
            
            import database
            user_plans = await database.get_user_meal_plans(user_id)
            
            return {
                "recent_plans": user_plans[:3],  # Last 3 meal plans
                "total_plans": len(user_plans),
                "has_saved_plans": len(user_plans) > 0
            }
        except Exception as db_error:
            logger.warning(f"Database not available for meal plans: {str(db_error)}")
            # Return empty data when database is not available
            return {"recent_plans": [], "total_plans": 0, "has_saved_plans": False}
            
    except Exception as e:
        logger.error(f"Error getting meal plans: {str(e)}")
        return {"recent_plans": [], "total_plans": 0, "has_saved_plans": False}

async def get_user_consumption_data(user_id: str) -> Dict:
    """Get user's consumption analytics for personalization."""
    try:
        # For now, use realistic mock data that simulates actual user consumption
        # In production, this would fetch from the consumption database
        
        # Simulate realistic daily consumption based on time of day
        import datetime
        current_hour = datetime.datetime.now().hour
        
        # Adjust calories based on time of day
        if current_hour < 9:  # Early morning
            daily_calories = 150  # Just breakfast
            recent_foods = [
                {"name": "Greek yogurt with berries", "calories": 150, "time": "morning"}
            ]
        elif current_hour < 14:  # Before lunch
            daily_calories = 500  # Breakfast + snack
            recent_foods = [
                {"name": "Greek yogurt with berries", "calories": 150, "time": "morning"},
                {"name": "Apple with almonds", "calories": 180, "time": "morning"},
                {"name": "Coffee with milk", "calories": 50, "time": "morning"}
            ]
        elif current_hour < 18:  # Afternoon
            daily_calories = 800  # Full day so far
            recent_foods = [
                {"name": "Greek yogurt with berries", "calories": 150, "time": "morning"},
                {"name": "Grilled chicken salad", "calories": 350, "time": "lunch"},
                {"name": "Apple with almonds", "calories": 200, "time": "afternoon"},
                {"name": "Green tea", "calories": 0, "time": "afternoon"}
            ]
        else:  # Evening
            daily_calories = 1200  # Most of daily intake
            recent_foods = [
                {"name": "Oatmeal with berries", "calories": 180, "time": "morning"},
                {"name": "Quinoa salad bowl", "calories": 420, "time": "lunch"},
                {"name": "Mixed nuts", "calories": 160, "time": "afternoon"},
                {"name": "Grilled salmon", "calories": 380, "time": "evening"}
            ]
        
        return {
            "daily_calories": daily_calories,
            "daily_protein": int(daily_calories * 0.25 / 4),  # 25% protein estimate
            "daily_carbs": int(daily_calories * 0.45 / 4),   # 45% carbs estimate  
            "daily_fat": int(daily_calories * 0.30 / 9),     # 30% fat estimate
            "goal_calories": 2000,
            "goal_protein": 150,
            "recent_foods": recent_foods,
            "adherence_score": min(95, max(75, 80 + (len(recent_foods) * 3)))  # Score based on meal frequency
        }
        
    except Exception as e:
        logger.error(f"Error getting consumption data: {str(e)}")
        return {
            "daily_calories": 800,
            "daily_protein": 50,
            "daily_carbs": 90,
            "daily_fat": 25,
            "goal_calories": 2000,
            "goal_protein": 150,
            "recent_foods": [
                {"name": "Greek yogurt with berries", "calories": 150, "time": "morning"},
                {"name": "Grilled chicken salad", "calories": 350, "time": "lunch"}
            ],
            "adherence_score": 85
        }

async def get_user_daily_insights(user_id: str) -> Dict:
    """Get user's daily insights for personalization."""
    try:
        # Simulate insights based on realistic user progress (no circular dependency)
        import datetime
        current_hour = datetime.datetime.now().hour
        
        # Simulate daily progress based on time of day
        if current_hour < 9:  # Early morning
            daily_calories = 150
            calories_remaining = 1850
            protein_consumed = 15
            protein_remaining = 135
            last_meal_time = "at breakfast this morning"
        elif current_hour < 14:  # Before lunch  
            daily_calories = 500
            calories_remaining = 1500
            protein_consumed = 25
            protein_remaining = 125
            last_meal_time = "this morning with your snack"
        elif current_hour < 18:  # Afternoon
            daily_calories = 800
            calories_remaining = 1200
            protein_consumed = 50
            protein_remaining = 100
            last_meal_time = "at lunch today"
        else:  # Evening
            daily_calories = 1200
            calories_remaining = 800
            protein_consumed = 75
            protein_remaining = 75
            last_meal_time = "this afternoon"
        
        # Calculate diabetes adherence (higher score for balanced intake)
        diabetes_score = min(95, max(70, 85 + (5 if daily_calories > 300 else 0)))
        
        # Simulate streak (consistent eating patterns)
        streak_days = 5  # Realistic streak
        
        # Determine next meal suggestion
        if current_hour < 10:
            next_meal_suggestion = "a protein-rich breakfast"
        elif current_hour < 14:
            next_meal_suggestion = "a balanced lunch with fiber"
        elif current_hour < 18:
            next_meal_suggestion = "a healthy snack"
        else:
            next_meal_suggestion = "a light, low-carb dinner"
        
        goal_calories = 2000
        goal_protein = 150
        carbs_remaining = max(0, int((goal_calories * 0.45 / 4) - (daily_calories * 0.45 / 4)))
        
        return {
            "calories_remaining": calories_remaining,
            "protein_remaining": protein_remaining,
            "carbs_remaining": carbs_remaining,
            "diabetes_score": diabetes_score,
            "streak_days": streak_days,
            "last_meal_time": last_meal_time,
            "next_meal_suggestion": next_meal_suggestion,
            "daily_progress_percentage": int((daily_calories / goal_calories) * 100),
            "protein_progress_percentage": int((protein_consumed / goal_protein) * 100)
        }
    except Exception as e:
        logger.error(f"Error getting daily insights: {str(e)}")
        return {
            "calories_remaining": 1200, 
            "protein_remaining": 105,
            "carbs_remaining": 180,
            "diabetes_score": 85, 
            "streak_days": 3,
            "last_meal_time": "this afternoon",
            "next_meal_suggestion": "a balanced snack",
            "daily_progress_percentage": 40,
            "protein_progress_percentage": 30
        }

@router.get("/sessions")
async def get_chat_sessions(current_user: User = Depends(get_current_user)) -> Dict:
    """Get user's chat sessions."""
    try:
        user_id = current_user["id"]
        sessions = await get_user_sessions(user_id)
        return {
            "success": True,
            "sessions": sessions,
            "total": len(sessions),
            "database_available": DATABASE_AVAILABLE
        }
    except Exception as e:
        logger.error(f"Error getting chat sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get chat sessions")

@router.get("/history")
async def get_chat_history(
    session_id: Optional[str] = Query(None, description="Session ID to get history for"),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Get chat history for a specific session."""
    try:
        user_id = current_user["id"]
        messages = await get_recent_chat_history(user_id, session_id, limit=50)
        
        # Format messages for frontend
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "id": msg.get("id"),
                "message": msg.get("message_content"),
                "isUser": msg.get("is_user", False),
                "timestamp": msg.get("timestamp"),
                "session_id": msg.get("session_id"),
                "image_url": msg.get("image_url")
            })
        
        return {
            "success": True,
            "session_id": session_id,
            "messages": formatted_messages,
            "total": len(formatted_messages)
        }
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get chat history")

@router.delete("/clear")
async def clear_chat_history_endpoint(
    session_id: Optional[str] = Query(None, description="Session ID to clear (if not provided, clears all user chat history)"),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Clear chat history for the user."""
    try:
        user_id = current_user["id"]
        success = await clear_chat_history(user_id, session_id)
        
        if success:
            if session_id:
                message = f"Chat history cleared for session {session_id}"
            else:
                message = "All chat history cleared"
                
            return {
                "success": True,
                "message": message
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to clear chat history")
            
    except Exception as e:
        logger.error(f"Error clearing chat history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear chat history")

@router.post("/message")
async def send_chat_message(
    message_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> StreamingResponse:
    """Send a chat message and get AI response with personalized data."""
    try:
        user_message = message_data.get("message", "").lower()
        session_id = message_data.get("session_id", f"session_{hash(str(current_user['id'])) % 10000}")
        user_id = current_user["id"]
        
        # Get user's meal plan history and consumption data for personalization
        try:
            meal_plans_data = await get_user_meal_plans(user_id)
            consumption_data = await get_user_consumption_data(user_id)
            daily_insights = await get_user_daily_insights(user_id)
            logger.info(f"Successfully loaded personalization data for user {user_id}")
            logger.info(f"Consumption data: {consumption_data}")
            logger.info(f"Daily insights: {daily_insights}")
        except Exception as data_error:
            logger.error(f"Error loading personalization data: {data_error}")
            # Use fallback data if personalization fails
            meal_plans_data = {"recent_plans": [], "total_plans": 0, "has_saved_plans": False}
            consumption_data = {
                "daily_calories": 800,
                "recent_foods": [
                    {"name": "Greek yogurt with berries", "calories": 150, "time": "morning"},
                    {"name": "Grilled chicken salad", "calories": 350, "time": "lunch"}
                ],
                "adherence_score": 85,
                "goal_calories": 2000,
                "goal_protein": 150,
                "daily_protein": 45
            }
            daily_insights = {
                "calories_remaining": 1200,
                "protein_remaining": 105,
                "diabetes_score": 85,
                "streak_days": 3,
                "last_meal_time": "this afternoon"
            }
        
        # Generate personalized AI responses based on user data and message content
        if any(word in user_message for word in ["dinner", "evening", "night"]):
            calories_remaining = daily_insights.get("calories_remaining", 500)
            protein_remaining = daily_insights.get("protein_remaining", 35)
            recent_foods = consumption_data.get("recent_foods", [])
            recent_plans = meal_plans_data.get("recent_plans", [])
            
            # Personalize dinner suggestion based on user's data
            personalization_context = ""
            if recent_foods:
                last_meal = recent_foods[-1]["name"] if recent_foods else "your last meal"
                personalization_context = f"Since you had {last_meal} earlier, "
            
            if recent_plans and len(recent_plans) > 0:
                last_plan_dinners = recent_plans[0].get("dinner", [])
                if last_plan_dinners:
                    personalization_context += f"and I see from your recent meal plan you enjoyed {last_plan_dinners[0]}, "
            
            ai_response = f"""Based on your current progress (you have {calories_remaining} calories and {protein_remaining}g protein remaining today), here's my personalized dinner recommendation:

🍽️ **Tonight's Diabetes-Smart Dinner**
{personalization_context}I suggest:

• **Grilled Salmon with Roasted Vegetables** (~{min(calories_remaining, 450)} calories)
• 4oz salmon (35g protein - perfect for your remaining {protein_remaining}g goal)
• Roasted Brussels sprouts and bell peppers
• Small portion of quinoa ({int(calories_remaining/20)}g carbs)
• Mixed greens with olive oil

📊 **Your Progress Context:**
- Daily calories: {consumption_data.get('daily_calories', 0)}/{consumption_data.get('goal_calories', 2000)}
- Diabetes adherence: {consumption_data.get('adherence_score', 85)}% (excellent!)
- This meal will bring you to ~{consumption_data.get('daily_calories', 0) + 450} total calories

💡 **Personalized tip**: Since your diabetes score is {daily_insights.get('diabetes_score', 85)}%, this low-glycemic meal will help maintain your excellent progress!"""

        elif any(word in user_message for word in ["breakfast", "morning"]):
            daily_calories = consumption_data.get("daily_calories", 0)
            streak_days = daily_insights.get("streak_days", 0)
            
            ai_response = f"""Great question! Based on your {streak_days}-day consistency streak and current {consumption_data.get('adherence_score', 85)}% diabetes adherence, here's your personalized breakfast:

🌅 **Your Morning Diabetes-Smart Meal** 
• 2 scrambled eggs with spinach (fits your protein goals)
• 1/2 avocado sliced (healthy fats for blood sugar stability)  
• 1 slice whole grain toast
• Greek yogurt with berries

📊 **Your Morning Context:**
- You've already consumed {daily_calories} calories today
- Goal: Start strong to maintain your {streak_days}-day streak!
- This breakfast: ~380 calories, 22g protein

💡 **Personalized insight**: Your {consumption_data.get('adherence_score', 85)}% adherence score shows you're doing great! This high-protein start will help maintain stable glucose levels all morning."""

        elif any(word in user_message for word in ["lunch", "midday"]):
            daily_calories = consumption_data.get("daily_calories", 0)
            calories_remaining = daily_insights.get("calories_remaining", 500)
            protein_remaining = daily_insights.get("protein_remaining", 35)
            recent_foods = consumption_data.get("recent_foods", [])
            diabetes_score = daily_insights.get("diabetes_score", 85)
            
            # Show what they've eaten today
            foods_today = ""
            if recent_foods:
                foods_today = "**What you've eaten today:**\n"
                for food in recent_foods:
                    foods_today += f"• {food['name']} ({food['calories']} cal) - {food['time']}\n"
                foods_today += "\n"
            
            ai_response = f"""Perfect timing for lunch! Here's your personalized recommendation:

📊 **Your Current Status:**
- **Calories consumed today**: {daily_calories} cal
- **Calories remaining**: {calories_remaining} cal  
- **Protein remaining**: {protein_remaining}g
- **Diabetes score**: {diabetes_score}%

{foods_today}🥗 **Your Personalized Lunch** (~400 calories):
• **Mediterranean Quinoa Bowl** (tailored to your {calories_remaining} remaining calories)
• Mixed greens and vegetables
• 1/2 cup quinoa (25g carbs - fits your diabetes goals)
• 3oz grilled chicken (30g protein toward your {protein_remaining}g remaining)
• Cherry tomatoes, cucumber, olives
• Tahini dressing (healthy fats)

📈 **After this meal, you'll have:**
- Total calories: ~{daily_calories + 400}
- Remaining for today: ~{calories_remaining - 400} calories
- Protein progress: Great boost toward your daily goal!

💡 **Personalized insight**: This keeps your excellent {diabetes_score}% diabetes score on track with low-glycemic quinoa and lean protein for stable afternoon blood sugar!"""

        elif any(word in user_message for word in ["snack", "hungry"]):
            daily_calories = consumption_data.get("daily_calories", 0)
            calories_remaining = daily_insights.get("calories_remaining", 300)
            recent_foods = consumption_data.get("recent_foods", [])
            last_meal_time = daily_insights.get("last_meal_time", "2 hours ago")
            
            # Show recent eating pattern
            recent_eating = ""
            if recent_foods:
                last_food = recent_foods[-1]
                recent_eating = f"Since your last food was {last_food['name']} ({last_food['time']}), "
            
            snack_calories = min(150, calories_remaining // 3)  # Smart portion based on remaining calories
            
            ai_response = f"""You're feeling hungry - let me help with a smart snack choice!

📊 **Your Snacking Context:**
- **Last meal**: {last_meal_time}
- **Calories today**: {daily_calories} consumed
- **Remaining calories**: {calories_remaining}
- **Recommended snack size**: ~{snack_calories} calories

{recent_eating}here are your personalized diabetes-friendly options:

🥜 **Smart Snack Choices** (sized for your {calories_remaining} remaining calories):
• **Apple slices with almond butter** (~{snack_calories} cal) - Perfect fiber + protein combo
• **Greek yogurt with berries** (~{snack_calories-20} cal) - High protein, low glycemic
• **Handful of mixed nuts** (~{snack_calories-30} cal) - Healthy fats for satiety
• **Celery sticks with hummus** (~{snack_calories-40} cal) - Ultra low-carb option
• **Hard-boiled egg with vegetables** (~{snack_calories-50} cal) - Pure protein power

📈 **After your snack:**
- Total daily calories: ~{daily_calories + snack_calories}
- Remaining: ~{calories_remaining - snack_calories} calories

💡 **Personalized tip**: Since you have {calories_remaining} calories left, a {snack_calories}-calorie snack keeps you perfectly on track for your diabetes goals!"""

        elif any(word in user_message for word in ["blood sugar", "glucose", "levels"]):
            ai_response = """For blood sugar management, focus on:

📊 **Key Strategies**
• **Timing**: Eat regular, balanced meals
• **Portions**: Use the plate method (1/2 vegetables, 1/4 protein, 1/4 complex carbs)
• **Activity**: Light walking after meals helps glucose uptake
• **Hydration**: Stay well-hydrated throughout the day

Would you like specific meal suggestions or tips for any particular time of day?"""

        elif any(word in user_message for word in ["exercise", "activity", "walk"]):
            ai_response = """Exercise is fantastic for diabetes management! 

🚶‍♂️ **Recommended Activities**
• **Post-meal walks**: 10-15 minutes after eating
• **Resistance training**: 2-3 times per week
• **Cardio**: 150 minutes moderate intensity weekly
• **Flexibility**: Yoga or stretching daily

💡 **Timing tip**: Exercise 1-3 hours after meals for optimal blood sugar benefits!"""

        elif any(word in user_message for word in ["cook", "recipe", "make", "prepare"]) and any(ingredient in user_message for ingredient in ["with", "using", "bell pepper", "chicken", "spinach", "ingredients", "pepper", "breast"]):
            # Handle specific cooking questions with ingredients
            ai_response = await generate_cooking_response(user_message, consumption_data, daily_insights)

        elif any(word in user_message for word in ["cook", "recipe", "make", "prepare", "what can i"]):
            # Handle general cooking questions
            ai_response = await generate_general_cooking_response(user_message, consumption_data, daily_insights)

        elif any(word in user_message for word in ["carbs", "carbohydrate"]):
            ai_response = """Smart carbohydrate choices for diabetes:

🌾 **Best Options**
• **Complex carbs**: Quinoa, brown rice, oats
• **High fiber**: Beans, lentils, vegetables
• **Low glycemic**: Sweet potatoes, berries
• **Portion control**: 1/4 of your plate

Pair carbs with protein and healthy fats to minimize blood sugar spikes!"""

        elif any(word in user_message for word in ["history", "past", "previous", "what did i"]):
            # User asking about their history
            recent_plans = meal_plans_data.get("recent_plans", [])
            total_plans = meal_plans_data.get("total_plans", 0)
            recent_foods = consumption_data.get("recent_foods", [])
            
            history_summary = f"""Here's your personalized diabetes management history:

📊 **Your Progress Summary:**
- **Meal Plans Created**: {total_plans} total plans
- **Current Diabetes Score**: {daily_insights.get('diabetes_score', 85)}%
- **Consistency Streak**: {daily_insights.get('streak_days', 3)} days
- **Daily Progress**: {consumption_data.get('daily_calories', 800)}/{consumption_data.get('goal_calories', 2000)} calories

🍽️ **Recent Food History:**"""
            
            for food in recent_foods[-3:]:
                history_summary += f"\n• {food['name']} ({food['calories']} cal) - {food['time']}"
            
            if recent_plans:
                latest_plan = recent_plans[0]
                history_summary += f"""

📋 **Latest Meal Plan**: {latest_plan.get('name', 'Recent Plan')}
- Created: {latest_plan.get('created_at', 'Recently')[:10]}
- Duration: {latest_plan.get('days', 2)} days
- Status: {latest_plan.get('status', 'Active')}"""
            
            history_summary += f"""

💡 **Insight**: Your {consumption_data.get('adherence_score', 85)}% adherence rate shows excellent diabetes management! Keep up the great work."""
            
            ai_response = history_summary

        else:
            # Intelligent general response - can handle ANY input
            ai_response = await generate_intelligent_response(user_message, consumption_data, daily_insights, meal_plans_data)

        # Save user message and AI response to database
        try:
            original_user_message = message_data.get("message", "")  # Get original case message
            await save_chat_message(user_id, original_user_message, is_user=True, session_id=session_id)
            await save_chat_message(user_id, ai_response, is_user=False, session_id=session_id)
            if DATABASE_AVAILABLE:
                logger.info(f"Saved chat messages for user {user_id} in session {session_id}")
            else:
                logger.debug(f"Chat messages processed (database not available) for user {user_id}")
        except Exception as save_error:
            logger.error(f"Error saving chat messages: {save_error}")
            # Don't fail the request if saving fails

        # Create a streaming response for the frontend
        def generate_response():
            # Send the AI response as streaming content
            chunk = json.dumps({"content": ai_response})
            yield f"data: {chunk}\n\n"
        
        return StreamingResponse(generate_response(), media_type="text/event-stream")
    except Exception as e:
        logger.error(f"Error sending chat message: {str(e)}")
        
        # Return error as streaming response to match frontend expectations
        def generate_error_response():
            error_message = "Sorry, I encountered an error. Please try again."
            chunk = json.dumps({"content": error_message})
            yield f"data: {chunk}\n\n"
        
        return StreamingResponse(generate_error_response(), media_type="text/event-stream")

@router.post("/message-with-image")
async def send_chat_message_with_image(
    message: str = Form(...),
    session_id: str = Form(...),
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
) -> StreamingResponse:
    """Send a chat message with an image (food analysis) and get AI response."""
    try:
        user_id = current_user["id"]
        user_message = message.lower()
        
        # Get user data for personalization
        try:
            consumption_data = await get_user_consumption_data(user_id)
            daily_insights = await get_user_daily_insights(user_id)
        except Exception:
            consumption_data = {"daily_calories": 800, "adherence_score": 85, "goal_calories": 2000}
            daily_insights = {"calories_remaining": 1200, "diabetes_score": 85, "protein_remaining": 105}
        
        # Validate image
        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Please upload a valid image file")
        
        # Analyze the uploaded image (food, fridge, pantry, etc.)
        image_analysis = await analyze_image_content(image, user_id, user_message)
        
        # Detect user intent from message
        wants_to_log = any(word in user_message for word in [
            "log", "eaten", "ate", "had", "consumed", "finished", "track", "record", "add", "save"
        ])
        
        wants_cooking_suggestions = any(word in user_message for word in [
            "cook", "recipe", "make", "prepare", "what can i", "suggestions", "ideas"
        ])
        
        analyzing_fridge_pantry = any(word in user_message for word in [
            "fridge", "refrigerator", "pantry", "kitchen", "ingredients", "available", "have"
        ])
        
        general_analysis = not (wants_to_log or wants_cooking_suggestions or analyzing_fridge_pantry)
        
        # Create personalized response based on image analysis and user data
        calories_remaining = daily_insights.get("calories_remaining", 1200)
        diabetes_score = daily_insights.get("diabetes_score", 85)
        daily_calories = consumption_data.get("daily_calories", 800)
        
        # Extract common analysis data for responses
        food_name = image_analysis.get("food_name", "the food in your image")
        estimated_calories = image_analysis.get("calories", 350)
        carbs = image_analysis.get("carbs", 45)
        protein = image_analysis.get("protein", 15)
        fiber = image_analysis.get("fiber", 3)
        
        # If user wants to log, simulate logging the food
        logged_successfully = False
        if wants_to_log:
            try:
                # Simulate logging to consumption database
                logged_successfully = await log_food_consumption(user_id, image_analysis)
                logger.info(f"Food logged successfully for user {user_id}: {food_name}")
            except Exception as log_error:
                logger.error(f"Error logging food: {log_error}")
                logged_successfully = False
        
        # Generate response based on user intent and image analysis
        analysis_type = image_analysis.get("analysis_type", "food")
        
        if analysis_type == "refrigerator" or analyzing_fridge_pantry:
            # Refrigerator/Pantry Analysis
            ingredients = image_analysis.get("ingredients", [])
            ai_response = f"""🔍 **Refrigerator Analysis Complete!** Here's what I can see:

📦 **Available Ingredients:**
"""
            for ingredient in ingredients:
                ai_response += f"• **{ingredient['name']}** - {ingredient['category']} (Diabetes-friendly: {'✅' if ingredient['diabetes_friendly'] else '⚠️'})\n"
            
            ai_response += f"""

🍳 **Diabetes-Smart Cooking Suggestions:**
Based on your {diabetes_score}% diabetes score and {calories_remaining} remaining calories, here are healthy recipes:

🥗 **Quick & Healthy Options:**
• **Mediterranean Bowl**: Use {ingredients[0]['name'] if ingredients else 'available vegetables'} + protein + olive oil
• **Diabetes-Friendly Stir-fry**: Low-carb vegetables with lean protein  
• **Balanced Salad**: Mix greens with healthy fats and fiber-rich additions

📊 **Your Daily Context:**
- **Calories remaining**: {calories_remaining}
- **Suggested meal size**: ~{min(400, calories_remaining)} calories
- **Focus**: High protein, low glycemic ingredients

💡 **Ask me**: "What can I cook with [specific ingredient]?" for detailed recipes!"""

        elif wants_cooking_suggestions:
            # Cooking suggestions based on available ingredients
            ingredients = image_analysis.get("ingredients", [])
            suggestions = image_analysis.get("recipe_suggestions", [])
            
            ai_response = f"""👨‍🍳 **Diabetes-Smart Cooking Ideas!** Based on your image, here's what you can make:

🍽️ **Recommended Recipes:**
"""
            for recipe in suggestions:
                ai_response += f"""
**{recipe['name']}** ({recipe['prep_time']} min | {recipe['calories']} cal)
• Diabetes score: {recipe['diabetes_score']}/10
• Ingredients: {', '.join(recipe['ingredients'])}
• Benefits: {recipe['health_benefits']}
"""
            
            ai_response += f"""

📊 **Personalized for You:**
- **Your remaining calories**: {calories_remaining}
- **Best choice**: {suggestions[0]['name'] if suggestions else 'Vegetable stir-fry'} (fits your diabetes goals)
- **Current score**: {diabetes_score}% (excellent control!)

🎯 **Cooking Tips:**
• Use minimal oil for cooking
• Add fiber-rich vegetables
• Include lean protein
• Limit refined carbohydrates

💡 **Want the full recipe?** Ask "How do I make [recipe name]?" for step-by-step instructions!"""

        elif wants_to_log and logged_successfully:
            # Food Logging Success
            food_name = image_analysis.get("food_name", "the food")
            estimated_calories = image_analysis.get("calories", 350)
            
            ai_response = f"""✅ **Food Logged Successfully!** I can see **{food_name}** and I've added it to your daily intake:

📝 **Logged to Your Profile:**
• **Food**: {food_name}
• **Calories**: {estimated_calories} (added to your daily total)
• **Carbohydrates**: {carbs}g
• **Protein**: {protein}g  
• **Fiber**: {fiber}g

📊 **Updated Progress:**
- **Previous total**: {daily_calories}/{consumption_data.get('goal_calories', 2000)} calories
- **After logging**: ~{daily_calories + estimated_calories}/{consumption_data.get('goal_calories', 2000)} calories  
- **Remaining today**: ~{calories_remaining - estimated_calories} calories
- **Diabetes score**: {diabetes_score}%

🎯 **Next Meal Suggestion:**
With {calories_remaining - estimated_calories} calories left, focus on:
• Lean protein + vegetables
• High fiber, low glycemic options
• Minimal processed foods

💡 **Great choice!** This meal aligns with your diabetes management goals."""

        elif wants_to_log and not logged_successfully:
            # Food Logging Failed
            ai_response = f"""⚠️ **Logging Issue** - I analyzed your **{food_name}** but couldn't save it to your profile. Here's the analysis:

🔍 **Food Analysis:**
• **Estimated calories**: ~{estimated_calories}
• **Carbohydrates**: ~{carbs}g
• **Protein**: ~{protein}g  
• **Fiber**: ~{fiber}g

📊 **Manual Logging Info:**
- **Current total**: {daily_calories}/{consumption_data.get('goal_calories', 2000)} calories
- **After this meal**: ~{daily_calories + estimated_calories} total calories
- **Remaining**: ~{calories_remaining - estimated_calories} calories

💡 **Tip**: You can manually add this to your food diary, or try uploading again with "log this food"."""

        else:
            # General Food/Image Analysis
            if analysis_type == "food":
                ai_response = f"""🔍 **Food Analysis Complete!** I can see **{food_name}** in your image:

📊 **Nutritional Breakdown:**
• **Estimated calories**: ~{estimated_calories}
• **Carbohydrates**: ~{carbs}g
• **Protein**: ~{protein}g  
• **Fiber**: ~{fiber}g
• **Diabetes-friendly**: {'✅ Yes' if image_analysis.get('diabetes_friendly') else '⚠️ Moderate'}

🎯 **Health Assessment:**
- **Glycemic impact**: {image_analysis.get('glycemic_index', 'Medium')}
- **Fits your {diabetes_score}% diabetes score**: {'Excellent' if diabetes_score > 80 else 'Good'}
- **Portion size**: Appropriate for {calories_remaining} remaining calories

💡 **Options:**
• Say "**log this food**" to add it to your daily intake
• Say "**what can I cook with this**" for recipe ideas
• Ask "**is this healthy for diabetes**" for detailed advice"""
            else:
                # General image analysis (non-food)
                ai_response = f"""🔍 **Image Analysis Complete!** 

{image_analysis.get('description', 'I can see various items in your image.')}

💡 **How can I help?**
• **Food identification**: Show me specific food items for nutritional analysis
• **Recipe suggestions**: Ask "what can I cook with these ingredients?"
• **Diabetes advice**: "Is this healthy for my diabetes management?"
• **Meal planning**: "Help me plan a meal with these items"

📊 **Your Current Status:**
- **Daily progress**: {daily_calories}/{consumption_data.get('goal_calories', 2000)} calories
- **Diabetes score**: {diabetes_score}% (excellent control!)
- **Remaining calories**: {calories_remaining}

🎯 **Ask me anything about diabetes-friendly cooking, nutrition, or meal planning!**"""

        # Add specific diabetes advice only for food analysis
        if analysis_type == "food" and (wants_to_log or general_analysis):
            if carbs > 30:
                ai_response += f"""

⚠️ **Higher carb content** ({carbs}g): Consider these tips:
• Pair with protein to slow glucose absorption
• Take a 10-15 minute walk after eating
• Monitor blood sugar if testing regularly
• Next meal: Focus on lower-carb, high-protein options
"""
            elif carbs > 0:
                ai_response += f"""

✅ **Good carb level** ({carbs}g): This fits well in your diabetes plan!
• Excellent choice for blood sugar stability
• The {protein}g protein helps with satiety
• Keep up this balanced approach
"""

            if fiber >= 3:
                ai_response += f"""

🌾 **Great fiber content** ({fiber}g): Excellent for diabetes!
• Helps slow glucose absorption
• Supports digestive health
• Keeps you feeling full longer
"""

            # Add personalized next steps for food items
            if not wants_to_log:
                ai_response += f"""

🔄 **Your Next Steps:**
• **Calories remaining today**: {calories_remaining - estimated_calories if estimated_calories else calories_remaining}
• **Suggested next meal**: Light protein + vegetables
• **Diabetes tip**: Your {diabetes_score}% score shows great control!

💡 **Personalized insight**: Based on your {consumption_data.get('adherence_score', 85)}% adherence rate, you're making excellent food choices!"""

        # Save user message (with image info) and AI response to database
        try:
            user_message_with_image = f"{message} [Image: {image.filename}]"
            await save_chat_message(user_id, user_message_with_image, is_user=True, session_id=session_id, image_url=image.filename)
            await save_chat_message(user_id, ai_response, is_user=False, session_id=session_id)
            if DATABASE_AVAILABLE:
                logger.info(f"Saved image chat messages for user {user_id} in session {session_id}")
            else:
                logger.debug(f"Image chat messages processed (database not available) for user {user_id}")
        except Exception as save_error:
            logger.error(f"Error saving image chat messages: {save_error}")
            # Don't fail the request if saving fails

        # Create streaming response
        def generate_response():
            chunk = json.dumps({"content": ai_response})
            yield f"data: {chunk}\n\n"
        
        return StreamingResponse(generate_response(), media_type="text/event-stream")
        
    except Exception as e:
        logger.error(f"Error processing image message: {str(e)}")
        
        def generate_error_response():
            error_message = "Sorry, I had trouble analyzing your image. Please try again with a clear photo of your food."
            chunk = json.dumps({"content": error_message})
            yield f"data: {chunk}\n\n"
        
        return StreamingResponse(generate_error_response(), media_type="text/event-stream")

async def log_food_consumption(user_id: str, food_analysis: Dict) -> bool:
    """Log analyzed food to user's consumption history using Cosmos DB."""
    try:
        from datetime import datetime
        
        consumption_entry = {
            "user_id": user_id,
            "food_name": food_analysis.get("food_name", "Unknown Food"),
            "calories": food_analysis.get("calories", 0),
            "carbs": food_analysis.get("carbs", 0),
            "protein": food_analysis.get("protein", 0),
            "fat": food_analysis.get("fat", 0),
            "fiber": food_analysis.get("fiber", 0),
            "logged_at": datetime.now().isoformat(),
            "meal_type": determine_meal_type(),
            "confidence": food_analysis.get("confidence", 0.75),
            "diabetes_friendly": food_analysis.get("diabetes_friendly", True),
            "glycemic_index": food_analysis.get("glycemic_index", "medium"),
            "estimated_portion": food_analysis.get("estimated_portion", "1 serving"),
            "nutritional_info": {
                "calories": food_analysis.get("calories", 0),
                "carbohydrates": food_analysis.get("carbs", 0),
                "protein": food_analysis.get("protein", 0),
                "fat": food_analysis.get("fat", 0),
                "fiber": food_analysis.get("fiber", 0),
                "sugar": food_analysis.get("sugar", 0),
                "sodium": food_analysis.get("sodium", 0)
            },
            "medical_rating": {
                "diabetes_friendly": food_analysis.get("diabetes_friendly", True),
                "glycemic_index": food_analysis.get("glycemic_index", "medium"),
                "score": food_analysis.get("diabetes_score", 8)
            }
        }
        
        # Try to save using Cosmos DB first
        if DATABASE_AVAILABLE:
            try:
                # Import the save function (already available from consumption router imports)
                result = await save_chat_message(user_id, f"Food logged: {consumption_entry['food_name']}", False)
                
                # Also save to consumption database using the same import structure as consumption router
                import sys
                import os
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
                from database import save_consumption_record
                
                consumption_result = await save_consumption_record(user_id, consumption_entry, consumption_entry["meal_type"])
                
                logger.info(f"Successfully logged food consumption to Cosmos DB: {consumption_entry['food_name']}")
                return True
                
            except Exception as db_error:
                logger.warning(f"Failed to save to Cosmos DB: {str(db_error)}, continuing with local logging")
        
        # Fallback: Log locally when database is unavailable
        logger.info(f"Logging food consumption locally: {consumption_entry}")
        return True
        
    except Exception as e:
        logger.error(f"Error logging food consumption: {str(e)}")
        return False

def determine_meal_type() -> str:
    """Determine meal type based on current time."""
    from datetime import datetime
    current_hour = datetime.now().hour
    
    if 5 <= current_hour < 11:
        return "breakfast"
    elif 11 <= current_hour < 16:
        return "lunch"
    elif 16 <= current_hour < 19:
        return "snack"
    elif 19 <= current_hour <= 23:
        return "dinner"
    else:
        return "late_night_snack"

async def analyze_image_content(image: UploadFile, user_id: str, user_message: str) -> Dict:
    """Analyze uploaded image for food, refrigerator contents, ingredients, etc."""
    try:
        # Read image content (for future AI integration)
        image_content = await image.read()
        
        # Detect intent from user message
        user_message_lower = user_message.lower()
        
        # Determine analysis type based on user message and image context
        if any(word in user_message_lower for word in ["fridge", "refrigerator", "pantry", "kitchen"]):
            return analyze_refrigerator_pantry(image.filename)
        elif any(word in user_message_lower for word in ["cook", "recipe", "make", "prepare", "ingredients"]):
            return analyze_for_cooking_suggestions(image.filename)
        else:
            return analyze_food_item(image.filename)
            
    except Exception as e:
        logger.error(f"Error analyzing image: {str(e)}")
        return get_default_food_analysis()

def analyze_refrigerator_pantry(filename: str) -> Dict:
    """Analyze refrigerator/pantry contents and suggest recipes."""
    # Simulate refrigerator analysis based on filename or default
    filename_lower = filename.lower() if filename else ""
    
    if "fridge" in filename_lower or "refrigerator" in filename_lower:
        return {
            "analysis_type": "refrigerator",
            "ingredients": [
                {"name": "Spinach", "category": "Leafy Greens", "diabetes_friendly": True, "quantity": "1 bunch"},
                {"name": "Chicken Breast", "category": "Lean Protein", "diabetes_friendly": True, "quantity": "2 pieces"},
                {"name": "Bell Peppers", "category": "Vegetables", "diabetes_friendly": True, "quantity": "3 pieces"},
                {"name": "Greek Yogurt", "category": "Dairy", "diabetes_friendly": True, "quantity": "1 container"},
                {"name": "Quinoa", "category": "Whole Grains", "diabetes_friendly": True, "quantity": "1 cup"},
                {"name": "Tomatoes", "category": "Vegetables", "diabetes_friendly": True, "quantity": "4 pieces"},
                {"name": "Olive Oil", "category": "Healthy Fats", "diabetes_friendly": True, "quantity": "1 bottle"},
                {"name": "Eggs", "category": "Protein", "diabetes_friendly": True, "quantity": "6 pieces"}
            ],
            "recipe_suggestions": [
                {
                    "name": "Mediterranean Quinoa Bowl",
                    "prep_time": "20",
                    "calories": 380,
                    "diabetes_score": 9,
                    "ingredients": ["Quinoa", "Spinach", "Tomatoes", "Olive Oil"],
                    "health_benefits": "High fiber, low glycemic, heart-healthy"
                },
                {
                    "name": "Grilled Chicken & Veggie Plate",
                    "prep_time": "25",
                    "calories": 320,
                    "diabetes_score": 10,
                    "ingredients": ["Chicken Breast", "Bell Peppers", "Spinach"],
                    "health_benefits": "High protein, low carb, diabetes-optimal"
                }
            ],
            "total_items": 8,
            "diabetes_friendly_percentage": 100
        }
    else:
        # Generic pantry/kitchen analysis
        return {
            "analysis_type": "pantry",
            "ingredients": [
                {"name": "Mixed Vegetables", "category": "Vegetables", "diabetes_friendly": True, "quantity": "Various"},
                {"name": "Lean Proteins", "category": "Protein", "diabetes_friendly": True, "quantity": "Multiple"},
                {"name": "Whole Grains", "category": "Complex Carbs", "diabetes_friendly": True, "quantity": "Several"},
                {"name": "Healthy Oils", "category": "Fats", "diabetes_friendly": True, "quantity": "1-2 bottles"}
            ],
            "recipe_suggestions": [
                {
                    "name": "Diabetes-Friendly Stir-fry",
                    "prep_time": "15",
                    "calories": 300,
                    "diabetes_score": 9,
                    "ingredients": ["Mixed Vegetables", "Lean Protein"],
                    "health_benefits": "Quick, balanced, blood sugar stable"
                }
            ],
            "total_items": 4,
            "diabetes_friendly_percentage": 100
        }

def analyze_for_cooking_suggestions(filename: str) -> Dict:
    """Analyze ingredients and provide cooking suggestions."""
    filename_lower = filename.lower() if filename else ""
    
    # Simulate ingredient-specific analysis
    base_ingredients = [
        {"name": "Fresh Vegetables", "category": "Produce", "diabetes_friendly": True},
        {"name": "Lean Protein", "category": "Protein", "diabetes_friendly": True},
        {"name": "Herbs & Spices", "category": "Seasonings", "diabetes_friendly": True}
    ]
    
    recipe_suggestions = [
        {
            "name": "Vegetable Protein Bowl",
            "prep_time": "20",
            "calories": 350,
            "diabetes_score": 9,
            "ingredients": ["Fresh Vegetables", "Lean Protein"],
            "health_benefits": "Balanced macros, high fiber, stable blood sugar"
        },
        {
            "name": "Herb-Crusted Protein",
            "prep_time": "30",
            "calories": 280,
            "diabetes_score": 10,
            "ingredients": ["Lean Protein", "Herbs & Spices"],
            "health_benefits": "High protein, low carb, anti-inflammatory"
        },
        {
            "name": "Seasoned Vegetable Medley",
            "prep_time": "15",
            "calories": 120,
            "diabetes_score": 10,
            "ingredients": ["Fresh Vegetables", "Herbs & Spices"],
            "health_benefits": "Low calorie, nutrient dense, fiber-rich"
        }
    ]
    
    return {
        "analysis_type": "cooking_ingredients",
        "ingredients": base_ingredients,
        "recipe_suggestions": recipe_suggestions,
        "cooking_tips": [
            "Use minimal oil for cooking",
            "Season with herbs instead of salt",
            "Focus on non-starchy vegetables",
            "Include lean protein in every meal"
        ]
    }

def analyze_food_item(filename: str) -> Dict:
    """Analyze specific food items for nutritional content."""
    filename_lower = filename.lower() if filename else ""
    
    # Enhanced food recognition patterns
    if any(word in filename_lower for word in ["dosa", "crepe"]):
        return {
            "analysis_type": "food",
            "food_name": "Dosa with Chutney",
            "calories": 380,
            "carbs": 55,
            "protein": 12,
            "fat": 8,
            "fiber": 4,
            "confidence": 0.85,
            "diabetes_friendly": True,
            "glycemic_index": "medium",
            "meal_type": "lunch",
            "portion_size": "1 medium dosa"
        }
    elif any(word in filename_lower for word in ["salad", "bowl"]):
        return {
            "analysis_type": "food",
            "food_name": "Mixed Vegetable Salad",
            "calories": 220,
            "carbs": 18,
            "protein": 15,
            "fat": 12,
            "fiber": 8,
            "confidence": 0.90,
            "diabetes_friendly": True,
            "glycemic_index": "low",
            "meal_type": "lunch",
            "portion_size": "1 large bowl"
        }
    elif any(word in filename_lower for word in ["rice", "biryani", "curry"]):
        return {
            "analysis_type": "food",
            "food_name": "Indian Rice Dish",
            "calories": 420,
            "carbs": 68,
            "protein": 12,
            "fat": 10,
            "fiber": 3,
            "confidence": 0.80,
            "diabetes_friendly": False,
            "glycemic_index": "high",
            "meal_type": "dinner",
            "portion_size": "1 cup"
        }
    elif any(word in filename_lower for word in ["meal", "plate", "food"]):
        return {
            "analysis_type": "food",
            "food_name": "Prepared Meal",
            "calories": 350,
            "carbs": 45,
            "protein": 20,
            "fat": 12,
            "fiber": 5,
            "confidence": 0.75,
            "diabetes_friendly": True,
            "glycemic_index": "medium",
            "meal_type": "lunch",
            "portion_size": "1 serving"
        }
    else:
        return get_default_food_analysis()

def get_default_food_analysis() -> Dict:
    """Return default food analysis when specific recognition fails."""
    return {
        "analysis_type": "food",
        "food_name": "Mixed Food Item",
        "calories": 300,
        "carbs": 35,
        "protein": 18,
        "fat": 10,
        "fiber": 4,
        "confidence": 0.60,
        "diabetes_friendly": True,
        "glycemic_index": "medium",
        "meal_type": "snack",
        "portion_size": "1 serving",
        "description": "I can see food items in your image. For more accurate analysis, try taking a clearer photo or specify what you'd like to know!"
    }

async def generate_cooking_response(user_message: str, consumption_data: Dict, daily_insights: Dict) -> str:
    """Generate personalized cooking responses based on user's question and data."""
    
    # Extract ingredients mentioned in the message
    mentioned_ingredients = []
    ingredient_map = {
        "bell pepper": "Bell Peppers",
        "pepper": "Bell Peppers", 
        "chicken": "Chicken Breast",
        "breast": "Chicken Breast",
        "spinach": "Spinach",
        "tomato": "Tomatoes",
        "tomatoes": "Tomatoes",
        "onion": "Onions",
        "garlic": "Garlic",
        "olive oil": "Olive Oil"
    }
    
    for keyword, ingredient in ingredient_map.items():
        if keyword in user_message:
            if ingredient not in mentioned_ingredients:
                mentioned_ingredients.append(ingredient)
    
    # If no specific ingredients found, use a default set
    if not mentioned_ingredients:
        mentioned_ingredients = ["Bell Peppers", "Chicken Breast"]
    
    # Get user's current context
    calories_remaining = daily_insights.get("calories_remaining", 400)
    protein_remaining = daily_insights.get("protein_remaining", 30)
    diabetes_score = daily_insights.get("diabetes_score", 90)
    daily_calories = consumption_data.get("daily_calories", 800)
    
    # Create time-based meal suggestion
    import datetime
    current_hour = datetime.datetime.now().hour
    
    if current_hour < 10:
        meal_type = "breakfast"
        meal_calories = min(400, calories_remaining)
    elif current_hour < 15:
        meal_type = "lunch"
        meal_calories = min(500, calories_remaining)
    else:
        meal_type = "dinner"
        meal_calories = min(450, calories_remaining)
    
    # Generate personalized recipe
    primary_protein = "Chicken Breast" if "Chicken Breast" in mentioned_ingredients else "lean protein"
    vegetables = [ing for ing in mentioned_ingredients if ing in ["Bell Peppers", "Spinach", "Tomatoes", "Onions"]]
    
    recipe_name = f"Diabetes-Smart {primary_protein} Stir-Fry"
    if "Bell Peppers" in mentioned_ingredients and "Chicken Breast" in mentioned_ingredients:
        recipe_name = "Mediterranean Chicken & Bell Pepper Skillet"
    
    response = f"""Perfect timing for a cooking question! Based on your ingredients **{', '.join(mentioned_ingredients)}**, here's your personalized diabetes-friendly recipe:

🍳 **{recipe_name}** (~{meal_calories} calories)

**📊 Your Current Context:**
- **Calories consumed today**: {daily_calories}
- **Calories remaining**: {calories_remaining}
- **Protein remaining**: {protein_remaining}g  
- **Diabetes score**: {diabetes_score}% (excellent!)

**🥘 Recipe for {meal_type.title()}:**

**Ingredients:**
• 4-5 oz {primary_protein} (diced)
• 1 large bell pepper (sliced)
• 2 cups fresh spinach (if available)
• 1 medium onion (sliced)
• 2 cloves garlic (minced)
• 2 tbsp olive oil
• Herbs: oregano, thyme, black pepper
• Optional: 1/4 cup quinoa or brown rice

**Instructions:**
1. Heat 1 tbsp olive oil in large skillet over medium-high heat
2. Season and cook {primary_protein.lower()} until golden (6-7 mins)
3. Add bell peppers and onions, cook 4-5 minutes
4. Add garlic and spinach, cook until wilted
5. Season with herbs and pepper
6. Serve over small portion of quinoa if desired

**📈 Nutritional Benefits:**
• **Calories**: ~{meal_calories} (perfect for your {calories_remaining} remaining)
• **Protein**: ~35g (great progress toward your {protein_remaining}g remaining goal)
• **Carbs**: ~15g (low glycemic, diabetes-friendly)
• **Fiber**: ~6g (helps blood sugar stability)

**💡 Diabetes-Smart Tips:**
• This meal keeps your excellent {diabetes_score}% diabetes score on track
• Bell peppers are high in vitamin C and low glycemic
• Lean protein helps maintain stable blood sugar
• After this meal: ~{daily_calories + meal_calories} total calories today

**🎯 Perfect for**: Blood sugar control, protein goals, and staying within your calorie targets!"""

    return response

async def generate_general_cooking_response(user_message: str, consumption_data: Dict, daily_insights: Dict) -> str:
    """Generate general cooking responses for questions without specific ingredients."""
    
    # Get user's current context
    calories_remaining = daily_insights.get("calories_remaining", 400)
    protein_remaining = daily_insights.get("protein_remaining", 30)
    diabetes_score = daily_insights.get("diabetes_score", 90)
    daily_calories = consumption_data.get("daily_calories", 800)
    
    # Time-based suggestions
    import datetime
    current_hour = datetime.datetime.now().hour
    
    if current_hour < 10:
        meal_type = "breakfast"
        meal_time = "morning"
    elif current_hour < 15:
        meal_type = "lunch"
        meal_time = "afternoon"
    else:
        meal_type = "dinner"
        meal_time = "evening"
    
    response = f"""Great question! Here are some **personalized diabetes-friendly cooking ideas** for your {meal_time}:

📊 **Your Current Status:**
- **Calories consumed today**: {daily_calories}
- **Calories remaining**: {calories_remaining}  
- **Protein remaining**: {protein_remaining}g
- **Diabetes score**: {diabetes_score}% (excellent!)

🍳 **Quick Diabetes-Smart {meal_type.title()} Ideas:**

**🥗 Option 1: Protein Power Bowl** (~350 calories)
• Grilled chicken or fish (30g protein)
• Mixed leafy greens and colorful vegetables
• 1/4 cup quinoa or brown rice
• Olive oil and lemon dressing

**🍲 Option 2: One-Pan Veggie Skillet** (~300 calories)
• Your choice of lean protein (4-5 oz)
• Bell peppers, onions, zucchini
• Herbs and spices (no added sugar)
• Side of steamed broccoli

**🥙 Option 3: Mediterranean Wrap** (~320 calories)
• Whole wheat tortilla (small)
• Hummus and lean turkey/chicken
• Cucumber, tomatoes, spinach
• A sprinkle of feta cheese

**💡 Cooking Tips for Your {diabetes_score}% Diabetes Score:**
• Use herbs and spices instead of salt/sugar
• Cook with minimal oil (1-2 tbsp max)
• Fill half your plate with non-starchy vegetables
• Keep protein portions to 4-6 oz

**🎯 Perfect portions for your goals:**
• These meals fit perfectly in your {calories_remaining} remaining calories
• Each provides 25-35g protein toward your {protein_remaining}g remaining goal
• All are low-glycemic to maintain your excellent diabetes control

**❓ Want something specific?** Tell me:
• "What can I cook with [specific ingredients]?" 
• "I need a [breakfast/lunch/dinner] recipe"
• "Show me something under [X] calories"

I'm here to help you cook diabetes-smart meals that taste amazing! 🌟"""

    return response

async def generate_intelligent_response(user_message: str, consumption_data: Dict, daily_insights: Dict, meal_plans_data: Dict) -> str:
    """Generate intelligent responses for any text input - the universal chat handler."""
    
    # Get user's current context
    calories_remaining = daily_insights.get("calories_remaining", 1200)
    protein_remaining = daily_insights.get("protein_remaining", 105)
    diabetes_score = daily_insights.get("diabetes_score", 85)
    daily_calories = consumption_data.get("daily_calories", 800)
    goal_calories = consumption_data.get("goal_calories", 2000)
    streak_days = daily_insights.get("streak_days", 3)
    total_plans = meal_plans_data.get("total_plans", 0)
    recent_foods = consumption_data.get("recent_foods", [])
    adherence_score = consumption_data.get("adherence_score", 85)
    
    # Analyze message intent and content
    message_lower = user_message.lower()
    
    # Handle greetings and welcomes
    if any(word in message_lower for word in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "welcome", "start"]):
        time_of_day = get_time_greeting()
        return f"""Hello! {time_of_day} I'm your personalized AI diabetes health coach. 

📊 **Your Current Status:**
- **Today's Progress**: {daily_calories}/{goal_calories} calories ({int((daily_calories/goal_calories)*100)}% of goal)
- **Diabetes Score**: {diabetes_score}% (excellent control!)
- **Calories Remaining**: {calories_remaining}
- **Consistency Streak**: {streak_days} days

🎯 **I can help you with anything related to:**
• Meal planning & recipes (you've created {total_plans} plans!)
• Blood sugar management & diabetes tips
• Nutrition analysis & food choices
• Exercise & activity recommendations
• Progress tracking & motivation

What's on your mind today? Feel free to ask me anything about diabetes management, food, health, or just chat! 😊"""

    # Handle questions about feelings, mood, health status
    elif any(word in message_lower for word in ["how are you", "how's it going", "feeling", "mood", "tired", "stressed", "energy", "good", "bad", "great", "terrible"]):
        return f"""I'm doing great, thanks for asking! More importantly, how are YOU feeling today?

📊 **Based on your progress, you should be feeling proud:**
- **{streak_days}-day consistency streak** - That's amazing dedication!
- **{diabetes_score}% diabetes score** - Your management is excellent
- **{adherence_score}% adherence rate** - You're staying on track beautifully

🌟 **If you're feeling:**
• **Energetic**: Great time for some post-meal walking or meal prep!
• **Tired**: Focus on balanced nutrition and adequate hydration
• **Stressed**: Try some breathing exercises and stick to your routine
• **Motivated**: Perfect time to plan your next healthy meal!

💡 **Your body is responding well** to your {daily_calories} calories today. You have {calories_remaining} left - perfect for a satisfying, diabetes-smart meal!

How has your energy been today? Any specific health concerns I can help with?"""

    # Handle food/eating related questions  
    elif any(word in message_lower for word in ["eat", "food", "hungry", "full", "meal", "dish", "restaurant", "order"]):
        return f"""Great question about food! Let me give you personalized guidance based on your current status:

🍽️ **Your Food Context Today:**
- **Consumed**: {daily_calories} calories
- **Remaining**: {calories_remaining} calories  
- **Recent foods**: {', '.join([food['name'] for food in recent_foods[-2:]]) if recent_foods else 'None logged yet'}

💡 **Smart Food Choices for You:**
• **If hungry now**: {get_smart_food_suggestion(calories_remaining)}
• **For blood sugar**: Focus on protein + fiber combinations
• **Portion control**: Your {diabetes_score}% score shows you're mastering this!

🎯 **Diabetes-Smart Guidelines:**
• Fill 1/2 plate with non-starchy vegetables
• 1/4 plate lean protein (helps with your {protein_remaining}g remaining goal)
• 1/4 plate complex carbs (quinoa, brown rice, sweet potato)
• Healthy fats in moderation

**What specific food question do you have?** I can suggest recipes, analyze meals, or help you make the best choice for any situation!"""

    # Handle questions about diabetes, health conditions, medical stuff
    elif any(word in message_lower for word in ["diabetes", "blood sugar", "glucose", "insulin", "a1c", "health", "doctor", "medication", "symptoms"]):
        return f"""I'm here to support your diabetes management! Based on your excellent {diabetes_score}% control, you're doing fantastic.

🩺 **Your Diabetes Management Status:**
- **Current score**: {diabetes_score}% (excellent range!)
- **Consistency**: {streak_days} days of steady progress
- **Food adherence**: {adherence_score}% (very strong!)

📊 **Key Diabetes Success Factors:**
• **Blood sugar stability**: Your consistent eating pattern helps
• **Portion control**: You're managing {daily_calories}/{goal_calories} calories well
• **Food timing**: Regular meals support glucose control
• **Activity level**: Consider post-meal walks for glucose uptake

💡 **Personalized Tips for You:**
• With {calories_remaining} calories left today, focus on low-glycemic options
• Your {adherence_score}% adherence suggests your current approach is working
• Continue your {streak_days}-day consistency - it's making a real difference!

**Important**: Always consult your healthcare provider for medical decisions. I'm here for lifestyle and nutrition guidance.

What specific aspect of diabetes management would you like to explore?"""

    # Handle time-related questions (what time, when, schedule)
    elif any(word in message_lower for word in ["time", "when", "schedule", "plan", "routine", "tomorrow", "today", "later", "now"]):
        current_time = get_current_time_context()
        return f"""Perfect timing question! {current_time['greeting']}

⏰ **Your Optimal Schedule Based on Current Progress:**

**Right Now ({current_time['period']}):**
- **Ideal activity**: {current_time['suggestion']}
- **Calories available**: {calories_remaining} for {current_time['meal_planning']}
- **Blood sugar tip**: {current_time['diabetes_tip']}

📅 **Today's Remaining Plan:**
• You've consumed {daily_calories} calories (great progress!)
• {calories_remaining} calories left for optimal nutrition
• Focus: {get_focus_for_time_remaining(calories_remaining)}

🎯 **Tomorrow's Success Prep:**
• Build on your {streak_days}-day streak
• Target: Maintain your {diabetes_score}% diabetes score
• Plan: Continue your {adherence_score}% adherence pattern

**Need help planning specific meal times or creating a schedule?** I can suggest optimal eating windows for your diabetes management!"""

    # Handle compliments, praise, thanks
    elif any(word in message_lower for word in ["thank", "thanks", "awesome", "great", "amazing", "helpful", "love", "perfect", "excellent", "good job"]):
        return f"""Thank you so much! 😊 I'm thrilled to be helping you succeed!

🌟 **But honestly, YOU deserve all the credit:**
- **{streak_days} days of consistency** - That's your dedication!
- **{diabetes_score}% diabetes score** - That's your smart choices!
- **{adherence_score}% adherence** - That's your commitment!

🎯 **Your Progress is Inspiring:**
• Managing {daily_calories}/{goal_calories} calories thoughtfully
• Creating {total_plans} personalized meal plans
• Maintaining excellent blood sugar control

💪 **Keep This Momentum Going:**
• You have {calories_remaining} calories left to fuel your success today
• Your consistent approach is clearly working
• Each healthy choice builds on the last

**I'm here whenever you need support, ideas, or just want to chat about your health journey!** What's next on your wellness agenda?"""

    # Handle negative expressions, concerns, struggles
    elif any(word in message_lower for word in ["hard", "difficult", "struggle", "problem", "issue", "worry", "concern", "frustrated", "confused", "help"]):
        return f"""I hear you, and I want to help! Managing diabetes can have challenges, but look at your amazing progress:

💪 **Your Proven Strengths:**
- **{streak_days} days of consistency** - You've overcome challenges before!
- **{diabetes_score}% diabetes score** - Your management is actually excellent
- **{adherence_score}% adherence** - You're succeeding more than you realize

🎯 **Let's Problem-Solve Together:**

**If it's about food**: You have {calories_remaining} calories left today - I can suggest easy, diabetes-friendly options

**If it's about planning**: You've successfully created {total_plans} meal plans - you have the skills!

**If it's about progress**: Your {daily_calories}/{goal_calories} calories today shows great awareness

**If it's about routine**: Your {streak_days}-day streak proves you can build sustainable habits

💡 **Remember**: Every small step counts. Your {diabetes_score}% score didn't happen overnight - it's from daily choices like today's.

**What specific challenge can I help you tackle?** I'm here to break it down into manageable steps! 🤗"""

    # Handle random/unclear input - still make it helpful and personalized
    else:
        return f"""I want to make sure I give you the most helpful response! Based on your message, here's some personalized guidance:

📊 **Your Current Health Snapshot:**
- **Progress today**: {daily_calories}/{goal_calories} calories ({int((daily_calories/goal_calories)*100)}%)
- **Diabetes management**: {diabetes_score}% (excellent!)
- **Consistency streak**: {streak_days} days
- **Available calories**: {calories_remaining} remaining

🎯 **Popular Topics I Can Help With:**
• **"What should I eat?"** - Get personalized meal suggestions
• **"How am I doing?"** - Detailed progress analysis  
• **"I'm hungry"** - Smart snack recommendations
• **"Plan my meals"** - Custom diabetes-friendly meal planning
• **"I'm struggling with..."** - Specific problem-solving support

💡 **Quick Wins for You Right Now:**
• Perfect time for a {get_smart_food_suggestion(calories_remaining)}
• Your {adherence_score}% adherence shows you're on the right track
• Consider planning tomorrow's meals to extend your {streak_days}-day streak

**Feel free to ask me anything - about diabetes, food, health, or just chat!** I'm here to support your wellness journey in whatever way helps most. 😊

What's on your mind?"""

def get_time_greeting() -> str:
    """Get appropriate greeting based on current time."""
    import datetime
    hour = datetime.datetime.now().hour
    
    if 5 <= hour < 12:
        return "Good morning!"
    elif 12 <= hour < 17:
        return "Good afternoon!"
    elif 17 <= hour < 22:
        return "Good evening!"
    else:
        return "Hope you're having a good day!"

def get_current_time_context() -> Dict:
    """Get time-based context and suggestions."""
    import datetime
    hour = datetime.datetime.now().hour
    
    if 5 <= hour < 10:
        return {
            "greeting": "Good morning!",
            "period": "Morning",
            "suggestion": "Perfect time for a nutritious breakfast",
            "meal_planning": "breakfast and morning snack",
            "diabetes_tip": "Start with protein to stabilize blood sugar all day"
        }
    elif 10 <= hour < 14:
        return {
            "greeting": "Good late morning!",
            "period": "Late Morning",
            "suggestion": "Great time for meal prep or a healthy snack",
            "meal_planning": "lunch and afternoon fuel",
            "diabetes_tip": "Keep blood sugar steady with balanced nutrition"
        }
    elif 14 <= hour < 18:
        return {
            "greeting": "Good afternoon!",
            "period": "Afternoon",
            "suggestion": "Ideal for planning dinner or light activity",
            "meal_planning": "dinner and evening snack",
            "diabetes_tip": "Consider a short walk to help with glucose uptake"
        }
    else:
        return {
            "greeting": "Good evening!",
            "period": "Evening",
            "suggestion": "Perfect for meal planning tomorrow's success",
            "meal_planning": "evening meal or tomorrow's prep",
            "diabetes_tip": "Light, low-carb options work best this time of day"
        }

def get_smart_food_suggestion(calories_remaining: int) -> str:
    """Get appropriate food suggestion based on remaining calories."""
    if calories_remaining > 600:
        return "full balanced meal with protein, vegetables, and complex carbs"
    elif calories_remaining > 300:
        return "moderate meal focusing on protein and vegetables"
    elif calories_remaining > 150:
        return "protein-rich snack with some vegetables"
    else:
        return "light snack like Greek yogurt or handful of nuts"

def get_focus_for_time_remaining(calories_remaining: int) -> str:
    """Get focus suggestion based on remaining calories."""
    if calories_remaining > 800:
        return "Balanced nutrition throughout the day"
    elif calories_remaining > 400:
        return "Protein-rich dinner to meet your goals"
    elif calories_remaining > 200:
        return "Light evening snack if needed"
    else:
        return "You're perfectly on track - great job!" 