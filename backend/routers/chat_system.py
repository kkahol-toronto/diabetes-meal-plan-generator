"""
Chat System Router
Handles all chat-related functionality including messaging, image analysis, session management, and AI coaching.
This module provides comprehensive chat capabilities with contextual AI responses.
"""

import os
import json
import base64
import asyncio
import re
from datetime import datetime, timedelta
from io import BytesIO
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Depends, Request as FastAPIRequest, File, Form, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from PIL import Image

from models import User, ChatMessage
from routers.auth import get_current_user
from database import (
    get_user_meal_plans, get_user_consumption_history, get_recent_chat_history,
    format_chat_history_for_prompt, clear_chat_history, get_user_sessions,
    save_chat_message, save_consumption_record
)
from services.openai_service import robust_openai_call, get_openai_client
from utils import filter_today_records
# Handle pending consumption import gracefully due to event loop issues
try:
    from pending_consumption import pending_consumption_manager
except RuntimeError as e:
    if "no running event loop" in str(e):
        print(f"Warning: Could not import pending_consumption_manager due to event loop issue: {e}")
        pending_consumption_manager = None
    else:
        raise

router = APIRouter()

# Helper functions for chat functionality
def has_logging_intent(message: str) -> bool:
    """Check if the user message indicates intent to log food."""
    logging_intents = [
        "log this", "add this to my history", "record this", "save this",
        "log it", "add this meal", "add this food", "log meal", "log food",
        "can you log", "please log", "log as my", "this as my", "this was my"
    ]
    return any(kw in message.lower() for kw in logging_intents)

def extract_nutrition_question(message: str):
    """
    Returns the nutrition field(s) the user is asking about, or None if not found.
    Supports: calories, protein, carbs, fat, fiber, sugar, sodium.
    """
    nutrition_keywords = {
        'calories': ['calorie', 'calories', 'kcal'],
        'protein': ['protein', 'proteins'],
        'carbohydrates': ['carb', 'carbs', 'carbohydrate', 'carbohydrates'],
        'fat': ['fat', 'fats'],
        'fiber': ['fiber', 'fibre'],
        'sugar': ['sugar', 'sugars'],
        'sodium': ['sodium', 'salt'],
    }
    found = []
    msg = message.lower()
    for field, keywords in nutrition_keywords.items():
        for kw in keywords:
            if re.search(rf'\b{re.escape(kw)}\b', msg):
                found.append(field)
                break
    return found if found else None

