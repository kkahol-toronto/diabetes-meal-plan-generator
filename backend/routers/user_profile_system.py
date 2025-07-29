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
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0
    
    async def attempt_save(profile_data: dict, user_email: str, attempt: int = 1) -> dict:
        """Attempt to save profile with atomic operations and error recovery"""
        import asyncio
        
        try:
            user_doc = await get_user_by_email(user_email)
            if not user_doc:
                raise HTTPException(status_code=404, detail="User not found")

            # Prepare both records that need to be saved
            updated_user_doc = user_doc.copy()
            updated_user_doc["profile"] = profile_data
            updated_user_doc["updated_at"] = datetime.utcnow().isoformat()
            
            profile_record = {
                "id": f"profile_{user_email}",
                "type": "user_profile", 
                "user_id": user_email,
                "profile": profile_data,
                "updated_at": datetime.utcnow().isoformat(),
                "created_at": user_doc.get("created_at", datetime.utcnow().isoformat()),
                "profile_completeness": calculate_profile_completeness(profile_data),
                "version": attempt  # Add version for conflict resolution
            }
            
            # Log attempt
            print(f"[save_user_profile] Attempt {attempt} - Saving profile for {user_email}")
            print(f"[save_user_profile] Profile fields: {list(profile_data.keys())}")
            print(f"[save_user_profile] Profile completeness: {profile_record['profile_completeness']}%")
            
            # Atomic save operations with error recovery
            user_save_success = False
            profile_save_success = False
            
            try:
                # Save to user document first
                user_container.replace_item(item=updated_user_doc["id"], body=updated_user_doc)
                user_save_success = True
                print(f"[save_user_profile] User document updated successfully (attempt {attempt})")
                
                # Save separate profile record
                user_container.upsert_item(body=profile_record)
                profile_save_success = True
                print(f"[save_user_profile] Profile record upserted successfully (attempt {attempt})")
                
            except Exception as db_error:
                print(f"[save_user_profile] Database error on attempt {attempt}: {str(db_error)}")
                
                # If user doc save succeeded but profile record failed, try to rollback
                if user_save_success and not profile_save_success:
                    try:
                        print(f"[save_user_profile] Rolling back user document changes...")
                        user_container.replace_item(item=user_doc["id"], body=user_doc)
                    except Exception as rollback_error:
                        print(f"[save_user_profile] Rollback failed: {str(rollback_error)}")
                
                raise db_error
            
            # Verify both saves succeeded
            if not (user_save_success and profile_save_success):
                raise Exception("Partial save detected - rolling back")
            
            return {
                "message": "Profile saved successfully",
                "timestamp": datetime.utcnow().isoformat(), 
                "profile_completeness": profile_record["profile_completeness"],
                "attempt": attempt,
                "user_save": user_save_success,
                "profile_save": profile_save_success
            }
            
        except Exception as e:
            if attempt < MAX_RETRIES:
                print(f"[save_user_profile] Attempt {attempt} failed: {str(e)}")
                print(f"[save_user_profile] Retrying in {RETRY_DELAY} seconds...")
                await asyncio.sleep(RETRY_DELAY)
                return await attempt_save(profile_data, user_email, attempt + 1)
            else:
                print(f"[save_user_profile] All {MAX_RETRIES} attempts failed for {user_email}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Failed to save profile after {MAX_RETRIES} attempts: {str(e)}"
                )

    try:
        # Parse and validate request data
        data = await request.json()
        profile = data.get("profile")
        if not profile:
            raise HTTPException(status_code=400, detail="No profile data provided")
        
        # Validate and normalize profile data
        profile = validate_and_normalize_profile(profile)
        
        # Attempt save with retry logic
        result = await attempt_save(profile, current_user["email"])
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[save_user_profile] Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error saving profile: {str(e)}")

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
    """Get user profile with robust fallback mechanisms"""
    try:
        user_email = current_user["email"]
        print(f"[get_user_profile] Retrieving profile for {user_email}")
        
        profile = {}
        profile_source = "none"
        
        # Method 1: Try to get from user document first
        try:
            user_doc = await get_user_by_email(user_email)
            if user_doc and user_doc.get("profile"):
                profile = user_doc["profile"]
                profile_source = "user_document"
                print(f"[get_user_profile] Loaded profile from user document for {user_email}")
        except Exception as e:
            print(f"[get_user_profile] Failed to load from user document: {str(e)}")
        
        # Method 2: If no profile in user doc, try separate profile record
        if not profile:
            try:
                profile_query = f"SELECT * FROM c WHERE c.type = 'user_profile' AND c.user_id = '{user_email}'"
                profiles = list(user_container.query_items(query=profile_query, enable_cross_partition_query=True))
                if profiles:
                    # Get the most recent profile if multiple exist
                    latest_profile = max(profiles, key=lambda x: x.get('updated_at', ''))
                    profile = latest_profile.get('profile', {})
                    profile_source = "profile_record"
                    print(f"[get_user_profile] Loaded profile from separate record for {user_email}")
                    
                    # Also try to sync it back to user document for consistency
                    try:
                        if user_doc:
                            user_doc["profile"] = profile
                            user_doc["updated_at"] = datetime.utcnow().isoformat()
                            user_container.replace_item(item=user_doc["id"], body=user_doc)
                            print(f"[get_user_profile] Synced profile back to user document")
                    except Exception as sync_error:
                        print(f"[get_user_profile] Failed to sync profile back: {str(sync_error)}")
                        
            except Exception as e:
                print(f"[get_user_profile] Failed to load from profile record: {str(e)}")
        
        # Method 3: Last resort - try to find by registration code if available
        if not profile and user_doc and user_doc.get("registration_code"):
            try:
                reg_code = user_doc["registration_code"]
                fallback_query = f"SELECT * FROM c WHERE c.type = 'user_profile' AND c.registration_code = '{reg_code}'"
                fallback_profiles = list(user_container.query_items(query=fallback_query, enable_cross_partition_query=True))
                if fallback_profiles:
                    latest_profile = max(fallback_profiles, key=lambda x: x.get('updated_at', ''))
                    profile = latest_profile.get('profile', {})
                    profile_source = "registration_fallback"
                    print(f"[get_user_profile] Loaded profile via registration code fallback for {user_email}")
            except Exception as e:
                print(f"[get_user_profile] Fallback by registration code failed: {str(e)}")
        
        # Validate and normalize the retrieved profile
        if profile:
            try:
                profile = validate_and_normalize_profile(profile)
                print(f"[get_user_profile] Profile validated and normalized")
            except Exception as e:
                print(f"[get_user_profile] Profile validation failed: {str(e)}")
                # Don't fail completely, just log the error
        
        # Calculate completeness
        completeness = calculate_profile_completeness(profile) if profile else 0.0
        
        print(f"[get_user_profile] Retrieved profile for {user_email}: {len(profile)} fields, {completeness}% complete, source: {profile_source}")
        
        return {
            "profile": profile,
            "profile_completeness": completeness,
            "source": profile_source,
            "timestamp": datetime.utcnow().isoformat(),
            "fields_count": len(profile)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[get_user_profile] Critical error retrieving profile: {str(e)}")
        # Return empty profile rather than failing completely
        return {
            "profile": {},
            "profile_completeness": 0.0,
            "source": "error_fallback", 
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "fields_count": 0
        }

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