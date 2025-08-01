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
        
        # Create email to name mapping for better readability
        email_to_name = {}
        for user in all_users:
            email = user.get("email")
            profile = user.get("profile", {})
            name = profile.get("name", "Unknown Patient")
            if email:
                email_to_name[email] = name if name else email
        
        # Identify users without consumption data
        users_with_consumption = set(user_consumption.keys())
        all_user_emails = {user.get("email") for user in all_users if user.get("email")}
        inactive_users = all_user_emails - users_with_consumption
        
        print(f"[NUTRIENT_ADEQUACY] Total registered users: {total_users_count}")
        print(f"[NUTRIENT_ADEQUACY] Inactive users (no consumption data): {len(inactive_users)}")
        if inactive_users:
            print(f"[NUTRIENT_ADEQUACY] Inactive user emails: {list(inactive_users)}")
        
        if active_users_count == 0:
            return {
                "cohort_size": active_users_count,
                "total_registered_patients": total_registered_patients,
                "total_registered_users": total_users_count,
                "inactive_patients_count": len(inactive_users),
                "inactive_patients": [{"user_id": email, "user_name": email_to_name.get(email, email)} for email in inactive_users],
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
        
        # Calculate percentages
        rda_compliance_percentages = {}
        for nutrient, counts in rda_compliance_counts.items():
            total = sum(counts.values())
            percentages = {}
            for category, count in counts.items():
                percentages[category] = {
                    "count": count,
                    "percentage": round((count / active_users_count) * 100, 1) if active_users_count > 0 else 0
                }
            rda_compliance_percentages[nutrient] = percentages
        
        # Calculate cohort averages
        cohort_averages = {}
        for nutrient, total in cohort_totals.items():
            cohort_averages[nutrient] = round(total / active_users_count, 1) if active_users_count > 0 else 0
        
        # Identify top deficiencies (sorted by prevalence)
        deficiency_rankings = [
            {
                "issue": "Low Fiber Intake",
                "affected_patients": cohort_deficiencies["low_fiber"],
                "percentage": round((cohort_deficiencies["low_fiber"] / active_users_count) * 100, 1),
                "severity": "high" if cohort_deficiencies["low_fiber"] / active_users_count > 0.7 else "medium",
                "recommendation": "Increase whole grains, fruits, and vegetables"
            },
            {
                "issue": "Excess Sodium",
                "affected_patients": cohort_deficiencies["excess_sodium"],
                "percentage": round((cohort_deficiencies["excess_sodium"] / active_users_count) * 100, 1),
                "severity": "high" if cohort_deficiencies["excess_sodium"] / active_users_count > 0.5 else "medium",
                "recommendation": "Reduce processed foods and restaurant meals"
            },
            {
                "issue": "Excess Sugar",
                "affected_patients": cohort_deficiencies["excess_sugar"],
                "percentage": round((cohort_deficiencies["excess_sugar"] / active_users_count) * 100, 1),
                "severity": "medium" if cohort_deficiencies["excess_sugar"] / active_users_count > 0.4 else "low",
                "recommendation": "Limit sugary beverages and desserts"
            },
            {
                "issue": "Low Protein",
                "affected_patients": cohort_deficiencies["low_protein"],
                "percentage": round((cohort_deficiencies["low_protein"] / active_users_count) * 100, 1),
                "severity": "medium" if cohort_deficiencies["low_protein"] / active_users_count > 0.3 else "low",
                "recommendation": "Include lean proteins at each meal"
            }
        ]
        
        # Sort by percentage (most prevalent first)
        deficiency_rankings.sort(key=lambda x: x["percentage"], reverse=True)
        
        return {
            "cohort_size": active_users_count,
            "total_registered_patients": total_registered_patients,
            "total_registered_users": total_users_count,
            "inactive_patients_count": len(inactive_users),
            "inactive_patients": [{"user_id": email, "user_name": email_to_name.get(email, email)} for email in inactive_users],
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
            name = profile.get("name", "Unknown Patient")
            if email:
                email_to_name[email] = name if name else email
        
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
                    engagement_level = "warning"
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
        engagement_priority = {"inactive": 0, "critical": 1, "warning": 2, "poor": 3, "good": 4, "excellent": 5}
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
            "poor": len([u for u in user_engagement_analysis if u["engagement_level"] == "poor"]),
            "warning": len([u for u in user_engagement_analysis if u["engagement_level"] == "warning"]),
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
                "warning_users": [{"user_id": u["user_id"], "user_name": u["user_name"]} for u in user_engagement_analysis if u["engagement_level"] == "warning"],
                "inactive_users": [{"user_id": u["user_id"], "user_name": u["user_name"]} for u in user_engagement_analysis if u["engagement_level"] == "inactive"]
            },
            "recommendations": {
                "immediate_followup": engagement_summary["critical"] + engagement_summary["inactive"],
                "needs_encouragement": engagement_summary["warning"] + engagement_summary["poor"],
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
        
        # Get all registered users (excluding admin) to map names
        all_users_query = "SELECT * FROM c WHERE c.type = 'user' AND c.is_admin != true"
        all_users = list(user_container.query_items(query=all_users_query, enable_cross_partition_query=True))
        total_users_count = len(all_users)
        
        # Create email to name mapping for better readability
        email_to_name = {}
        for user in all_users:
            email = user.get("email")
            profile = user.get("profile", {})
            name = profile.get("name", "Unknown Patient")
            if email:
                email_to_name[email] = name if name else email
        
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
        for record in all_consumption:
            user_id = record.get("user_id")
            timestamp = record.get("timestamp", "")
            nutrition = record.get("nutrition", {})
            
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
                    
            except Exception as date_error:
                print(f"[OUTLIER_DETECTION] Date parsing error: {date_error}")
                continue
        
        # Analyze for outliers
        extreme_calorie_outliers = []
        nutrient_spike_outliers = []
        daily_outliers = []
        outlier_users = set()
        
        for user_id, user_days in user_daily_totals.items():
            user_name = email_to_name.get(user_id, user_id)
            
            for date_key, daily_totals in user_days.items():
                outliers_found = []
                
                # Check for extreme calorie intake
                calories = daily_totals["calories"]
                calorie_severity = None
                
                if calories <= OUTLIER_THRESHOLDS["calories"]["extremely_low"]:
                    calorie_severity = "extremely_low"
                elif calories <= OUTLIER_THRESHOLDS["calories"]["very_low"]:
                    calorie_severity = "very_low"
                elif calories >= OUTLIER_THRESHOLDS["calories"]["extremely_high"]:
                    calorie_severity = "extremely_high"
                elif calories >= OUTLIER_THRESHOLDS["calories"]["very_high"]:
                    calorie_severity = "very_high"
                
                if calorie_severity:
                    calorie_outlier = {
                        "user_id": user_id,
                        "user_name": user_name,
                        "date": date_key,
                        "calories": round(calories, 1),
                        "severity": calorie_severity,
                        "threshold": OUTLIER_THRESHOLDS["calories"][calorie_severity],
                        "record_count": daily_totals["record_count"],
                        "medical_concern": get_calorie_medical_concern(calorie_severity, calories)
                    }
                    extreme_calorie_outliers.append(calorie_outlier)
                    outliers_found.append("extreme_calories")
                    outlier_users.add(user_id)
                
                # Check for nutrient spikes
                for nutrient in ["protein", "carbohydrates", "fat", "fiber", "sodium", "sugar"]:
                    nutrient_value = daily_totals[nutrient]
                    threshold_data = OUTLIER_THRESHOLDS[nutrient]
                    spike_threshold = threshold_data["rda"] * threshold_data["spike_multiplier"]
                    
                    if nutrient_value > spike_threshold:
                        spike_multiplier = nutrient_value / threshold_data["rda"]
                        spike_outlier = {
                            "user_id": user_id,
                            "user_name": user_name,
                            "date": date_key,
                            "nutrient": nutrient,
                            "value": round(nutrient_value, 1),
                            "rda": threshold_data["rda"],
                            "spike_multiplier": round(spike_multiplier, 1),
                            "threshold": round(spike_threshold, 1),
                            "severity": get_spike_severity(spike_multiplier),
                            "medical_concern": get_nutrient_medical_concern(nutrient, spike_multiplier),
                            "record_count": daily_totals["record_count"]
                        }
                        nutrient_spike_outliers.append(spike_outlier)
                        outliers_found.append(f"{nutrient}_spike")
                        outlier_users.add(user_id)
                
                # Record daily summary if any outliers found
                if outliers_found:
                    daily_outlier = {
                        "user_id": user_id,
                        "user_name": user_name,
                        "date": date_key,
                        "outlier_types": outliers_found,
                        "daily_totals": {
                            "calories": round(daily_totals["calories"], 1),
                            "protein": round(daily_totals["protein"], 1),
                            "carbohydrates": round(daily_totals["carbohydrates"], 1),
                            "fat": round(daily_totals["fat"], 1),
                            "fiber": round(daily_totals["fiber"], 1),
                            "sodium": round(daily_totals["sodium"], 1),
                            "sugar": round(daily_totals["sugar"], 1)
                        },
                        "record_count": daily_totals["record_count"]
                    }
                    daily_outliers.append(daily_outlier)
        
        # Sort outliers by severity/magnitude
        extreme_calorie_outliers.sort(key=lambda x: (
            {"extremely_high": 4, "very_high": 3, "extremely_low": 2, "very_low": 1}.get(x["severity"], 0),
            abs(x["calories"] - 2000)  # Distance from normal 2000 calorie baseline
        ), reverse=True)
        
        nutrient_spike_outliers.sort(key=lambda x: x["spike_multiplier"], reverse=True)
        
        # Calculate summary statistics
        total_outlier_users = len(outlier_users)
        extreme_calorie_days = len(extreme_calorie_outliers)
        nutrient_spike_days = len(nutrient_spike_outliers)
        
        # Find most common outlier type
        outlier_type_counts = defaultdict(int)
        for outlier in daily_outliers:
            for outlier_type in outlier["outlier_types"]:
                outlier_type_counts[outlier_type] += 1
        
        most_common_outlier = max(outlier_type_counts.items(), key=lambda x: x[1])[0] if outlier_type_counts else "None"
        
        return {
            "total_registered_patients": total_registered_patients,
            "total_registered_users": total_users_count,
            "analysis_period": {
                "days": days,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "total_records_analyzed": len(all_consumption)
            },
            "outliers": {
                "extreme_calorie_intake": extreme_calorie_outliers,
                "nutrient_spikes": nutrient_spike_outliers,
                "daily_outliers": daily_outliers
            },
            "summary": {
                "total_outlier_users": total_outlier_users,
                "extreme_calorie_days": extreme_calorie_days,
                "nutrient_spike_days": nutrient_spike_days,
                "most_common_outlier": most_common_outlier.replace("_", " ").title(),
                "outlier_user_names": [email_to_name.get(user_id, user_id) for user_id in outlier_users]
            },
            "thresholds": OUTLIER_THRESHOLDS,
            "recommendations": {
                "immediate_attention": [
                    f"{len([o for o in extreme_calorie_outliers if o['severity'] in ['extremely_low', 'extremely_high']])} days with dangerous calorie levels",
                    f"{len([o for o in nutrient_spike_outliers if o['spike_multiplier'] >= 4.0])} days with severe nutrient spikes",
                    f"{total_outlier_users} patients need dietary counseling"
                ],
                "monitoring_priorities": [
                    "Review meal planning for extreme calorie days",
                    "Investigate causes of nutrient spikes", 
                    "Consider medication or supplement adjustments",
                    "Schedule follow-up consultations"
                ]
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
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