@router.post("/chat/message")
async def send_chat_message(
    message: ChatMessage,
    current_user: User = Depends(get_current_user)
):
    
    # Get chat history for context
    chat_history = await format_chat_history_for_prompt(
        current_user["id"],
        message.session_id
    )
    
    # 🧠 ENHANCED AI COACH CONTEXT - Get comprehensive user data
    profile = current_user.get("profile", {})
    
    # Extract current medications for AI context
    current_medications = profile.get("currentMedications", [])
    
    # Get recent meal plans (last 3 for context)
    try:
        recent_meal_plans = await get_user_meal_plans(current_user["id"])
        recent_meal_plans = recent_meal_plans[:3]  # Last 3 meal plans
    except Exception as e:
        print(f"Error fetching meal plans for chat context: {e}")
        recent_meal_plans = []
    
    # Get recent consumption history (last 7 days) - INCREASED LIMIT to ensure we get ALL today's meals
    try:
        recent_consumption = await get_user_consumption_history(current_user["id"], limit=200)
        # Filter to last 7 days
        from datetime import datetime, timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_consumption = [
            record for record in recent_consumption 
            if datetime.fromisoformat(record.get("timestamp", "").replace("Z", "+00:00")) > seven_days_ago
        ]
    except Exception as e:
        print(f"Error fetching consumption history for chat context: {e}")
        recent_consumption = []
    
    # Get today's consumption for daily tracking - USE PROPER TIMEZONE-AWARE FILTERING
    try:
        # Use the new timezone-aware filtering function that resets at midnight
        user_timezone = profile.get("timezone", "UTC")
        today_consumption = filter_today_records(recent_consumption, user_timezone=user_timezone)
        
        print(f"[CHAT_DEBUG] Found {len(today_consumption)} meals for today using timezone-aware filtering")
        
    except Exception as e:
        print(f"Error filtering today's consumption: {e}")
        today_consumption = []
    
    # Calculate today's nutritional totals - ENHANCED with comprehensive tracking
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
    print(f"[CHAT_DEBUG] Found {len(today_consumption)} meals for today")
    print(f"[CHAT_DEBUG] Today's totals: {today_totals}")
    if today_consumption:
        print(f"[CHAT_DEBUG] Today's meals: {[record.get('food_name') for record in today_consumption]}")
    else:
        print(f"[CHAT_DEBUG] No meals found for today - recent_consumption had {len(recent_consumption)} records")
    
    # Get user's goals from profile or latest meal plan
    calorie_goal = 2000  # Default
    macro_goals = {"protein": 100, "carbs": 250, "fat": 70}  # Defaults
    
    if profile.get("calorieTarget"):
        try:
            calorie_goal = int(profile["calorieTarget"])
        except:
            pass
    elif recent_meal_plans and recent_meal_plans[0].get("dailyCalories"):
        calorie_goal = recent_meal_plans[0]["dailyCalories"]
    
    if profile.get("macroGoals"):
        macro_goals.update(profile["macroGoals"])
    elif recent_meal_plans and recent_meal_plans[0].get("macronutrients"):
        macros = recent_meal_plans[0]["macronutrients"]
        macro_goals = {
            "protein": macros.get("protein", 100),
            "carbs": macros.get("carbs", 250),
            "fat": macros.get("fats", 70)
        }
    
    # Calculate adherence and progress
    calorie_adherence = (today_totals["calories"] / calorie_goal * 100) if calorie_goal > 0 else 0
    protein_adherence = (today_totals["protein"] / macro_goals["protein"] * 100) if macro_goals["protein"] > 0 else 0
    carb_adherence = (today_totals["carbs"] / macro_goals["carbs"] * 100) if macro_goals["carbs"] > 0 else 0
    fat_adherence = (today_totals["fat"] / macro_goals["fat"] * 100) if macro_goals["fat"] > 0 else 0
    
    # Analyze recent consumption patterns
    diabetes_suitable_count = 0
    total_recent_records = len(recent_consumption)
    for record in recent_consumption:
        medical_rating = record.get("medical_rating", {})
        diabetes_suitability = medical_rating.get("diabetes_suitability", "").lower()
        if diabetes_suitability in ["high", "good", "suitable"]:
            diabetes_suitable_count += 1
    
    diabetes_adherence = (diabetes_suitable_count / total_recent_records * 100) if total_recent_records > 0 else 0
    
    # 🧠 COMPREHENSIVE HEALTH ANALYSIS - Match AI coach sophistication
    high_carb_meals = 0
    high_sugar_meals = 0
    high_sodium_meals = 0
    recent_meals = []
    today_meals = []
    
    for record in recent_consumption:
        nutritional_info = record.get("nutritional_info", {})
        food_name = record.get("food_name", "Unknown food")
        recent_meals.append(food_name)
        
        # Track concerning patterns
        if nutritional_info.get("carbohydrates", 0) > 45:
            high_carb_meals += 1
        if nutritional_info.get("sugar", 0) > 15:
            high_sugar_meals += 1
        if nutritional_info.get("sodium", 0) > 800:
            high_sodium_meals += 1
    
    # Today's meal names
    for record in today_consumption:
        food_name = record.get("food_name", "Unknown food")
        portion = record.get("estimated_portion", "Unknown portion")
        calories = record.get("nutritional_info", {}).get("calories", "N/A")
        today_meals.append(f"{food_name} ({portion}) - {calories} kcal")
    
    # Additional user profile data for comprehensive personalization
    food_preferences = profile.get("foodPreferences", [])
    strong_dislikes = profile.get("strongDislikes", [])
    primary_goals = profile.get("primaryGoals", [])
    readiness_to_change = profile.get("readinessToChange", "")
    meal_prep_capability = profile.get("mealPrepCapability", "")
    eating_schedule = profile.get("eatingSchedule", "")
    exercise_frequency = profile.get("exerciseFrequency", "")
    exercise_types = profile.get("exerciseTypes", [])
    
    # Create comprehensive AI Coach system prompt
    system_prompt = f"""You are an advanced AI Diet Coach and Diabetes Management Specialist. You are the central intelligence of a comprehensive diabetes meal planning and tracking system.

🎯 **YOUR ROLE**: You are not just a chatbot - you are the user's personal diet coach, meal planner, and diabetes management companion. You have full access to their meal plans, consumption history, and progress data.

👤 **USER PROFILE**:
- Name: {profile.get('name', 'Not specified')}
- Age: {profile.get('age', 'Not specified')}
- Gender: {profile.get('gender', 'Not specified')}
- Weight: {profile.get('weight', 'Not specified')} kg
- Height: {profile.get('height', 'Not specified')} cm
- BMI: {profile.get('bmi', 'Not calculated')}
- Blood Pressure: {profile.get('systolicBP', 'Not specified')}/{profile.get('diastolicBP', 'Not specified')} mmHg
- Medical Conditions: {', '.join(profile.get('medicalConditions', []))}
- Current Medications: {', '.join(current_medications) if current_medications else 'None specified'}
- Allergies: {', '.join(profile.get('allergies', [])) if profile.get('allergies') else 'None specified'}
- Diet Type: {', '.join(profile.get('dietType', [])) if profile.get('dietType') else 'None specified'}
- Dietary Features: {', '.join(profile.get('dietaryFeatures', []) or profile.get('diet_features', [])) if profile.get('dietaryFeatures') or profile.get('diet_features') else 'None specified'}
- Dietary Restrictions: {', '.join(profile.get('dietaryRestrictions', [])) if profile.get('dietaryRestrictions') else 'None specified'}
- Food Preferences: {', '.join(food_preferences) if food_preferences else 'None specified'}
- Strong Dislikes: {', '.join(strong_dislikes) if strong_dislikes else 'None specified'}

🎯 **HEALTH GOALS & LIFESTYLE**:
- Primary Goals: {', '.join(primary_goals) if primary_goals else 'None specified'}
- Readiness to Change: {readiness_to_change if readiness_to_change else 'Not specified'}
- Meal Prep Capability: {meal_prep_capability if meal_prep_capability else 'Not specified'}
- Eating Schedule: {eating_schedule if eating_schedule else 'Not specified'}
- Exercise Frequency: {exercise_frequency if exercise_frequency else 'Not specified'}
- Exercise Types: {', '.join(exercise_types) if exercise_types else 'None specified'}

🎯 **DAILY GOALS & PROGRESS**:
- Calorie Goal: {calorie_goal} kcal
- Protein Goal: {macro_goals['protein']}g
- Carb Goal: {macro_goals['carbs']}g  
- Fat Goal: {macro_goals['fat']}g

📊 **TODAY'S PROGRESS** ({datetime.utcnow().strftime('%B %d, %Y')}):
- Calories: {today_totals['calories']:.0f}/{calorie_goal} ({calorie_adherence:.1f}%)
- Protein: {today_totals['protein']:.1f}/{macro_goals['protein']}g ({protein_adherence:.1f}%)
- Carbs: {today_totals['carbs']:.1f}/{macro_goals['carbs']}g ({carb_adherence:.1f}%)
- Fat: {today_totals['fat']:.1f}/{macro_goals['fat']}g ({fat_adherence:.1f}%)
- Fiber: {today_totals['fiber']:.1f}g | Sugar: {today_totals['sugar']:.1f}g | Sodium: {today_totals['sodium']:.0f}mg
- Meals logged today: {len(today_consumption)}

📈 **RECENT PERFORMANCE** (Last 7 days):
- Total meals logged: {total_recent_records}
- Diabetes-suitable meals: {diabetes_suitable_count}/{total_recent_records} ({diabetes_adherence:.1f}%)
- High-carb meals (>45g): {high_carb_meals} | High-sugar meals (>15g): {high_sugar_meals}
- High-sodium meals (>800mg): {high_sodium_meals}
- Recent meal plans available: {len(recent_meal_plans)}

🎯 **HEALTH INSIGHTS**:
- Diabetes adherence trend: {diabetes_adherence:.1f}% (Target: >80%)
- Carb management: {'Good' if high_carb_meals < total_recent_records * 0.3 else 'Needs attention'}
- Sugar control: {'Good' if high_sugar_meals < total_recent_records * 0.2 else 'Needs attention'}  
- Sodium management: {'Good' if high_sodium_meals < total_recent_records * 0.3 else 'Needs attention'}

🍽️ **RECENT MEAL PLANS**:
{chr(10).join([f"- Plan {i+1} (Created: {plan.get('created_at', 'Unknown')[:10]}): {plan.get('dailyCalories', 'N/A')} kcal/day" for i, plan in enumerate(recent_meal_plans[:2])]) if recent_meal_plans else "- No recent meal plans found"}

🥗 **TODAY'S DETAILED CONSUMPTION**:
{chr(10).join([f"- {meal}" for meal in today_meals]) if today_meals else "- No meals logged today yet"}

🍽️ **RECENT MEAL HISTORY**:
- Recent meals: {', '.join(recent_meals[:8]) if recent_meals else 'No recent meals'}
- Today's meal count: {len(today_consumption)} meals

🧠 **YOUR COMPREHENSIVE COACHING INTELLIGENCE**:
You have COMPLETE ACCESS to their full health ecosystem. Use ALL available data for hyper-personalized responses:
1. **Medical-Grade Personalization**: Factor in medical conditions, medications, and health metrics
2. **Comprehensive Nutritional Analysis**: Consider calories, macros, fiber, sugar, sodium trends
3. **Lifestyle-Informed Guidance**: Account for exercise habits, meal prep capability, eating schedule
4. **Goal-Aligned Coaching**: Reference their specific health goals and readiness to change
5. **Pattern-Based Insights**: Identify trends in their consumption and provide targeted feedback
6. **Real-time Adaptation**: Suggest meal adjustments based on today's detailed intake

🎯 **COACHING PRIORITIES**:
1. **Diabetes Management**: Always prioritize blood sugar stability
2. **Adherence Support**: Help user stick to their meal plans while being flexible
3. **Behavioral Coaching**: Encourage positive habits and address challenges
4. **Nutritional Education**: Explain the 'why' behind recommendations
5. **Motivation**: Keep user engaged and motivated in their health journey

💡 **COMPREHENSIVE RESPONSE STYLE**:
- Reference SPECIFIC data points from their complete health profile
- Integrate medical conditions, medications, and lifestyle factors in advice
- Use detailed nutritional analysis (including fiber, sugar, sodium patterns)
- Acknowledge their exercise habits, eating schedule, and meal prep reality
- Align recommendations with their stated health goals and readiness level
- Provide evidence-based advice considering their full health ecosystem
- Be encouraging while addressing specific areas needing attention

Remember: You have access to their complete meal planning and consumption history. Use this data to provide highly personalized, contextual advice that feels like it comes from someone who truly knows their journey."""
    
    # Ensure chat history is a list of message objects
    formatted_chat_history = []
    for msg in chat_history:
        if isinstance(msg, tuple) and len(msg) == 2:
            content, is_user = msg
            formatted_chat_history.append(
                {"role": "user", "content": content} if is_user else {"role": "assistant", "content": content}
            )
    
    # Generate response using OpenAI with simulated streaming (fallback approach)
    try:
        print(f"[CHAT_STREAMING] Starting message generation...")
        
        # First get the complete response (temporarily)
        api_result = await robust_openai_call(
            messages=[
                {"role": "system", "content": system_prompt},
                *formatted_chat_history,
                {"role": "user", "content": message.message}
            ],
            max_tokens=1000,
            temperature=0.8,
            max_retries=3,
            timeout=60,
            context="chat_message"
        )
        
        if not api_result["success"]:
            error_response = "I'm experiencing technical difficulties right now. Please try again in a moment."
            return StreamingResponse(
                iter([f"data: {json.dumps({'content': error_response})}\n\n"]),
                media_type="text/event-stream"
            )
        
        full_message = api_result["content"]
        print(f"[CHAT_STREAMING] Got full response: {len(full_message)} characters")

        # Stream the response word by word
        async def generate():
            try:
                import asyncio
                words = full_message.split(' ')
                print(f"[CHAT_STREAMING] Streaming {len(words)} words...")
                
                for i, word in enumerate(words):
                    # Add space back except for first word
                    chunk = f" {word}" if i > 0 else word
                    print(f"[CHAT_STREAMING] Chunk {i+1}/{len(words)}: '{chunk}'")
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
                    # Small delay to simulate real streaming
                    await asyncio.sleep(0.05)  # 50ms delay between words
                
                print(f"[CHAT_STREAMING] Streaming complete!")
                
                # Save the complete assistant message after streaming
                await save_chat_message(
                    current_user["id"],
                    full_message,
                    is_user=False,
                    session_id=message.session_id if hasattr(message, 'session_id') else None
                )
                print(f"[CHAT_STREAMING] Message saved to database")
                
            except Exception as e:
                print(f"Error in streaming response: {str(e)}")
                yield f"data: {json.dumps({'content': 'Error occurred during streaming'})}\n\n"

        # Create a streaming response with proper headers
        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
        return StreamingResponse(
            generate(), 
            media_type="text/event-stream",
            headers=headers
        )

    except Exception as e:
        print(f"Error setting up OpenAI streaming: {str(e)}")
        # If OpenAI setup fails, return a helpful error message
        error_response = "I'm experiencing technical difficulties right now. Please try again in a moment."
        return StreamingResponse(
            iter([f"data: {json.dumps({'content': error_response})}\n\n"]),
            media_type="text/event-stream"
        )

