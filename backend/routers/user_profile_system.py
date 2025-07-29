"""
User Profile System Router
Handles all user profile management, shopping lists, and recipe storage functionality.
This module provides comprehensive user data management capabilities.
"""

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Request as FastAPIRequest
from fastapi.responses import JSONResponse

from models import User
from routers.auth import get_current_user
from database import (
    get_user_by_email, get_patient_by_id, get_user_shopping_lists, 
    save_shopping_list, get_user_recipes, save_recipes, user_container
)
from utils import validate_and_normalize_profile, calculate_profile_completeness

router = APIRouter()

@router.get("/users/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    print("Current user data:", current_user)  # Add logging
    
    # Get patient info if available
    patient_name = None
    if current_user.get("patient_id"):
        try:
            patient = await get_patient_by_id(current_user["patient_id"])
            if patient:
                patient_name = patient.get("name")
        except Exception as e:
            print(f"Error fetching patient info: {str(e)}")
    
    return {
        "email": current_user["email"],
        "username": current_user["username"],
        "is_admin": current_user.get("is_admin", False),
        "name": patient_name,
        "consent_given": current_user.get("consent_given", False),
        "consent_timestamp": current_user.get("consent_timestamp", None),
        "policy_version": current_user.get("policy_version", None)
    }

@router.post("/user/profile")
async def save_user_profile(
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        data = await request.json()
        profile = data.get("profile")
        if not profile:
            raise HTTPException(status_code=400, detail="No profile data provided")
        
        # Validate and normalize profile data
        profile = validate_and_normalize_profile(profile)
        
        user_doc = await get_user_by_email(current_user["email"])
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")

        # Update the profile with validation
        user_doc["profile"] = profile
        user_doc["updated_at"] = datetime.utcnow().isoformat()
        
        # Log profile structure for debugging
        print(f"[save_user_profile] Saving profile for {current_user['email']}:")
        print(f"[save_user_profile] Profile fields: {list(profile.keys())}")
        print(f"[save_user_profile] Array fields: {[k for k, v in profile.items() if isinstance(v, list)]}")
        print(f"[save_user_profile] Dict fields: {[k for k, v in profile.items() if isinstance(v, dict)]}")
        
        # Save to database with proper error handling
        try:
            result = user_container.replace_item(item=user_doc["id"], body=user_doc)
            print(f"[save_user_profile] Profile saved to user doc successfully for {current_user['email']}")
            
            # Also create/update a separate profile record for easier querying
            profile_record = {
                "id": f"profile_{current_user['email']}",
                "type": "user_profile",
                "user_id": current_user["email"],
                "profile": profile,
                "updated_at": datetime.utcnow().isoformat(),
                "created_at": user_doc.get("created_at", datetime.utcnow().isoformat()),
                "profile_completeness": calculate_profile_completeness(profile)
            }
            
            user_container.upsert_item(body=profile_record)
            print(f"[save_user_profile] Profile record upserted for {current_user['email']}")
            
        except Exception as db_error:
            print(f"[save_user_profile] Database error: {str(db_error)}")
            raise HTTPException(status_code=500, detail=f"Failed to save profile: {str(db_error)}")
        
        return {
            "message": "Profile saved successfully", 
            "timestamp": datetime.utcnow().isoformat(),
            "profile_completeness": calculate_profile_completeness(profile)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[save_user_profile] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/user/profile-analysis")
async def get_profile_analysis(current_user: User = Depends(get_current_user)):
    """Show users exactly what comprehensive profile data is being used for AI meal planning."""
    try:
        user_email = current_user["email"]
        user_doc = await get_user_by_email(user_email)
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_profile = user_doc.get("profile", {})
        
        # Quick analysis of what data is available for AI
        analysis = {
            "medical_data_available": {
                "conditions": len(user_profile.get('medicalConditions', [])) > 0,
                "medications": len(user_profile.get('currentMedications', [])) > 0,
                "lab_values": len(user_profile.get('labValues', {})) > 0,
                "vital_signs": bool(user_profile.get('height') and user_profile.get('weight'))
            },
            "dietary_intelligence": {
                "cuisine_preferences": len(user_profile.get('dietType', [])) > 0,
                "dietary_features": len(user_profile.get('dietaryFeatures', [])) > 0,
                "restrictions_allergies": len(user_profile.get('dietaryRestrictions', []) + user_profile.get('allergies', [])) > 0,
                "food_preferences": len(user_profile.get('foodPreferences', [])) > 0
            },
            "lifestyle_factors": {
                "activity_level": bool(user_profile.get('workActivityLevel') and user_profile.get('exerciseFrequency')),
                "health_goals": len(user_profile.get('primaryGoals', [])) > 0,
                "meal_prep_info": bool(user_profile.get('mealPrepCapability')),
                "eating_schedule": bool(user_profile.get('eatingSchedule'))
            },
            "ai_utilization_summary": "The AI uses comprehensive health data including medical conditions, medications, dietary preferences, physical characteristics, activity levels, and health goals for personalized meal planning"
        }
        return analysis
    except Exception as e:
        print(f"Error in profile analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Profile analysis failed")

@router.get("/user/profile")
async def get_user_profile(current_user: User = Depends(get_current_user)):
    try:
        user_doc = await get_user_by_email(current_user["email"])
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        profile = user_doc.get("profile", {})
        
        # If no profile in user doc, try to get from separate profile record
        if not profile:
            try:
                profile_query = f"SELECT * FROM c WHERE c.type = 'user_profile' AND c.user_id = '{current_user['email']}'"
                profiles = list(user_container.query_items(query=profile_query, enable_cross_partition_query=True))
                if profiles:
                    profile = profiles[0].get('profile', {})
                    print(f"[get_user_profile] Loaded profile from separate record for {current_user['email']}")
            except Exception as e:
                print(f"[get_user_profile] Error loading profile record: {str(e)}")
        
        # If still no profile, return empty dict wrapped in profile object
        if not profile:
            print(f"[get_user_profile] No profile found for user {current_user['email']}")
            return {"profile": {}}
        
        # Log profile structure for debugging
        print(f"[get_user_profile] Profile loaded for {current_user['email']}:")
        print(f"[get_user_profile] Profile fields: {list(profile.keys())}")
        print(f"[get_user_profile] Array fields: {[k for k, v in profile.items() if isinstance(v, list)]}")
        print(f"[get_user_profile] Dict fields: {[k for k, v in profile.items() if isinstance(v, dict)]}")
        
        # Ensure profile is properly structured
        validated_profile = validate_and_normalize_profile(profile)
        
        return {
            "profile": validated_profile,
            "profile_completeness": calculate_profile_completeness(validated_profile)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[get_user_profile] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/user/shopping-list")
async def get_user_shopping_list(current_user: User = Depends(get_current_user)):
    """Get the most recent shopping list for the current user"""
    try:
        shopping_lists = await get_user_shopping_lists(current_user["email"])
        if not shopping_lists:
            return {"items": []}
        # Return the most recent shopping list (assuming sorted by creation time or session_id)
        # If not sorted, sort by session_id or add a timestamp in the future
        return shopping_lists[-1]
    except Exception as e:
        print(f"Error fetching shopping list: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/user/shopping-list")
async def save_user_shopping_list(request: FastAPIRequest, current_user: User = Depends(get_current_user)):
    data = await request.json()
    items = data.get("items")
    if not items or not isinstance(items, list):
        raise HTTPException(status_code=400, detail="No items provided or invalid format")
    try:
        await save_shopping_list(current_user["email"], {"items": items})
        return {"message": "Shopping list saved successfully"}
    except Exception as e:
        print(f"Error saving shopping list: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/recipes")
async def get_user_recipes_endpoint(current_user: User = Depends(get_current_user)):
    """Get the most recent recipes for the current user"""
    try:
        recipes_list = await get_user_recipes(current_user["email"])
        if not recipes_list:
            return {"recipes": []}
        return recipes_list[-1]
    except Exception as e:
        print(f"Error fetching recipes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/user/recipes")
async def save_user_recipes(request: FastAPIRequest, current_user: User = Depends(get_current_user)):
    data = await request.json()
    recipes = data.get("recipes")
    if not recipes or not isinstance(recipes, list):
        raise HTTPException(status_code=400, detail="No recipes provided or invalid format")
    try:
        await save_recipes(current_user["email"], recipes)
        return {"message": "Recipes saved"}
    except Exception as e:
        print(f"Error saving recipes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))