"""
Consumption Analysis Router (Part 1 of 3)
Handles core food analysis and recording functionality including image analysis, 
structured nutrition analysis, and text-based food analysis.
This module provides the foundational analysis capabilities for the consumption tracking system.
"""

import os
import json
import base64
import traceback
from io import BytesIO

from fastapi import APIRouter, HTTPException, Depends, File, Form, UploadFile
from PIL import Image

from models import User
from routers.auth import get_current_user
from database import save_consumption_record, save_chat_message
from services.openai_service import get_openai_client, robust_openai_call
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

@router.post("/consumption/analyze-and-record")
async def analyze_and_record_food(
    image: UploadFile = File(...),
    session_id: str = Form(None),
    meal_type: str = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Analyze food image and optionally record to consumption history"""
    try:
        print(f"[analyze_and_record_food] Starting analysis for user {current_user['id']}")
        
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
            
            print("[analyze_and_record_food] Image processed and converted to base64")
            
        except Exception as img_error:
            print(f"[analyze_and_record_food] Image processing error: {str(img_error)}")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid or corrupted image file. Please upload a valid image in one of these formats: {', '.join(allowed_extensions)}"
            )
        
        # Generate structured analysis using OpenAI
        response = get_openai_client().chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {
                    "role": "system",
                    "content": """You are a nutrition analysis expert for diabetes patients. 
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
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this food image and provide detailed nutritional information and diabetes suitability rating."
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
            max_tokens=800,
            temperature=0.3
        )
        
        print("[analyze_and_record_food] Received analysis from OpenAI")
        
        # Get the response content
        analysis_text = response.choices[0].message.content
        
        # Try to parse JSON from the response
        try:
            import json
            # Extract JSON from response (in case there's additional text)
            start_idx = analysis_text.find('{')
            end_idx = analysis_text.rfind('}') + 1
            json_str = analysis_text[start_idx:end_idx]
            analysis_data = json.loads(json_str)
            print(f"[analyze_and_record_food] Successfully parsed analysis data: {analysis_data}")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[analyze_and_record_food] Error parsing analysis data: {str(e)}")
            # If JSON parsing fails, create a structured response from the text
            analysis_data = {
                "food_name": "Unknown food item",
                "estimated_portion": "Unable to determine",
                "nutritional_info": {
                    "calories": 0,
                    "carbohydrates": 0,
                    "protein": 0,
                    "fat": 0,
                    "fiber": 0,
                    "sugar": 0,
                    "sodium": 0
                },
                "medical_rating": {
                    "diabetes_suitability": "unknown",
                    "glycemic_impact": "unknown",
                    "recommended_frequency": "consult nutritionist",
                    "portion_recommendation": "consult nutritionist"
                },
                "analysis_notes": analysis_text
            }
        
        # Prepare consumption data
        consumption_data = {
            "food_name": analysis_data.get("food_name"),
            "estimated_portion": analysis_data.get("estimated_portion"),
            "nutritional_info": analysis_data.get("nutritional_info", {}),
            "medical_rating": analysis_data.get("medical_rating", {}),
            "image_analysis": analysis_data.get("analysis_notes"),
            "image_url": img_str,
            "meal_type": (meal_type or "").lower()
        }
        
        print(f"[analyze_and_record_food] Prepared consumption data: {consumption_data}")
        
        # Save to consumption history
        print(f"[analyze_and_record_food] Attempting to save consumption record for user {current_user['id']}")
        # Get user timezone for proper meal type determination
        user_timezone = current_user.get("profile", {}).get("timezone", "UTC")
        consumption_record = await save_consumption_record(current_user["email"], consumption_data, meal_type=meal_type or "", user_timezone=user_timezone)
        print(f"[analyze_and_record_food] Successfully saved consumption record with ID: {consumption_record['id']}")
        
        # Also save to chat if session_id is provided
        if session_id:
            print(f"[analyze_and_record_food] Saving to chat with session_id: {session_id}")
            # Save user message with image
            await save_chat_message(
                current_user["id"],
                "Recorded food consumption",
                is_user=True,
                session_id=session_id,
                image_url=img_str
            )
            
            # Save assistant response
            summary_message = f"**Food Recorded: {analysis_data.get('food_name')}**\n\n"
            summary_message += f"📊 **Nutritional Info (per {analysis_data.get('estimated_portion')}):**\n"
            summary_message += f"- Calories: {analysis_data.get('nutritional_info', {}).get('calories', 'N/A')}\n"
            summary_message += f"- Carbs: {analysis_data.get('nutritional_info', {}).get('carbohydrates', 'N/A')}g\n"
            summary_message += f"- Protein: {analysis_data.get('nutritional_info', {}).get('protein', 'N/A')}g\n"
            summary_message += f"- Fat: {analysis_data.get('nutritional_info', {}).get('fat', 'N/A')}g\n\n"
            summary_message += f"🩺 **Diabetes Suitability:** {analysis_data.get('medical_rating', {}).get('diabetes_suitability', 'N/A').title()}\n"
            summary_message += f"📈 **Glycemic Impact:** {analysis_data.get('medical_rating', {}).get('glycemic_impact', 'N/A').title()}\n\n"
            summary_message += f"💡 **Notes:** {analysis_data.get('analysis_notes', '')}"
            
            await save_chat_message(
                current_user["email"],
                summary_message,
                is_user=False,
                session_id=session_id
            )
            print("[analyze_and_record_food] Successfully saved chat messages")
        
        return {"consumption_record_id": consumption_record["id"], "analysis": analysis_data}
        
    except Exception as e:
        print(f"[analyze_and_record_food] Error: {str(e)}")
        print(f"[analyze_and_record_food] Full error details:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/consumption/analyze-only")
