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
    get_user_by_email, user_container, interactions_container
)
from utils import send_registration_code

router = APIRouter()

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
        
        # Try to find associated user account
        user_doc = None
        try:
            # Look for user with matching registration code
            user_query = f"SELECT * FROM c WHERE c.registration_code = '{registration_code}' AND c.type = 'user'"
            users = list(user_container.query_items(query=user_query, enable_cross_partition_query=True))
            if users:
                user_doc = users[0]
        except Exception as user_error:
            print(f"Error finding user for patient {registration_code}: {str(user_error)}")
        
        return {
            "patient": patient,
            "user_account": user_doc,
            "has_user_account": bool(user_doc),
            "profile": user_doc.get("profile", {}) if user_doc else {}
        }
        
    except Exception as e:
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
    
    try:
        # Get the profile data from request
        profile_data = await request.json()
        
        # Get patient by registration code
        patient = await get_patient_by_registration_code(registration_code)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Save the profile data to user document
        # Find user with registration code
        user_query = f"SELECT * FROM c WHERE c.registration_code = '{registration_code}' AND c.type = 'user'"
        users = list(user_container.query_items(query=user_query, enable_cross_partition_query=True))
        
        if users:
            # Update existing user's profile
            user = users[0]
            user['profile'] = profile_data
            user['updated_at'] = datetime.utcnow().isoformat()
            user_container.replace_item(item=user['id'], body=user)
        else:
            # Create new profile document
            profile_doc = {
                "id": f"profile_{registration_code}",
                "type": "user_profile",
                "registration_code": registration_code,
                "profile": profile_data,
                "created_at": datetime.utcnow().isoformat()
            }
            user_container.create_item(body=profile_doc)
        
        return {
            "message": "Profile saved successfully",
            "registration_code": registration_code,
            "profile": profile_data
        }
        
    except Exception as e:
        print(f"Error saving patient profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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

@router.post("/admin/send-reminder")
async def send_reminder(
    reminder_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Send a reminder notification to a patient"""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Create notification record
        notification = {
            "id": f"reminder_{reminder_data['patient_id']}_{int(datetime.now().timestamp())}",
            "type": "notification",
            "notification_type": "reminder",
            "patient_id": reminder_data["patient_id"],
            "patient_name": reminder_data["patient_name"],
            "message": reminder_data["message"],
            "priority": reminder_data.get("priority", "medium"),
            "created_at": datetime.now().isoformat(),
            "expires_at": reminder_data.get("expires_at", (datetime.now() + timedelta(days=14)).isoformat()),
            "read": False,
            "sent_by": current_user.get("email", "admin"),
            "created_by": "admin_system"
        }
        
        # Store notification in database
        interactions_container.create_item(body=notification)
        
        print(f"[REMINDER_SENT] Notification sent to patient {reminder_data['patient_id']}: {reminder_data['message']}")
        
        return JSONResponse(content={
            "status": "success",
            "message": f"Reminder sent successfully to {reminder_data['patient_name']}",
            "notification_id": notification["id"]
        })
        
    except Exception as e:
        print(f"[REMINDER_ERROR] Failed to send reminder: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send reminder: {str(e)}")

@router.get("/admin/patient-profile/{patient_id}")
async def get_patient_profile_by_id(
    patient_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed patient profile information"""
    # URL decode the patient_id in case it contains encoded characters like %40 for @
    import urllib.parse
    decoded_patient_id = urllib.parse.unquote(patient_id)
    
    print(f"[PATIENT_PROFILE] Request for patient_id: {patient_id}")
    print(f"[PATIENT_PROFILE] Decoded patient_id: {decoded_patient_id}")
    print(f"[PATIENT_PROFILE] Current user: {current_user.get('email', 'Unknown')}")
    
    if not current_user.get("is_admin"):
        print(f"[PATIENT_PROFILE] Access denied - user is not admin")
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Debug: Let's see what users actually exist in the database
        all_users_query = "SELECT c.id, c.email, c.profile FROM c WHERE c.type = 'user'"
        all_users = list(user_container.query_items(query=all_users_query, enable_cross_partition_query=True))
        print(f"[PATIENT_PROFILE] Total users in database: {len(all_users)}")
        print(f"[PATIENT_PROFILE] Sample user IDs: {[user.get('id', 'No ID')[:50] for user in all_users[:5]]}")
        
        # Get patient from users collection using the decoded ID
        user_query = f"SELECT * FROM c WHERE c.type = 'user' AND c.id = '{decoded_patient_id}'"
        print(f"[PATIENT_PROFILE] Executing query: {user_query}")
        
        users = list(user_container.query_items(query=user_query, enable_cross_partition_query=True))
        print(f"[PATIENT_PROFILE] Found {len(users)} users with decoded ID")
        
        if not users:
            print(f"[PATIENT_PROFILE] No user found with id: {decoded_patient_id}")
            
            # Try with email field instead of id
            email_query = f"SELECT * FROM c WHERE c.type = 'user' AND c.email = '{decoded_patient_id}'"
            print(f"[PATIENT_PROFILE] Trying with email field: {email_query}")
            users = list(user_container.query_items(query=email_query, enable_cross_partition_query=True))
            print(f"[PATIENT_PROFILE] Found {len(users)} users with email field")
            
            if not users:
                # Also try with the original encoded ID in case that's how it's stored
                user_query_encoded = f"SELECT * FROM c WHERE c.type = 'user' AND c.id = '{patient_id}'"
                print(f"[PATIENT_PROFILE] Trying with encoded ID: {user_query_encoded}")
                users = list(user_container.query_items(query=user_query_encoded, enable_cross_partition_query=True))
                print(f"[PATIENT_PROFILE] Found {len(users)} users with encoded ID")
                
                if not users:
                    # Try partial matching to see if there's a similar ID
                    partial_query = f"SELECT * FROM c WHERE c.type = 'user' AND CONTAINS(c.id, 'anka')"
                    partial_users = list(user_container.query_items(query=partial_query, enable_cross_partition_query=True))
                    print(f"[PATIENT_PROFILE] Found {len(partial_users)} users with partial match 'anka'")
                    if partial_users:
                        print(f"[PATIENT_PROFILE] Similar user IDs: {[user.get('id', 'No ID') for user in partial_users[:3]]}")
                    
                    raise HTTPException(status_code=404, detail=f"Patient not found. Searched for: {decoded_patient_id}, {patient_id}. Total users in DB: {len(all_users)}")
        
        user = users[0]
        print(f"[PATIENT_PROFILE] User found: {user.get('email', 'No email')}")
        
        # Use the decoded patient_id for all subsequent operations
        effective_patient_id = decoded_patient_id
        
        # Get additional engagement data using the effective patient ID
        consumption_query = f"SELECT * FROM c WHERE c.type = 'consumption_record' AND c.user_id = '{effective_patient_id}' ORDER BY c.timestamp DESC"
        print(f"[PATIENT_PROFILE] Consumption query: {consumption_query}")
        consumption_records = list(interactions_container.query_items(query=consumption_query, enable_cross_partition_query=True))
        print(f"[PATIENT_PROFILE] Found {len(consumption_records)} consumption records")
        
        # Calculate engagement metrics
        total_logs = len(consumption_records)
        last_log_date = None
        if consumption_records:
            try:
                last_log_date = datetime.fromisoformat(consumption_records[0].get("timestamp", "").replace('Z', '+00:00'))
            except:
                pass
        
        days_since_last = (datetime.now() - last_log_date).days if last_log_date else 999
        
        profile_data = {
            "patient_id": effective_patient_id,
            "patient_name": user.get("profile", {}).get("name", "Unknown"),
            "email": user.get("email", ""),
            "profile": {
                "email": user.get("email", ""),
                "phone": user.get("profile", {}).get("phone", ""),
                "age": user.get("profile", {}).get("age", ""),
                "diabetes_type": user.get("profile", {}).get("diabetes_type", ""),
                "created_at": user.get("created_at", ""),
                "last_login": user.get("last_login", ""),
            },
            "engagement": {
                "total_logs": total_logs,
                "days_since_last_log": days_since_last,
                "last_log_date": last_log_date.isoformat() if last_log_date else None,
                "registration_date": user.get("created_at", "")
            }
        }
        
        return JSONResponse(content=profile_data)
        
    except HTTPException as e:
        print(f"[PATIENT_PROFILE] HTTP Exception: {e.detail}")
        raise
    except Exception as e:
        print(f"[PATIENT_PROFILE] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get patient profile: {str(e)}")

@router.post("/admin/mark-contacted")
async def mark_patient_contacted(
    contact_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Mark a patient as contacted by admin"""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Create contact record
        contact_record = {
            "id": f"contact_{contact_data['patient_id']}_{int(datetime.now().timestamp())}",
            "type": "admin_contact",
            "patient_id": contact_data["patient_id"],
            "contacted_at": contact_data.get("contacted_at", datetime.now().isoformat()),
            "contacted_by": contact_data.get("contacted_by", current_user.get("email", "admin")),
            "contact_method": "admin_action",
            "notes": contact_data.get("notes", "Patient marked as contacted via admin panel"),
            "created_at": datetime.now().isoformat()
        }
        
        # Store contact record in database
        interactions_container.create_item(body=contact_record)
        
        print(f"[CONTACT_MARKED] Patient {contact_data['patient_id']} marked as contacted by {contact_record['contacted_by']}")
        
        return JSONResponse(content={
            "status": "success", 
            "message": "Patient marked as contacted successfully",
            "contact_record_id": contact_record["id"]
        })
        
    except Exception as e:
        print(f"[CONTACT_ERROR] Failed to mark patient as contacted: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to mark as contacted: {str(e)}")