@router.get("/chat/history")
async def get_chat_history(
    session_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    messages = await get_recent_chat_history(current_user["id"], session_id)
    return messages

@router.get("/chat/sessions")
async def get_chat_sessions(current_user: User = Depends(get_current_user)):
    sessions = await get_user_sessions(current_user["id"])
    return sessions

@router.delete("/chat/history")
async def delete_chat_history(
    session_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    await clear_chat_history(current_user["id"], session_id)
    return {"message": "Chat history cleared successfully"}

@router.post("/chat/analyze-image")
async def analyze_image(
    image: UploadFile = File(...),
    prompt: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    try:
        # Read and validate image
        contents = await image.read()
        
        # Validate file type and size
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        if len(contents) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB")
        
        # Check file extension
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        file_extension = image.filename.lower().split('.')[-1] if image.filename else ''
        if not file_extension or f'.{file_extension}' not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Unsupported file format. Allowed formats: {', '.join(allowed_extensions)}")
        
        try:
            # Try to open and validate the image
            img = Image.open(BytesIO(contents))
            
            # Convert to RGB if necessary (handles RGBA, P modes, etc.)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if too large (max 1024x1024 for processing efficiency)
            max_size = 1024
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Convert image to base64
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=85, optimize=True)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
        except Exception as img_error:
            print(f"[analyze_image] Image processing error: {str(img_error)}")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid or corrupted image file. Please upload a valid image in one of these formats: {', '.join(allowed_extensions)}"
            )
        
        # Save user message with image
        user_message = await save_chat_message(
            current_user["id"],
            "Analyzing food image...",
            is_user=True,
            session_id=None,  # You might want to handle session_id differently
            image_url=img_str
        )
        
        # Generate response using OpenAI with image
        response = get_openai_client().chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful diet assistant for diabetes patients. Analyze the food image and provide detailed nutritional information, including estimated calories, macronutrients, and any relevant dietary considerations for diabetes patients."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_str}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500,
            temperature=0.7,
            stream=True
        )
        
        # Stream the response
        async def generate():
            full_message = ""
            try:
                for chunk in response:
                    if not chunk.choices:
                        continue
                    if not chunk.choices[0].delta:
                        continue
                    content = chunk.choices[0].delta.content
                    if content:
                        full_message += content
                        # Yield as SSE JSON event
                        yield f"data: {json.dumps({'content': content})}\n\n"
            except Exception as e:
                print(f"Error in streaming response: {str(e)}")
                if full_message:
                    # Send whatever was accumulated as final SSE event
                    yield f"data: {json.dumps({'content': full_message})}\n\n"
            
            # Save the complete assistant message after streaming
            if full_message:
                await save_chat_message(
                    current_user["id"],
                    full_message,
                    is_user=False,
                    session_id=user_message["session_id"],
                    image_url=img_str
                )
        
        return StreamingResponse(generate(), media_type="text/event-stream")
        
    except Exception as e:
        print(f"Error in image analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/message-with-image")