async def analyze_food_only(
    image: UploadFile = File(...),
    meal_type: str = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Analyze food image but don't save to database - returns pending_id for Accept/Edit/Delete"""
    try:
        print(f"[analyze_food_only] Starting analysis for user {current_user['id']}")
        
        # Read and validate image (same logic as analyze-and-record)
        contents = await image.read()
        
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
            # Process image (same logic as analyze-and-record)
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
            
        except Exception as img_error:
            print(f"[analyze_food_only] Image processing error: {str(img_error)}")
            raise HTTPException(status_code=400, detail="Invalid or corrupted image file.")
        
        # Generate structured analysis using OpenAI (same logic as analyze-and-record)
        response = get_openai_client().chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {
                    "role": "system",
                    "content": """You are a nutrition analysis expert for diabetes patients. 
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
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this food image and provide detailed nutritional information and diabetes suitability rating."
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
            max_tokens=800,
            temperature=0.3
        )
        
        analysis_text = response.choices[0].message.content
        
        # Parse JSON from response
        try:
            import json
            start_idx = analysis_text.find('{')
            end_idx = analysis_text.rfind('}') + 1
            json_str = analysis_text[start_idx:end_idx]
            analysis_data = json.loads(json_str)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[analyze_food_only] Error parsing analysis data: {str(e)}")
            analysis_data = {
                "food_name": "Unknown food item",
                "estimated_portion": "Unable to determine",
                "nutritional_info": {
                    "calories": 0,
                    "carbohydrates": 0,
                    "protein": 0,
                    "fat": 0,
                    "fiber": 0,
                    "sugar": 0,
                    "sodium": 0
                },
                "medical_rating": {
                    "diabetes_suitability": "unknown",
                    "glycemic_impact": "unknown",
                    "recommended_frequency": "consult nutritionist",
                    "portion_recommendation": "consult nutritionist"
                },
                "analysis_notes": analysis_text
            }
        
        # Create pending record instead of saving to database
        if pending_consumption_manager is not None:
            pending_id = await pending_consumption_manager.create_pending_record(
                user_email=current_user["email"],
                user_id=current_user["id"],
                analysis_data=analysis_data,
                image_url=img_str,
                meal_type=meal_type
            )
            print(f"[analyze_food_only] Created pending record {pending_id}")
        else:
            print(f"[analyze_food_only] Pending consumption manager unavailable, using fallback")
            pending_id = f"fallback_{current_user['id']}_{analysis_data.get('food_name', 'unknown')}"
        
        return {
            "pending_id": pending_id,
            "analysis": analysis_data,
            "message": "Food analyzed successfully. Use Accept/Edit/Delete options to proceed."
        }
        
    except Exception as e:
        print(f"[analyze_food_only] Error: {str(e)}")
        print(f"[analyze_food_only] Full error details:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/consumption/analyze-text-only")
async def analyze_text_food_only(
    food_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Analyze text-based food input but don't save to database - returns pending_id for Accept/Edit/Delete"""
    try:
        print(f"[analyze_text_food_only] Starting analysis for user {current_user['id']}")
        print(f"[analyze_text_food_only] Food data received: {food_data}")
        
        food_name = food_data.get("food_name", "").strip()
        portion = food_data.get("portion", "medium portion").strip()
        meal_type = food_data.get("meal_type", "").strip()
        
        if not food_name:
            raise HTTPException(status_code=400, detail="Food name is required")
        
        # Use AI to estimate nutritional values (same logic as quick-log)
        prompt = f"""
        Analyze the food item: {food_name} ({portion})
        
        Provide a comprehensive JSON response with this exact structure:
        {{
            "food_name": "{food_name}",
            "estimated_portion": "{portion}",
            "nutritional_info": {{
                "calories": number,
                "carbohydrates": number,
                "protein": number,
                "fat": number,
                "fiber": number,
                "sugar": number,
                "sodium": number
            }},
            "medical_rating": {{
                "diabetes_suitability": "high/medium/low",
                "glycemic_impact": "low/medium/high",
                "recommended_frequency": "daily/weekly/occasional/avoid",
                "portion_recommendation": "recommended portion size for diabetes patients"
            }},
            "analysis_notes": "detailed explanation of nutritional analysis and diabetes considerations"
        }}
        
        Provide realistic nutritional estimates. Be conservative with diabetes suitability ratings.
        Focus on how this food affects blood sugar and overall diabetes management.
        """
        
        # Generate analysis using OpenAI with robust fallback
        analysis_data = None
        ai_result = await robust_openai_call(
            messages=[
                {
                    "role": "system",
                    "content": "You are a comprehensive nutrition analysis expert specializing in diabetes management. Provide accurate nutritional estimates and diabetes-specific guidance."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=800,
            temperature=0.3,
            context="analyze_text_food_only"
        )

        if ai_result.get("success"):
            analysis_text = ai_result.get("content", "")
            # Parse JSON from response
            try:
                import json
                start_idx = analysis_text.find('{')
                end_idx = analysis_text.rfind('}') + 1
                json_str = analysis_text[start_idx:end_idx]
                analysis_data = json.loads(json_str)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"[analyze_text_food_only] Error parsing analysis data: {str(e)}")
                analysis_data = None

        if analysis_data is None:
            # Deterministic fallback to avoid 500s when AI fails (e.g., 401 key issues)
            print("[analyze_text_food_only] Using deterministic fallback due to AI failure")
            analysis_data = {
                "food_name": food_name,
                "estimated_portion": portion,
                "nutritional_info": {
                    "calories": 200,
                    "carbohydrates": 30,
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
                    "portion_recommendation": "moderate portions recommended"
                },
                "analysis_notes": f"Nutritional analysis for {food_name}. AI unavailable; using conservative defaults."
            }
        
        # Create pending record
        if pending_consumption_manager is not None:
            pending_id = await pending_consumption_manager.create_pending_record(
                user_email=current_user["email"],
                user_id=current_user["id"],
                analysis_data=analysis_data,
                image_url=None,  # No image for text-based analysis
                meal_type=meal_type
            )
            print(f"[analyze_text_food_only] Created pending record {pending_id}")
        else:
            print(f"[analyze_text_food_only] Pending consumption manager unavailable, using fallback")
            pending_id = f"text_fallback_{current_user['id']}_{food_name}"
        
        return {
            "pending_id": pending_id,
            "analysis": analysis_data,
            "message": "Food analyzed successfully. Use Accept/Edit/Delete options to proceed."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[analyze_text_food_only] Error: {str(e)}")
        print(f"[analyze_text_food_only] Full error details:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to analyze food: {str(e)}")