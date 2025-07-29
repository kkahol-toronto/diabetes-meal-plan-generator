from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.responses import JSONResponse
from typing import Dict, Any
from datetime import datetime
import json
import os
from models import User
from routers.auth import get_current_user
from database import save_consumption_record
from services.openai_service import get_openai_client
from services.consumption_analysis import trigger_meal_plan_recalibration
import traceback

router = APIRouter()

# Handle pending consumption import gracefully due to event loop issues
try:
    from pending_consumption import pending_consumption_manager
except RuntimeError as e:
    if "no running event loop" in str(e):
        print(f"Warning: Could not import pending_consumption_manager due to event loop issue: {e}")
        pending_consumption_manager = None
    else:
        raise

@router.get("/consumption/pending/{pending_id}")
async def get_pending_consumption(
    pending_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a pending consumption record"""
    try:
        record = pending_consumption_manager.get_pending_record(pending_id)
        
        if not record:
            raise HTTPException(status_code=404, detail="Pending record not found or expired")
        
        # Verify user ownership
        if record.user_email != current_user["email"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "pending_record": record.to_dict(),
            "analysis": {
                "food_name": record.food_name,
                "estimated_portion": record.estimated_portion,
                "nutritional_info": record.nutritional_info,
                "medical_rating": record.medical_rating,
                "analysis_notes": record.analysis_notes
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[get_pending_consumption] Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get pending record")

@router.post("/consumption/pending/{pending_id}/accept")
async def accept_pending_consumption(
    pending_id: str,
    current_user: User = Depends(get_current_user)
):
    """Accept a pending consumption record and save to database"""
    try:
        record = pending_consumption_manager.get_pending_record(pending_id)
        
        if not record:
            raise HTTPException(status_code=404, detail="Pending record not found or expired")
        
        # Verify user ownership
        if record.user_email != current_user["email"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Prepare consumption data for saving
        consumption_data = {
            "food_name": record.food_name,
            "estimated_portion": record.estimated_portion,
            "nutritional_info": record.nutritional_info,
            "medical_rating": record.medical_rating,
            "image_analysis": record.analysis_notes,
            "image_url": record.image_url,
            "meal_type": record.meal_type or ""
        }
        
        # Save to consumption history
        consumption_record = await save_consumption_record(
            current_user["email"], 
            consumption_data, 
            meal_type=record.meal_type or ""
        )
        
        # Trigger meal plan recalibration
        try:
            profile = current_user.get("profile", {})
            await trigger_meal_plan_recalibration(current_user["email"], profile)
            print(f"[accept_pending_consumption] Meal plan recalibrated after accepting food")
        except Exception as recal_error:
            print(f"[accept_pending_consumption] Error in meal plan recalibration: {recal_error}")
        
        # Delete the pending record
        pending_consumption_manager.delete_pending_record(pending_id)
        
        print(f"[accept_pending_consumption] Accepted and saved pending record {pending_id}")
        
        return {
            "success": True,
            "message": f"Successfully logged: {record.food_name}",
            "consumption_record_id": consumption_record["id"],
            "food_name": record.food_name,
            "nutritional_summary": {
                "calories": record.nutritional_info.get("calories", 0),
                "carbohydrates": record.nutritional_info.get("carbohydrates", 0),
                "protein": record.nutritional_info.get("protein", 0),
                "fat": record.nutritional_info.get("fat", 0)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[accept_pending_consumption] Error: {str(e)}")
        print(f"[accept_pending_consumption] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to accept pending record")

@router.put("/consumption/pending/{pending_id}")
async def update_pending_consumption(
    pending_id: str,
    updates: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Update a pending consumption record during editing"""
    try:
        record = pending_consumption_manager.get_pending_record(pending_id)
        
        if not record:
            raise HTTPException(status_code=404, detail="Pending record not found or expired")
        
        # Verify user ownership
        if record.user_email != current_user["email"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Update the pending record
        success = pending_consumption_manager.update_pending_record(pending_id, updates)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update pending record")
        
        # Get updated record
        updated_record = pending_consumption_manager.get_pending_record(pending_id)
        
        return {
            "success": True,
            "message": "Pending record updated successfully",
            "updated_record": updated_record.to_dict() if updated_record else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[update_pending_consumption] Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update pending record")

@router.delete("/consumption/pending/{pending_id}")
async def delete_pending_consumption(
    pending_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a pending consumption record"""
    try:
        record = pending_consumption_manager.get_pending_record(pending_id)
        
        if not record:
            raise HTTPException(status_code=404, detail="Pending record not found or expired")
        
        # Verify user ownership
        if record.user_email != current_user["email"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete the pending record
        success = pending_consumption_manager.delete_pending_record(pending_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to delete pending record")
        
        print(f"[delete_pending_consumption] Deleted pending record {pending_id}")
        
        return {
            "success": True,
            "message": "Food log discarded successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[delete_pending_consumption] Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete pending record")

@router.post("/consumption/pending/{pending_id}/chat")
async def chat_with_pending_consumption(
    pending_id: str,
    chat_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Chat interface for editing pending consumption record using AI"""
    try:
        record = pending_consumption_manager.get_pending_record(pending_id)
        
        if not record:
            raise HTTPException(status_code=404, detail="Pending record not found or expired")
        
        # Verify user ownership
        if record.user_email != current_user["email"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        user_message = chat_data.get("message", "").strip()
        if not user_message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Create AI prompt for editing food details
        current_food_info = f"""
        Current Food Details:
        - Name: {record.food_name}
        - Portion: {record.estimated_portion}
        - Calories: {record.nutritional_info.get('calories', 0)}
        - Carbohydrates: {record.nutritional_info.get('carbohydrates', 0)}g
        - Protein: {record.nutritional_info.get('protein', 0)}g
        - Fat: {record.nutritional_info.get('fat', 0)}g
        - Fiber: {record.nutritional_info.get('fiber', 0)}g
        - Sugar: {record.nutritional_info.get('sugar', 0)}g
        - Sodium: {record.nutritional_info.get('sodium', 0)}mg
        """
        
        ai_prompt = f"""You are a helpful nutrition assistant helping a user edit their food log details. 

{current_food_info}

The user said: "{user_message}"

Your task is to:
1. Understand what the user wants to change
2. Provide a conversational response
3. If the user is making a specific change, return a JSON object with the updates

If the user is making a clear change request, respond with:
{{
    "response": "conversational response to the user",
    "updates": {{
        "food_name": "new name if changed",
        "estimated_portion": "new portion if changed", 
        "nutritional_info": {{
            "calories": number,
            "carbohydrates": number,
            "protein": number,
            "fat": number,
            "fiber": number,
            "sugar": number,
            "sodium": number
        }}
    }},
    "has_updates": true
}}

If the user is just asking questions or being unclear, respond with:
{{
    "response": "helpful conversational response",
    "has_updates": false
}}
Examples of what to detect:
- "French Fries, 1 Cup" → Change food name to "French Fries" and portion to "1 Cup"
- "Make it 500 calories" → Update calories to 500
- "Change to grilled chicken" → Update food name to "grilled chicken"
- "2 servings" → Update portion to "2 servings"

Be conversational and helpful. If you make nutritional updates, recalculate all values proportionally when possible."""

        # Get AI response
        response = get_openai_client().chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful nutrition assistant. Always respond with valid JSON."
                },
                {
                    "role": "user", 
                    "content": ai_prompt
                }
            ],
            max_tokens=800,
            temperature=0.3
        )
        
        response_text = response.choices[0].message.content
        
        try:
            # Parse AI response
            import json
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            json_str = response_text[start_idx:end_idx]
            ai_response = json.loads(json_str)
            
            # Apply updates if any
            if ai_response.get("has_updates", False) and ai_response.get("updates"):
                updates = ai_response["updates"]
                success = pending_consumption_manager.update_pending_record(pending_id, updates)
                
                if not success:
                    raise HTTPException(status_code=400, detail="Failed to update pending record")
            
            # Get updated record for response
            updated_record = pending_consumption_manager.get_pending_record(pending_id)
            
            return {
                "response": ai_response.get("response", "I've processed your request."),
                "has_updates": ai_response.get("has_updates", False),
                "updated_record": updated_record.to_dict() if updated_record else None
            }
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[chat_with_pending_consumption] Error parsing AI response: {str(e)}")
            # Fallback response
            return {
                "response": "I understand you want to make changes. Could you please be more specific about what you'd like to update?",
                "has_updates": False,
                "updated_record": record.to_dict()
            }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[chat_with_pending_consumption] Error: {str(e)}")
        print(f"[chat_with_pending_consumption] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to process chat message") 