async def chat_message_with_image(
    message: str = Form(...),
    image: UploadFile = File(None),
    session_id: str = Form(None),
    analysis_mode: str = Form("analysis"),  # New parameter for analysis mode
    meal_type: str = Form(None),  # Accept meal type from frontend
    current_user: User = Depends(get_current_user)
):
    """
    Comprehensive health coach chat with full user context integration.
    Uses the unified AI system for personalized responses based on all health conditions.
    """
    image_url = None
    img_str = None
    analysis_data = None

    # --- Determine meal type: use provided meal_type first, then try to parse from message, then auto-detect ---
    if meal_type and meal_type.strip():
        # Use the meal type provided by the frontend (from dropdown selection)
        meal_type = meal_type.strip().lower()
    else:
        # Fall back to parsing from message text
        meal_type_match = re.search(r"\b(breakfast|lunch|dinner|snack)s?\b", message.lower())
        if meal_type_match:
            meal_type = meal_type_match.group(1)
        else:
            # Auto-determine based on current time when not explicitly mentioned
            current_hour = datetime.utcnow().hour
            if 5 <= current_hour < 11:
                meal_type = "breakfast"
            elif 11 <= current_hour < 16:
                meal_type = "lunch"
            elif 16 <= current_hour < 22:
                meal_type = "dinner"
            else:
                meal_type = "snack"

    # 🧠 GET COMPREHENSIVE USER CONTEXT - This is the key integration!
    try:
        # Import here to avoid circular import issues
        from main import get_comprehensive_user_context
        user_context = await get_comprehensive_user_context(current_user["email"])
        print(f"✅ Retrieved comprehensive context for user: {len(user_context.get('health_conditions', []))} conditions, {len(user_context.get('consumption_history', []))} recent meals")
    except Exception as e:
        print(f"❌ Error getting comprehensive context: {str(e)}")
        user_context = {"error": "Could not retrieve user context"}

    # 🧠 CONTEXT RETRIEVAL - Get recent chat history for context
    recent_context = None
    if has_logging_intent(message) and not image:
        # User wants to log something but didn't provide an image
        # Look for recent food analysis in chat history
        try:
            recent_messages = await get_recent_chat_history(current_user["id"], session_id, limit=10)
            for msg in recent_messages:
                if not msg.get("is_user", True) and "Food Analysis:" in msg.get("message_content", ""):
                    # Found a recent food analysis - extract the analysis data
                    msg_content = msg.get("message_content", "")
                    if "Food Analysis:" in msg_content:
                        # Try to extract food name and nutritional info from the message
                        lines = msg_content.split('\n')
                        food_name = None
                        calories = None
                        carbs = None
                        protein = None
                        fat = None
                        
                        for line in lines:
                            if "Food Analysis:" in line:
                                food_name = line.split("Food Analysis:")[1].strip().replace("**", "")
                            elif "Calories:" in line:
                                try:
                                    calories = int(line.split("Calories:")[1].strip().split()[0])
                                except:
                                    pass
                            elif "Carbs:" in line:
                                try:
                                    carbs = float(line.split("Carbs:")[1].strip().replace("g", ""))
                                except:
                                    pass
                            elif "Protein:" in line:
                                try:
                                    protein = float(line.split("Protein:")[1].strip().replace("g", ""))
                                except:
                                    pass
                            elif "Fat:" in line:
                                try:
                                    fat = float(line.split("Fat:")[1].strip().replace("g", ""))
                                except:
                                    pass
                        
                        if food_name:
                            recent_context = {
                                "food_name": food_name,
                                "estimated_portion": "1 serving",
                                "nutritional_info": {
                                    "calories": calories or 0,
                                    "carbohydrates": carbs or 0,
                                    "protein": protein or 0,
                                    "fat": fat or 0,
                                    "fiber": 0,
                                    "sugar": 0,
                                    "sodium": 0
                                },
                                "medical_rating": {
                                    "diabetes_suitability": "medium",
                                    "glycemic_impact": "medium",
                                    "recommended_frequency": "weekly",
                                    "portion_recommendation": "moderate portion"
                                },
                                "analysis_notes": f"Previously analyzed {food_name}"
                            }
                            break
        except Exception as e:
            print(f"Error retrieving context: {str(e)}")

    # If image is present, process it
    if image:
        contents = await image.read()
        try:
            img = Image.open(BytesIO(contents))
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            max_size = 1024
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=85, optimize=True)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            image_url = img_str
        except Exception as img_error:
            raise HTTPException(status_code=400, detail="Invalid or corrupted image file.")

    # Save user message (with or without image)
    user_message = await save_chat_message(
        current_user["id"],
        message,
        is_user=True,
        session_id=session_id,
        image_url=image_url
    )

    # If there's an image, analyze it based on the analysis mode
    if img_str:
        # Configure analysis based on mode
        if analysis_mode == "fridge":
            # Fridge analysis - different approach
            system_prompt = """You are a culinary AI assistant specializing in fridge analysis for diabetes patients. 
            Analyze the fridge/pantry image and provide helpful cooking suggestions.
            Return a JSON response with this format:
            {
                "items_detected": ["list of food items visible"],
                "suggested_meals": ["3-4 diabetes-friendly meal suggestions using these ingredients"],
                "cooking_tips": "practical cooking advice for diabetes management",
                "missing_ingredients": ["optional ingredients that would complement these items"],
                "health_notes": "diabetes-specific guidance for using these ingredients"
            }
            Focus on diabetes-friendly combinations and portion control."""
            
            user_prompt = "Analyze my fridge/pantry contents and suggest what I can cook that's suitable for diabetes management."
            
        else:
            # Food analysis (logging, analysis, question modes)
            system_prompt = """You are a nutrition analysis expert for diabetes patients. 
            Analyze the food image and return a structured JSON response with the following format:
            {
                "food_name": "descriptive name of the food",
                "estimated_portion": "portion size estimate",
                "nutritional_info": {
                    "calories": number,
                    "carbohydrates": number (in grams),
                    "protein": number (in grams),
                    "fat": number (in grams),
                    "fiber": number (in grams),
                    "sugar": number (in grams),
                    "sodium": number (in mg)
                },
                "medical_rating": {
                    "diabetes_suitability": "high/medium/low",
                    "glycemic_impact": "low/medium/high",
                    "recommended_frequency": "daily/weekly/occasional/avoid",
                    "portion_recommendation": "recommended portion size for diabetes patients"
                },
                "analysis_notes": "detailed explanation of nutritional analysis and diabetes considerations"
            }
            Provide realistic estimates based on visual analysis. Be conservative with diabetes suitability ratings."""
            
            if analysis_mode == "question":
                user_prompt = f"Analyze this food image and then answer this specific question: {message}"
            else:
                user_prompt = "Analyze this food image and provide detailed nutritional information and diabetes suitability rating."

        # Generate structured analysis using OpenAI
        response = get_openai_client().chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_str}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000,
            temperature=0.3
        )
        analysis_text = response.choices[0].message.content
        try:
            import json
            start_idx = analysis_text.find('{')
            end_idx = analysis_text.rfind('}') + 1
            json_str = analysis_text[start_idx:end_idx]
            analysis_data = json.loads(json_str)
        except Exception:
            analysis_data = None

    # Handle different analysis modes
    if analysis_mode == "fridge" and analysis_data:
        # Fridge analysis response
        items = analysis_data.get('items_detected', [])
        meals = analysis_data.get('suggested_meals', [])
        tips = analysis_data.get('cooking_tips', '')
        missing = analysis_data.get('missing_ingredients', [])
        health_notes = analysis_data.get('health_notes', '')
        
        assistant_message = f"""🧊 **Fridge Analysis Complete!**

📋 **Items Detected:**
{chr(10).join([f"• {item}" for item in items]) if items else "• No specific items detected"}

👩‍🍳 **Diabetes-Friendly Meal Suggestions:**
{chr(10).join([f"{i+1}. {meal}" for i, meal in enumerate(meals)]) if meals else "1. No specific suggestions available"}

💡 **Cooking Tips for Diabetes Management:**
{tips if tips else "Cook with minimal added sugars and focus on portion control."}

🛒 **Optional Ingredients to Enhance Your Meals:**
{chr(10).join([f"• {item}" for item in missing]) if missing else "• Your fridge looks well-stocked!"}

🏥 **Health Notes:**
{health_notes if health_notes else "Focus on balanced portions and regular meal timing for optimal blood sugar management."}

Would you like me to create a detailed recipe for any of these meal suggestions?"""

    elif analysis_mode == "logging" and analysis_data:
        # Food logging mode - create pending record for review instead of directly saving
        if pending_consumption_manager is not None:
            pending_id = await pending_consumption_manager.create_pending_record(
                user_email=current_user["email"],
                user_id=current_user["id"],
                analysis_data=analysis_data,
                image_url=img_str,
                meal_type=meal_type
            )
        else:
            # Fallback to direct logging if pending system unavailable
            print(f"[chat_message_with_image] Pending consumption manager unavailable, logging directly")
            consumption_data = {
                "food_name": analysis_data.get("food_name"),
                "estimated_portion": analysis_data.get("estimated_portion"),
                "nutritional_info": analysis_data.get("nutritional_info", {}),
                "image_analysis": analysis_data.get("analysis_notes"),
                "image_url": img_str
            }
            await save_consumption_record(current_user["email"], consumption_data, meal_type=meal_type)
            pending_id = None
        
        if pending_id:
            print(f"[chat_message_with_image] Created pending record {pending_id} for food logging review")
        else:
            print(f"[chat_message_with_image] Logged food directly to consumption history")
        
        meal_type_text = f" as your **{meal_type}**" if meal_type else ""
        
        assistant_message = f"""🍽️ **Food Analyzed for Logging{meal_type_text}: {analysis_data.get('food_name')}**

📊 **Nutritional Info** (per {analysis_data.get('estimated_portion')}):
• Calories: {analysis_data.get('nutritional_info', {}).get('calories', 'N/A')}
• Carbs: {analysis_data.get('nutritional_info', {}).get('carbohydrates', 'N/A')}g
• Protein: {analysis_data.get('nutritional_info', {}).get('protein', 'N/A')}g
• Fat: {analysis_data.get('nutritional_info', {}).get('fat', 'N/A')}g
• Fiber: {analysis_data.get('nutritional_info', {}).get('fiber', 'N/A')}g

🩺 **Diabetes Suitability:** {analysis_data.get('medical_rating', {}).get('diabetes_suitability', 'N/A').title()}
📈 **Glycemic Impact:** {analysis_data.get('medical_rating', {}).get('glycemic_impact', 'N/A').title()}

🔍 **Please review the analysis above and use the Accept/Edit/Delete options to proceed with logging.**

💡 **Analysis Notes:** {analysis_data.get('analysis_notes', 'No additional notes available.')}"""

    elif analysis_mode == "question" and analysis_data:
        # Question mode - provide specific answer based on the user's question
        assistant_message = f"""❓ **Question about {analysis_data.get('food_name', 'your food')}:**

Based on the image analysis, here's what I can tell you:

📊 **Nutritional Breakdown** (per {analysis_data.get('estimated_portion')}):
• Calories: {analysis_data.get('nutritional_info', {}).get('calories', 'N/A')}
• Carbs: {analysis_data.get('nutritional_info', {}).get('carbohydrates', 'N/A')}g
• Protein: {analysis_data.get('nutritional_info', {}).get('protein', 'N/A')}g
• Fat: {analysis_data.get('nutritional_info', {}).get('fat', 'N/A')}g
• Fiber: {analysis_data.get('nutritional_info', {}).get('fiber', 'N/A')}g
• Sugar: {analysis_data.get('nutritional_info', {}).get('sugar', 'N/A')}g

🩺 **For Diabetes Management:**
• **Suitability:** {analysis_data.get('medical_rating', {}).get('diabetes_suitability', 'N/A').title()}
• **Glycemic Impact:** {analysis_data.get('medical_rating', {}).get('glycemic_impact', 'N/A').title()}
• **Recommended Frequency:** {analysis_data.get('medical_rating', {}).get('recommended_frequency', 'N/A')}

💡 **Additional Notes:** {analysis_data.get('analysis_notes', 'No additional analysis available.')}

Is there anything specific about this food you'd like me to explain further?"""

    elif analysis_mode == "analysis" and analysis_data:
        # Pure analysis mode - no logging
        assistant_message = f"""🔍 **Food Analysis: {analysis_data.get('food_name')}**

📊 **Nutritional Breakdown** (per {analysis_data.get('estimated_portion')}):
• Calories: {analysis_data.get('nutritional_info', {}).get('calories', 'N/A')}
• Carbs: {analysis_data.get('nutritional_info', {}).get('carbohydrates', 'N/A')}g
• Protein: {analysis_data.get('nutritional_info', {}).get('protein', 'N/A')}g
• Fat: {analysis_data.get('nutritional_info', {}).get('fat', 'N/A')}g
• Fiber: {analysis_data.get('nutritional_info', {}).get('fiber', 'N/A')}g
• Sugar: {analysis_data.get('nutritional_info', {}).get('sugar', 'N/A')}g
• Sodium: {analysis_data.get('nutritional_info', {}).get('sodium', 'N/A')}mg

🩺 **Diabetes Management Insights:**
• **Suitability:** {analysis_data.get('medical_rating', {}).get('diabetes_suitability', 'N/A').title()}
• **Glycemic Impact:** {analysis_data.get('medical_rating', {}).get('glycemic_impact', 'N/A').title()}
• **Recommended Frequency:** {analysis_data.get('medical_rating', {}).get('recommended_frequency', 'N/A')}
• **Portion Recommendation:** {analysis_data.get('medical_rating', {}).get('portion_recommendation', 'N/A')}

💡 **Analysis Notes:** {analysis_data.get('analysis_notes', 'No additional notes available.')}

Would you like me to log this to your consumption history? Just say "log this as my [breakfast/lunch/dinner/snack]"!"""

    elif has_logging_intent(message) and (analysis_data or recent_context):
        # Legacy logging support
        food_data = analysis_data or recent_context
        consumption_data = {
            "food_name": food_data.get("food_name"),
            "estimated_portion": food_data.get("estimated_portion"),
            "nutritional_info": food_data.get("nutritional_info", {}),
            "image_analysis": food_data.get("analysis_notes"),
            "image_url": img_str if analysis_data else None
        }
        await save_consumption_record(current_user["email"], consumption_data, meal_type=meal_type)

        # Trigger meal plan recalibration after logging food
        try:
            from main import trigger_meal_plan_recalibration
            profile = current_user.get("profile", {})
            await trigger_meal_plan_recalibration(current_user["email"], profile)
            print(f"[chat_message_with_image] Meal plan recalibrated after legacy food logging")
        except Exception as recal_error:
            print(f"[chat_message_with_image] Error in meal plan recalibration: {recal_error}")

        context_note = " (from previous analysis)" if recent_context and not analysis_data else ""
        meal_type_text = f" as your **{meal_type}**" if meal_type else ""
        
        assistant_message = f"""🍽️ **Food Logged{meal_type_text}: {food_data.get('food_name')}{context_note}**

📊 **Nutritional Info** (per {food_data.get('estimated_portion')}):
• Calories: {food_data.get('nutritional_info', {}).get('calories', 'N/A')}
• Carbs: {food_data.get('nutritional_info', {}).get('carbohydrates', 'N/A')}g
• Protein: {food_data.get('nutritional_info', {}).get('protein', 'N/A')}g
• Fat: {food_data.get('nutritional_info', {}).get('fat', 'N/A')}g

🩺 **Diabetes Suitability:** {food_data.get('medical_rating', {}).get('diabetes_suitability', 'N/A').title()}

✅ **Successfully recorded to your consumption history with meal type: {meal_type or 'unspecified'}!**

Your meal plan will be updated to reflect this logged meal."""

    else:
        # 🚀 USE COMPREHENSIVE AI SYSTEM FOR NON-LOGGING RESPONSES
        try:
            # Determine query type
            nutrition_fields = extract_nutrition_question(message)
            
            if img_str and analysis_data and nutrition_fields:
                query_type = "nutrition_question"
                specific_data = {
                    "nutrition_fields": nutrition_fields,
                    "food_data": analysis_data,
                    "user_message": message
                }
            elif img_str and analysis_data:
                query_type = "food_analysis"
                specific_data = {
                    "food_data": analysis_data,
                    "user_message": message
                }
            elif has_logging_intent(message) and not image and not recent_context:
                query_type = "logging_help"
                specific_data = {
                    "user_message": message
                }
            else:
                query_type = "general_health_chat"
                specific_data = {
                    "user_message": message
                }

            # 🧠 GET AI RESPONSE USING COMPREHENSIVE SYSTEM
            from main import get_ai_health_coach_response
            assistant_message = await get_ai_health_coach_response(
                user_context=user_context,
                query_type=query_type,
                specific_data=specific_data
            )
            
            print(f"✅ Generated comprehensive AI response for query type: {query_type}")

        except Exception as e:
            print(f"❌ Error in comprehensive AI system: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            
            # Fallback responses
            nutrition_fields = extract_nutrition_question(message)
            
            if img_str and analysis_data and nutrition_fields:
                # Focused answer for specific nutrition questions
                nutri = analysis_data.get('nutritional_info', {})
                food_name = analysis_data.get('food_name', 'this food')
                portion = analysis_data.get('estimated_portion', '')
                responses = []
                for field in nutrition_fields:
                    value = nutri.get(field, None)
                    if value is not None:
                        field_label = field.capitalize()
                        unit = 'mg' if field == 'sodium' else 'g' if field in ['protein', 'carbohydrates', 'fat', 'fiber', 'sugar'] else 'kcal' if field == 'calories' else ''
                        responses.append(f"{field_label} in {food_name} ({portion}): {value} {unit}".strip())
                
                if responses:
                    assistant_message = f"📊 **Nutrition Info:**\n\n" + '\n'.join(responses)
                    assistant_message += f"\n\n⚠️ **Note:** Using fallback response - comprehensive AI system temporarily unavailable."
                else:
                    assistant_message = "Sorry, I couldn't find that specific nutrition information for this food."
                    
            elif img_str and analysis_data:
                # General food analysis without logging
                assistant_message = f"""🔍 **Food Analysis: {analysis_data.get('food_name')}**

📊 **Nutritional Breakdown** (per {analysis_data.get('estimated_portion')}):
• Calories: {analysis_data.get('nutritional_info', {}).get('calories', 'N/A')}
• Carbs: {analysis_data.get('nutritional_info', {}).get('carbohydrates', 'N/A')}g
• Protein: {analysis_data.get('nutritional_info', {}).get('protein', 'N/A')}g
• Fat: {analysis_data.get('nutritional_info', {}).get('fat', 'N/A')}g

💡 **Notes:** {analysis_data.get('analysis_notes', 'No additional notes available.')}

Would you like me to record this to your consumption history? Just say "log this as my [breakfast/lunch/dinner/snack]"!

⚠️ **Note:** Using fallback response - comprehensive AI system temporarily unavailable."""
            elif has_logging_intent(message) and not image and not recent_context:
                # User wants to log something but we have no context
                assistant_message = """🤔 **I'd love to help you log your food!**

However, I don't see any recent food analysis in our conversation. To log food, you can:

1. **Share a photo** of your food with a message like "this is my snack"
2. **Or first share a photo** for analysis, then say "log this as my [meal type]"

I'm here to help track your nutrition and provide personalized health guidance! 📸🍽️

⚠️ **Note:** Using fallback response - comprehensive AI system temporarily unavailable."""
            else:
                assistant_message = """Hello! I'm your comprehensive health coach. I can help you with:

🍽️ **Food Analysis & Logging** - Upload food images for nutritional analysis
🏥 **Multi-Condition Health Management** - Personalized advice for all your health conditions  
📊 **Meal Planning & Tracking** - Smart recommendations based on your health profile
💊 **Medication & Treatment Integration** - Holistic health management

How can I help you today?

⚠️ **Note:** Using fallback response - comprehensive AI system temporarily unavailable."""

    # Save assistant response
    await save_chat_message(
        current_user["email"],
        assistant_message,
        is_user=False,
        session_id=session_id
    )

    # --- Stream response back so the frontend can progressively render ---
    import json as _json

    def _event_stream():
        # Include pending data if this was a logging operation
        if analysis_mode == "logging" and analysis_data and pending_id:
            # Include pending data for frontend to show review dialog
            chunk = _json.dumps({
                "content": assistant_message,
                "pending_id": pending_id,
                "analysis": analysis_data
            })
        else:
            chunk = _json.dumps({"content": assistant_message})
        yield f"data: {chunk}\n\n"

    return StreamingResponse(_event_stream(), media_type="text/event-stream")