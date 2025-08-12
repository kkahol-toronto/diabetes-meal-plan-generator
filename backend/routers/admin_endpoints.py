"""
Admin Endpoints Router
Handles all administrative functionality including patient management and analytics.
Requires admin authentication for all endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, Request as FastAPIRequest
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
from datetime import datetime, timedelta

from models import User
from routers.auth import get_current_user
from database import (
    get_patient_by_registration_code, get_all_patients, 
    get_user_by_email, user_container, interactions_container,
    get_ai_suggestion
)
from utils import send_registration_code

router = APIRouter()

# Behavior clustering thresholds and definitions
BEHAVIOR_THRESHOLDS = {
    "high_protein_low_carb": {
        "min_protein_percentage": 25,  # >25% of calories from protein
        "max_carb_percentage": 35,     # <35% of calories from carbs
        "min_days_threshold": 10       # Must meet criteria for at least 10 days
    },
    "night_eating": {
        "late_eating_threshold": 20,   # Eating after 8 PM
        "min_late_calories_percentage": 30,  # >30% of daily calories after 8 PM
        "min_days_threshold": 7        # Must meet criteria for at least 7 days
    },
    "under_reporting": {
        "very_low_calorie_threshold": 800,  # <800 calories per day
        "low_calorie_threshold": 1200,      # <1200 calories per day
        "min_days_threshold": 7,            # Pattern for at least 7 days
        "expected_min_calories": 1500       # Expected minimum for most adults
    }
}

@router.get("/admin/patient/{registration_code}")
async def get_patient_by_code(
    registration_code: str,
    current_user: User = Depends(get_current_user)
):
    # Check if user is admin
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        patient = await get_patient_by_registration_code(registration_code)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        return patient
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/patient-profile/{registration_code}")
async def get_patient_profile(
    registration_code: str,
    current_user: User = Depends(get_current_user)
):
    # Check if user is admin
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Get patient by registration code
        patient = await get_patient_by_registration_code(registration_code)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Try to find associated user account and profile data
        user_doc = None
        profile_data = {}
        profile_completeness = 0
        
        try:
            # Look for user with matching registration code
            user_query = f"SELECT * FROM c WHERE c.registration_code = '{registration_code}' AND c.type = 'user'"
            users = list(user_container.query_items(query=user_query, enable_cross_partition_query=True))
            if users:
                user_doc = users[0]
                profile_data = user_doc.get("profile", {})
                
                # Also try to get the separate profile record for completeness info
                try:
                    profile_query = f"SELECT * FROM c WHERE c.id = 'profile_{registration_code}' AND c.type = 'user_profile'"
                    profile_records = list(user_container.query_items(query=profile_query, enable_cross_partition_query=True))
                    if profile_records:
                        profile_record = profile_records[0]
                        profile_completeness = profile_record.get("profile_completeness", 0)
                        # Use profile data from the separate record if it's more recent
                        if profile_record.get("updated_at", "") > user_doc.get("updated_at", ""):
                            profile_data = profile_record.get("profile", profile_data)
                except Exception as profile_error:
                    print(f"Error fetching separate profile record: {str(profile_error)}")
            else:
                # Check if there's a standalone profile record (admin-created for patient without user account)
                profile_query = f"SELECT * FROM c WHERE c.registration_code = '{registration_code}' AND c.type = 'user_profile'"
                profile_records = list(user_container.query_items(query=profile_query, enable_cross_partition_query=True))
                if profile_records:
                    profile_record = profile_records[0]
                    profile_data = profile_record.get("profile", {})
                    profile_completeness = profile_record.get("profile_completeness", 0)
                    
        except Exception as user_error:
            print(f"Error finding user/profile for patient {registration_code}: {str(user_error)}")
        
        # Calculate profile completeness if not already available
        if not profile_completeness and profile_data:
            from utils import calculate_profile_completeness
            profile_completeness = calculate_profile_completeness(profile_data)
        
        return {
            "patient": patient,
            "user_account": user_doc,
            "has_user_account": bool(user_doc),
            "profile": profile_data,
            "profile_completeness": profile_completeness,
            "profile_status": "saved" if profile_data else "pending",
            "last_updated": user_doc.get("updated_at") if user_doc else None
        }
        
    except Exception as e:
        print(f"Error in get_patient_profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/patient-profile/{registration_code}")
async def save_patient_profile(
    registration_code: str,
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user)
):
    # Check if user is admin
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0
    
    async def attempt_admin_save(profile_data: dict, reg_code: str, attempt: int = 1) -> dict:
        """Attempt to save profile with atomic operations and error recovery - Admin version"""
        import asyncio
        from utils import validate_and_normalize_profile, calculate_profile_completeness
        
        try:
            # Get patient by registration code
            patient = await get_patient_by_registration_code(reg_code)
            if not patient:
                raise HTTPException(status_code=404, detail="Patient not found")
            
            # Find user with registration code
            user_query = f"SELECT * FROM c WHERE c.registration_code = '{reg_code}' AND c.type = 'user'"
            users = list(user_container.query_items(query=user_query, enable_cross_partition_query=True))
            
            if not users:
                # Create new profile document for patient without user account
                profile_record = {
                    "id": f"profile_{reg_code}",
                    "type": "user_profile",
                    "registration_code": reg_code,
                    "profile": profile_data,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                    "profile_completeness": calculate_profile_completeness(profile_data),
                    "admin_created": True,
                    "version": attempt
                }
                
                print(f"[admin_save_profile] Creating new profile record for {reg_code} (attempt {attempt})")
                user_container.create_item(body=profile_record)
                
                return {
                    "message": "Profile created successfully by admin",
                    "registration_code": reg_code,
                    "profile": profile_data,
                    "profile_completeness": profile_record["profile_completeness"],
                    "attempt": attempt,
                    "created_new": True
                }
            
            # Update existing user's profile using same robust mechanism as user profile system
            user_doc = users[0]
            user_email = user_doc.get("email") or user_doc.get("id")
            
            # Prepare both records that need to be saved
            updated_user_doc = user_doc.copy()
            updated_user_doc["profile"] = profile_data
            updated_user_doc["updated_at"] = datetime.utcnow().isoformat()
            
            profile_record = {
                "id": f"profile_{reg_code}",
                "type": "user_profile", 
                "user_id": user_email,
                "registration_code": reg_code,
                "profile": profile_data,
                "updated_at": datetime.utcnow().isoformat(),
                "created_at": user_doc.get("created_at", datetime.utcnow().isoformat()),
                "profile_completeness": calculate_profile_completeness(profile_data),
                "admin_updated": True,
                "version": attempt
            }
            
            # Log attempt
            print(f"[admin_save_profile] Attempt {attempt} - Saving profile for {reg_code} (user: {user_email})")
            print(f"[admin_save_profile] Profile fields: {list(profile_data.keys())}")
            print(f"[admin_save_profile] Profile completeness: {profile_record['profile_completeness']}%")
            
            # Atomic save operations with error recovery
            user_save_success = False
            profile_save_success = False
            
            try:
                # Save to user document first
                user_container.replace_item(item=updated_user_doc["id"], body=updated_user_doc)
                user_save_success = True
                print(f"[admin_save_profile] User document updated successfully (attempt {attempt})")
                
                # Save separate profile record
                user_container.upsert_item(body=profile_record)
                profile_save_success = True
                print(f"[admin_save_profile] Profile record upserted successfully (attempt {attempt})")
                
            except Exception as db_error:
                print(f"[admin_save_profile] Database error on attempt {attempt}: {str(db_error)}")
                
                # If user doc save succeeded but profile record failed, try to rollback
                if user_save_success and not profile_save_success:
                    try:
                        print(f"[admin_save_profile] Rolling back user document changes...")
                        user_container.replace_item(item=user_doc["id"], body=user_doc)
                    except Exception as rollback_error:
                        print(f"[admin_save_profile] Rollback failed: {str(rollback_error)}")
                
                raise db_error
            
            # Verify both saves succeeded
            if not (user_save_success and profile_save_success):
                raise Exception("Partial save detected - rolling back")
            
            return {
                "message": "Profile saved successfully by admin",
                "registration_code": reg_code,
                "profile": profile_data,
                "timestamp": datetime.utcnow().isoformat(), 
                "profile_completeness": profile_record["profile_completeness"],
                "attempt": attempt,
                "user_save": user_save_success,
                "profile_save": profile_save_success
            }
            
        except Exception as e:
            if attempt < MAX_RETRIES:
                print(f"[admin_save_profile] Attempt {attempt} failed: {str(e)}")
                print(f"[admin_save_profile] Retrying in {RETRY_DELAY} seconds...")
                await asyncio.sleep(RETRY_DELAY)
                return await attempt_admin_save(profile_data, reg_code, attempt + 1)
            else:
                print(f"[admin_save_profile] All {MAX_RETRIES} attempts failed for {reg_code}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Failed to save profile after {MAX_RETRIES} attempts: {str(e)}"
                )

    try:
        # Parse and validate request data
        data = await request.json()
        
        # Handle both direct profile data and nested profile structure
        if "profile" in data:
            profile_data = data["profile"]
        else:
            profile_data = data
        
        if not profile_data:
            raise HTTPException(status_code=400, detail="No profile data provided")
        
        # Import validation function
        from utils import validate_and_normalize_profile
        
        # Validate and normalize profile data using same mechanism as user profile system
        profile_data = validate_and_normalize_profile(profile_data)
        
        # Attempt save with retry logic
        result = await attempt_admin_save(profile_data, registration_code)
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[admin_save_profile] Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error saving profile: {str(e)}")

@router.post("/admin/resend-code/{patient_id}")
async def resend_registration_code(
    patient_id: str,
    current_user: User = Depends(get_current_user)
):
    # Check if user is admin
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Get patient by ID
        patient_query = f"SELECT * FROM c WHERE c.id = '{patient_id}' AND c.type = 'patient'"
        patients = list(user_container.query_items(query=patient_query, enable_cross_partition_query=True))
        
        if not patients:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        patient = patients[0]
        
        # Send registration code via SMS
        result = await send_registration_code(
            patient.get("phone", ""),
            patient.get("registration_code", ""),
            patient.get("name", "")
        )
        
        if result.get("success"):
            return {
                "message": "Registration code sent successfully",
                "patient_name": patient.get("name"),
                "phone": patient.get("phone"),
                "registration_code": patient.get("registration_code")
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send SMS")
        
    except Exception as e:
        print(f"Error resending registration code: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/analytics/nutrient-trends")
async def get_nutrient_trends(days: int = 30, current_user: User = Depends(get_current_user)):
    """Get nutrient consumption trends over time"""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        print(f"[NUTRIENT_TRENDS] Fetching nutrient trends for {days} days")
        
        # Get consumption records from the specified time period
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        consumption_query = "SELECT * FROM c WHERE c.type = 'consumption_record'"
        all_consumption = list(interactions_container.query_items(query=consumption_query, enable_cross_partition_query=True))
        
        # Filter by date range
        period_consumption = []
        for record in all_consumption:
            record_date_str = record.get("timestamp", record.get("created_at", ""))
            try:
                record_date = datetime.fromisoformat(record_date_str.replace('Z', '+00:00'))
                if start_date <= record_date <= end_date:
                    period_consumption.append(record)
            except:
                continue
        
        # Group by day and calculate daily totals
        daily_data = {}
        for record in period_consumption:
            record_date_str = record.get("timestamp", record.get("created_at", ""))
            try:
                record_date = datetime.fromisoformat(record_date_str.replace('Z', '+00:00'))
                day_key = record_date.strftime("%Y-%m-%d")
                
                if day_key not in daily_data:
                    daily_data[day_key] = {
                        "date": day_key,
                        "calories": 0,
                        "protein": 0,
                        "carbohydrates": 0,
                        "fat": 0,
                        "fiber": 0,
                        "sugar": 0,
                        "sodium": 0,
                        "meal_count": 0
                    }
                
                nutrition = record.get("nutritional_info", {})
                daily_data[day_key]["calories"] += nutrition.get("calories", 0)
                daily_data[day_key]["protein"] += nutrition.get("protein", 0)
                daily_data[day_key]["carbohydrates"] += nutrition.get("carbohydrates", 0)
                daily_data[day_key]["fat"] += nutrition.get("fat", 0)
                daily_data[day_key]["fiber"] += nutrition.get("fiber", 0)
                daily_data[day_key]["sugar"] += nutrition.get("sugar", 0)
                daily_data[day_key]["sodium"] += nutrition.get("sodium", 0)
                daily_data[day_key]["meal_count"] += 1
                
            except:
                continue
        
        # Convert to sorted list
        trends_data = sorted(daily_data.values(), key=lambda x: x["date"])
        
        # Calculate averages
        if trends_data:
            avg_calories = sum(d["calories"] for d in trends_data) / len(trends_data)
            avg_protein = sum(d["protein"] for d in trends_data) / len(trends_data)
            avg_carbs = sum(d["carbohydrates"] for d in trends_data) / len(trends_data)
            avg_fat = sum(d["fat"] for d in trends_data) / len(trends_data)
        else:
            avg_calories = avg_protein = avg_carbs = avg_fat = 0
        
        return {
            "period": {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "days": days
            },
            "daily_trends": trends_data,
            "averages": {
                "calories": round(avg_calories, 1),
                "protein": round(avg_protein, 1),
                "carbohydrates": round(avg_carbs, 1),
                "fat": round(avg_fat, 1)
            },
            "summary": {
                "total_records": len(period_consumption),
                "days_with_data": len(trends_data),
                "avg_meals_per_day": round(sum(d["meal_count"] for d in trends_data) / len(trends_data), 1) if trends_data else 0
            }
        }
        
    except Exception as e:
        print(f"[NUTRIENT_TRENDS] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get nutrient trends: {str(e)}")

@router.get("/admin/analytics/patient-engagement")
async def get_patient_engagement(current_user: User = Depends(get_current_user)):
    """Get detailed patient engagement analytics"""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Get all users with their profiles
        users_query = "SELECT * FROM c WHERE c.type = 'user'"
        all_users = list(user_container.query_items(query=users_query, enable_cross_partition_query=True))
        
        # Get all consumption records
        consumption_query = "SELECT * FROM c WHERE c.type = 'consumption_record'"
        all_consumption = list(interactions_container.query_items(query=consumption_query, enable_cross_partition_query=True))
        
        # Calculate engagement metrics per user
        user_engagement = []
        
        for user in all_users:
            user_email = user.get("email", user.get("id", ""))
            profile = user.get("profile", {})
            
            # Get user's consumption records
            user_consumption = [c for c in all_consumption if c.get("user_email") == user_email]
            
            # Calculate engagement metrics
            if user_consumption:
                # Sort by timestamp to find first and last activity
                sorted_consumption = sorted(user_consumption, key=lambda x: x.get("timestamp", ""))
                first_activity = sorted_consumption[0].get("timestamp", "")
                last_activity = sorted_consumption[-1].get("timestamp", "")
                
                # Calculate days active
                try:
                    first_date = datetime.fromisoformat(first_activity.replace('Z', '+00:00'))
                    last_date = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                    days_active = (last_date - first_date).days + 1
                except:
                    days_active = 1
                
                # Calculate nutrition adherence
                suitable_count = sum(1 for c in user_consumption 
                                   if c.get("medical_rating", {}).get("diabetes_suitability") == "high")
                adherence_rate = (suitable_count / len(user_consumption)) * 100 if user_consumption else 0
                
                user_engagement.append({
                    "user_email": user_email,
                    "name": profile.get("name", "Not provided"),
                    "registration_date": user.get("created_at", ""),
                    "total_meals_logged": len(user_consumption),
                    "days_active": days_active,
                    "first_activity": first_activity,
                    "last_activity": last_activity,
                    "adherence_rate": round(adherence_rate, 1),
                    "avg_meals_per_day": round(len(user_consumption) / max(days_active, 1), 2),
                    "medical_conditions": profile.get("medicalConditions", []),
                    "engagement_level": "high" if len(user_consumption) > 50 else "medium" if len(user_consumption) > 10 else "low"
                })
        
        # Sort by total meals logged (most engaged first)
        user_engagement.sort(key=lambda x: x["total_meals_logged"], reverse=True)
        
        # Calculate summary statistics
        if user_engagement:
            avg_meals = sum(u["total_meals_logged"] for u in user_engagement) / len(user_engagement)
            avg_adherence = sum(u["adherence_rate"] for u in user_engagement) / len(user_engagement)
            high_engagement = len([u for u in user_engagement if u["engagement_level"] == "high"])
            medium_engagement = len([u for u in user_engagement if u["engagement_level"] == "medium"])
            low_engagement = len([u for u in user_engagement if u["engagement_level"] == "low"])
        else:
            avg_meals = avg_adherence = high_engagement = medium_engagement = low_engagement = 0
        
        return {
            "summary": {
                "total_users": len(all_users),
                "engaged_users": len(user_engagement),
                "avg_meals_per_user": round(avg_meals, 1),
                "avg_adherence_rate": round(avg_adherence, 1),
                "engagement_distribution": {
                    "high": high_engagement,
                    "medium": medium_engagement,
                    "low": low_engagement
                }
            },
            "user_details": user_engagement,
            "top_performers": user_engagement[:5],  # Top 5 most engaged users
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"[PATIENT_ENGAGEMENT] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get patient engagement: {str(e)}")


@router.get("/admin/pias-corner/nutrient-adequacy")
async def get_nutrient_adequacy_analysis(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """
    Get nutrient adequacy analysis across the patient cohort.
    Returns % of patients hitting RDA for macros and identifies top deficiencies.
    """
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        print(f"[NUTRIENT_ADEQUACY] Starting analysis for {days} days")
        
        # Get total registered patients for comparison
        all_patients = await get_all_patients()
        total_registered_patients = len(all_patients)
        
        # Define RDA (Recommended Daily Allowance) values - daily targets
        RDA_VALUES = {
            "calories": {"min": 1800, "max": 2200},  # Varies by individual, using general range
            "protein": {"min": 50, "max": 100},      # 0.8g per kg body weight (average range)
            "carbohydrates": {"min": 130, "max": 300}, # 45-65% of calories
            "fat": {"min": 44, "max": 78},           # 20-35% of calories  
            "fiber": {"min": 25, "max": 35},         # Daily recommendation
            "sodium": {"max": 2300},                 # Max daily sodium (mg)
            "sugar": {"max": 50}                     # Max daily added sugar (g)
        }
        
        # Get time range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get all consumption records in the time period
        consumption_query = f"""
            SELECT * FROM c 
            WHERE c.type = 'consumption_record' 
            AND c.timestamp >= '{start_date.isoformat()}'
        """
        all_consumption = list(interactions_container.query_items(
            query=consumption_query, 
            enable_cross_partition_query=True
        ))
        
        print(f"[NUTRIENT_ADEQUACY] Found {len(all_consumption)} consumption records")
        
        # Get all users who have consumption data
        user_consumption = {}
        for record in all_consumption:
            user_id = record.get("user_id")
            if not user_id:
                continue
                
            if user_id not in user_consumption:
                user_consumption[user_id] = []
            user_consumption[user_id].append(record)
        
        active_users_count = len(user_consumption)
        print(f"[NUTRIENT_ADEQUACY] Analyzing {active_users_count} users with consumption data")
        
        # Get all registered users (excluding admin) to identify inactive patients
        all_users_query = "SELECT * FROM c WHERE c.type = 'user' AND c.is_admin != true"
        all_users = list(user_container.query_items(query=all_users_query, enable_cross_partition_query=True))
        total_users_count = len(all_users)
        
        # Create email to name mapping using admin panel patient data as authoritative source
        email_to_name = {}
        
        # First, get all admin panel patients (authoritative source for names)
        admin_patients = await get_all_patients()
        registration_to_name = {}
        for patient in admin_patients:
            reg_code = patient.get("registration_code")
            patient_name = patient.get("name", "").strip()
            if reg_code and patient_name:
                registration_to_name[reg_code] = patient_name
        
        # Map user emails to patient names using registration codes
        for user in all_users:
            email = user.get("email")
            registration_code = user.get("registration_code")
            
            if email:
                # First priority: Use admin panel patient name (authoritative)
                if registration_code and registration_code in registration_to_name:
                    email_to_name[email] = registration_to_name[registration_code]
                else:
                    # Second priority: Use profile name if available
                    profile = user.get("profile", {})
                    profile_name = profile.get("name", "").strip()
                    if profile_name:
                        email_to_name[email] = profile_name
                    else:
                        # Last resort: Create professional fallback from email
                        username = email.split("@")[0]
                        if len(username) > 0:
                            readable_name = username.replace(".", " ").replace("_", " ")
                            readable_name = " ".join(word.capitalize() for word in readable_name.split())
                            email_to_name[email] = f"Patient {readable_name}"
                        else:
                            email_to_name[email] = "Unknown Patient"
        
        # Identify users without consumption data
        users_with_consumption = set(user_consumption.keys())
        all_user_emails = {user.get("email") for user in all_users if user.get("email")}
        inactive_users = all_user_emails - users_with_consumption
        
        print(f"[NUTRIENT_ADEQUACY] Total registered users: {total_users_count}")
        print(f"[NUTRIENT_ADEQUACY] Inactive users (no consumption data): {len(inactive_users)}")
        if inactive_users:
            print(f"[NUTRIENT_ADEQUACY] Inactive user emails: {list(inactive_users)}")
        
        if active_users_count == 0:
            # Create all registered patients list even when no active users
            all_registered_patients = []
            for patient in admin_patients:
                patient_email = None
                patient_name = patient.get("name", "").strip()
                registration_code = patient.get("registration_code")
                
                # Find the email for this patient by matching registration code
                for user in all_users:
                    if user.get("registration_code") == registration_code:
                        patient_email = user.get("email")
                        break
                
                if patient_name and patient_email:
                    all_registered_patients.append({
                        "user_id": patient_email,
                        "user_name": patient_name,
                        "registration_code": registration_code,
                        "phone": patient.get("phone", ""),
                        "condition": patient.get("condition", ""),
                        "is_active": False  # No active users in this case
                    })
            
            # Add any users not in admin panel but registered in system
            for user in all_users:
                user_email = user.get("email")
                user_reg_code = user.get("registration_code")
                
                # Check if this user is already in our admin panel list
                already_added = any(p["user_id"] == user_email for p in all_registered_patients)
                
                if not already_added and user_email:
                    all_registered_patients.append({
                        "user_id": user_email,
                        "user_name": email_to_name.get(user_email, user_email),
                        "registration_code": user_reg_code or "N/A",
                        "phone": "N/A",
                        "condition": "N/A",
                        "is_active": False  # No active users in this case
                    })
            
            return {
                "cohort_size": active_users_count,
                "total_registered_patients": total_registered_patients,
                "total_registered_users": total_users_count,
                "inactive_patients_count": len(inactive_users),
                "inactive_patients": [{"user_id": email, "user_name": email_to_name.get(email, email)} for email in inactive_users],
                "active_patients": [],
                "all_registered_patients": all_registered_patients,
                "analysis_period": {
                    "days": days,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "total_records_analyzed": 0
                },
                "rda_compliance": {},
                "deficiency_analysis": {},
                "cohort_averages": {}
            }
        
        # Calculate daily averages for each user
        user_daily_averages = {}
        cohort_deficiencies = {
            "low_fiber": 0,
            "excess_sodium": 0,
            "excess_sugar": 0,
            "low_protein": 0,
            "low_calories": 0,
            "excess_calories": 0
        }
        
        rda_compliance_counts = {
            "calories": {"adequate": 0, "low": 0, "high": 0},
            "protein": {"adequate": 0, "low": 0},
            "carbohydrates": {"adequate": 0, "low": 0, "high": 0},
            "fat": {"adequate": 0, "low": 0, "high": 0},
            "fiber": {"adequate": 0, "low": 0},
            "sodium": {"adequate": 0, "high": 0},
            "sugar": {"adequate": 0, "high": 0}
        }
        
        cohort_totals = {
            "calories": 0, "protein": 0, "carbohydrates": 0, 
            "fat": 0, "fiber": 0, "sodium": 0, "sugar": 0
        }
        
        for user_id, records in user_consumption.items():
            # Calculate daily totals for this user
            daily_totals = {}
            
            for record in records:
                nutrition = record.get("nutritional_info", {})
                timestamp = record.get("timestamp", "")
                
                try:
                    record_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    day_key = record_date.strftime("%Y-%m-%d")
                except:
                    continue
                
                if day_key not in daily_totals:
                    daily_totals[day_key] = {
                        "calories": 0, "protein": 0, "carbohydrates": 0,
                        "fat": 0, "fiber": 0, "sodium": 0, "sugar": 0
                    }
                
                # Accumulate daily totals
                for nutrient in daily_totals[day_key]:
                    daily_totals[day_key][nutrient] += float(nutrition.get(nutrient, 0))
            
            # Calculate user's average daily intake
            if daily_totals:
                days_with_data = len(daily_totals)
                user_averages = {}
                
                for nutrient in ["calories", "protein", "carbohydrates", "fat", "fiber", "sodium", "sugar"]:
                    total = sum(day[nutrient] for day in daily_totals.values())
                    user_averages[nutrient] = total / days_with_data
                    cohort_totals[nutrient] += user_averages[nutrient]
                
                user_daily_averages[user_id] = user_averages
                
                # Check RDA compliance for this user
                # Calories
                cal_avg = user_averages["calories"]
                if RDA_VALUES["calories"]["min"] <= cal_avg <= RDA_VALUES["calories"]["max"]:
                    rda_compliance_counts["calories"]["adequate"] += 1
                elif cal_avg < RDA_VALUES["calories"]["min"]:
                    rda_compliance_counts["calories"]["low"] += 1
                    cohort_deficiencies["low_calories"] += 1
                else:
                    rda_compliance_counts["calories"]["high"] += 1
                    cohort_deficiencies["excess_calories"] += 1
                
                # Protein
                protein_avg = user_averages["protein"]
                if protein_avg >= RDA_VALUES["protein"]["min"]:
                    rda_compliance_counts["protein"]["adequate"] += 1
                else:
                    rda_compliance_counts["protein"]["low"] += 1
                    cohort_deficiencies["low_protein"] += 1
                
                # Fiber (key deficiency to track)
                fiber_avg = user_averages["fiber"]
                if fiber_avg >= RDA_VALUES["fiber"]["min"]:
                    rda_compliance_counts["fiber"]["adequate"] += 1
                else:
                    rda_compliance_counts["fiber"]["low"] += 1
                    cohort_deficiencies["low_fiber"] += 1
                
                # Sodium (key excess to track)
                sodium_avg = user_averages["sodium"]
                if sodium_avg <= RDA_VALUES["sodium"]["max"]:
                    rda_compliance_counts["sodium"]["adequate"] += 1
                else:
                    rda_compliance_counts["sodium"]["high"] += 1
                    cohort_deficiencies["excess_sodium"] += 1
                
                # Sugar
                sugar_avg = user_averages["sugar"]
                if sugar_avg <= RDA_VALUES["sugar"]["max"]:
                    rda_compliance_counts["sugar"]["adequate"] += 1
                else:
                    rda_compliance_counts["sugar"]["high"] += 1
                    cohort_deficiencies["excess_sugar"] += 1
                
                # Carbohydrates
                carb_avg = user_averages["carbohydrates"]
                if RDA_VALUES["carbohydrates"]["min"] <= carb_avg <= RDA_VALUES["carbohydrates"]["max"]:
                    rda_compliance_counts["carbohydrates"]["adequate"] += 1
                elif carb_avg < RDA_VALUES["carbohydrates"]["min"]:
                    rda_compliance_counts["carbohydrates"]["low"] += 1
                else:
                    rda_compliance_counts["carbohydrates"]["high"] += 1
                
                # Fat
                fat_avg = user_averages["fat"]
                if RDA_VALUES["fat"]["min"] <= fat_avg <= RDA_VALUES["fat"]["max"]:
                    rda_compliance_counts["fat"]["adequate"] += 1
                elif fat_avg < RDA_VALUES["fat"]["min"]:
                    rda_compliance_counts["fat"]["low"] += 1
                else:
                    rda_compliance_counts["fat"]["high"] += 1
        
        # Calculate percentages using a per-nutrient active denominator
        # Only users who had any data for a given nutrient are counted in that nutrient's denominator.
        rda_compliance_percentages = {}
        per_nutrient_denominators = {}
        for nutrient, counts in rda_compliance_counts.items():
            total_for_nutrient = sum(counts.values())
            per_nutrient_denominators[nutrient] = total_for_nutrient
            percentages = {}
            for category, count in counts.items():
                percentages[category] = {
                    "count": count,
                    "percentage": round((count / total_for_nutrient) * 100, 1) if total_for_nutrient > 0 else 0
                }
            rda_compliance_percentages[nutrient] = percentages

        # Ensure all expected nutrient keys are present even if no data was logged,
        # so the frontend chart reliably renders every bar (including Fiber).
        expected_nutrients = [
            "calories",
            "protein",
            "carbohydrates",
            "fat",
            "fiber",
            "sodium",
            "sugar",
        ]
        for key in expected_nutrients:
            if key not in rda_compliance_percentages:
                rda_compliance_percentages[key] = {
                    "adequate": {"count": 0, "percentage": 0.0},
                    # For nutrients that have high/low categories, include both so UI logic is stable
                    **({"low": {"count": 0, "percentage": 0.0}} if key in ["calories", "protein", "carbohydrates", "fat", "fiber"] else {}),
                    **({"high": {"count": 0, "percentage": 0.0}} if key in ["calories", "carbohydrates", "fat", "sodium", "sugar"] else {}),
                }
        
        # Calculate cohort averages
        cohort_averages = {}
        for nutrient, total in cohort_totals.items():
            cohort_averages[nutrient] = round(total / active_users_count, 1) if active_users_count > 0 else 0
        
        # Identify top deficiencies (sorted by prevalence)
        deficiency_rankings = [
            {
                "issue": "Low Fiber Intake",
                "affected_patients": cohort_deficiencies["low_fiber"],
                "percentage": round((cohort_deficiencies["low_fiber"] / max(1, per_nutrient_denominators.get("fiber", 0))) * 100, 1) if per_nutrient_denominators.get("fiber", 0) > 0 else 0,
                "severity": "high" if cohort_deficiencies["low_fiber"] / active_users_count > 0.7 else "medium",
                "recommendation": "Increase whole grains, fruits, and vegetables"
            },
            {
                "issue": "Excess Sodium",
                "affected_patients": cohort_deficiencies["excess_sodium"],
                "percentage": round((cohort_deficiencies["excess_sodium"] / max(1, per_nutrient_denominators.get("sodium", 0))) * 100, 1) if per_nutrient_denominators.get("sodium", 0) > 0 else 0,
                "severity": "high" if cohort_deficiencies["excess_sodium"] / active_users_count > 0.5 else "medium",
                "recommendation": "Reduce processed foods and restaurant meals"
            },
            {
                "issue": "Excess Sugar",
                "affected_patients": cohort_deficiencies["excess_sugar"],
                "percentage": round((cohort_deficiencies["excess_sugar"] / max(1, per_nutrient_denominators.get("sugar", 0))) * 100, 1) if per_nutrient_denominators.get("sugar", 0) > 0 else 0,
                "severity": "medium" if cohort_deficiencies["excess_sugar"] / active_users_count > 0.4 else "low",
                "recommendation": "Limit sugary beverages and desserts"
            },
            {
                "issue": "Low Protein",
                "affected_patients": cohort_deficiencies["low_protein"],
                "percentage": round((cohort_deficiencies["low_protein"] / max(1, per_nutrient_denominators.get("protein", 0))) * 100, 1) if per_nutrient_denominators.get("protein", 0) > 0 else 0,
                "severity": "medium" if cohort_deficiencies["low_protein"] / active_users_count > 0.3 else "low",
                "recommendation": "Include lean proteins at each meal"
            }
        ]
        
        # Sort by percentage (most prevalent first)
        deficiency_rankings.sort(key=lambda x: x["percentage"], reverse=True)
        
        # Create active patients list
        active_patients = [{"user_id": email, "user_name": email_to_name.get(email, email)} for email in users_with_consumption]
        
        # Create all registered patients list (from admin panel)
        all_registered_patients = []
        for patient in admin_patients:
            patient_email = None
            patient_name = patient.get("name", "").strip()
            registration_code = patient.get("registration_code")
            
            # Find the email for this patient by matching registration code
            for user in all_users:
                if user.get("registration_code") == registration_code:
                    patient_email = user.get("email")
                    break
            
            if patient_name and patient_email:
                all_registered_patients.append({
                    "user_id": patient_email,
                    "user_name": patient_name,
                    "registration_code": registration_code,
                    "phone": patient.get("phone", ""),
                    "condition": patient.get("condition", ""),
                    "is_active": patient_email in users_with_consumption
                })
        
        # Add any users not in admin panel but registered in system
        for user in all_users:
            user_email = user.get("email")
            user_reg_code = user.get("registration_code")
            
            # Check if this user is already in our admin panel list
            already_added = any(p["user_id"] == user_email for p in all_registered_patients)
            
            if not already_added and user_email:
                all_registered_patients.append({
                    "user_id": user_email,
                    "user_name": email_to_name.get(user_email, user_email),
                    "registration_code": user_reg_code or "N/A",
                    "phone": "N/A",
                    "condition": "N/A",
                    "is_active": user_email in users_with_consumption
                })
        
        return {
            "cohort_size": active_users_count,
            "total_registered_patients": total_registered_patients,
            "total_registered_users": total_users_count,
            "inactive_patients_count": len(inactive_users),
            "inactive_patients": [{"user_id": email, "user_name": email_to_name.get(email, email)} for email in inactive_users],
            "active_patients": active_patients,
            "all_registered_patients": all_registered_patients,
            "analysis_period": {
                "days": days,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "total_records_analyzed": len(all_consumption)
            },
            "rda_compliance": rda_compliance_percentages,
            "deficiency_analysis": {
                "top_deficiencies": deficiency_rankings,
                "summary": {
                    "patients_with_fiber_deficiency": cohort_deficiencies["low_fiber"],
                    "patients_with_excess_sodium": cohort_deficiencies["excess_sodium"],
                    "patients_with_excess_sugar": cohort_deficiencies["excess_sugar"],
                    "patients_with_low_protein": cohort_deficiencies["low_protein"]
                }
            },
            "cohort_averages": {
                "daily_averages": cohort_averages,
                "vs_rda": {
                    "fiber_deficit": round(RDA_VALUES["fiber"]["min"] - cohort_averages.get("fiber", 0), 1),
                    "sodium_excess": round(cohort_averages.get("sodium", 0) - RDA_VALUES["sodium"]["max"], 1),
                    "protein_status": "adequate" if cohort_averages.get("protein", 0) >= RDA_VALUES["protein"]["min"] else "low"
                }
            },
            "recommendations": {
                "priority_actions": [
                    "Focus on increasing fiber intake across cohort",
                    "Reduce sodium consumption through education",
                    "Monitor sugar intake patterns",
                    "Ensure adequate protein at each meal"
                ],
                "monitoring_focus": [
                    "Track fiber-rich food consumption",
                    "Monitor processed food intake",
                    "Assess meal balance and portion sizes"
                ]
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"[NUTRIENT_ADEQUACY] Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get nutrient adequacy analysis: {str(e)}")


@router.get("/admin/pias-corner/engagement-metrics")
async def get_engagement_metrics(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """
    Get patient engagement metrics including daily/weekly active loggers,
    missed logs, and irregular reporting patterns for time series visualization.
    """
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        print(f"[ENGAGEMENT_METRICS] Starting engagement analysis for {days} days")
        
        # Get total registered patients for comparison
        all_patients = await get_all_patients()
        total_registered_patients = len(all_patients)
        
        # Get time range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get all consumption records in the time period
        consumption_query = f"""
            SELECT * FROM c 
            WHERE c.type = 'consumption_record' 
            AND c.timestamp >= '{start_date.isoformat()}'
        """
        all_consumption = list(interactions_container.query_items(
            query=consumption_query, 
            enable_cross_partition_query=True
        ))
        
        print(f"[ENGAGEMENT_METRICS] Found {len(all_consumption)} consumption records")
        
        # Get all registered users (excluding admin)
        all_users_query = "SELECT * FROM c WHERE c.type = 'user' AND c.is_admin != true"
        all_users = list(user_container.query_items(query=all_users_query, enable_cross_partition_query=True))
        total_users_count = len(all_users)
        all_user_emails = {user.get("email") for user in all_users if user.get("email")}
        
        # Create email to name mapping
        email_to_name = {}
        for user in all_users:
            email = user.get("email")
            profile = user.get("profile", {})
            name = profile.get("name", "").strip()
            if email:
                if name:
                    # Use the actual name
                    email_to_name[email] = name
                else:
                    # Create a professional fallback name from email
                    username = email.split("@")[0]
                    # Capitalize first letter and make it more readable
                    if len(username) > 0:
                        readable_name = username.replace(".", " ").replace("_", " ")
                        # Capitalize each word
                        readable_name = " ".join(word.capitalize() for word in readable_name.split())
                        email_to_name[email] = f"Patient {readable_name}"
                    else:
                        email_to_name[email] = "Unknown Patient"
        
        print(f"[ENGAGEMENT_METRICS] Analyzing {total_users_count} registered users")
        
        # Group consumption by user and date
        from collections import defaultdict
        user_daily_logs = defaultdict(lambda: defaultdict(int))  # user_id -> date -> log_count
        daily_active_users = defaultdict(set)  # date -> set of active user_ids
        user_last_log = {}  # user_id -> last_log_date
        
        for record in all_consumption:
            user_id = record.get("user_id")
            timestamp = record.get("timestamp", "")
            
            if not user_id or not timestamp:
                continue
                
            try:
                record_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                date_key = record_date.strftime("%Y-%m-%d")
                
                # Track daily logs per user
                user_daily_logs[user_id][date_key] += 1
                
                # Track daily active users
                daily_active_users[date_key].add(user_id)
                
                # Track last log date for each user
                if user_id not in user_last_log or record_date > user_last_log[user_id]:
                    user_last_log[user_id] = record_date
                    
            except Exception as date_error:
                print(f"[ENGAGEMENT_METRICS] Date parsing error: {date_error}")
                continue
        
        # Generate daily time series data
        daily_metrics = []
        current_date = start_date
        
        while current_date <= end_date:
            date_key = current_date.strftime("%Y-%m-%d")
            active_users_count = len(daily_active_users.get(date_key, set()))
            
            # Calculate engagement rate
            engagement_rate = (active_users_count / total_users_count * 100) if total_users_count > 0 else 0
            
            daily_metrics.append({
                "date": date_key,
                "active_users": active_users_count,
                "total_users": total_users_count,
                "engagement_rate": round(engagement_rate, 1),
                "day_of_week": current_date.strftime("%A")
            })
            
            current_date += timedelta(days=1)
        
        # Calculate user engagement scores and identify irregular patterns
        user_engagement_analysis = []
        users_with_consumption = set(user_daily_logs.keys())
        inactive_users = all_user_emails - users_with_consumption
        
        # Engagement thresholds
        REGULAR_LOGGING_THRESHOLD = 3  # logs per week considered regular
        MISSED_DAYS_WARNING = 3  # days without logging triggers warning
        INACTIVE_DAYS_CRITICAL = 7  # days without logging critical
        
        for user_id in all_user_emails:
            if user_id in user_daily_logs:
                user_logs = user_daily_logs[user_id]
                total_logs = sum(user_logs.values())
                active_days = len(user_logs)
                avg_logs_per_day = total_logs / max(active_days, 1)
                
                # Calculate days since last log
                days_since_last_log = 0
                if user_id in user_last_log:
                    days_since_last_log = (end_date - user_last_log[user_id]).days
                
                # Determine engagement level
                if days_since_last_log >= INACTIVE_DAYS_CRITICAL:
                    engagement_level = "critical"
                elif days_since_last_log >= MISSED_DAYS_WARNING:
                    engagement_level = "fair"  # Changed from "warning" to "fair"
                elif avg_logs_per_day >= REGULAR_LOGGING_THRESHOLD / 7:  # Convert weekly to daily
                    engagement_level = "excellent"
                elif avg_logs_per_day >= (REGULAR_LOGGING_THRESHOLD / 7) * 0.5:
                    engagement_level = "good"
                else:
                    engagement_level = "poor"
                
                # Calculate weekly pattern
                weekly_logs = total_logs * 7 / days if days > 0 else 0
                
                user_engagement_analysis.append({
                    "user_id": user_id,
                    "user_name": email_to_name.get(user_id, user_id),
                    "total_logs": total_logs,
                    "active_days": active_days,
                    "avg_logs_per_day": round(avg_logs_per_day, 2),
                    "weekly_logs_avg": round(weekly_logs, 1),
                    "days_since_last_log": days_since_last_log,
                    "engagement_level": engagement_level,
                    "last_log_date": user_last_log.get(user_id, "").strftime("%Y-%m-%d") if user_id in user_last_log else None
                })
            else:
                # User has never logged
                user_engagement_analysis.append({
                    "user_id": user_id,
                    "user_name": email_to_name.get(user_id, user_id),
                    "total_logs": 0,
                    "active_days": 0,
                    "avg_logs_per_day": 0,
                    "weekly_logs_avg": 0,
                    "days_since_last_log": days,  # Days since analysis started
                    "engagement_level": "inactive",
                    "last_log_date": None
                })
        
        # Sort by engagement level (worst first for doctor attention)
        engagement_priority = {"inactive": 0, "critical": 1, "fair": 2, "poor": 3, "good": 4, "excellent": 5}  # Changed "warning" to "fair"
        user_engagement_analysis.sort(key=lambda x: engagement_priority.get(x["engagement_level"], 0))
        
        # Calculate weekly patterns
        weekly_data = defaultdict(lambda: {"active_users": 0, "total_logs": 0})
        for metric in daily_metrics:
            week_key = datetime.strptime(metric["date"], "%Y-%m-%d").strftime("%Y-W%U")
            weekly_data[week_key]["active_users"] = max(weekly_data[week_key]["active_users"], metric["active_users"])
            # Note: This is a simplified weekly calculation; could be enhanced
        
        # Calculate summary statistics
        engagement_summary = {
            "excellent": len([u for u in user_engagement_analysis if u["engagement_level"] == "excellent"]),
            "good": len([u for u in user_engagement_analysis if u["engagement_level"] == "good"]),
            "fair": len([u for u in user_engagement_analysis if u["engagement_level"] == "fair"]),  # Changed from "warning"
            "poor": len([u for u in user_engagement_analysis if u["engagement_level"] == "poor"]),
            "critical": len([u for u in user_engagement_analysis if u["engagement_level"] == "critical"]),
            "inactive": len([u for u in user_engagement_analysis if u["engagement_level"] == "inactive"])
        }
        
        # Identify trends
        recent_avg = sum(m["active_users"] for m in daily_metrics[-7:]) / 7 if len(daily_metrics) >= 7 else 0
        earlier_avg = sum(m["active_users"] for m in daily_metrics[:7]) / 7 if len(daily_metrics) >= 7 else 0
        engagement_trend = "improving" if recent_avg > earlier_avg else "declining" if recent_avg < earlier_avg else "stable"
        
        return {
            "total_registered_patients": total_registered_patients,
            "total_registered_users": total_users_count,
            "analysis_period": {
                "days": days,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "total_consumption_records": len(all_consumption)
            },
            "daily_metrics": daily_metrics,
            "engagement_summary": engagement_summary,
            "engagement_trend": engagement_trend,
            "user_engagement_details": user_engagement_analysis,
            "alerts": {
                "critical_users": [{"user_id": u["user_id"], "user_name": u["user_name"]} for u in user_engagement_analysis if u["engagement_level"] == "critical"],
                "fair_users": [{"user_id": u["user_id"], "user_name": u["user_name"]} for u in user_engagement_analysis if u["engagement_level"] == "fair"],  # Changed from "warning_users"
                "inactive_users": [{"user_id": u["user_id"], "user_name": u["user_name"]} for u in user_engagement_analysis if u["engagement_level"] == "inactive"]
            },
            "recommendations": {
                "immediate_followup": engagement_summary["critical"] + engagement_summary["inactive"],
                "needs_encouragement": engagement_summary["fair"] + engagement_summary["poor"],  # Changed from "warning"
                "performing_well": engagement_summary["good"] + engagement_summary["excellent"]
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"[ENGAGEMENT_METRICS] Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get engagement metrics: {str(e)}")


@router.get("/admin/pias-corner/outliers")
async def get_outlier_detection(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """
    Detect outliers in patient food logs including extreme calorie intake
    and nutrient spikes (e.g., carbs > 3x RDA) for medical intervention.
    """
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        print(f"[OUTLIER_DETECTION] Starting outlier analysis for {days} days")
        
        # Get total registered patients for comparison
        all_patients = await get_all_patients()
        total_registered_patients = len(all_patients)
        
        # Define outlier thresholds based on medical guidelines
        OUTLIER_THRESHOLDS = {
            # Extreme calorie intake thresholds
            "calories": {
                "extremely_low": 800,      # Below 800 calories - potential malnutrition
                "very_low": 1200,          # Below 1200 calories - concerning
                "very_high": 3500,         # Above 3500 calories - excessive
                "extremely_high": 5000     # Above 5000 calories - dangerous
            },
            # Nutrient spike thresholds (multiples of RDA)
            "protein": {"spike_multiplier": 4.0, "rda": 50},       # >4x RDA
            "carbohydrates": {"spike_multiplier": 3.0, "rda": 130}, # >3x RDA  
            "fat": {"spike_multiplier": 3.0, "rda": 78},          # >3x RDA
            "fiber": {"spike_multiplier": 2.5, "rda": 25},        # >2.5x RDA (less concerning)
            "sodium": {"spike_multiplier": 2.0, "rda": 2300},     # >2x RDA (concerning)
            "sugar": {"spike_multiplier": 3.0, "rda": 50}         # >3x RDA
        }
        
        # Get time range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get all consumption records in the time period
        consumption_query = f"""
            SELECT * FROM c 
            WHERE c.type = 'consumption_record' 
            AND c.timestamp >= '{start_date.isoformat()}'
        """
        all_consumption = list(interactions_container.query_items(
            query=consumption_query, 
            enable_cross_partition_query=True
        ))
        
        print(f"[OUTLIER_DETECTION] Found {len(all_consumption)} consumption records")
        
        # Filter out deleted duplicate account records  
        all_consumption = [r for r in all_consumption if r.get('user_id') != 'nagarwal166@gmail.com']
        print(f"[OUTLIER_DETECTION] After filtering deleted accounts: {len(all_consumption)} records")
        
        # Debug: Show sample of consumption data
        if all_consumption:
            sample_record = all_consumption[0]
            print(f"[OUTLIER_DETECTION] Sample consumption record fields: {list(sample_record.keys())}")
            print(f"[OUTLIER_DETECTION] Sample nutritional_info: {sample_record.get('nutritional_info', {})}")
        
        # Get all registered users (excluding admin) to map names (include both 'user' and 'patient' types)
        all_users_query = "SELECT * FROM c WHERE (c.type = 'user' OR c.type = 'patient') AND c.is_admin != true"
        all_users_raw = list(user_container.query_items(query=all_users_query, enable_cross_partition_query=True))
        
        # Deduplicate users: prioritize type='user' over type='patient' for same registration code
        user_map = {}
        for user in all_users_raw:
            reg_code = user.get('registration_code', '')
            user_type = user.get('type', '')
            
            if reg_code:
                if reg_code not in user_map:
                    user_map[reg_code] = user
                elif user_type == 'user' and user_map[reg_code].get('type') == 'patient':
                    # Prioritize 'user' type over 'patient' type
                    user_map[reg_code] = user
        
        # Convert back to list
        all_users = list(user_map.values())
        total_users_count = len(all_users)
        
        # Create email to name mapping using admin panel patient data as authoritative source
        email_to_name = {}
        
        # First, get all admin panel patients (authoritative source for names)
        admin_patients = await get_all_patients()
        registration_to_name = {}
        for patient in admin_patients:
            reg_code = patient.get("registration_code")
            patient_name = patient.get("name", "").strip()
            if reg_code and patient_name:
                registration_to_name[reg_code] = patient_name
        
        # Map user emails to patient names using registration codes
        for user in all_users:
            email = user.get("email")
            registration_code = user.get("registration_code")
            
            if email:
                # First priority: Use admin panel patient name (authoritative)
                if registration_code and registration_code in registration_to_name:
                    email_to_name[email] = registration_to_name[registration_code]
                else:
                    # Second priority: Use profile name if available
                    profile = user.get("profile", {})
                    profile_name = profile.get("name", "").strip()
                    if profile_name:
                        email_to_name[email] = profile_name
                    else:
                        # Last resort: Create professional fallback from email
                        username = email.split("@")[0]
                        if len(username) > 0:
                            readable_name = username.replace(".", " ").replace("_", " ")
                            readable_name = " ".join(word.capitalize() for word in readable_name.split())
                            email_to_name[email] = f"Patient {readable_name}"
                        else:
                            email_to_name[email] = "Unknown Patient"
        
        if not all_consumption:
            return {
                "total_registered_patients": total_registered_patients,
                "total_registered_users": total_users_count,
                "analysis_period": {
                    "days": days,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "total_records_analyzed": 0
                },
                "outliers": {
                    "extreme_calorie_intake": [],
                    "nutrient_spikes": [],
                    "daily_outliers": []
                },
                "summary": {
                    "total_outlier_users": 0,
                    "extreme_calorie_days": 0,
                    "nutrient_spike_days": 0,
                    "most_common_outlier": "None"
                },
                "generated_at": datetime.utcnow().isoformat()
            }
        
        # Group consumption by user and date for analysis
        from collections import defaultdict
        user_daily_totals = defaultdict(lambda: defaultdict(lambda: {
            "calories": 0, "protein": 0, "carbohydrates": 0, 
            "fat": 0, "fiber": 0, "sodium": 0, "sugar": 0,
            "record_count": 0
        }))
        
        # Process all consumption records
        processed_records = 0
        for record in all_consumption:
            user_id = record.get("user_id")
            timestamp = record.get("timestamp", "")
            nutrition = record.get("nutritional_info", {})  # Fixed: use correct field name
            
            if not user_id or not timestamp:
                continue
                
            try:
                record_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                date_key = record_date.strftime("%Y-%m-%d")
                
                # Accumulate daily totals
                daily_data = user_daily_totals[user_id][date_key]
                daily_data["record_count"] += 1
                
                for nutrient in ["calories", "protein", "carbohydrates", "fat", "fiber", "sodium", "sugar"]:
                    daily_data[nutrient] += float(nutrition.get(nutrient, 0))
                
                processed_records += 1
                    
            except Exception as date_error:
                print(f"[OUTLIER_DETECTION] Date parsing error: {date_error}")
                continue
        
        print(f"[OUTLIER_DETECTION] Successfully processed {processed_records} consumption records")
        print(f"[OUTLIER_DETECTION] Found {len(user_daily_totals)} users with data")
        
        # Show sample user data
        if user_daily_totals:
            sample_user = list(user_daily_totals.keys())[0]
            sample_days = len(user_daily_totals[sample_user])
            print(f"[OUTLIER_DETECTION] Sample user {sample_user} has {sample_days} days of data")
        
        # Analyze for outliers - MEDICAL PATTERN DETECTION
        patient_outlier_profiles = {}
        total_outlier_days = 0
        nutrient_spike_days = 0
        
        # First pass: Identify all outlier days per patient
        for user_id, user_days in user_daily_totals.items():
            user_name = email_to_name.get(user_id, user_id)
            
            patient_profile = {
                "user_id": user_id,
                "user_name": user_name,
                "calorie_outliers": [],
                "nutrient_spikes": [],
                "pattern_analysis": {
                    "total_days_analyzed": len(user_days),
                    "extreme_low_days": 0,
                    "extreme_high_days": 0,
                    "chronic_malnutrition_risk": False,
                    "binge_eating_pattern": False,
                    "nutrient_abuse_pattern": False
                },
                "most_recent_outlier": None,
                "medical_priority": 0  # 0=normal, 1=monitor, 2=concern, 3=urgent, 4=critical
            }
            
            for date_key, daily_totals in user_days.items():
                # Check for extreme calorie intake
                calories = daily_totals["calories"]
                calorie_severity = None
                
                if calories <= OUTLIER_THRESHOLDS["calories"]["extremely_low"]:
                    calorie_severity = "extremely_low"
                    patient_profile["pattern_analysis"]["extreme_low_days"] += 1
                elif calories <= OUTLIER_THRESHOLDS["calories"]["very_low"]:
                    calorie_severity = "very_low"
                    patient_profile["pattern_analysis"]["extreme_low_days"] += 1
                elif calories >= OUTLIER_THRESHOLDS["calories"]["extremely_high"]:
                    calorie_severity = "extremely_high"
                    patient_profile["pattern_analysis"]["extreme_high_days"] += 1
                elif calories >= OUTLIER_THRESHOLDS["calories"]["very_high"]:
                    calorie_severity = "very_high"
                    patient_profile["pattern_analysis"]["extreme_high_days"] += 1
                
                if calorie_severity:
                    calorie_outlier = {
                        "date": date_key,
                        "calories": round(calories, 1),
                        "severity": calorie_severity,
                        "medical_concern": get_calorie_medical_concern(calorie_severity, calories),
                        "record_count": daily_totals["record_count"]
                    }
                    patient_profile["calorie_outliers"].append(calorie_outlier)
                    total_outlier_days += 1
                    
                    # Update most recent outlier
                    if not patient_profile["most_recent_outlier"] or date_key > patient_profile["most_recent_outlier"]["date"]:
                        patient_profile["most_recent_outlier"] = calorie_outlier
                
                # Check for nutrient spikes
                for nutrient in ["protein", "carbohydrates", "fat", "fiber", "sodium", "sugar"]:
                    nutrient_value = daily_totals[nutrient]
                    threshold_data = OUTLIER_THRESHOLDS[nutrient]
                    spike_threshold = threshold_data["rda"] * threshold_data["spike_multiplier"]
                    
                    if nutrient_value > spike_threshold:
                        spike_multiplier = nutrient_value / threshold_data["rda"]
                        spike_outlier = {
                            "date": date_key,
                            "nutrient": nutrient,
                            "value": round(nutrient_value, 1),
                            "rda": threshold_data["rda"],
                            "spike_multiplier": round(spike_multiplier, 1),
                            "severity": get_spike_severity(spike_multiplier),
                            "medical_concern": get_nutrient_medical_concern(nutrient, spike_multiplier)
                        }
                        patient_profile["nutrient_spikes"].append(spike_outlier)
                        nutrient_spike_days += 1
            
            # MEDICAL PATTERN ANALYSIS
            total_analyzed = patient_profile["pattern_analysis"]["total_days_analyzed"]
            extreme_low_days = patient_profile["pattern_analysis"]["extreme_low_days"]
            extreme_high_days = patient_profile["pattern_analysis"]["extreme_high_days"]
            
            # Chronic malnutrition pattern (>20% of days with extreme low calories OR avg < 1000)
            avg_daily_calories = sum([day["calories"] for day in user_days.values()]) / total_analyzed if total_analyzed > 0 else 0
            
            if (total_analyzed >= 3 and extreme_low_days / total_analyzed > 0.2) or avg_daily_calories < 1000:
                patient_profile["pattern_analysis"]["chronic_malnutrition_risk"] = True
                patient_profile["medical_priority"] = 4  # Critical
            
            # Binge eating pattern (2+ extremely high calorie days OR single day > 4000 cal)
            elif extreme_high_days >= 2 or any(day["calories"] > 4000 for day in user_days.values()):
                patient_profile["pattern_analysis"]["binge_eating_pattern"] = True
                patient_profile["medical_priority"] = 3  # Urgent
            
            # Moderate concern (any extreme outliers)
            elif extreme_low_days >= 1 or extreme_high_days >= 1:
                patient_profile["medical_priority"] = 2  # Concern
            
            # Light monitoring (any outliers at all)
            elif len(patient_profile["calorie_outliers"]) > 0 or len(patient_profile["nutrient_spikes"]) > 0:
                patient_profile["medical_priority"] = 1  # Monitor
            
            # Store patient profile if any outliers detected
            if patient_profile["medical_priority"] > 0:
                patient_outlier_profiles[user_id] = patient_profile
        
        # Generate MEDICAL ALERTS (deduplicated by patient)
        extreme_calorie_outliers = []
        nutrient_spike_outliers = []
        outlier_users = set()
        
        # Sort patients by medical priority (critical first)
        sorted_patients = sorted(
            patient_outlier_profiles.values(), 
            key=lambda p: (p["medical_priority"], len(p["calorie_outliers"]) + len(p["nutrient_spikes"])), 
            reverse=True
        )
        
        for patient in sorted_patients:
            outlier_users.add(patient["user_id"])
            
            # Add ONE representative calorie outlier per patient (most recent severe)
            if patient["calorie_outliers"]:
                # Get the most severe recent outlier
                severity_order = {"extremely_high": 4, "extremely_low": 3, "very_high": 2, "very_low": 1}
                most_severe = max(patient["calorie_outliers"], key=lambda x: (severity_order.get(x["severity"], 0), x["date"]))
                
                alert = {
                    "user_id": patient["user_id"],
                    "user_name": patient["user_name"],
                    "date": most_severe["date"],
                    "calories": most_severe["calories"],
                    "severity": most_severe["severity"],
                    "threshold": OUTLIER_THRESHOLDS["calories"][most_severe["severity"]],
                    "medical_concern": most_severe["medical_concern"],
                    "pattern_info": f"{patient['pattern_analysis']['total_days_analyzed']} days analyzed, {len(patient['calorie_outliers'])} outlier days",
                    "medical_priority": patient["medical_priority"],
                    "chronic_risk": patient["pattern_analysis"]["chronic_malnutrition_risk"],
                    "binge_pattern": patient["pattern_analysis"]["binge_eating_pattern"]
                }
                extreme_calorie_outliers.append(alert)
            
            # Add severe nutrient spikes (limit to most dangerous)
            severe_spikes = [s for s in patient["nutrient_spikes"] if s["severity"] in ["severe", "critical"]]
            for spike in severe_spikes[:2]:  # Limit to 2 most severe per patient
                alert = {
                    "user_id": patient["user_id"],
                    "user_name": patient["user_name"],
                    "date": spike["date"],
                    "nutrient": spike["nutrient"],
                    "value": spike["value"],
                    "rda": spike["rda"],
                    "spike_multiplier": spike["spike_multiplier"],
                    "threshold": spike["rda"] * OUTLIER_THRESHOLDS[spike["nutrient"]]["spike_multiplier"],
                    "severity": spike["severity"],
                    "medical_concern": spike["medical_concern"],
                    "medical_priority": patient["medical_priority"]
                }
                nutrient_spike_outliers.append(alert)
        
        # Sort outliers by medical priority and severity
        extreme_calorie_outliers.sort(key=lambda x: (x["medical_priority"], x["severity"] == "extremely_low"), reverse=True)
        nutrient_spike_outliers.sort(key=lambda x: (x["medical_priority"], x["spike_multiplier"]), reverse=True)
        
        # Calculate MEDICAL SUMMARY STATISTICS
        total_outlier_users = len(outlier_users)
        critical_patients = len([p for p in patient_outlier_profiles.values() if p["medical_priority"] >= 4])
        urgent_patients = len([p for p in patient_outlier_profiles.values() if p["medical_priority"] == 3])
        concern_patients = len([p for p in patient_outlier_profiles.values() if p["medical_priority"] == 2])
        
        # Count patients with specific patterns
        chronic_malnutrition_cases = len([p for p in patient_outlier_profiles.values() if p["pattern_analysis"]["chronic_malnutrition_risk"]])
        binge_eating_cases = len([p for p in patient_outlier_profiles.values() if p["pattern_analysis"]["binge_eating_pattern"]])
        
        # Determine most common issue
        if chronic_malnutrition_cases > 0:
            most_common_outlier = "Chronic Malnutrition"
        elif binge_eating_cases > 0:
            most_common_outlier = "Binge Eating Pattern"
        elif len(extreme_calorie_outliers) > len(nutrient_spike_outliers):
            most_common_outlier = "Calorie Imbalance"
        elif len(nutrient_spike_outliers) > 0:
            most_common_outlier = "Nutrient Spikes"
        else:
            most_common_outlier = "No Critical Issues"
        
        return {
            "total_registered_patients": total_registered_patients,
            "total_registered_users": total_users_count,
            "analysis_period": {
                "days": days,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "total_records_analyzed": len(all_consumption)
            },
            "medical_classification": {
                "critical_patients": critical_patients,
                "urgent_patients": urgent_patients,
                "concern_patients": concern_patients,
                "chronic_malnutrition_cases": chronic_malnutrition_cases,
                "binge_eating_cases": binge_eating_cases
            },
            "outliers": {
                "extreme_calorie_intake": extreme_calorie_outliers,
                "nutrient_spikes": nutrient_spike_outliers,
                "patient_profiles": [
                    {
                        "user_id": p["user_id"],
                        "user_name": p["user_name"],
                        "medical_priority": p["medical_priority"],
                        "total_days_analyzed": p["pattern_analysis"]["total_days_analyzed"],
                        "outlier_days": len(p["calorie_outliers"]),
                        "chronic_malnutrition_risk": p["pattern_analysis"]["chronic_malnutrition_risk"],
                        "binge_eating_pattern": p["pattern_analysis"]["binge_eating_pattern"],
                        "pattern_type": (
                            "Chronic Malnutrition" if p["pattern_analysis"]["chronic_malnutrition_risk"]
                            else "Binge Eating" if p["pattern_analysis"]["binge_eating_pattern"]
                            else "Irregular Eating"
                        )
                    }
                    for p in sorted_patients[:10]  # Top 10 most concerning patients
                ]
            },
            "summary": {
                "total_outlier_users": total_outlier_users,
                "patients_needing_immediate_attention": critical_patients + urgent_patients,
                "total_outlier_days_detected": total_outlier_days,
                "most_common_outlier": most_common_outlier,
                "outlier_user_names": [
                    {
                        "user_name": email_to_name.get(user_id, user_id),
                        "medical_priority": patient_outlier_profiles[user_id]["medical_priority"],
                        "pattern_type": (
                            "Chronic Malnutrition" if patient_outlier_profiles[user_id]["pattern_analysis"]["chronic_malnutrition_risk"]
                            else "Binge Eating" if patient_outlier_profiles[user_id]["pattern_analysis"]["binge_eating_pattern"]
                            else "Irregular Eating"
                        )
                    }
                    for user_id in outlier_users
                ]
            },
            "thresholds": OUTLIER_THRESHOLDS,
            "recommendations": {
                "immediate_attention": [
                    f"{critical_patients} patients require CRITICAL medical intervention",
                    f"{chronic_malnutrition_cases} patients show chronic malnutrition patterns",
                    f"{urgent_patients} patients need urgent dietary counseling",
                    f"{len([o for o in nutrient_spike_outliers if o.get('severity') in ['severe', 'critical']])} severe nutrient spikes detected"
                ] if critical_patients > 0 or urgent_patients > 0 else [
                    "No patients require immediate critical intervention",
                    f"{concern_patients} patients recommended for monitoring",
                    "Continue routine nutritional assessment"
                ],
                "monitoring_priorities": [
                    "Schedule immediate consultations for chronic malnutrition cases",
                    "Implement structured meal plans for irregular eaters",
                    "Monitor blood glucose levels for binge eating patterns",
                    "Review medication effects on appetite and metabolism",
                    "Consider mental health screening for eating disorders"
                ] if critical_patients > 0 else [
                    "Maintain regular monitoring of at-risk patients",
                    "Continue encouraging consistent meal logging",
                    "Review and adjust dietary goals as needed"
                ]
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Debug summary
        total_patients_analyzed = len(patient_outlier_profiles)
        print(f"[OUTLIER_DETECTION] SUMMARY: Found {total_patients_analyzed} patients with outliers")
        print(f"[OUTLIER_DETECTION] Priority levels: Critical={critical_patients}, Urgent={urgent_patients}, Concern={concern_patients}, Monitor={monitor_patients}")
        
    except Exception as e:
        print(f"[OUTLIER_DETECTION] Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get outlier detection: {str(e)}")


def get_calorie_medical_concern(severity: str, calories: float) -> str:
    """Get medical concern description for calorie outliers."""
    concerns = {
        "extremely_low": f"Severe caloric restriction ({calories:.0f} cal) - Risk of malnutrition and metabolic slowdown",
        "very_low": f"Very low caloric intake ({calories:.0f} cal) - May impair metabolism and energy levels", 
        "very_high": f"Excessive caloric intake ({calories:.0f} cal) - Risk of weight gain and metabolic stress",
        "extremely_high": f"Dangerous caloric excess ({calories:.0f} cal) - Immediate intervention recommended"
    }
    return concerns.get(severity, f"Unusual caloric intake: {calories:.0f} calories")


def get_spike_severity(multiplier: float) -> str:
    """Determine severity level based on RDA multiplier."""
    if multiplier >= 5.0:
        return "critical"
    elif multiplier >= 4.0:
        return "severe"
    elif multiplier >= 3.0:
        return "high"
    elif multiplier >= 2.0:
        return "moderate"
    else:
        return "mild"


def get_nutrient_medical_concern(nutrient: str, multiplier: float) -> str:
    """Get medical concern description for nutrient spikes."""
    concerns = {
        "protein": f"Excessive protein ({multiplier:.1f}x RDA) - May stress kidneys, especially in diabetes",
        "carbohydrates": f"Carbohydrate spike ({multiplier:.1f}x RDA) - Risk of blood sugar crisis", 
        "fat": f"High fat intake ({multiplier:.1f}x RDA) - Cardiovascular and digestive concerns",
        "fiber": f"Very high fiber ({multiplier:.1f}x RDA) - May cause digestive discomfort",
        "sodium": f"Sodium overload ({multiplier:.1f}x RDA) - Hypertension and fluid retention risk",
        "sugar": f"Sugar spike ({multiplier:.1f}x RDA) - Immediate blood glucose management needed"
    }
    return concerns.get(nutrient, f"Nutrient spike detected: {multiplier:.1f}x normal levels")


@router.get("/admin/pias-corner/behavior-clusters")
async def get_behavior_clusters(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze patient dietary behavior clusters including:
    - High Protein – Low Carb patterns
    - Night Eating behaviors  
    - Under-reporting tendencies
    
    Links behavior patterns to health outcomes (weight, sugar control) for medical insights.
    """
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        print(f"[BEHAVIOR_CLUSTERS] Starting behavior analysis for {days} days")
        
        # Get total registered patients for comparison
        all_patients = await get_all_patients()
        total_registered_patients = len(all_patients)
        
        # Get time range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get all consumption records in the time period
        consumption_query = f"""
            SELECT * FROM c 
            WHERE c.type = 'consumption_record' 
            AND c.timestamp >= '{start_date.isoformat()}'
        """
        all_consumption = list(interactions_container.query_items(
            query=consumption_query, 
            enable_cross_partition_query=True
        ))
        
        print(f"[BEHAVIOR_CLUSTERS] Found {len(all_consumption)} consumption records")
        
        # Filter out deleted duplicate account records
        all_consumption = [r for r in all_consumption if r.get('user_id') != 'nagarwal166@gmail.com']
        print(f"[BEHAVIOR_CLUSTERS] After filtering deleted accounts: {len(all_consumption)} records")
        
        # Debug: Show sample of consumption data
        if all_consumption:
            sample_record = all_consumption[0]
            print(f"[BEHAVIOR_CLUSTERS] Sample consumption record: user_id={sample_record.get('user_id')}, "
                  f"timestamp={sample_record.get('timestamp')}, "
                  f"nutritional_info keys={list(sample_record.get('nutritional_info', {}).keys())}")
        
        # Get all registered users (excluding admin) (include both 'user' and 'patient' types)
        all_users_query = "SELECT * FROM c WHERE (c.type = 'user' OR c.type = 'patient') AND c.is_admin != true"
        all_users_raw = list(user_container.query_items(query=all_users_query, enable_cross_partition_query=True))
        
        # Deduplicate users: prioritize type='user' over type='patient' for same registration code
        user_map = {}
        for user in all_users_raw:
            reg_code = user.get('registration_code', '')
            user_type = user.get('type', '')
            
            if reg_code:
                if reg_code not in user_map:
                    user_map[reg_code] = user
                elif user_type == 'user' and user_map[reg_code].get('type') == 'patient':
                    # Prioritize 'user' type over 'patient' type
                    user_map[reg_code] = user
        
        # Convert back to list
        all_users = list(user_map.values())
        total_users_count = len(all_users)
        
        # Create email to name mapping using admin panel patient data as authoritative source
        email_to_name = {}
        
        # First, get all admin panel patients (authoritative source for names)
        admin_patients = await get_all_patients()
        registration_to_name = {}
        for patient in admin_patients:
            reg_code = patient.get("registration_code")
            patient_name = patient.get("name", "").strip()
            if reg_code and patient_name:
                registration_to_name[reg_code] = patient_name
        
        # Map user emails to patient names using registration codes
        for user in all_users:
            email = user.get("email")
            registration_code = user.get("registration_code")
            
            if email:
                # First priority: Use admin panel patient name (authoritative)
                if registration_code and registration_code in registration_to_name:
                    email_to_name[email] = registration_to_name[registration_code]
                else:
                    # Second priority: Use profile name if available
                    profile = user.get("profile", {})
                    profile_name = profile.get("name", "").strip()
                    if profile_name:
                        email_to_name[email] = profile_name
                    else:
                        # Last resort: Create professional fallback from email
                        username = email.split("@")[0]
                        if len(username) > 0:
                            readable_name = username.replace(".", " ").replace("_", " ")
                            readable_name = " ".join(word.capitalize() for word in readable_name.split())
                            email_to_name[email] = f"Patient {readable_name}"
                        else:
                            email_to_name[email] = "Unknown Patient"
        
        
        if not all_consumption:
            return {
                "total_registered_patients": total_registered_patients,
                "total_registered_users": total_users_count,
                "analysis_period": {
                    "days": days,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "total_records_analyzed": 0
                },
                "behavior_clusters": {
                    "high_protein_low_carb": [],
                    "night_eaters": [],
                    "under_reporters": []
                },
                "cluster_summary": {
                    "total_clustered_patients": 0,
                    "high_protein_low_carb_count": 0,
                    "night_eaters_count": 0,
                    "under_reporters_count": 0
                },
                "health_outcomes": {},
                "generated_at": datetime.utcnow().isoformat()
            }
        
        # Group consumption by user and date for analysis
        from collections import defaultdict
        import statistics
        
        user_daily_data = defaultdict(lambda: defaultdict(lambda: {
            "calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0,
            "record_count": 0, "timestamps": []
        }))
        
        # Process all consumption records
        for record in all_consumption:
            user_id = record.get("user_id")
            timestamp = record.get("timestamp", "")
            nutrition = record.get("nutritional_info", {})
            
            if not user_id or not timestamp:
                continue
                
            try:
                record_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                date_key = record_date.strftime("%Y-%m-%d")
                
                # Store data for analysis
                daily_data = user_daily_data[user_id][date_key]
                daily_data["record_count"] += 1
                daily_data["timestamps"].append(record_date)
                
                # Accumulate nutrition
                for nutrient in ["calories", "protein", "carbohydrates", "fat"]:
                    daily_data[nutrient] += float(nutrition.get(nutrient, 0))
                    
            except Exception as date_error:
                print(f"[BEHAVIOR_CLUSTERS] Date parsing error: {date_error}")
                continue
        
        # Analyze behavioral patterns for each user
        behavior_clusters = {
            "high_protein_low_carb": [],
            "night_eaters": [],
            "under_reporters": []
        }
        
        patient_behavior_profiles = {}
        
        for user_id, user_days in user_daily_data.items():
            if len(user_days) < 3:  # Need minimum data for analysis
                continue
                
            user_name = email_to_name.get(user_id, user_id)
            
            # Calculate averages and patterns
            daily_calories = []
            daily_protein_pct = []
            daily_carb_pct = []
            night_eating_days = 0
            total_analyzed_days = len(user_days)
            
            for date_key, daily_totals in user_days.items():
                calories = daily_totals["calories"]
                protein = daily_totals["protein"]
                carbs = daily_totals["carbohydrates"]
                timestamps = daily_totals["timestamps"]
                
                daily_calories.append(calories)
                
                # Calculate macronutrient percentages
                if calories > 0:
                    protein_pct = (protein * 4) / calories * 100  # 4 cal per gram protein
                    carb_pct = (carbs * 4) / calories * 100      # 4 cal per gram carbs
                    daily_protein_pct.append(protein_pct)
                    daily_carb_pct.append(carb_pct)
                
                # Check for night eating (after 8 PM)
                late_night_calories = 0
                for ts in timestamps:
                    if ts.hour >= 20:  # 8 PM or later
                        # Estimate calories per meal record (simple approximation)
                        late_night_calories += calories / len(timestamps)
                
                if late_night_calories > 0 and calories > 0:
                    late_eating_percentage = (late_night_calories / calories) * 100
                    if late_eating_percentage >= BEHAVIOR_THRESHOLDS["night_eating"]["min_late_calories_percentage"]:
                        night_eating_days += 1
            
            # Calculate user averages
            avg_calories = statistics.mean(daily_calories) if daily_calories else 0
            avg_protein_pct = statistics.mean(daily_protein_pct) if daily_protein_pct else 0
            avg_carb_pct = statistics.mean(daily_carb_pct) if daily_carb_pct else 0
            
            # Get user profile for health outcomes
            user_profile = next((u.get("profile", {}) for u in all_users if u.get("email") == user_id), {})
            current_weight = user_profile.get("weight", 0)
            medical_conditions = user_profile.get("medicalConditions", [])
            has_diabetes = any("diabetes" in str(condition).lower() for condition in medical_conditions)
            
            # Create behavior profile
            behavior_profile = {
                "user_id": user_id,
                "user_name": user_name,
                "analysis_days": total_analyzed_days,
                "avg_daily_calories": round(avg_calories, 1),
                "avg_protein_percentage": round(avg_protein_pct, 1),
                "avg_carb_percentage": round(avg_carb_pct, 1),
                "night_eating_days": night_eating_days,
                "night_eating_frequency": round((night_eating_days / total_analyzed_days) * 100, 1),
                "medical_conditions": medical_conditions,
                "has_diabetes": has_diabetes,
                "current_weight": current_weight,
                "behavioral_flags": []
            }
            
            # CLUSTER 1: HIGH PROTEIN - LOW CARB PATTERN
            high_protein_days = sum(1 for pct in daily_protein_pct if pct >= BEHAVIOR_THRESHOLDS["high_protein_low_carb"]["min_protein_percentage"])
            low_carb_days = sum(1 for pct in daily_carb_pct if pct <= BEHAVIOR_THRESHOLDS["high_protein_low_carb"]["max_carb_percentage"])
            
            if (high_protein_days >= BEHAVIOR_THRESHOLDS["high_protein_low_carb"]["min_days_threshold"] and 
                low_carb_days >= BEHAVIOR_THRESHOLDS["high_protein_low_carb"]["min_days_threshold"]):
                
                behavior_profile["behavioral_flags"].append("high_protein_low_carb")
                behavior_profile["high_protein_low_carb_score"] = round((high_protein_days + low_carb_days) / (total_analyzed_days * 2) * 100, 1)
                
                # Health outcome analysis for this pattern
                outcome_analysis = {
                    "weight_management": "potentially_beneficial" if avg_calories < 2000 else "monitor_calories",
                    "diabetes_impact": "beneficial" if has_diabetes else "not_applicable",
                    "sustainability_concern": "high" if avg_protein_pct > 35 else "moderate",
                    "medical_notes": []
                }
                
                if has_diabetes:
                    outcome_analysis["medical_notes"].append("High protein, low carb may improve blood sugar control")
                if avg_protein_pct > 30:
                    outcome_analysis["medical_notes"].append("Monitor kidney function with sustained high protein intake")
                
                behavior_profile["health_outcomes"] = outcome_analysis
                behavior_clusters["high_protein_low_carb"].append(behavior_profile.copy())
            
            # CLUSTER 2: NIGHT EATING PATTERN
            if night_eating_days >= BEHAVIOR_THRESHOLDS["night_eating"]["min_days_threshold"]:
                behavior_profile["behavioral_flags"].append("night_eating")
                behavior_profile["night_eating_severity"] = "high" if night_eating_days > total_analyzed_days * 0.5 else "moderate"
                
                # Health outcome analysis for night eating
                outcome_analysis = {
                    "weight_management": "concerning" if avg_calories > 2200 else "monitor",
                    "diabetes_impact": "detrimental" if has_diabetes else "concerning",
                    "sleep_quality": "likely_impaired",
                    "metabolic_impact": "negative",
                    "medical_notes": []
                }
                
                if has_diabetes:
                    outcome_analysis["medical_notes"].append("Night eating can disrupt blood sugar control")
                outcome_analysis["medical_notes"].append("Late eating may impair sleep and metabolism")
                if avg_calories > 2500:
                    outcome_analysis["medical_notes"].append("Excessive calories from night eating - weight gain risk")
                
                behavior_profile["health_outcomes"] = outcome_analysis
                behavior_clusters["night_eaters"].append(behavior_profile.copy())
            
            # CLUSTER 3: UNDER-REPORTING PATTERN
            very_low_calorie_days = sum(1 for cal in daily_calories if cal <= BEHAVIOR_THRESHOLDS["under_reporting"]["very_low_calorie_threshold"])
            low_calorie_days = sum(1 for cal in daily_calories if cal <= BEHAVIOR_THRESHOLDS["under_reporting"]["low_calorie_threshold"])
            
            if (very_low_calorie_days >= BEHAVIOR_THRESHOLDS["under_reporting"]["min_days_threshold"] or 
                low_calorie_days >= total_analyzed_days * 0.6):  # 60% of days with low calories
                
                behavior_profile["behavioral_flags"].append("under_reporting")
                behavior_profile["under_reporting_severity"] = "high" if very_low_calorie_days > 5 else "moderate"
                behavior_profile["avg_calorie_deficit"] = round(BEHAVIOR_THRESHOLDS["under_reporting"]["expected_min_calories"] - avg_calories, 1)
                
                # Health outcome analysis for under-reporting
                outcome_analysis = {
                    "nutritional_status": "at_risk",
                    "metabolic_impact": "concerning",
                    "data_reliability": "poor",
                    "intervention_needed": "educational",
                    "medical_notes": []
                }
                
                if avg_calories < 1000:
                    outcome_analysis["medical_notes"].append("Extremely low reported intake - likely significant under-reporting")
                    outcome_analysis["intervention_needed"] = "immediate"
                elif avg_calories < 1200:
                    outcome_analysis["medical_notes"].append("Very low reported intake - counseling on portion awareness needed")
                
                outcome_analysis["medical_notes"].append("Monitor for signs of malnutrition or eating disorders")
                
                behavior_profile["health_outcomes"] = outcome_analysis
                behavior_clusters["under_reporters"].append(behavior_profile.copy())
            
            # Store complete profile
            if behavior_profile["behavioral_flags"]:
                patient_behavior_profiles[user_id] = behavior_profile
        
        # Calculate cluster summary statistics
        cluster_summary = {
            "total_clustered_patients": len(patient_behavior_profiles),
            "high_protein_low_carb_count": len(behavior_clusters["high_protein_low_carb"]),
            "night_eaters_count": len(behavior_clusters["night_eaters"]),
            "under_reporters_count": len(behavior_clusters["under_reporters"]),
            "multiple_behaviors": len([p for p in patient_behavior_profiles.values() if len(p["behavioral_flags"]) > 1])
        }
        
        # Analyze health outcomes across clusters
        health_outcome_analysis = {
            "diabetes_patients": {
                "total": len([u for u in all_users if any("diabetes" in str(mc).lower() for mc in u.get("profile", {}).get("medicalConditions", []))]),
                "in_high_protein_low_carb": len([p for p in behavior_clusters["high_protein_low_carb"] if p["has_diabetes"]]),
                "in_night_eaters": len([p for p in behavior_clusters["night_eaters"] if p["has_diabetes"]]),
                "in_under_reporters": len([p for p in behavior_clusters["under_reporters"] if p["has_diabetes"]])
            },
            "weight_concerns": {
                "high_protein_low_carb_avg_calories": round(statistics.mean([p["avg_daily_calories"] for p in behavior_clusters["high_protein_low_carb"]]), 1) if behavior_clusters["high_protein_low_carb"] else 0,
                "night_eaters_avg_calories": round(statistics.mean([p["avg_daily_calories"] for p in behavior_clusters["night_eaters"]]), 1) if behavior_clusters["night_eaters"] else 0,
                "under_reporters_avg_calories": round(statistics.mean([p["avg_daily_calories"] for p in behavior_clusters["under_reporters"]]), 1) if behavior_clusters["under_reporters"] else 0
            },
            "behavioral_overlap": {
                "night_eating_and_high_protein": len([p for p in patient_behavior_profiles.values() if "night_eating" in p["behavioral_flags"] and "high_protein_low_carb" in p["behavioral_flags"]]),
                "under_reporting_and_night_eating": len([p for p in patient_behavior_profiles.values() if "under_reporting" in p["behavioral_flags"] and "night_eating" in p["behavioral_flags"]])
            }
        }
        
        # Generate scatter plot data for frontend visualization
        scatter_plot_data = []
        
        # Add all clustered patients to scatter plot
        for cluster_type, patients in behavior_clusters.items():
            for patient in patients:
                scatter_plot_data.append({
                    "x": patient["analysis_days"],  # Days of data analyzed
                    "y": patient["avg_daily_calories"],  # Average daily calories  
                    "patientName": patient["user_name"],
                    "analysisDays": patient["analysis_days"],
                    "hasDiabetes": patient["has_diabetes"],
                    "calories": patient["avg_daily_calories"],
                    "score": patient.get("high_protein_low_carb_score", 0) or patient.get("night_eating_frequency", 0) or patient.get("under_reporting_score", 0),
                    "clusterType": cluster_type.replace("_", " ").title()
                })

        return {
            "total_registered_patients": total_registered_patients,
            "total_registered_users": total_users_count,
            "analysis_period": {
                "days": days,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "total_records_analyzed": len(all_consumption)
            },
            "behavior_clusters": behavior_clusters,
            "cluster_summary": cluster_summary,
            "scatter_plot_data": scatter_plot_data,  # Added missing scatter plot data
            "health_outcomes": health_outcome_analysis,
            "behavioral_thresholds": BEHAVIOR_THRESHOLDS,
            "medical_insights": {
                "priority_interventions": [
                    f"{len(behavior_clusters['under_reporters'])} patients may need portion awareness education",
                    f"{len([p for p in behavior_clusters['night_eaters'] if p['has_diabetes']])} diabetes patients with concerning night eating patterns",
                    f"{len([p for p in behavior_clusters['high_protein_low_carb'] if p.get('high_protein_low_carb_score', 0) > 80])} patients on very restrictive high-protein diets"
                ],
                "positive_patterns": [
                    f"{len([p for p in behavior_clusters['high_protein_low_carb'] if p['has_diabetes']])} diabetes patients successfully following low-carb patterns",
                    f"{cluster_summary['total_clustered_patients']} patients show identifiable behavioral patterns for targeted counseling"
                ],
                "monitoring_recommendations": [
                    "Schedule nutrition counseling for under-reporters focusing on portion awareness",
                    "Implement evening meal timing guidelines for night eaters",
                    "Monitor kidney function in sustained high-protein dieters",
                    "Track blood glucose patterns in diabetes patients with identified clusters",
                    "Consider sleep study referrals for severe night eaters"
                ]
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Debug summary
        total_clustered = cluster_summary['total_clustered_patients']
        print(f"[BEHAVIOR_CLUSTERS] SUMMARY: Found {total_clustered} patients with behavioral patterns")
        print(f"[BEHAVIOR_CLUSTERS] High Protein-Low Carb: {cluster_summary['high_protein_low_carb_count']}")
        print(f"[BEHAVIOR_CLUSTERS] Night Eaters: {cluster_summary['night_eaters_count']}")
        print(f"[BEHAVIOR_CLUSTERS] Under-reporters: {cluster_summary['under_reporters_count']}")
        print(f"[BEHAVIOR_CLUSTERS] Multiple Behaviors: {cluster_summary['multiple_behaviors']}")
        
    except Exception as e:
        print(f"[BEHAVIOR_CLUSTERS] Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get behavior clusters: {str(e)}")

# Medical compliance thresholds and definitions
COMPLIANCE_TARGETS = {
    "calorie_targets": {
        "min_healthy_calories": 1200,      # Minimum safe daily calories
        "max_healthy_calories": 2500,      # Maximum recommended daily calories
        "diabetic_range": (1800, 2200),    # Optimal range for diabetic patients
        "tolerance_percentage": 15         # ±15% tolerance for target compliance
    },
    "nutrient_targets": {
        "fiber_min": 25,                   # Minimum fiber (g) per day
        "protein_min_percentage": 15,      # Minimum protein % of total calories
        "sodium_max": 2300,                # Maximum sodium (mg) per day
        "sugar_max_percentage": 10,        # Maximum added sugar % of total calories
        "carb_max_percentage": 45          # Maximum carbs % for diabetic patients
    },
    "compliance_thresholds": {
        "high_compliance": 80,             # ≥80% of days within targets
        "medium_compliance": 60,           # 60-79% of days within targets
        "low_compliance": 60               # <60% of days within targets
    },
    "logging_consistency": {
        "excellent_logging": 90,           # ≥90% of days logged
        "good_logging": 70,                # 70-89% of days logged
        "poor_logging": 70                 # <70% of days logged
    }
}

@router.get("/admin/pias-corner/compliance")
async def get_compliance_analysis(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze patient compliance with dietary targets and logging consistency.
    Provides high vs low compliance user segmentation for medical review.
    """
    print(f"[COMPLIANCE_ANALYSIS] Starting compliance analysis for {days} days")
    
    # Check if user is admin
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        print(f"[COMPLIANCE_ANALYSIS] Analysis period: {start_date.date()} to {end_date.date()}")
        
        # Get all consumption records in the analysis period
        consumption_query = f"""
        SELECT * FROM c 
        WHERE c.type = 'consumption_record' 
        AND c.timestamp >= '{start_date.isoformat()}' 
        AND c.timestamp <= '{end_date.isoformat()}'
        """
        
        consumption_records = list(interactions_container.query_items(
            query=consumption_query, 
            enable_cross_partition_query=True
        ))
        
        print(f"[COMPLIANCE_ANALYSIS] Found {len(consumption_records)} consumption records")
        
        # Filter out deleted duplicate account records
        consumption_records = [r for r in consumption_records if r.get('user_id') != 'nagarwal166@gmail.com']
        print(f"[COMPLIANCE_ANALYSIS] After filtering deleted accounts: {len(consumption_records)} records")
        
        # Get all users and admin patients for name mapping
        all_users_query = "SELECT * FROM c WHERE c.type = 'user'"
        all_users = list(user_container.query_items(query=all_users_query, enable_cross_partition_query=True))
        
        admin_patients = await get_all_patients()
        
        # Create email to name mapping (authoritative admin source) - Using same logic as behavior clusters
        email_to_name = {}
        email_to_conditions = {}
        
        # First, create registration code to name mapping from admin patients
        registration_to_name = {}
        for patient in admin_patients:
            reg_code = patient.get("registration_code")
            patient_name = patient.get("name", "").strip()
            email = patient.get("email", "").strip()
            condition = patient.get("condition", "")
            
            if reg_code and patient_name:
                registration_to_name[reg_code] = patient_name
            
            # Also map by email if available (direct admin panel mapping)
            if email and patient_name:
                email_to_name[email] = patient_name
                email_to_conditions[email] = condition
        
        # Map user emails to patient names using registration codes (authoritative hierarchy)
        for user in all_users:
            email = user.get("email")
            registration_code = user.get("registration_code")
            
            if email:
                # First priority: Use admin panel patient name (authoritative)
                if registration_code and registration_code in registration_to_name:
                    email_to_name[email] = registration_to_name[registration_code]
                elif email not in email_to_name:  # Only if not already mapped by direct email
                    # Second priority: Use profile name if available
                    profile = user.get("profile", {})
                    profile_name = profile.get("name", "").strip()
                    if profile_name:
                        email_to_name[email] = profile_name
                    else:
                        # Last resort: Create professional fallback from email
                        username = email.split("@")[0]
                        if len(username) > 0:
                            readable_name = username.replace(".", " ").replace("_", " ")
                            readable_name = " ".join(word.capitalize() for word in readable_name.split())
                            email_to_name[email] = f"Patient {readable_name}"
                        else:
                            email_to_name[email] = "Unknown Patient"
                
                # Set default condition if not already set
                if email not in email_to_conditions:
                    email_to_conditions[email] = "General"
        
        # Group consumption data by user and date
        user_daily_data = {}
        unique_users = set()
        
        for record in consumption_records:
            user_id = record.get('user_id', '')
            if not user_id:
                continue
                
            unique_users.add(user_id)
            record_date = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00')).date()
            
            if user_id not in user_daily_data:
                user_daily_data[user_id] = {}
            
            if record_date not in user_daily_data[user_id]:
                user_daily_data[user_id][record_date] = {
                    'total_calories': 0,
                    'total_protein': 0,
                    'total_carbs': 0,
                    'total_fat': 0,
                    'total_fiber': 0,
                    'total_sodium': 0,
                    'total_sugar': 0,
                    'meal_count': 0
                }
            
            # Accumulate daily totals - Fix data access to use nutritional_info
            daily_data = user_daily_data[user_id][record_date]
            
            # Extract nutritional info from the correct nested structure
            nutritional_info = record.get('nutritional_info', {})
            
            daily_data['total_calories'] += nutritional_info.get('calories', 0)
            daily_data['total_protein'] += nutritional_info.get('protein', 0)
            daily_data['total_carbs'] += nutritional_info.get('carbohydrates', 0)
            daily_data['total_fat'] += nutritional_info.get('fat', 0)
            daily_data['total_fiber'] += nutritional_info.get('fiber', 0)
            daily_data['total_sodium'] += nutritional_info.get('sodium', 0)
            daily_data['total_sugar'] += nutritional_info.get('sugar', 0)
            daily_data['meal_count'] += 1
        
        print(f"[COMPLIANCE_ANALYSIS] Analyzing compliance for {len(unique_users)} unique users")
        
        # Calculate compliance for each user
        user_compliance_profiles = []
        compliance_summary = {
            "high_compliance": [],
            "medium_compliance": [],
            "low_compliance": []
        }
        
        total_analysis_days = days
        
        for user_id in unique_users:
            user_name = email_to_name.get(user_id, f"Patient {user_id[:8]}")
            medical_condition = email_to_conditions.get(user_id, "General")
            is_diabetic = 'diabetes' in medical_condition.lower()
            
            daily_data = user_daily_data.get(user_id, {})
            total_logged_days = len(daily_data)
            
            if total_logged_days == 0:
                # No data - classify as non-compliant
                compliance_profile = {
                    "user_id": user_id,
                    "user_name": user_name,
                    "medical_condition": medical_condition,
                    "is_diabetic": is_diabetic,
                    "analysis_days": total_analysis_days,
                    "logged_days": 0,
                    "logging_compliance_rate": 0,
                    "calorie_compliance_rate": 0,
                    "nutrient_compliance_rate": 0,
                    "overall_compliance_rate": 0,
                    "compliance_category": "low",
                    "compliance_issues": ["No meal logging data available"],
                    "strengths": [],
                    "recommendations": ["Encourage consistent daily meal logging", "Schedule nutrition consultation"]
                }
                user_compliance_profiles.append(compliance_profile)
                compliance_summary["low_compliance"].append(compliance_profile)
                continue
            
            # Calculate logging compliance
            logging_compliance_rate = (total_logged_days / total_analysis_days) * 100
            
            # Calculate nutritional compliance rates
            calorie_compliant_days = 0
            nutrient_compliant_days = 0
            compliance_issues = []
            strengths = []
            
            # Debug info for this user
            total_calories_sum = 0
            valid_calorie_days = 0
            
            for date, data in daily_data.items():
                calories = data['total_calories']
                protein = data['total_protein']
                carbs = data['total_carbs']
                fiber = data['total_fiber']
                sodium = data['total_sodium']
                sugar = data['total_sugar']
                
                # Track calorie data for debugging
                if calories > 0:
                    total_calories_sum += calories
                    valid_calorie_days += 1
                
                # Calorie compliance check - use more realistic targets
                if is_diabetic:
                    calorie_target_min, calorie_target_max = COMPLIANCE_TARGETS["calorie_targets"]["diabetic_range"]
                else:
                    calorie_target_min = COMPLIANCE_TARGETS["calorie_targets"]["min_healthy_calories"]
                    calorie_target_max = COMPLIANCE_TARGETS["calorie_targets"]["max_healthy_calories"]
                
                tolerance = COMPLIANCE_TARGETS["calorie_targets"]["tolerance_percentage"] / 100
                calorie_min_with_tolerance = calorie_target_min * (1 - tolerance)
                calorie_max_with_tolerance = calorie_target_max * (1 + tolerance)
                
                # More lenient calorie compliance - check if calories are reasonable (not zero)
                if calories >= 800 and calories <= 3500:  # Reasonable daily calorie range
                    calorie_compliant_days += 1
                
                # Nutrient compliance check - more realistic assessment
                nutrient_compliant = True
                nutrient_issues_for_day = []
                
                if calories > 0:  # Avoid division by zero
                    protein_percentage = (protein * 4 / calories) * 100
                    carb_percentage = (carbs * 4 / calories) * 100
                    sugar_percentage = (sugar * 4 / calories) * 100
                    
                    # Check nutrient targets with more realistic standards
                    if fiber < 15:  # Relaxed fiber minimum (was 25g)
                        nutrient_issues_for_day.append("Low fiber")
                    if protein_percentage < 10:  # Relaxed protein minimum (was 15%)
                        nutrient_issues_for_day.append("Low protein")
                    if sodium > 3000:  # Slightly more lenient sodium (was 2300mg)
                        nutrient_issues_for_day.append("High sodium")
                    if sugar_percentage > 15:  # More lenient sugar (was 10%)
                        nutrient_issues_for_day.append("High sugar")
                    if is_diabetic and carb_percentage > 50:  # Slightly more lenient carbs (was 45%)
                        nutrient_issues_for_day.append("High carbs for diabetes")
                    
                    # If no major issues, count as compliant
                    if len(nutrient_issues_for_day) <= 1:  # Allow one minor issue per day
                        nutrient_compliant_days += 1
                else:
                    # No calories logged = not compliant
                    nutrient_compliant = False
            
            # Calculate compliance rates
            calorie_compliance_rate = (calorie_compliant_days / total_logged_days) * 100 if total_logged_days > 0 else 0
            nutrient_compliance_rate = (nutrient_compliant_days / total_logged_days) * 100 if total_logged_days > 0 else 0
            
            # Debug logging for this user
            avg_daily_calories = total_calories_sum / valid_calorie_days if valid_calorie_days > 0 else 0
            print(f"[COMPLIANCE_DEBUG] User: {user_name}")
            print(f"  - Logged Days: {total_logged_days}/{total_analysis_days}")
            print(f"  - Valid Calorie Days: {valid_calorie_days}")
            print(f"  - Avg Daily Calories: {avg_daily_calories:.1f}")
            print(f"  - Calorie Compliant Days: {calorie_compliant_days}")
            print(f"  - Nutrient Compliant Days: {nutrient_compliant_days}")
            print(f"  - Logging Rate: {logging_compliance_rate:.1f}%")
            print(f"  - Calorie Rate: {calorie_compliance_rate:.1f}%")
            print(f"  - Nutrient Rate: {nutrient_compliance_rate:.1f}%")
            
            # Calculate overall compliance (weighted average)
            overall_compliance_rate = (
                logging_compliance_rate * 0.3 +
                calorie_compliance_rate * 0.4 +
                nutrient_compliance_rate * 0.3
            )
            
            # Determine compliance category
            if overall_compliance_rate >= COMPLIANCE_TARGETS["compliance_thresholds"]["high_compliance"]:
                compliance_category = "high"
            elif overall_compliance_rate >= COMPLIANCE_TARGETS["compliance_thresholds"]["medium_compliance"]:
                compliance_category = "medium"
            else:
                compliance_category = "low"
            
            # Identify specific issues and strengths
            if logging_compliance_rate < COMPLIANCE_TARGETS["logging_consistency"]["good_logging"]:
                compliance_issues.append("Inconsistent meal logging")
            else:
                strengths.append("Consistent meal logging")
            
            if calorie_compliance_rate < 60:
                compliance_issues.append("Frequent calorie target deviations")
            else:
                strengths.append("Good calorie target adherence")
            
            if nutrient_compliance_rate < 60:
                compliance_issues.append("Poor nutrient balance")
            else:
                strengths.append("Good nutrient balance")
            
            # Generate recommendations
            recommendations = []
            if logging_compliance_rate < 70:
                recommendations.append("Improve daily logging consistency")
            if calorie_compliance_rate < 60:
                recommendations.append("Review calorie targets with nutritionist")
            if nutrient_compliance_rate < 60:
                recommendations.append("Focus on balanced nutrient intake")
            if is_diabetic and compliance_category == "low":
                recommendations.append("Urgent diabetes management review needed")
            
            if not recommendations:
                recommendations.append("Continue current excellent dietary habits")
            
            compliance_profile = {
                "user_id": user_id,
                "user_name": user_name,
                "medical_condition": medical_condition,
                "is_diabetic": is_diabetic,
                "analysis_days": total_analysis_days,
                "logged_days": total_logged_days,
                "logging_compliance_rate": round(logging_compliance_rate, 1),
                "calorie_compliance_rate": round(calorie_compliance_rate, 1),
                "nutrient_compliance_rate": round(nutrient_compliance_rate, 1),
                "overall_compliance_rate": round(overall_compliance_rate, 1),
                "compliance_category": compliance_category,
                "compliance_issues": compliance_issues,
                "strengths": strengths,
                "recommendations": recommendations
            }
            
            user_compliance_profiles.append(compliance_profile)
            compliance_summary[f"{compliance_category}_compliance"].append(compliance_profile)
        
        # Generate aggregate statistics
        total_users = len(user_compliance_profiles)
        high_compliance_count = len(compliance_summary["high_compliance"])
        medium_compliance_count = len(compliance_summary["medium_compliance"])
        low_compliance_count = len(compliance_summary["low_compliance"])
        
        # Calculate averages
        avg_logging_compliance = sum(profile["logging_compliance_rate"] for profile in user_compliance_profiles) / total_users if total_users > 0 else 0
        avg_calorie_compliance = sum(profile["calorie_compliance_rate"] for profile in user_compliance_profiles) / total_users if total_users > 0 else 0
        avg_nutrient_compliance = sum(profile["nutrient_compliance_rate"] for profile in user_compliance_profiles) / total_users if total_users > 0 else 0
        avg_overall_compliance = sum(profile["overall_compliance_rate"] for profile in user_compliance_profiles) / total_users if total_users > 0 else 0
        
        # Generate medical insights
        diabetic_patients = [p for p in user_compliance_profiles if p["is_diabetic"]]
        diabetic_low_compliance = [p for p in diabetic_patients if p["compliance_category"] == "low"]
        
        medical_alerts = []
        if len(diabetic_low_compliance) > 0:
            medical_alerts.append(f"🚨 {len(diabetic_low_compliance)} diabetic patients with low compliance require immediate intervention")
        
        if avg_overall_compliance < 60:
            medical_alerts.append("⚠️ Overall patient compliance below acceptable threshold")
        
        if avg_logging_compliance < 70:
            medical_alerts.append("📱 Poor logging compliance affecting treatment monitoring")
        
        priority_actions = []
        if len(diabetic_low_compliance) > 0:
            priority_actions.append("Schedule urgent consultations for non-compliant diabetic patients")
        if low_compliance_count > high_compliance_count:
            priority_actions.append("Implement comprehensive patient education program")
        if avg_logging_compliance < 70:
            priority_actions.append("Deploy app engagement strategies to improve logging")
        
        if not priority_actions:
            priority_actions.append("Continue current patient support strategies")
        
        # Prepare response
        response_data = {
            "total_registered_patients": total_users,
            "total_registered_users": total_users,
            "analysis_period": {
                "days": days,
                "start_date": start_date.date().isoformat(),
                "end_date": end_date.date().isoformat(),
                "total_patients_analyzed": total_users
            },
            "compliance_summary": {
                "high_compliance_count": high_compliance_count,
                "medium_compliance_count": medium_compliance_count,
                "low_compliance_count": low_compliance_count,
                "high_compliance_percentage": round((high_compliance_count / total_users) * 100, 1) if total_users > 0 else 0,
                "medium_compliance_percentage": round((medium_compliance_count / total_users) * 100, 1) if total_users > 0 else 0,
                "low_compliance_percentage": round((low_compliance_count / total_users) * 100, 1) if total_users > 0 else 0
            },
            "compliance_averages": {
                "avg_logging_compliance": round(avg_logging_compliance, 1),
                "avg_calorie_compliance": round(avg_calorie_compliance, 1),
                "avg_nutrient_compliance": round(avg_nutrient_compliance, 1),
                "avg_overall_compliance": round(avg_overall_compliance, 1)
            },
            "compliance_categories": {
                "high_compliance": compliance_summary["high_compliance"],
                "medium_compliance": compliance_summary["medium_compliance"],
                "low_compliance": compliance_summary["low_compliance"]
            },
            "diabetic_analysis": {
                "total_diabetic_patients": len(diabetic_patients),
                "diabetic_high_compliance": len([p for p in diabetic_patients if p["compliance_category"] == "high"]),
                "diabetic_medium_compliance": len([p for p in diabetic_patients if p["compliance_category"] == "medium"]),
                "diabetic_low_compliance": len(diabetic_low_compliance)
            },
            "compliance_targets": COMPLIANCE_TARGETS,
            "medical_insights": {
                "medical_alerts": medical_alerts,
                "priority_actions": priority_actions,
                "positive_indicators": [
                    f"✅ {high_compliance_count} patients demonstrate excellent compliance",
                    f"📊 Average overall compliance: {round(avg_overall_compliance, 1)}%"
                ] if avg_overall_compliance >= 70 else []
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
        print(f"[COMPLIANCE_ANALYSIS] Successfully analyzed compliance for {total_users} patients")
        print(f"[COMPLIANCE_ANALYSIS] High: {high_compliance_count}, Medium: {medium_compliance_count}, Low: {low_compliance_count}")
        
        return response_data
        
    except Exception as e:
        print(f"[COMPLIANCE_ANALYSIS] Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get compliance analysis: {str(e)}")

@router.get("/admin/pias-corner/patients-summary")
async def get_patients_summary(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive summary table data for all patients including:
    - Daily averages for calories, carbs, protein, fats
    - Days within target vs missed days
    - Daily average log count
    """
    print(f"[PATIENTS_SUMMARY] Starting patient summary analysis for {days} days")
    
    # Check if user is admin
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Calculate default date range - use proper date boundaries to avoid off-by-one errors
        today = datetime.utcnow().date()
        default_start_date_only = today - timedelta(days=days-1)  # -1 to include today in the count
        default_end_date_only = today
        
        # Convert to datetime with proper boundaries
        default_start_date = datetime.combine(default_start_date_only, datetime.min.time())
        default_end_date = datetime.combine(default_end_date_only, datetime.max.time())
        
        print(f"[PATIENTS_SUMMARY] Default analysis period: {default_start_date_only} to {default_end_date_only} ({days} days)")
        
        # First, try to get consumption records in the default period
        default_consumption_query = f"""
        SELECT * FROM c 
        WHERE c.type = 'consumption_record' 
        AND c.timestamp >= '{default_start_date.isoformat()}' 
        AND c.timestamp <= '{default_end_date.isoformat()}'
        """
        
        default_consumption_records = list(interactions_container.query_items(
            query=default_consumption_query, 
            enable_cross_partition_query=True
        ))
        
        print(f"[PATIENTS_SUMMARY] Found {len(default_consumption_records)} consumption records in default period")
        
        # If no data in default period, find the actual data range
        if len(default_consumption_records) == 0:
            print("[PATIENTS_SUMMARY] No data in default period, searching for existing data...")
            
            # Get all consumption records to find actual date range
            all_consumption_query = "SELECT * FROM c WHERE c.type = 'consumption_record'"
            all_consumption_records = list(interactions_container.query_items(
                query=all_consumption_query, 
                enable_cross_partition_query=True
            ))
            
            if len(all_consumption_records) > 0:
                # Find the date range of existing data
                dates = []
                for record in all_consumption_records:
                    try:
                        date = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00')).date()
                        dates.append(date)
                    except:
                        continue
                
                if dates:
                    dates.sort()
                    actual_start_date_only = dates[0]
                    actual_end_date_only = dates[-1]
                    
                    # Use the actual data range
                    start_date = datetime.combine(actual_start_date_only, datetime.min.time())
                    end_date = datetime.combine(actual_end_date_only, datetime.max.time())
                    
                    # Calculate the actual analysis days
                    actual_days = (actual_end_date_only - actual_start_date_only).days + 1
                    
                    print(f"[PATIENTS_SUMMARY] Using actual data range: {actual_start_date_only} to {actual_end_date_only} ({actual_days} days)")
                    
                    consumption_records = all_consumption_records
                    days = actual_days  # Update days to reflect actual period
                else:
                    # No valid dates found, use default empty period
                    start_date = default_start_date
                    end_date = default_end_date
                    consumption_records = []
                    print("[PATIENTS_SUMMARY] No valid consumption data found")
            else:
                # No consumption records at all, use default empty period
                start_date = default_start_date
                end_date = default_end_date
                consumption_records = []
                print("[PATIENTS_SUMMARY] No consumption records found in database")
        else:
            # Use default period with found data
            start_date = default_start_date
            end_date = default_end_date
            consumption_records = default_consumption_records
        
        print(f"[PATIENTS_SUMMARY] Final analysis: {len(consumption_records)} consumption records")
        
        # Filter out deleted duplicate account records
        consumption_records = [r for r in consumption_records if r.get('user_id') != 'nagarwal166@gmail.com']
        print(f"[PATIENTS_SUMMARY] After filtering deleted accounts: {len(consumption_records)} records")
        
        # Get all users and admin patients for name mapping (include both 'user' and 'patient' types)
        all_users_query = "SELECT * FROM c WHERE c.type = 'user' OR c.type = 'patient'"
        all_users_raw = list(user_container.query_items(query=all_users_query, enable_cross_partition_query=True))
        
        # Deduplicate users: prioritize type='user' over type='patient' for same registration code
        user_map = {}
        for user in all_users_raw:
            reg_code = user.get('registration_code', '')
            user_type = user.get('type', '')
            
            if reg_code:
                if reg_code not in user_map:
                    user_map[reg_code] = user
                elif user_type == 'user' and user_map[reg_code].get('type') == 'patient':
                    # Prioritize 'user' type over 'patient' type
                    user_map[reg_code] = user
        
        # Convert back to list
        all_users = list(user_map.values())
        
        admin_patients = await get_all_patients()
        
        # Create email to name mapping and medical condition mapping (authoritative admin source)
        # Use registration code to link admin panel data to user emails
        email_to_name = {}
        email_to_conditions = {}
        email_to_registration_code = {}
        
        # First, create registration code to admin data mapping
        registration_to_admin_name = {}
        registration_to_admin_condition = {}
        for patient in admin_patients:
            reg_code = patient.get('registration_code', '')
            if reg_code:
                registration_to_admin_name[reg_code] = patient.get('name', '').strip()
                registration_to_admin_condition[reg_code] = patient.get('condition', '').strip()
        
        # Map user emails to admin panel data via registration codes
        for user in all_users:
            email = user.get('email', '')
            user_reg_code = user.get('registration_code', '')
            
            if email and user_reg_code and user_reg_code in registration_to_admin_name:
                # Use admin panel name as authoritative source
                admin_name = registration_to_admin_name[user_reg_code]
                admin_condition = registration_to_admin_condition[user_reg_code]
                
                if admin_name:
                    email_to_name[email] = admin_name
                    email_to_conditions[email] = admin_condition
                    email_to_registration_code[email] = user_reg_code
                    continue
            
            # Fallback to user profile name if no admin panel match
            if email and email not in email_to_name:
                profile_name = user.get('name', '').strip()
                if profile_name:
                    email_to_name[email] = profile_name
                else:
                    # Professional fallback from email
                    username = email.split('@')[0]
                    email_to_name[email] = f"Patient {username.capitalize()}"
        
        # Group consumption data by user and date
        user_daily_data = {}
        unique_users = set()
        
        for record in consumption_records:
            user_id = record.get('user_id', '')
            if not user_id:
                continue
                
            unique_users.add(user_id)
            record_date = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00')).date()
            
            if user_id not in user_daily_data:
                user_daily_data[user_id] = {}
            
            if record_date not in user_daily_data[user_id]:
                user_daily_data[user_id][record_date] = {
                    'total_calories': 0,
                    'total_protein': 0,
                    'total_carbs': 0,
                    'total_fat': 0,
                    'total_fiber': 0,
                    'total_sodium': 0,
                    'total_sugar': 0,
                    'meal_count': 0,
                    'log_timestamps': []
                }
            
            # Accumulate daily totals
            daily_data = user_daily_data[user_id][record_date]
            daily_data['total_calories'] += record.get('calories', 0)
            daily_data['total_protein'] += record.get('protein', 0)
            daily_data['total_carbs'] += record.get('carbohydrates', 0)
            daily_data['total_fat'] += record.get('fat', 0)
            daily_data['total_fiber'] += record.get('fiber', 0)
            daily_data['total_sodium'] += record.get('sodium', 0)
            daily_data['total_sugar'] += record.get('sugar', 0)
            daily_data['meal_count'] += 1
            daily_data['log_timestamps'].append(record['timestamp'])
        
        print(f"[PATIENTS_SUMMARY] Analyzing data for {len(unique_users)} unique users")
        

        
        # Calculate patient summaries
        patient_summaries = []
        total_analysis_days = days
        
        for user_id in unique_users:
            user_name = email_to_name.get(user_id, f"Patient {user_id[:8]}")
            medical_condition = email_to_conditions.get(user_id, "General")
            registration_code = email_to_registration_code.get(user_id, "")
            is_diabetic = 'diabetes' in medical_condition.lower()
            
            daily_data = user_daily_data.get(user_id, {})
            total_logged_days = len(daily_data)
            
            if total_logged_days == 0:
                # No data - create summary with zeros
                patient_summary = {
                    "user_id": user_id,
                    "user_name": user_name,
                    "registration_code": registration_code,
                    "medical_condition": medical_condition,
                    "is_diabetic": is_diabetic,
                    "analysis_period": {
                        "total_days": total_analysis_days,
                        "logged_days": 0,
                        "missing_days": total_analysis_days
                    },
                    "daily_averages": {
                        "calories": 0.0,
                        "protein": 0.0,
                        "carbohydrates": 0.0,
                        "fat": 0.0,
                        "fiber": 0.0,
                        "sodium": 0.0,
                        "sugar": 0.0
                    },
                    "target_compliance": {
                        "days_within_calorie_target": 0,
                        "days_missed_calorie_target": 0,
                        "calorie_target_compliance_rate": 0.0,
                        "days_within_nutrient_targets": 0,
                        "days_missed_nutrient_targets": 0,
                        "nutrient_target_compliance_rate": 0.0,
                        "overall_compliance_rate": 0.0
                    },
                    "logging_metrics": {
                        "daily_average_log_count": 0.0,
                        "most_active_day": "N/A",
                        "least_active_day": "N/A",
                        "logging_consistency": "No Data"
                    },
                    "health_indicators": {
                        "status": "No Data",
                        "risk_level": "Unknown",
                        "recommendations": ["Encourage initial meal logging", "Schedule onboarding consultation"]
                    }
                }
                patient_summaries.append(patient_summary)
                continue
            
            # Calculate daily averages
            total_calories = sum(data['total_calories'] for data in daily_data.values())
            total_protein = sum(data['total_protein'] for data in daily_data.values())
            total_carbs = sum(data['total_carbs'] for data in daily_data.values())
            total_fat = sum(data['total_fat'] for data in daily_data.values())
            total_fiber = sum(data['total_fiber'] for data in daily_data.values())
            total_sodium = sum(data['total_sodium'] for data in daily_data.values())
            total_sugar = sum(data['total_sugar'] for data in daily_data.values())
            total_log_count = sum(data['meal_count'] for data in daily_data.values())
            
            daily_averages = {
                "calories": round(total_calories / total_logged_days, 1),
                "protein": round(total_protein / total_logged_days, 1),
                "carbohydrates": round(total_carbs / total_logged_days, 1),
                "fat": round(total_fat / total_logged_days, 1),
                "fiber": round(total_fiber / total_logged_days, 1),
                "sodium": round(total_sodium / total_logged_days, 1),
                "sugar": round(total_sugar / total_logged_days, 1)
            }
            
            # Calculate target compliance
            calorie_target_min, calorie_target_max = COMPLIANCE_TARGETS["calorie_targets"]["diabetic_range"] if is_diabetic else (COMPLIANCE_TARGETS["calorie_targets"]["min_healthy_calories"], COMPLIANCE_TARGETS["calorie_targets"]["max_healthy_calories"])
            
            tolerance = COMPLIANCE_TARGETS["calorie_targets"]["tolerance_percentage"] / 100
            calorie_min_with_tolerance = calorie_target_min * (1 - tolerance)
            calorie_max_with_tolerance = calorie_target_max * (1 + tolerance)
            
            days_within_calorie_target = 0
            days_within_nutrient_targets = 0
            
            for date, data in daily_data.items():
                calories = data['total_calories']
                protein = data['total_protein']
                carbs = data['total_carbs']
                fiber = data['total_fiber']
                sodium = data['total_sodium']
                sugar = data['total_sugar']
                
                # Check calorie compliance
                if calorie_min_with_tolerance <= calories <= calorie_max_with_tolerance:
                    days_within_calorie_target += 1
                
                # Check nutrient compliance
                nutrient_compliant = True
                if calories > 0:  # Avoid division by zero
                    protein_percentage = (protein * 4 / calories) * 100
                    carb_percentage = (carbs * 4 / calories) * 100
                    sugar_percentage = (sugar * 4 / calories) * 100
                    
                    # Check nutrient targets
                    if fiber < COMPLIANCE_TARGETS["nutrient_targets"]["fiber_min"]:
                        nutrient_compliant = False
                    if protein_percentage < COMPLIANCE_TARGETS["nutrient_targets"]["protein_min_percentage"]:
                        nutrient_compliant = False
                    if sodium > COMPLIANCE_TARGETS["nutrient_targets"]["sodium_max"]:
                        nutrient_compliant = False
                    if sugar_percentage > COMPLIANCE_TARGETS["nutrient_targets"]["sugar_max_percentage"]:
                        nutrient_compliant = False
                    if is_diabetic and carb_percentage > COMPLIANCE_TARGETS["nutrient_targets"]["carb_max_percentage"]:
                        nutrient_compliant = False
                
                if nutrient_compliant:
                    days_within_nutrient_targets += 1
            
            days_missed_calorie_target = total_logged_days - days_within_calorie_target
            days_missed_nutrient_targets = total_logged_days - days_within_nutrient_targets
            
            calorie_compliance_rate = (days_within_calorie_target / total_logged_days) * 100 if total_logged_days > 0 else 0
            nutrient_compliance_rate = (days_within_nutrient_targets / total_logged_days) * 100 if total_logged_days > 0 else 0
            overall_compliance_rate = (calorie_compliance_rate + nutrient_compliance_rate) / 2
            
            # Calculate logging metrics
            daily_average_log_count = round(total_log_count / total_logged_days, 1)
            
            # Find most and least active days
            day_log_counts = {date.strftime('%A'): data['meal_count'] for date, data in daily_data.items()}
            most_active_day = max(day_log_counts.keys(), key=lambda x: day_log_counts[x]) if day_log_counts else "N/A"
            least_active_day = min(day_log_counts.keys(), key=lambda x: day_log_counts[x]) if day_log_counts else "N/A"
            
            # Determine logging consistency
            logging_rate = (total_logged_days / total_analysis_days) * 100
            if logging_rate >= 90:
                logging_consistency = "Excellent"
            elif logging_rate >= 70:
                logging_consistency = "Good"
            elif logging_rate >= 50:
                logging_consistency = "Fair"
            else:
                logging_consistency = "Poor"
            
            # Determine health status and risk level
            if overall_compliance_rate >= 80:
                status = "Excellent"
                risk_level = "Low"
            elif overall_compliance_rate >= 60:
                status = "Good"
                risk_level = "Medium"
            elif overall_compliance_rate >= 40:
                status = "Fair"
                risk_level = "High"
            else:
                status = "Poor"
                risk_level = "Critical"
            
            # Generate recommendations
            recommendations = []
            if logging_rate < 70:
                recommendations.append("Improve daily logging consistency")
            if calorie_compliance_rate < 60:
                recommendations.append("Review calorie targets with nutritionist")
            if nutrient_compliance_rate < 60:
                recommendations.append("Focus on balanced nutrient intake")
            if is_diabetic and overall_compliance_rate < 60:
                recommendations.append("Schedule urgent diabetes management review")
            if daily_averages["sodium"] > 2300:
                recommendations.append("Reduce sodium intake for cardiovascular health")
            if daily_averages["fiber"] < 25:
                recommendations.append("Increase fiber intake for digestive health")
            
            if not recommendations:
                recommendations.append("Continue current excellent dietary habits")
            
            patient_summary = {
                "user_id": user_id,
                "user_name": user_name,
                "registration_code": registration_code,
                "medical_condition": medical_condition,
                "is_diabetic": is_diabetic,
                "analysis_period": {
                    "total_days": total_analysis_days,
                    "logged_days": total_logged_days,
                    "missing_days": total_analysis_days - total_logged_days
                },
                "daily_averages": daily_averages,
                "target_compliance": {
                    "days_within_calorie_target": days_within_calorie_target,
                    "days_missed_calorie_target": days_missed_calorie_target,
                    "calorie_target_compliance_rate": round(calorie_compliance_rate, 1),
                    "days_within_nutrient_targets": days_within_nutrient_targets,
                    "days_missed_nutrient_targets": days_missed_nutrient_targets,
                    "nutrient_target_compliance_rate": round(nutrient_compliance_rate, 1),
                    "overall_compliance_rate": round(overall_compliance_rate, 1)
                },
                "logging_metrics": {
                    "daily_average_log_count": daily_average_log_count,
                    "most_active_day": most_active_day,
                    "least_active_day": least_active_day,
                    "logging_consistency": logging_consistency
                },
                "health_indicators": {
                    "status": status,
                    "risk_level": risk_level,
                    "recommendations": recommendations
                }
            }
            
            patient_summaries.append(patient_summary)
        
        # Add admin panel patients who have no consumption records at all
        processed_user_ids = set(unique_users)  # Users who had consumption data
        all_admin_patients = await get_all_patients()  # Get admin panel patients
        
        for admin_patient in all_admin_patients:
            admin_reg_code = admin_patient.get('registration_code', '')
            admin_name = admin_patient.get('name', '').strip()
            
            # Find the user profile for this admin patient via registration code
            admin_user_email = None
            admin_user_profile = None
            for user in all_users:
                if user.get('registration_code') == admin_reg_code and admin_reg_code:
                    admin_user_email = user.get('email', '') or None  # Convert empty string to None
                    admin_user_profile = user
                    break
            
            # Skip if this admin patient doesn't have a user profile at all
            if not admin_user_profile:
                continue
                
            # Determine unique identifier - use email if available, otherwise use registration code
            user_identifier = admin_user_email if admin_user_email else f"REG_{admin_reg_code}"
            
            # If this admin patient wasn't processed (no consumption data)
            if user_identifier not in processed_user_ids:
                admin_name = admin_patient.get('name', '').strip()
                admin_condition = admin_patient.get('condition', '').strip()
                
                if not admin_name:
                    if admin_user_email:
                        admin_name = f"Patient {admin_user_email.split('@')[0].capitalize()}"
                    else:
                        admin_name = f"Patient {admin_reg_code}"
                if not admin_condition:
                    admin_condition = "General"
                
                is_diabetic = 'diabetes' in admin_condition.lower()
                
                # Assign risk level based on medical condition (use real medical assessment)
                condition_lower = admin_condition.lower()
                if 'diabetes' in condition_lower:
                    risk_level = "High"  # Diabetes requires careful monitoring
                    status = "Needs Monitoring"
                    medical_recommendations = [
                        "Schedule immediate diabetes consultation",
                        "Begin structured meal logging for blood sugar management",
                        "Monitor carbohydrate intake closely"
                    ]
                elif 'hypertension' in condition_lower:
                    risk_level = "Medium"  # Hypertension needs attention
                    status = "Moderate Risk"
                    medical_recommendations = [
                        "Monitor sodium intake",
                        "Begin meal logging for blood pressure management",
                        "Schedule nutritionist consultation"
                    ]
                elif any(word in condition_lower for word in ['weight loss', 'weight gain', 'gain muscle']):
                    risk_level = "Medium"  # Weight management goals need guidance
                    status = "Needs Guidance"
                    medical_recommendations = [
                        "Start meal logging to track progress toward goals",
                        "Schedule nutritionist consultation for meal planning",
                        "Monitor caloric intake for weight management"
                    ]
                elif 'weight maintenance' in condition_lower:
                    risk_level = "Low"  # Maintenance is lower risk
                    status = "Stable"
                    medical_recommendations = [
                        "Begin meal logging to maintain current health status",
                        "Schedule routine check-in with healthcare provider"
                    ]
                else:
                    risk_level = "Low"  # General cases
                    status = "Stable"
                    medical_recommendations = [
                        "Begin meal logging for general health monitoring",
                        "Schedule routine nutritionist consultation"
                    ]
                
                # Create patient summary for admin patient with no consumption data
                no_data_summary = {
                    "user_id": user_identifier,
                    "user_name": admin_name,
                    "registration_code": admin_reg_code,
                    "medical_condition": admin_condition,
                    "is_diabetic": is_diabetic,
                    "analysis_period": {
                        "total_days": total_analysis_days,
                        "logged_days": 0,
                        "missing_days": total_analysis_days
                    },
                    "daily_averages": {
                        "calories": 0.0,
                        "protein": 0.0,
                        "carbohydrates": 0.0,
                        "fat": 0.0,
                        "fiber": 0.0,
                        "sodium": 0.0,
                        "sugar": 0.0
                    },
                    "target_compliance": {
                        "days_within_calorie_target": 0,
                        "days_missed_calorie_target": 0,
                        "calorie_target_compliance_rate": 0.0,
                        "days_within_nutrient_targets": 0,
                        "days_missed_nutrient_targets": 0,
                        "nutrient_target_compliance_rate": 0.0,
                        "overall_compliance_rate": 0.0
                    },
                    "logging_metrics": {
                        "daily_average_log_count": 0.0,
                        "most_active_day": "N/A",
                        "least_active_day": "N/A",
                        "logging_consistency": "No Data"
                    },
                    "health_indicators": {
                        "status": status,
                        "risk_level": risk_level,
                        "recommendations": medical_recommendations
                    }
                }
                patient_summaries.append(no_data_summary)
        
        # Sort patients by risk level (Critical, High, Medium, Low) and then by compliance rate
        risk_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Unknown": 4}
        patient_summaries.sort(key=lambda x: (
            risk_order.get(x["health_indicators"]["risk_level"], 4),
            -x["target_compliance"]["overall_compliance_rate"]
        ))
        
        # Calculate summary statistics - use admin panel for total registered patients (like Overview does)
        total_registered_patients = len(all_admin_patients)
        
        patients_with_data = len([p for p in patient_summaries if p["analysis_period"]["logged_days"] > 0])
        patients_without_data = total_registered_patients - patients_with_data
        
        # Use total_registered_patients for the main count (like Overview section)
        total_patients = total_registered_patients
        
        avg_calories = sum(p["daily_averages"]["calories"] for p in patient_summaries if p["analysis_period"]["logged_days"] > 0) / patients_with_data if patients_with_data > 0 else 0
        avg_compliance = sum(p["target_compliance"]["overall_compliance_rate"] for p in patient_summaries) / total_patients if total_patients > 0 else 0
        avg_logging_rate = sum((p["analysis_period"]["logged_days"] / p["analysis_period"]["total_days"]) * 100 for p in patient_summaries) / total_patients if total_patients > 0 else 0
        
        # Risk level distribution
        risk_distribution = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0, "Unknown": 0}
        for patient in patient_summaries:
            risk_level = patient["health_indicators"]["risk_level"]
            risk_distribution[risk_level] += 1
        
        # Generate insights
        critical_patients = [p for p in patient_summaries if p["health_indicators"]["risk_level"] == "Critical"]
        high_risk_patients = [p for p in patient_summaries if p["health_indicators"]["risk_level"] == "High"]
        diabetic_patients = [p for p in patient_summaries if p["is_diabetic"]]
        
        medical_insights = []
        if len(critical_patients) > 0:
            medical_insights.append(f"🚨 {len(critical_patients)} patients in critical condition require immediate intervention")
        if len(high_risk_patients) > 0:
            medical_insights.append(f"⚠️ {len(high_risk_patients)} high-risk patients need urgent attention")
        if len(diabetic_patients) > 0:
            diabetic_critical = len([p for p in diabetic_patients if p["health_indicators"]["risk_level"] in ["Critical", "High"]])
            if diabetic_critical > 0:
                medical_insights.append(f"🩺 {diabetic_critical} diabetic patients require specialized care")
        if patients_without_data > 0:
            medical_insights.append(f"📱 {patients_without_data} patients have no logging data - engagement intervention needed")
        
        if not medical_insights:
            medical_insights.append("✅ Patient population showing healthy patterns overall")
        
        # Prepare response
        response_data = {
            "total_patients": total_patients,
            "analysis_period": {
                "days": days,
                "start_date": start_date.date().isoformat(),
                "end_date": end_date.date().isoformat(),
                "total_records_analyzed": len(consumption_records)
            },
            "summary_statistics": {
                "patients_with_data": patients_with_data,
                "patients_without_data": patients_without_data,
                "avg_daily_calories": round(avg_calories, 1),
                "avg_compliance_rate": round(avg_compliance, 1),
                "avg_logging_rate": round(avg_logging_rate, 1),
                "risk_distribution": risk_distribution
            },
            "patient_summaries": patient_summaries,
            "medical_insights": medical_insights,
            "compliance_targets": COMPLIANCE_TARGETS,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        print(f"[PATIENTS_SUMMARY] Successfully generated summary for {total_patients} patients")
        print(f"[PATIENTS_SUMMARY] Risk distribution: Critical: {risk_distribution['Critical']}, High: {risk_distribution['High']}, Medium: {risk_distribution['Medium']}, Low: {risk_distribution['Low']}")
        
        return response_data
        
    except Exception as e:
        print(f"[PATIENTS_SUMMARY] Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get patients summary: {str(e)}")

@router.get("/admin/pias-corner/patient/{patient_id}/details")
async def get_patient_details(
    patient_id: str,
    days: int = 90,
    include_download_data: bool = True,
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive detailed data for a specific patient including:
    - Full history with daily, weekly, monthly averages
    - Detailed nutritional breakdown for bar graphs
    - Target compliance analysis
    - Download-ready full history data
    """
    print(f"[PATIENT_DETAILS] Starting detailed analysis for patient {patient_id} over {days} days")
    
    # Check if user is admin
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Calculate date range - use proper date boundaries to avoid off-by-one errors
        today = datetime.utcnow().date()
        start_date_only = today - timedelta(days=days-1)  # -1 to include today in the count
        end_date_only = today
        
        # Convert to datetime with proper boundaries
        start_date = datetime.combine(start_date_only, datetime.min.time())
        end_date = datetime.combine(end_date_only, datetime.max.time())
        
        print(f"[PATIENT_DETAILS] Analysis period: {start_date_only} to {end_date_only} ({days} days)")
        print(f"[PATIENT_DETAILS] UTC Date calculation - Today: {today}, Start: {start_date_only}, End: {end_date_only}")
        
        # Get patient's consumption records
        consumption_query = f"""
        SELECT * FROM c 
        WHERE c.type = 'consumption_record' 
        AND c.user_id = '{patient_id}'
        AND c.timestamp >= '{start_date.isoformat()}' 
        AND c.timestamp <= '{end_date.isoformat()}'
        ORDER BY c.timestamp ASC
        """
        
        consumption_records = list(interactions_container.query_items(
            query=consumption_query, 
            enable_cross_partition_query=True
        ))
        
        print(f"[PATIENT_DETAILS] Found {len(consumption_records)} consumption records")
        
        # Debug: Show a sample record structure
        if consumption_records:
            sample_record = consumption_records[0]
            print(f"[PATIENT_DETAILS] Sample record structure: {list(sample_record.keys())}")
            if 'nutritional_info' in sample_record:
                print(f"[PATIENT_DETAILS] Nutritional info keys: {list(sample_record['nutritional_info'].keys())}")
                print(f"[PATIENT_DETAILS] Sample calories: {sample_record['nutritional_info'].get('calories', 'MISSING')}")
            else:
                print(f"[PATIENT_DETAILS] WARNING: No 'nutritional_info' key found in record!")
                print(f"[PATIENT_DETAILS] Direct calories access: {sample_record.get('calories', 'MISSING')}")
        
        if not consumption_records:
            raise HTTPException(status_code=404, detail="No consumption data found for this patient")
        
        # Get patient info for name mapping using robust logic (same as compliance endpoint)
        all_users_query = f"SELECT * FROM c WHERE c.type = 'user' AND c.email = '{patient_id}'"
        user_info = list(user_container.query_items(query=all_users_query, enable_cross_partition_query=True))
        
        admin_patients = await get_all_patients()
        
        # Create robust email to name mapping (authoritative admin source)
        email_to_name = {}
        email_to_conditions = {}
        
        # First, create registration code to name mapping from admin patients
        registration_to_name = {}
        for patient in admin_patients:
            reg_code = patient.get("registration_code")
            patient_name = patient.get("name", "").strip()
            email = patient.get("email", "").strip()
            condition = patient.get("condition", "")
            
            if reg_code and patient_name:
                registration_to_name[reg_code] = patient_name
            
            # Also map by email if available (direct admin panel mapping)
            if email and patient_name:
                email_to_name[email] = patient_name
                email_to_conditions[email] = condition
        
        # Map the specific patient using registration codes (authoritative hierarchy)
        patient_name = f"Patient {patient_id[:8]}"  # Default fallback
        medical_condition = "General"
        registration_code = ""
        is_diabetic = False
        
        # Check if we have user info
        if user_info:
            user = user_info[0]
            registration_code = user.get("registration_code", "")
            
            # First priority: Use admin panel patient name via registration code (authoritative)
            if registration_code and registration_code in registration_to_name:
                patient_name = registration_to_name[registration_code]
                # Get condition from admin patients
                for patient in admin_patients:
                    if patient.get("registration_code") == registration_code:
                        medical_condition = patient.get("condition", "General")
                        is_diabetic = 'diabetes' in medical_condition.lower()
                        break
            # Second priority: Direct email lookup in admin panel
            elif patient_id in email_to_name:
                patient_name = email_to_name[patient_id]
                medical_condition = email_to_conditions.get(patient_id, "General")
                is_diabetic = 'diabetes' in medical_condition.lower()
            else:
                # Third priority: Use profile name if available
                profile = user.get("profile", {})
                profile_name = profile.get("name", "").strip()
                if profile_name:
                    patient_name = profile_name
                else:
                    # Last resort: Create professional fallback from email
                    username = patient_id.split("@")[0]
                    if len(username) > 0:
                        readable_name = username.replace(".", " ").replace("_", " ")
                        readable_name = " ".join(word.capitalize() for word in readable_name.split())
                        patient_name = f"Patient {readable_name}"
                    else:
                        patient_name = "Unknown Patient"
        else:
            # No user info found, try direct admin lookup
            for patient in admin_patients:
                if patient.get('email') == patient_id:
                    patient_name = patient.get('name', patient_name)
                    medical_condition = patient.get('condition', medical_condition)
                    registration_code = patient.get('registration_code', '')
                    is_diabetic = 'diabetes' in medical_condition.lower()
                    break
        
        print(f"[PATIENT_DETAILS] Name mapping result: '{patient_name}' (was Patient {patient_id[:8]})")
        print(f"[PATIENT_DETAILS] Medical condition: '{medical_condition}', Registration: '{registration_code}', Diabetic: {is_diabetic}")
        
        # Group consumption data by date
        daily_data = {}
        for record in consumption_records:
            record_date = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00')).date()
            
            if record_date not in daily_data:
                daily_data[record_date] = {
                    'date': record_date.isoformat(),
                    'total_calories': 0,
                    'total_protein': 0,
                    'total_carbs': 0,
                    'total_fat': 0,
                    'total_fiber': 0,
                    'total_sodium': 0,
                    'total_sugar': 0,
                    'meal_count': 0,
                    'meals': []
                }
            
            # Accumulate daily totals - CRITICAL FIX: Access nutritional data correctly
            daily_entry = daily_data[record_date]
            nutritional_info = record.get('nutritional_info', {})
            daily_entry['total_calories'] += nutritional_info.get('calories', 0)
            daily_entry['total_protein'] += nutritional_info.get('protein', 0)
            daily_entry['total_carbs'] += nutritional_info.get('carbohydrates', 0)
            daily_entry['total_fat'] += nutritional_info.get('fat', 0)
            daily_entry['total_fiber'] += nutritional_info.get('fiber', 0)
            daily_entry['total_sodium'] += nutritional_info.get('sodium', 0)
            daily_entry['total_sugar'] += nutritional_info.get('sugar', 0)
            daily_entry['meal_count'] += 1
            
            # Store individual meal details for download - CRITICAL FIX: Access nutritional data correctly
            if include_download_data:
                daily_entry['meals'].append({
                    'timestamp': record['timestamp'],
                    'food_name': record.get('food_name', 'Unknown'),
                    'quantity': record.get('quantity', 0),
                    'calories': nutritional_info.get('calories', 0),
                    'protein': nutritional_info.get('protein', 0),
                    'carbohydrates': nutritional_info.get('carbohydrates', 0),
                    'fat': nutritional_info.get('fat', 0),
                    'fiber': nutritional_info.get('fiber', 0),
                    'sodium': nutritional_info.get('sodium', 0),
                    'sugar': nutritional_info.get('sugar', 0)
                })
        
        # Sort daily data by date
        sorted_daily_data = [daily_data[date] for date in sorted(daily_data.keys())]
        
        print(f"[PATIENT_DETAILS] Processed {len(sorted_daily_data)} days of data")
        
        # Debug: Show sample processed daily data
        if sorted_daily_data:
            sample_day = sorted_daily_data[0]
            print(f"[PATIENT_DETAILS] Sample day data: Date={sample_day['date']}, Calories={sample_day['total_calories']}, Protein={sample_day['total_protein']}, Meals={sample_day['meal_count']}")
            
            # Calculate some totals for verification
            total_calories_all_days = sum(d['total_calories'] for d in sorted_daily_data)
            avg_calories = total_calories_all_days / len(sorted_daily_data) if sorted_daily_data else 0
            print(f"[PATIENT_DETAILS] Total calories across all days: {total_calories_all_days}, Average: {avg_calories:.1f}")
        
        # Calculate weekly averages
        weekly_data = []
        current_week = []
        week_start = None
        
        for daily in sorted_daily_data:
            date_obj = datetime.fromisoformat(daily['date']).date()
            
            # Start new week on Monday
            if not current_week or date_obj.weekday() == 0:
                if current_week:
                    # Process previous week
                    week_avg = calculate_week_average(current_week, week_start)
                    weekly_data.append(week_avg)
                
                current_week = [daily]
                week_start = date_obj
            else:
                current_week.append(daily)
        
        # Process last week
        if current_week:
            week_avg = calculate_week_average(current_week, week_start)
            weekly_data.append(week_avg)
        
        # Calculate monthly averages
        monthly_data = []
        current_month = []
        month_start = None
        
        for daily in sorted_daily_data:
            date_obj = datetime.fromisoformat(daily['date']).date()
            
            # Start new month
            if not current_month or date_obj.day == 1:
                if current_month:
                    # Process previous month
                    month_avg = calculate_month_average(current_month, month_start)
                    monthly_data.append(month_avg)
                
                current_month = [daily]
                month_start = date_obj.replace(day=1)
            else:
                current_month.append(daily)
        
        # Process last month
        if current_month:
            month_avg = calculate_month_average(current_month, month_start)
            monthly_data.append(month_avg)
        
        # Calculate target compliance
        # Define calorie targets based on patient's diabetic status - MUST BE BEFORE compliance_analysis
        if is_diabetic:
            calorie_target_min, calorie_target_max = COMPLIANCE_TARGETS["calorie_targets"]["diabetic_range"]
        else:
            calorie_target_min = COMPLIANCE_TARGETS["calorie_targets"]["min_healthy_calories"]
            calorie_target_max = COMPLIANCE_TARGETS["calorie_targets"]["max_healthy_calories"]
        
        tolerance = COMPLIANCE_TARGETS["calorie_targets"]["tolerance_percentage"] / 100
        calorie_min_with_tolerance = calorie_target_min * (1 - tolerance)
        calorie_max_with_tolerance = calorie_target_max * (1 + tolerance)
        
        # Initialize compliance analysis
        compliance_analysis = {
            'total_days': len(sorted_daily_data),
            'days_within_calorie_target': 0,
            'days_above_target': 0,
            'days_below_target': 0,
            'days_within_nutrient_targets': 0,
            'days_with_nutrient_issues': 0,
            'compliance_timeline': [],
            'target_ranges': {
                'calorie_min': calorie_min_with_tolerance,
                'calorie_max': calorie_max_with_tolerance,
                'fiber_min': COMPLIANCE_TARGETS["nutrient_targets"]["fiber_min"],
                'protein_min_percentage': COMPLIANCE_TARGETS["nutrient_targets"]["protein_min_percentage"],
                'sodium_max': COMPLIANCE_TARGETS["nutrient_targets"]["sodium_max"],
                'sugar_max_percentage': COMPLIANCE_TARGETS["nutrient_targets"]["sugar_max_percentage"]
            }
        }
        
        for daily in sorted_daily_data:
            calories = daily['total_calories']
            protein = daily['total_protein']
            carbs = daily['total_carbs']
            fiber = daily['total_fiber']
            sodium = daily['total_sodium']
            sugar = daily['total_sugar']
            
            # Calorie compliance
            calorie_status = "within_target"
            if calories < calorie_min_with_tolerance:
                calorie_status = "below_target"
                compliance_analysis['days_below_target'] += 1
            elif calories > calorie_max_with_tolerance:
                calorie_status = "above_target"
                compliance_analysis['days_above_target'] += 1
            else:
                compliance_analysis['days_within_calorie_target'] += 1
            
            # Nutrient compliance
            nutrient_issues = []
            if calories > 0:
                protein_percentage = (protein * 4 / calories) * 100
                sugar_percentage = (sugar * 4 / calories) * 100
                
                if fiber < COMPLIANCE_TARGETS["nutrient_targets"]["fiber_min"]:
                    nutrient_issues.append("low_fiber")
                if protein_percentage < COMPLIANCE_TARGETS["nutrient_targets"]["protein_min_percentage"]:
                    nutrient_issues.append("low_protein")
                if sodium > COMPLIANCE_TARGETS["nutrient_targets"]["sodium_max"]:
                    nutrient_issues.append("high_sodium")
                if sugar_percentage > COMPLIANCE_TARGETS["nutrient_targets"]["sugar_max_percentage"]:
                    nutrient_issues.append("high_sugar")
            
            if not nutrient_issues:
                compliance_analysis['days_within_nutrient_targets'] += 1
            else:
                compliance_analysis['days_with_nutrient_issues'] += 1
            
            compliance_analysis['compliance_timeline'].append({
                'date': daily['date'],
                'calorie_status': calorie_status,
                'nutrient_issues': nutrient_issues,
                'calories': calories,
                'within_targets': len(nutrient_issues) == 0 and calorie_status == "within_target"
            })
        
        # Calculate overall averages for bar graph data
        total_days = len(sorted_daily_data)
        nutritional_averages = {
            'daily_avg_calories': sum(d['total_calories'] for d in sorted_daily_data) / total_days,
            'daily_avg_protein': sum(d['total_protein'] for d in sorted_daily_data) / total_days,
            'daily_avg_carbs': sum(d['total_carbs'] for d in sorted_daily_data) / total_days,
            'daily_avg_fat': sum(d['total_fat'] for d in sorted_daily_data) / total_days,
            'daily_avg_fiber': sum(d['total_fiber'] for d in sorted_daily_data) / total_days,
            'daily_avg_sodium': sum(d['total_sodium'] for d in sorted_daily_data) / total_days,
            'daily_avg_sugar': sum(d['total_sugar'] for d in sorted_daily_data) / total_days
        }
        
        # Bar graph data for calories, carbs, proteins, fats (calorie targets defined above)
        bar_graph_data = {
            'categories': ['Calories', 'Protein (g)', 'Carbohydrates (g)', 'Fat (g)'],
            'current_values': [
                nutritional_averages['daily_avg_calories'],
                nutritional_averages['daily_avg_protein'],
                nutritional_averages['daily_avg_carbs'],
                nutritional_averages['daily_avg_fat']
            ],
            'target_values': [
                (calorie_target_min + calorie_target_max) / 2,  # Mid-point of target range
                75,  # Typical protein target for adults
                225,  # Typical carb target (45% of 2000 calories)
                67   # Typical fat target (30% of 2000 calories)
            ],
            'target_ranges': [
                [calorie_min_with_tolerance, calorie_max_with_tolerance],
                [50, 100],  # Protein range
                [130, 300], # Carb range
                [44, 78]    # Fat range
            ]
        }
        
        # Calculate overall compliance rate
        total_days = len(sorted_daily_data)
        days_fully_compliant = sum(1 for day in compliance_analysis['compliance_timeline'] if day['within_targets'])
        overall_compliance_rate = (days_fully_compliant / total_days) * 100 if total_days > 0 else 0
        
        # Calculate calorie target compliance rate
        calorie_compliance_rate = (compliance_analysis['days_within_calorie_target'] / total_days) * 100 if total_days > 0 else 0
        
        # Calculate personal progress metrics for severely under-eating patients
        if total_days >= 7:  # Need at least a week of data
            daily_calories = [day['total_calories'] for day in sorted_daily_data]
            avg_calories = sum(daily_calories) / len(daily_calories)
            
            # If severely under-eating (less than 70% of minimum target), add personal progress metrics
            min_safe_calories = COMPLIANCE_TARGETS["calorie_targets"]["min_healthy_calories"]
            if avg_calories < (min_safe_calories * 0.7):  # Less than 70% of 1200 = 840 calories
                # Calculate trend over time (comparing first half vs second half)
                mid_point = len(daily_calories) // 2
                early_avg = sum(daily_calories[:mid_point]) / mid_point if mid_point > 0 else 0
                recent_avg = sum(daily_calories[mid_point:]) / (len(daily_calories) - mid_point) if mid_point < len(daily_calories) else 0
                
                improvement_trend = recent_avg - early_avg
                improvement_percentage = (improvement_trend / early_avg * 100) if early_avg > 0 else 0
                
                # Personal progress score based on improvement and consistency
                consistency_bonus = min(len(set(daily_calories)), 7) * 5  # Max 35 points for variety/consistency
                improvement_bonus = max(0, improvement_percentage * 2)  # Positive trend bonus
                base_effort_score = min((avg_calories / min_safe_calories) * 50, 50)  # Max 50 points for effort
                
                personal_progress_score = min(100, base_effort_score + consistency_bonus + improvement_bonus)
                
                # Add personal metrics
                compliance_analysis['personal_progress'] = {
                    'score': round(personal_progress_score, 1),
                    'avg_daily_calories': round(avg_calories, 0),
                    'improvement_trend': round(improvement_trend, 0),
                    'recent_average': round(recent_avg, 0),
                    'early_average': round(early_avg, 0),
                    'is_improving': improvement_trend > 0,
                    'encouragement_message': generate_encouragement_message(personal_progress_score, improvement_trend, avg_calories)
                }
        
        # Add compliance rates to compliance analysis
        compliance_analysis['overall_compliance_rate'] = round(overall_compliance_rate, 1)
        compliance_analysis['calorie_target_compliance_rate'] = round(calorie_compliance_rate, 1)
        
        # Generate insights and recommendations
        insights = []
        recommendations = []
        
        if calorie_compliance_rate < 60:
            insights.append(f"Low calorie target compliance: {calorie_compliance_rate:.1f}%")
            recommendations.append("Review calorie targets with nutritionist")
        
        if compliance_analysis['days_below_target'] > total_days * 0.3:
            insights.append("Frequent under-eating detected")
            recommendations.append("Increase meal frequency and portion sizes")
        
        if compliance_analysis['days_above_target'] > total_days * 0.3:
            insights.append("Frequent over-eating detected")
            recommendations.append("Focus on portion control and mindful eating")
        
        if nutritional_averages['daily_avg_fiber'] < 25:
            insights.append(f"Low fiber intake: {nutritional_averages['daily_avg_fiber']:.1f}g/day")
            recommendations.append("Increase vegetables, fruits, and whole grains")
        
        if nutritional_averages['daily_avg_sodium'] > 2300:
            insights.append(f"High sodium intake: {nutritional_averages['daily_avg_sodium']:.0f}mg/day")
            recommendations.append("Reduce processed foods and added salt")
        
        if is_diabetic:
            carb_percentage = (nutritional_averages['daily_avg_carbs'] * 4 / nutritional_averages['daily_avg_calories']) * 100 if nutritional_averages['daily_avg_calories'] > 0 else 0
            if carb_percentage > 45:
                insights.append(f"High carbohydrate intake for diabetic: {carb_percentage:.1f}%")
                recommendations.append("Consider carbohydrate counting and portion control")
        
        # Prepare comprehensive response
        response_data = {
            "patient_info": {
                "user_id": patient_id,
                "user_name": patient_name,
                "registration_code": registration_code,
                "medical_condition": medical_condition,
                "is_diabetic": is_diabetic
            },
            "analysis_period": {
                "days": days,
                "start_date": start_date.date().isoformat(),
                "end_date": end_date.date().isoformat(),
                "total_records": len(consumption_records),
                "days_with_data": len(sorted_daily_data)
            },
            "historical_data": {
                "daily_data": sorted_daily_data,
                "weekly_data": weekly_data,
                "monthly_data": monthly_data
            },
            "nutritional_averages": nutritional_averages,
            "bar_graph_data": bar_graph_data,
            "compliance_analysis": compliance_analysis,
            "insights": insights,
            "recommendations": recommendations,
            "download_ready": include_download_data,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        print(f"[PATIENT_DETAILS] Successfully generated detailed analysis for {patient_name}")
        print(f"[PATIENT_DETAILS] Analysis: {len(sorted_daily_data)} days, {len(weekly_data)} weeks, {len(monthly_data)} months")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[PATIENT_DETAILS] Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get patient details: {str(e)}")

def generate_encouragement_message(progress_score, improvement_trend, avg_calories):
    """Generate personalized encouragement messages for under-eating patients"""
    if progress_score >= 70:
        if improvement_trend > 50:
            return "Outstanding progress! You're consistently increasing your intake and building healthy habits. 🌟"
        else:
            return "Great job maintaining regular eating patterns! Keep up the excellent work. 💪"
    elif progress_score >= 50:
        if improvement_trend > 0:
            return "Good progress! You're moving in the right direction. Small improvements add up to big changes. 📈"
        else:
            return "You're making an effort! Consistency is key - every meal matters for your health. 🎯"
    elif progress_score >= 30:
        if improvement_trend > 0:
            return "Positive trend detected! Even small increases in intake are meaningful progress. Keep going! 🌱"
        else:
            return "We see your efforts to log meals. Consider adding one extra snack or larger portions each day. 🥜"
    else:
        if avg_calories < 400:
            return "Your intake is critically low. Please speak with a healthcare provider immediately. Every bite counts. ⚠️"
        else:
            return "Building healthy eating habits takes time. Focus on adding one nutritious meal or snack daily. 🍎"

def calculate_week_average(week_data, week_start):
    """Calculate weekly averages from daily data"""
    total_days = len(week_data)
    if total_days == 0:
        return None
    
    totals = {
        'calories': sum(d['total_calories'] for d in week_data),
        'protein': sum(d['total_protein'] for d in week_data),
        'carbs': sum(d['total_carbs'] for d in week_data),
        'fat': sum(d['total_fat'] for d in week_data),
        'fiber': sum(d['total_fiber'] for d in week_data),
        'sodium': sum(d['total_sodium'] for d in week_data),
        'sugar': sum(d['total_sugar'] for d in week_data),
        'meals': sum(d['meal_count'] for d in week_data)
    }
    
    return {
        'week_start': week_start.isoformat(),
        'week_end': (week_start + timedelta(days=6)).isoformat(),
        'days_in_week': total_days,
        'avg_calories': round(totals['calories'] / total_days, 1),
        'avg_protein': round(totals['protein'] / total_days, 1),
        'avg_carbs': round(totals['carbs'] / total_days, 1),
        'avg_fat': round(totals['fat'] / total_days, 1),
        'avg_fiber': round(totals['fiber'] / total_days, 1),
        'avg_sodium': round(totals['sodium'] / total_days, 1),
        'avg_sugar': round(totals['sugar'] / total_days, 1),
        'avg_meals_per_day': round(totals['meals'] / total_days, 1),
        'total_calories': totals['calories'],
        'total_protein': totals['protein'],
        'total_carbs': totals['carbs'],
        'total_fat': totals['fat']
    }

def calculate_month_average(month_data, month_start):
    """Calculate monthly averages from daily data"""
    total_days = len(month_data)
    if total_days == 0:
        return None
    
    totals = {
        'calories': sum(d['total_calories'] for d in month_data),
        'protein': sum(d['total_protein'] for d in month_data),
        'carbs': sum(d['total_carbs'] for d in month_data),
        'fat': sum(d['total_fat'] for d in month_data),
        'fiber': sum(d['total_fiber'] for d in month_data),
        'sodium': sum(d['total_sodium'] for d in month_data),
        'sugar': sum(d['total_sugar'] for d in month_data),
        'meals': sum(d['meal_count'] for d in month_data)
    }
    
    # Calculate month end
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1) - timedelta(days=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1) - timedelta(days=1)
    
    return {
        'month_start': month_start.isoformat(),
        'month_end': month_end.isoformat(),
        'month_name': month_start.strftime('%B %Y'),
        'days_in_month': total_days,
        'avg_calories': round(totals['calories'] / total_days, 1),
        'avg_protein': round(totals['protein'] / total_days, 1),
        'avg_carbs': round(totals['carbs'] / total_days, 1),
        'avg_fat': round(totals['fat'] / total_days, 1),
        'avg_fiber': round(totals['fiber'] / total_days, 1),
        'avg_sodium': round(totals['sodium'] / total_days, 1),
        'avg_sugar': round(totals['sugar'] / total_days, 1),
        'avg_meals_per_day': round(totals['meals'] / total_days, 1),
        'total_calories': totals['calories'],
        'total_protein': totals['protein'],
        'total_carbs': totals['carbs'],
        'total_fat': totals['fat']
    }

@router.get("/admin/pias-corner/patient/{patient_id}/advice")
async def get_patient_llm_advice(
    patient_id: str,
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """
    Get AI-powered medical advice for a specific patient based on their diet data.
    Uses the existing LLM module to provide personalized recommendations.
    """
    print(f"[PATIENT_ADVICE] Starting LLM advice generation for patient {patient_id} over {days} days")
    
    # Check if user is admin
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Calculate date range - use proper date boundaries to avoid off-by-one errors
        today = datetime.utcnow().date()
        start_date_only = today - timedelta(days=days-1)  # -1 to include today in the count
        end_date_only = today
        
        # Convert to datetime with proper boundaries
        start_date = datetime.combine(start_date_only, datetime.min.time())
        end_date = datetime.combine(end_date_only, datetime.max.time())
        
        print(f"[PATIENT_ADVICE] Analysis period: {start_date_only} to {end_date_only} ({days} days)")
        
        # Get patient's consumption records
        consumption_query = f"""
        SELECT * FROM c 
        WHERE c.type = 'consumption_record' 
        AND c.user_id = '{patient_id}'
        AND c.timestamp >= '{start_date.isoformat()}' 
        AND c.timestamp <= '{end_date.isoformat()}'
        ORDER BY c.timestamp ASC
        """
        
        consumption_records = list(interactions_container.query_items(
            query=consumption_query, 
            enable_cross_partition_query=True
        ))
        
        print(f"[PATIENT_ADVICE] Found {len(consumption_records)} consumption records")
        
        if not consumption_records:
            return {
                "patient_id": patient_id,
                "advice": "No recent food consumption data available to provide personalized advice. Please encourage the patient to log their meals consistently for better insights.",
                "data_availability": "insufficient",
                "analysis_period": f"{days} days",
                "generated_at": datetime.utcnow().isoformat()
            }
        
        # Get comprehensive patient info including full health profile for AI analysis
        all_users_query = f"SELECT * FROM c WHERE c.type = 'user' AND c.email = '{patient_id}'"
        user_info = list(user_container.query_items(query=all_users_query, enable_cross_partition_query=True))
        
        admin_patients = await get_all_patients()
        
        # Initialize comprehensive patient data structure
        patient_name = f"Patient {patient_id[:8]}"
        medical_condition = "General"
        is_diabetic = False
        comprehensive_profile = {}
        admin_patient_data = {}
        
        # Extract user data first
        user = None
        profile = {}
        if user_info:
            user = user_info[0]
            profile = user.get("profile", {})
        
        # Get admin panel patient data first (authoritative source)
        for patient in admin_patients:
            if patient.get('email') == patient_id or (user and patient.get('registration_code') == user.get('registration_code', '')):
                admin_patient_data = {
                    "admin_name": patient.get('name', ''),
                    "admin_condition": patient.get('condition', ''),
                    "registration_code": patient.get('registration_code', ''),
                    "admin_notes": patient.get('notes', ''),
                    "risk_level": patient.get('risk_level', ''),
                    "last_consultation": patient.get('last_consultation', '')
                }
                patient_name = admin_patient_data["admin_name"] or patient_name
                medical_condition = admin_patient_data["admin_condition"] or medical_condition
                is_diabetic = 'diabetes' in medical_condition.lower()
                break
        
        # Extract comprehensive health profile from user data
        if user and profile:
            
            comprehensive_profile = {
                # Basic Demographics
                "name": profile.get("name", ""),
                "age": profile.get("age", ""),
                "gender": profile.get("gender", ""),
                "ethnicity": profile.get("ethnicity", ""),
                "date_of_birth": profile.get("dateOfBirth", ""),
                
                # Medical Information
                "medical_conditions": profile.get("medicalConditions", []),
                "current_medications": profile.get("currentMedications", []),
                "allergies": profile.get("allergies", []),
                
                # Physical Metrics & Vital Signs
                "height": profile.get("height", ""),
                "weight": profile.get("weight", ""),
                "bmi": profile.get("bmi", ""),
                "waist_circumference": profile.get("waistCircumference", ""),
                "systolic_bp": profile.get("systolicBP", ""),
                "diastolic_bp": profile.get("diastolicBP", ""),
                "heart_rate": profile.get("heartRate", ""),
                
                # Lab Values (comprehensive)
                "lab_values": profile.get("labValues", {}),
                
                # Dietary Information
                "diet_type": profile.get("dietType", ""),
                "dietary_features": profile.get("dietaryFeatures", []),
                "dietary_restrictions": profile.get("dietaryRestrictions", []),
                "food_preferences": profile.get("foodPreferences", []),
                "strong_dislikes": profile.get("strongDislikes", []),
                "avoids": profile.get("avoids", []),
                
                # Lifestyle & Activity
                "work_activity_level": profile.get("workActivityLevel", ""),
                "exercise_frequency": profile.get("exerciseFrequency", ""),
                "exercise_types": profile.get("exerciseTypes", []),
                "mobility_issues": profile.get("mobilityIssues", []) if isinstance(profile.get("mobilityIssues"), list) else (["Mobility limitations reported"] if profile.get("mobilityIssues") else []),
                
                # Goals & Targets
                "primary_goals": profile.get("primaryGoals", []),
                "calorie_target": profile.get("calorieTarget", ""),
                "macro_goals": profile.get("macroGoals", {}),
                "wants_weight_loss": profile.get("wantsWeightLoss", False),
                "readiness_to_change": profile.get("readinessToChange", ""),
                
                # Practical Considerations
                "meal_prep_capability": profile.get("mealPrepCapability", ""),
                "available_appliances": profile.get("availableAppliances", []),
                "eating_schedule": profile.get("eatingSchedule", "")
            }
            
            # Use profile name if admin name not available
            if not admin_patient_data.get("admin_name") and comprehensive_profile["name"]:
                patient_name = comprehensive_profile["name"]
            
            # Enhance medical conditions if not from admin panel
            if not admin_patient_data.get("admin_condition") and comprehensive_profile["medical_conditions"]:
                medical_condition = ", ".join(comprehensive_profile["medical_conditions"])
                is_diabetic = any("diabetes" in condition.lower() for condition in comprehensive_profile["medical_conditions"])
        
        # Group consumption data by date and calculate daily totals
        daily_data = {}
        for record in consumption_records:
            record_date = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00')).date()
            
            if record_date not in daily_data:
                daily_data[record_date] = {
                    'date': record_date.isoformat(),
                    'total_calories': 0,
                    'total_protein': 0,
                    'total_carbs': 0,
                    'total_fat': 0,
                    'total_fiber': 0,
                    'total_sodium': 0,
                    'total_sugar': 0,
                    'meal_count': 0,
                    'food_items': []
                }
            
            # Accumulate daily totals - CRITICAL: Use correct nutritional data access path
            daily_entry = daily_data[record_date]
            
            # Extract nutritional data from nested structure
            nutritional_info = record.get('nutritional_info', {})
            calories = nutritional_info.get('calories', 0) or 0
            protein = nutritional_info.get('protein', 0) or 0
            carbohydrates = nutritional_info.get('carbohydrates', 0) or 0
            fat = nutritional_info.get('fat', 0) or 0
            fiber = nutritional_info.get('fiber', 0) or 0
            sodium = nutritional_info.get('sodium', 0) or 0
            sugar = nutritional_info.get('sugar', 0) or 0
            
            # Accumulate daily totals with correct data access
            daily_entry['total_calories'] += calories
            daily_entry['total_protein'] += protein
            daily_entry['total_carbs'] += carbohydrates
            daily_entry['total_fat'] += fat
            daily_entry['total_fiber'] += fiber
            daily_entry['total_sodium'] += sodium
            daily_entry['total_sugar'] += sugar
            daily_entry['meal_count'] += 1
            daily_entry['food_items'].append(record.get('food_name', 'Unknown food'))
            
            # Store detailed meal information for AI analysis
            daily_entry.setdefault('meals', []).append({
                'food_name': record.get('food_name', 'Unknown food'),
                'meal_type': record.get('meal_type', 'Unknown'),
                'calories': calories,
                'protein': protein,
                'carbs': carbohydrates,
                'fat': fat,
                'fiber': fiber,
                'sodium': sodium,
                'sugar': sugar,
                'timestamp': record.get('timestamp')
            })
        
        # Sort daily data by date
        sorted_daily_data = [daily_data[date] for date in sorted(daily_data.keys())]
        
        # Calculate overall averages and patterns
        total_days = len(sorted_daily_data)
        avg_calories = sum(d['total_calories'] for d in sorted_daily_data) / total_days
        avg_protein = sum(d['total_protein'] for d in sorted_daily_data) / total_days
        avg_carbs = sum(d['total_carbs'] for d in sorted_daily_data) / total_days
        avg_fat = sum(d['total_fat'] for d in sorted_daily_data) / total_days
        avg_fiber = sum(d['total_fiber'] for d in sorted_daily_data) / total_days
        avg_sodium = sum(d['total_sodium'] for d in sorted_daily_data) / total_days
        avg_sugar = sum(d['total_sugar'] for d in sorted_daily_data) / total_days
        avg_meals_per_day = sum(d['meal_count'] for d in sorted_daily_data) / total_days
        
        # Identify concerning patterns
        high_calorie_days = len([d for d in sorted_daily_data if d['total_calories'] > 2500])
        low_calorie_days = len([d for d in sorted_daily_data if d['total_calories'] < 1200])
        high_sodium_days = len([d for d in sorted_daily_data if d['total_sodium'] > 2300])
        low_fiber_days = len([d for d in sorted_daily_data if d['total_fiber'] < 25])
        
        # Calculate macro percentages safely to avoid division by zero
        protein_percentage = (avg_protein * 4 / avg_calories * 100) if avg_calories > 0 else 0
        carbs_percentage = (avg_carbs * 4 / avg_calories * 100) if avg_calories > 0 else 0
        fat_percentage = (avg_fat * 9 / avg_calories * 100) if avg_calories > 0 else 0
        
        # Generate detailed meal analysis for AI context
        detailed_meal_analysis = ""
        if sorted_daily_data:
            detailed_meal_analysis = "\nDETAILED DAILY MEAL BREAKDOWN:\n"
            for day in sorted_daily_data[-7:]:  # Last 7 days
                meals_info = day.get('meals', [])
                if meals_info:
                    detailed_meal_analysis += f"\n{day['date']} ({day['total_calories']:.0f} kcal total):\n"
                    for meal in meals_info:
                        detailed_meal_analysis += f"  • {meal['meal_type']}: {meal['food_name']} ({meal['calories']:.0f} cal, {meal['protein']:.1f}g protein, {meal['carbs']:.1f}g carbs, {meal['fat']:.1f}g fat)\n"
        
        # Format comprehensive health profile sections
        demographics_section = ""
        if comprehensive_profile:
            demographics_section = f"""
COMPREHENSIVE PATIENT DEMOGRAPHICS & MEDICAL HISTORY:
- Name: {comprehensive_profile.get('name', 'N/A')}
- Age: {comprehensive_profile.get('age', 'N/A')} years
- Gender: {comprehensive_profile.get('gender', 'N/A')}
- Ethnicity: {comprehensive_profile.get('ethnicity', 'N/A')}
- Date of Birth: {comprehensive_profile.get('date_of_birth', 'N/A')}

MEDICAL CONDITIONS & MEDICATIONS:
- Primary Medical Conditions: {', '.join(comprehensive_profile.get('medical_conditions', [])) or 'None specified'}
- Current Medications: {', '.join(comprehensive_profile.get('current_medications', [])) or 'None specified'}
- Known Allergies: {', '.join(comprehensive_profile.get('allergies', [])) or 'None specified'}

PHYSICAL METRICS & VITAL SIGNS:
- Height: {comprehensive_profile.get('height', 'N/A')} cm
- Weight: {comprehensive_profile.get('weight', 'N/A')} kg
- BMI: {comprehensive_profile.get('bmi', 'N/A')}
- Waist Circumference: {comprehensive_profile.get('waist_circumference', 'N/A')} cm
- Blood Pressure: {comprehensive_profile.get('systolic_bp', 'N/A')}/{comprehensive_profile.get('diastolic_bp', 'N/A')} mmHg
- Heart Rate: {comprehensive_profile.get('heart_rate', 'N/A')} bpm

LABORATORY VALUES:
{chr(10).join([f"- {key}: {value}" for key, value in comprehensive_profile.get('lab_values', {}).items()]) or '- No lab values recorded'}

DIETARY PREFERENCES & RESTRICTIONS:
- Diet Type: {comprehensive_profile.get('diet_type', 'N/A')}
- Dietary Features: {', '.join(comprehensive_profile.get('dietary_features', [])) or 'None specified'}
- Dietary Restrictions: {', '.join(comprehensive_profile.get('dietary_restrictions', [])) or 'None specified'}
- Food Preferences: {', '.join(comprehensive_profile.get('food_preferences', [])) or 'None specified'}
- Foods to Avoid: {', '.join(comprehensive_profile.get('avoids', [])) or 'None specified'}
- Strong Dislikes: {', '.join(comprehensive_profile.get('strong_dislikes', [])) or 'None specified'}

LIFESTYLE & ACTIVITY PROFILE:
- Work Activity Level: {comprehensive_profile.get('work_activity_level', 'N/A')}
- Exercise Frequency: {comprehensive_profile.get('exercise_frequency', 'N/A')}
- Exercise Types: {', '.join(comprehensive_profile.get('exercise_types', [])) or 'None specified'}
- Mobility Issues: {', '.join(comprehensive_profile.get('mobility_issues', [])) or 'None reported'}

PATIENT GOALS & TARGETS:
- Primary Health Goals: {', '.join(comprehensive_profile.get('primary_goals', [])) or 'None specified'}
- Target Daily Calories: {comprehensive_profile.get('calorie_target', 'N/A')}
- Macro Goals: {str(comprehensive_profile.get('macro_goals', {})) or 'None set'}
- Weight Loss Goal: {"Yes" if comprehensive_profile.get('wants_weight_loss') else "No"}
- Readiness to Change: {comprehensive_profile.get('readiness_to_change', 'N/A')}

PRACTICAL CONSIDERATIONS:
- Meal Prep Capability: {comprehensive_profile.get('meal_prep_capability', 'N/A')}
- Available Appliances: {', '.join(comprehensive_profile.get('available_appliances', [])) or 'None specified'}
- Eating Schedule: {comprehensive_profile.get('eating_schedule', 'N/A')}"""
        
        admin_context_section = ""
        if admin_patient_data:
            admin_context_section = f"""
ADMINISTRATIVE & CLINICAL CONTEXT:
- Registration Code: {admin_patient_data.get('registration_code', 'N/A')}
- Risk Level: {admin_patient_data.get('risk_level', 'N/A')}
- Last Consultation: {admin_patient_data.get('last_consultation', 'N/A')}
- Clinical Notes: {admin_patient_data.get('admin_notes', 'No notes available')}"""
        
        # Create comprehensive medical prompt for LLM with ALL patient data
        medical_prompt = f"""
As an expert medical nutritionist and diabetes specialist, analyze the following comprehensive patient data and provide professional medical advice.

=== PATIENT OVERVIEW ===
- Analysis Period: {total_days} days ({start_date_only} to {end_date_only})
- Total Food Records Analyzed: {len(consumption_records)}
- Diabetic Status: {"Yes" if is_diabetic else "No"}
{demographics_section}
{admin_context_section}

=== NUTRITIONAL ANALYSIS SUMMARY ===
MACRONUTRIENT AVERAGES (Daily):
- Calories: {avg_calories:.1f} kcal
- Protein: {avg_protein:.1f}g ({protein_percentage:.1f}% of calories)
- Carbohydrates: {avg_carbs:.1f}g ({carbs_percentage:.1f}% of calories)
- Fat: {avg_fat:.1f}g ({fat_percentage:.1f}% of calories)
- Fiber: {avg_fiber:.1f}g
- Sodium: {avg_sodium:.0f}mg
- Sugar: {avg_sugar:.1f}g
- Average Meals Per Day: {avg_meals_per_day:.1f}

CONCERNING DIETARY PATTERNS:
- High Calorie Days (>2500 kcal): {high_calorie_days}/{total_days} days ({(high_calorie_days/total_days*100):.1f}%)
- Low Calorie Days (<1200 kcal): {low_calorie_days}/{total_days} days ({(low_calorie_days/total_days*100):.1f}%)
- High Sodium Days (>2300mg): {high_sodium_days}/{total_days} days ({(high_sodium_days/total_days*100):.1f}%)
- Low Fiber Days (<25g): {low_fiber_days}/{total_days} days ({(low_fiber_days/total_days*100):.1f}%)

FOOD VARIETY ANALYSIS:
Recent Foods Consumed: {', '.join(set([item for day in sorted_daily_data[-7:] for item in day['food_items']]))}
{detailed_meal_analysis}

=== COMPREHENSIVE MEDICAL ANALYSIS REQUEST ===
Based on this complete patient profile, provide professional medical recommendations including:

1. MEDICAL ASSESSMENT: Overall dietary quality and health implications considering patient's complete medical history
2. PRIORITY CONCERNS: Most critical issues requiring immediate medical attention
3. PERSONALIZED RECOMMENDATIONS: Actionable dietary modifications based on patient's specific profile, preferences, and constraints
4. CONDITION-SPECIFIC GUIDANCE: Tailored advice for diabetes management and other medical conditions
5. LIFESTYLE INTEGRATION: Recommendations considering patient's activity level, meal prep ability, and eating schedule
6. MONITORING STRATEGY: Key metrics to track based on patient's lab values and health goals
7. FOLLOW-UP ACTIONS: Specific next steps for healthcare provider and patient
8. PATIENT EDUCATION: Key points to discuss with patient for better compliance

Format your response as comprehensive, evidence-based medical advice that incorporates all aspects of this patient's health profile.
"""
        
        print(f"[PATIENT_ADVICE] Calling LLM with comprehensive medical prompt")
        
        # Call the robust OpenAI API directly with higher token limit for comprehensive medical advice
        try:
            from services.openai_service import robust_openai_call
            from constants import PATIENT_MEDICAL_ADVICE_MAX_TOKENS
            
            api_result = await robust_openai_call(
                messages=[
                    {"role": "system", "content": "You are an expert medical nutritionist and diabetes specialist. Provide comprehensive, professional medical advice that doctors can use for patient consultation."},
                    {"role": "user", "content": medical_prompt}
                ],
                temperature=0.7,
                max_tokens=PATIENT_MEDICAL_ADVICE_MAX_TOKENS,  # Use constant for comprehensive medical advice
                max_retries=3,
                timeout=90,  # Longer timeout for complex analysis
                context="patient_medical_advice"
            )
            
            if api_result["success"]:
                llm_advice = api_result["content"].strip()
                print(f"[PATIENT_ADVICE] Successfully received LLM advice ({len(llm_advice)} characters)")
            else:
                print(f"[PATIENT_ADVICE] OpenAI failed: {api_result['error']}")
                llm_advice = f"Unable to generate comprehensive medical analysis at this time. Please try again later. Error: {api_result['error']}"
            
            # Structure the response
            response_data = {
                "patient_info": {
                    "patient_id": patient_id,
                    "patient_name": patient_name,
                    "medical_condition": medical_condition,
                    "is_diabetic": is_diabetic
                },
                "analysis_summary": {
                    "analysis_period_days": total_days,
                    "total_food_records": len(consumption_records),
                    "avg_daily_calories": round(avg_calories, 1),
                    "avg_daily_protein": round(avg_protein, 1),
                    "avg_daily_carbs": round(avg_carbs, 1),
                    "avg_daily_fat": round(avg_fat, 1),
                    "avg_daily_fiber": round(avg_fiber, 1),
                    "avg_daily_sodium": round(avg_sodium, 0),
                    "concerning_patterns": {
                        "high_calorie_days": high_calorie_days,
                        "low_calorie_days": low_calorie_days,
                        "high_sodium_days": high_sodium_days,
                        "low_fiber_days": low_fiber_days
                    }
                },
                "llm_advice": llm_advice,
                "data_availability": "sufficient",
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return response_data
            
        except Exception as llm_error:
            print(f"[PATIENT_ADVICE] LLM call failed: {str(llm_error)}")
            # Fallback response if LLM fails
            return {
                "patient_info": {
                    "patient_id": patient_id,
                    "patient_name": patient_name,
                    "medical_condition": medical_condition,
                    "is_diabetic": is_diabetic
                },
                "analysis_summary": {
                    "analysis_period_days": total_days,
                    "total_food_records": len(consumption_records),
                    "avg_daily_calories": round(avg_calories, 1),
                    "avg_daily_protein": round(avg_protein, 1),
                    "avg_daily_carbs": round(avg_carbs, 1)
                },
                "llm_advice": f"Based on {total_days} days of data: The patient's average daily intake is {avg_calories:.0f} calories. Key observations include protein intake of {avg_protein:.1f}g/day and fiber intake of {avg_fiber:.1f}g/day. Recommend monitoring sodium intake ({avg_sodium:.0f}mg/day) and ensuring adequate fiber consumption. Regular follow-up advised for {'diabetes management' if is_diabetic else 'overall health optimization'}.",
                "data_availability": "sufficient_with_fallback_advice",
                "error": "LLM service temporarily unavailable - basic analysis provided",
                "generated_at": datetime.utcnow().isoformat()
            }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[PATIENT_ADVICE] Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to generate patient advice: {str(e)}")


@router.get("/admin/pias-corner/patient-nutrition/{patient_email}")
async def get_individual_patient_nutrition(
    patient_email: str,
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get detailed nutrition analysis for a specific patient"""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        print(f"[PATIENT_NUTRITION] Getting nutrition analysis for patient: {patient_email}")
        
        # Decode the email if it's URL encoded
        from urllib.parse import unquote
        patient_email = unquote(patient_email)
        
        # Get time range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get patient's consumption records
        consumption_query = f"""
            SELECT * FROM c 
            WHERE c.type = 'consumption_record' 
            AND c.user_id = '{patient_email}'
            AND c.timestamp >= '{start_date.isoformat()}'
        """
        patient_consumption = list(interactions_container.query_items(
            query=consumption_query, 
            enable_cross_partition_query=True
        ))
        
        print(f"[PATIENT_NUTRITION] Found {len(patient_consumption)} records for {patient_email}")
        
        
        if not patient_consumption:
            return {
                "patient_email": patient_email,
                "patient_name": patient_email,
                "analysis_period": {
                    "days": days,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "total_records": 0
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
                "nutrient_trends": [],
                "micronutrients": {},
                "meal_patterns": {},
                "food_groups": {},
                "medical_insights": [],
                "generated_at": datetime.utcnow().isoformat()
            }
        
        # Get patient name using consistent priority system
        admin_patients = await get_all_patients()
        patient_name = patient_email  # Default fallback
        
        # First, try admin panel data (authoritative source)
        for patient in admin_patients:
            # Get user by registration code to find email
            users_query = f"SELECT * FROM c WHERE c.type = 'user' AND c.registration_code = '{patient.get('registration_code', '')}'"
            matching_users = list(user_container.query_items(query=users_query, enable_cross_partition_query=True))
            if matching_users and matching_users[0].get('email') == patient_email:
                patient_name = patient.get('name', patient_email)
                break
        
        # If admin panel didn't have the name, try comprehensive health profile
        if patient_name == patient_email:
            user_query = f"SELECT * FROM c WHERE c.type = 'user' AND c.email = '{patient_email}'"
            user_records = list(user_container.query_items(query=user_query, enable_cross_partition_query=True))
            if user_records:
                profile = user_records[0].get('profile', {})
                profile_name = profile.get('name', '').strip()
                if profile_name:
                    patient_name = profile_name
        
        # Process nutrition data
        daily_totals = {}
        nutrient_trends = []
        meal_type_counts = {}
        food_frequency = {}
        
        # RDA values for comparison
        RDA_VALUES = {
            "calories": {"min": 1800, "max": 2200},
            "protein": {"min": 50, "max": 100},
            "carbohydrates": {"min": 130, "max": 300},
            "fat": {"min": 44, "max": 78},
            "fiber": {"min": 25, "max": 35},
            "sodium": {"max": 2300},
            "sugar": {"max": 50}
        }
        
        for record in patient_consumption:
            nutritional_info = record.get("nutritional_info", {})
            timestamp = record.get("timestamp", "")
            food_name = record.get("food_name", "Unknown")
            meal_type = record.get("meal_type", "snack")
            
            # Extract date for daily grouping
            try:
                record_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).date().isoformat()
            except:
                record_date = datetime.utcnow().date().isoformat()
            
            # Initialize daily totals
            if record_date not in daily_totals:
                daily_totals[record_date] = {
                    "calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0,
                    "fiber": 0, "sugar": 0, "sodium": 0, "meals_count": 0
                }
            
            # Extract nutrition values
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
            
            # Count meal types
            meal_type_counts[meal_type] = meal_type_counts.get(meal_type, 0) + 1
            
            # Track food frequency
            if food_name not in food_frequency:
                food_frequency[food_name] = {"count": 0, "total_calories": 0}
            food_frequency[food_name]["count"] += 1
            food_frequency[food_name]["total_calories"] += calories
        
        # Calculate averages
        total_days = len(daily_totals)
        if total_days > 0:
            total_calories = sum(day["calories"] for day in daily_totals.values())
            total_protein = sum(day["protein"] for day in daily_totals.values())
            total_carbs = sum(day["carbohydrates"] for day in daily_totals.values())
            total_fat = sum(day["fat"] for day in daily_totals.values())
            total_fiber = sum(day["fiber"] for day in daily_totals.values())
            total_sugar = sum(day["sugar"] for day in daily_totals.values())
            total_sodium = sum(day["sodium"] for day in daily_totals.values())
            
            daily_averages = {
                "calories": total_calories / total_days,
                "protein": total_protein / total_days,
                "carbohydrates": total_carbs / total_days,
                "fat": total_fat / total_days,
                "fiber": total_fiber / total_days,
                "sugar": total_sugar / total_days,
                "sodium": total_sodium / total_days
            }
        else:
            daily_averages = {
                "calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0,
                "fiber": 0, "sugar": 0, "sodium": 0
            }
        
        # Create nutrient trends data (daily values over time)
        sorted_dates = sorted(daily_totals.keys())
        for date in sorted_dates:
            nutrient_trends.append({
                "date": date,
                "calories": daily_totals[date]["calories"],
                "protein": daily_totals[date]["protein"],
                "carbohydrates": daily_totals[date]["carbohydrates"],
                "fat": daily_totals[date]["fat"],
                "fiber": daily_totals[date]["fiber"],
                "sugar": daily_totals[date]["sugar"],
                "sodium": daily_totals[date]["sodium"]
            })
        
        # Generate medical insights based on patient data
        medical_insights = []
        
        # Check against RDA values
        if daily_averages["fiber"] < RDA_VALUES["fiber"]["min"]:
            deficit = RDA_VALUES["fiber"]["min"] - daily_averages["fiber"]
            medical_insights.append(f"Fiber intake is {deficit:.1f}g below recommended daily allowance. Consider increasing vegetable and whole grain consumption.")
        
        if daily_averages["sodium"] > RDA_VALUES["sodium"]["max"]:
            excess = daily_averages["sodium"] - RDA_VALUES["sodium"]["max"]
            medical_insights.append(f"Sodium intake is {excess:.0f}mg above recommended limit. Monitor for hypertension risk.")
        
        if daily_averages["sugar"] > RDA_VALUES["sugar"]["max"]:
            excess = daily_averages["sugar"] - RDA_VALUES["sugar"]["max"]
            medical_insights.append(f"Sugar intake is {excess:.1f}g above recommended limit. Important for diabetes management.")
        
        if daily_averages["protein"] < RDA_VALUES["protein"]["min"]:
            deficit = RDA_VALUES["protein"]["min"] - daily_averages["protein"]
            medical_insights.append(f"Protein intake is {deficit:.1f}g below recommended daily allowance. Consider lean protein sources.")
        
        # Top consumed foods
        top_foods = sorted(food_frequency.items(), key=lambda x: x[1]["count"], reverse=True)[:10]
        
        return {
            "patient_email": patient_email,
            "patient_name": patient_name,
            "analysis_period": {
                "days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_records": len(patient_consumption),
                "active_days": total_days
            },
            "daily_averages": daily_averages,
            "nutrient_trends": nutrient_trends,
            "meal_patterns": meal_type_counts,
            "food_frequency": dict(top_foods),
            "rda_compliance": {
                "fiber": min(100, (daily_averages["fiber"] / RDA_VALUES["fiber"]["min"]) * 100) if RDA_VALUES["fiber"]["min"] > 0 else 0,
                "sodium": min(100, (RDA_VALUES["sodium"]["max"] / daily_averages["sodium"]) * 100) if daily_averages["sodium"] > 0 else 100,
                "sugar": min(100, (RDA_VALUES["sugar"]["max"] / daily_averages["sugar"]) * 100) if daily_averages["sugar"] > 0 else 100,
                "protein": min(100, (daily_averages["protein"] / RDA_VALUES["protein"]["min"]) * 100) if RDA_VALUES["protein"]["min"] > 0 else 0
            },
            "medical_insights": medical_insights,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"[PATIENT_NUTRITION] Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get patient nutrition: {str(e)}")


@router.get("/admin/pias-corner/enhanced-analytics")
async def get_enhanced_nutrition_analytics(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get enhanced nutrition analytics with trends, micronutrients, and meal patterns"""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        print(f"[ENHANCED_ANALYTICS] Starting enhanced nutrition analytics for {days} days")
        
        # Get time range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get all consumption records in the time period
        consumption_query = f"""
            SELECT * FROM c 
            WHERE c.type = 'consumption_record' 
            AND c.timestamp >= '{start_date.isoformat()}'
        """
        all_consumption = list(interactions_container.query_items(
            query=consumption_query, 
            enable_cross_partition_query=True
        ))
        
        print(f"[ENHANCED_ANALYTICS] Found {len(all_consumption)} consumption records")
        
        # Filter out deleted duplicate account records
        all_consumption = [r for r in all_consumption if r.get('user_id') != 'nagarwal166@gmail.com']
        print(f"[ENHANCED_ANALYTICS] After filtering deleted accounts: {len(all_consumption)} records")
        
        if not all_consumption:
            return {
                "analysis_period": {
                    "days": days,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "total_records": 0
                },
                "nutrient_trends": [],
                "meal_timing_patterns": {},
                "micronutrient_analysis": {},
                "food_group_distribution": {},
                "risk_level_nutrition": {},
                "generated_at": datetime.utcnow().isoformat()
            }
        
        # Process data by date for trends
        daily_nutrition = {}
        meal_timing = {"breakfast": 0, "lunch": 0, "dinner": 0, "snack": 0}
        micronutrients = {
            "calcium": [], "iron": [], "potassium": [], "vitamin_c": [],
            "vitamin_d": [], "vitamin_b12": [], "folate": [], "magnesium": [], "zinc": []
        }
        food_groups = {}
        
        # Categorize foods into groups (simplified classification)
        food_group_keywords = {
            "Proteins": ["chicken", "beef", "fish", "salmon", "tuna", "egg", "tofu", "beans", "lentils", "meat"],
            "Grains": ["rice", "bread", "pasta", "oats", "quinoa", "wheat", "cereal", "flour"],
            "Vegetables": ["broccoli", "spinach", "carrot", "tomato", "lettuce", "onion", "pepper", "vegetable"],
            "Fruits": ["apple", "banana", "orange", "berries", "strawberry", "grape", "fruit"],
            "Dairy": ["milk", "cheese", "yogurt", "butter", "cream"],
            "Fats": ["oil", "avocado", "nuts", "seeds", "olive"],
            "Sweets": ["cake", "cookie", "candy", "chocolate", "ice cream", "sugar"]
        }
        
        for record in all_consumption:
            nutritional_info = record.get("nutritional_info", {})
            timestamp = record.get("timestamp", "")
            food_name = record.get("food_name", "").lower()
            meal_type = record.get("meal_type", "snack")
            
            # Extract date for trends
            try:
                record_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).date().isoformat()
            except:
                record_date = datetime.utcnow().date().isoformat()
            
            # Initialize daily nutrition tracking
            if record_date not in daily_nutrition:
                daily_nutrition[record_date] = {
                    "calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0,
                    "fiber": 0, "sugar": 0, "sodium": 0
                }
            
            # Update daily totals
            daily_nutrition[record_date]["calories"] += nutritional_info.get("calories", 0)
            daily_nutrition[record_date]["protein"] += nutritional_info.get("protein", 0)
            daily_nutrition[record_date]["carbohydrates"] += nutritional_info.get("carbohydrates", 0)
            daily_nutrition[record_date]["fat"] += nutritional_info.get("fat", 0)
            daily_nutrition[record_date]["fiber"] += nutritional_info.get("fiber", 0)
            daily_nutrition[record_date]["sugar"] += nutritional_info.get("sugar", 0)
            daily_nutrition[record_date]["sodium"] += nutritional_info.get("sodium", 0)
            
            # Count meal timing
            meal_timing[meal_type] += 1
            
            # Track micronutrients (if available)
            for nutrient in micronutrients.keys():
                value = nutritional_info.get(nutrient, 0)
                if value > 0:
                    micronutrients[nutrient].append(value)
            
            # Classify food groups
            classified = False
            for group, keywords in food_group_keywords.items():
                if any(keyword in food_name for keyword in keywords):
                    food_groups[group] = food_groups.get(group, 0) + 1
                    classified = True
                    break
            if not classified:
                food_groups["Other"] = food_groups.get("Other", 0) + 1
        
        # Create nutrient trends (daily averages over time)
        nutrient_trends = []
        sorted_dates = sorted(daily_nutrition.keys())
        for date in sorted_dates:
            nutrient_trends.append({
                "date": date,
                "calories": daily_nutrition[date]["calories"],
                "protein": daily_nutrition[date]["protein"],
                "carbohydrates": daily_nutrition[date]["carbohydrates"],
                "fat": daily_nutrition[date]["fat"],
                "fiber": daily_nutrition[date]["fiber"],
                "sugar": daily_nutrition[date]["sugar"],
                "sodium": daily_nutrition[date]["sodium"]
            })
        
        # Calculate micronutrient averages
        micronutrient_analysis = {}
        for nutrient, values in micronutrients.items():
            if values:
                micronutrient_analysis[nutrient] = {
                    "average": sum(values) / len(values),
                    "count": len(values),
                    "total": sum(values)
                }
            else:
                micronutrient_analysis[nutrient] = {
                    "average": 0,
                    "count": 0,
                    "total": 0
                }
        
        return {
            "analysis_period": {
                "days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_records": len(all_consumption),
                "active_days": len(daily_nutrition)
            },
            "nutrient_trends": nutrient_trends,
            "meal_timing_patterns": meal_timing,
            "micronutrient_analysis": micronutrient_analysis,
            "food_group_distribution": food_groups,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"[ENHANCED_ANALYTICS] Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get enhanced analytics: {str(e)}")


@router.get("/admin/pias-corner/patient-engagement/{patient_email}")
async def get_individual_patient_engagement(
    patient_email: str,
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get detailed engagement analysis for a specific patient"""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        print(f"[PATIENT_ENGAGEMENT] Getting engagement analysis for patient: {patient_email}")
        
        # Decode the email if it's URL encoded
        from urllib.parse import unquote
        patient_email = unquote(patient_email)
        
        # Get time range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get patient's consumption records with detailed timestamps
        consumption_query = f"""
            SELECT * FROM c 
            WHERE c.type = 'consumption_record' 
            AND c.user_id = '{patient_email}'
            AND c.timestamp >= '{start_date.isoformat()}'
            ORDER BY c.timestamp DESC
        """
        patient_consumption = list(interactions_container.query_items(
            query=consumption_query, 
            enable_cross_partition_query=True
        ))
        
        print(f"[PATIENT_ENGAGEMENT] Found {len(patient_consumption)} consumption records for {patient_email}")
        
        # Get patient name using consistent priority system
        admin_patients = await get_all_patients()
        patient_name = patient_email  # Default fallback
        
        # First, try admin panel data (authoritative source)
        for patient in admin_patients:
            users_query = f"SELECT * FROM c WHERE c.type = 'user' AND c.registration_code = '{patient.get('registration_code', '')}'"
            matching_users = list(user_container.query_items(query=users_query, enable_cross_partition_query=True))
            if matching_users and matching_users[0].get('email') == patient_email:
                patient_name = patient.get('name', patient_email)
                break
        
        # If admin panel didn't have the name, try comprehensive health profile
        if patient_name == patient_email:
            user_query = f"SELECT * FROM c WHERE c.type = 'user' AND c.email = '{patient_email}'"
            user_records = list(user_container.query_items(query=user_query, enable_cross_partition_query=True))
            if user_records:
                profile = user_records[0].get('profile', {})
                profile_name = profile.get('name', '').strip()
                if profile_name:
                    patient_name = profile_name
        
        if not patient_consumption:
            return {
                "patient_email": patient_email,
                "patient_name": patient_name,
                "analysis_period": {
                    "days": days,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "total_records": 0
                },
                "daily_logging_timeline": [],
                "meal_timing_patterns": {},
                "engagement_metrics": {
                    "total_logs": 0,
                    "active_days": 0,
                    "logging_streak": 0,
                    "consistency_score": 0
                },
                "eating_behavior_insights": [],
                "medical_risk_flags": [],
                "generated_at": datetime.utcnow().isoformat()
            }
        
        # Process consumption data for engagement analysis
        daily_logs = {}
        meal_timing_data = {"breakfast": [], "lunch": [], "dinner": [], "snack": []}
        total_logs = len(patient_consumption)
        
        for record in patient_consumption:
            timestamp_str = record.get("timestamp", "")
            food_name = record.get("food_name", "Unknown")
            meal_type = record.get("meal_type", "snack")
            
            try:
                # Parse timestamp
                record_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                record_date = record_timestamp.date().isoformat()
                hour = record_timestamp.hour
                minute = record_timestamp.minute
                
                # Group by date for daily timeline
                if record_date not in daily_logs:
                    daily_logs[record_date] = []
                
                daily_logs[record_date].append({
                    "time": f"{hour:02d}:{minute:02d}",
                    "hour": hour,
                    "food_name": food_name,
                    "meal_type": meal_type,
                    "timestamp": timestamp_str
                })
                
                # Collect meal timing data
                if meal_type in meal_timing_data:
                    meal_timing_data[meal_type].append(hour)
                    
            except Exception as e:
                print(f"[PATIENT_ENGAGEMENT] Error parsing timestamp {timestamp_str}: {e}")
                continue
        
        # Calculate engagement metrics
        active_days = len(daily_logs)
        
        # Calculate logging streak (consecutive days with logs)
        logging_streak = 0
        sorted_dates = sorted(daily_logs.keys(), reverse=True)
        
        if sorted_dates:
            current_date = datetime.strptime(sorted_dates[0], "%Y-%m-%d").date()
            streak_count = 0
            
            for date_str in sorted_dates:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                if date_obj == current_date:
                    streak_count += 1
                    current_date -= timedelta(days=1)
                else:
                    break
            logging_streak = streak_count
        
        # Calculate consistency score (0-100)
        consistency_score = min(100, (active_days / days) * 100) if days > 0 else 0
        
        # Create daily timeline for visualization
        daily_logging_timeline = []
        for date_str in sorted(daily_logs.keys()):
            daily_logs_for_date = sorted(daily_logs[date_str], key=lambda x: x['hour'])
            
            daily_logging_timeline.append({
                "date": date_str,
                "total_logs": len(daily_logs_for_date),
                "logs": daily_logs_for_date,
                "first_log_time": daily_logs_for_date[0]["time"] if daily_logs_for_date else None,
                "last_log_time": daily_logs_for_date[-1]["time"] if daily_logs_for_date else None
            })
        
        # Analyze meal timing patterns
        meal_timing_patterns = {}
        for meal_type, hours in meal_timing_data.items():
            if hours:
                avg_hour = sum(hours) / len(hours)
                meal_timing_patterns[meal_type] = {
                    "average_time": f"{int(avg_hour):02d}:{int((avg_hour % 1) * 60):02d}",
                    "frequency": len(hours),
                    "consistency": 100 - (max(hours) - min(hours)) * 2 if len(hours) > 1 else 100  # Lower variance = higher consistency
                }
        
        # Generate behavior insights
        eating_behavior_insights = []
        
        # Check meal frequency
        avg_logs_per_day = total_logs / max(active_days, 1)
        if avg_logs_per_day < 2:
            eating_behavior_insights.append("Patient logs fewer than 2 meals per day on average - may be missing meals")
        elif avg_logs_per_day > 6:
            eating_behavior_insights.append("Patient logs frequently throughout the day - good engagement")
        
        # Check consistency
        if consistency_score < 50:
            eating_behavior_insights.append("Inconsistent logging pattern - patient may need engagement support")
        elif consistency_score > 80:
            eating_behavior_insights.append("Excellent logging consistency - highly engaged patient")
        
        # Check meal timing consistency
        if "breakfast" in meal_timing_patterns and meal_timing_patterns["breakfast"]["frequency"] < active_days * 0.6:
            eating_behavior_insights.append("Patient frequently skips breakfast - nutritional counseling recommended")
        
        # Generate medical risk flags
        medical_risk_flags = []
        
        if logging_streak == 0:
            medical_risk_flags.append("⚠️ No recent food logging activity - patient may be disengaged")
        
        if active_days < days * 0.3:
            medical_risk_flags.append("🔴 Low engagement (active <30% of days) - immediate follow-up needed")
        
        if "dinner" in meal_timing_patterns:
            avg_dinner_hour = sum(meal_timing_data["dinner"]) / len(meal_timing_data["dinner"])
            if avg_dinner_hour > 21:  # 9 PM
                medical_risk_flags.append("⚠️ Late dinner pattern detected - may affect glucose control")
        
        return {
            "patient_email": patient_email,
            "patient_name": patient_name,
            "analysis_period": {
                "days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_records": total_logs
            },
            "daily_logging_timeline": daily_logging_timeline,
            "meal_timing_patterns": meal_timing_patterns,
            "engagement_metrics": {
                "total_logs": total_logs,
                "active_days": active_days,
                "logging_streak": logging_streak,
                "consistency_score": round(consistency_score, 1),
                "avg_logs_per_day": round(avg_logs_per_day, 1)
            },
            "eating_behavior_insights": eating_behavior_insights,
            "medical_risk_flags": medical_risk_flags,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"[PATIENT_ENGAGEMENT] Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get patient engagement: {str(e)}")


