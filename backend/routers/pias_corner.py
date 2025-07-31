"""
Pia's Corner Admin Analytics Router
Provides analytics dashboard functionality for administrators.
Requires admin authentication for all endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict
import json

from models import User
from routers.auth import get_current_user
from database import (
    get_all_patients, 
    get_user_consumption_history, 
    get_user_meal_plans, 
    get_consumption_analytics,
    get_patient_by_id,
    get_patient_by_registration_code,
    user_container
)
import random

router = APIRouter()

def generate_realistic_trend(baseline_value, patient_id, nutrient_type):
    """Generate realistic nutrient trend data over 8 weeks for a specific patient"""
    
    # Use patient_id hash as seed for consistent results per patient
    random.seed(hash(patient_id + nutrient_type))
    
    # Define trend patterns based on patient profile
    patient_hash = hash(patient_id)
    trend_type = patient_hash % 4  # 4 different trend patterns
    
    weeks = 8
    trend_data = []
    current_value = baseline_value
    
    if trend_type == 0:  # Improving patient - gradual increase
        for week in range(weeks):
            if week == 0:
                trend_data.append(round(current_value * 0.85, 1))  # Start lower
            else:
                # Gradual improvement with some weekly variation
                improvement = random.uniform(0.02, 0.08) * baseline_value
                weekly_noise = random.uniform(-0.03, 0.03) * baseline_value
                current_value = min(baseline_value * 1.1, current_value + improvement + weekly_noise)
                trend_data.append(round(max(0, current_value), 1))
    
    elif trend_type == 1:  # Declining patient - gradual decrease
        for week in range(weeks):
            if week == 0:
                trend_data.append(round(current_value * 1.15, 1))  # Start higher
            else:
                # Gradual decline with variation
                decline = random.uniform(0.01, 0.05) * baseline_value
                weekly_noise = random.uniform(-0.03, 0.03) * baseline_value
                current_value = max(baseline_value * 0.7, current_value - decline + weekly_noise)
                trend_data.append(round(max(0, current_value), 1))
    
    elif trend_type == 2:  # Stable patient with normal variation
        for week in range(weeks):
            # Stay around baseline with realistic weekly variation
            weekly_variation = random.uniform(-0.1, 0.1) * baseline_value
            current_value = baseline_value + weekly_variation
            trend_data.append(round(max(0, current_value), 1))
    
    else:  # Inconsistent patient - more erratic pattern
        for week in range(weeks):
            if week < 3:
                # Poor compliance early on
                variation = random.uniform(-0.2, 0.05) * baseline_value
            elif week < 6:
                # Improvement period
                variation = random.uniform(-0.05, 0.15) * baseline_value
            else:
                # Slight decline
                variation = random.uniform(-0.1, 0.05) * baseline_value
            
            current_value = baseline_value + variation
            trend_data.append(round(max(0, current_value), 1))
    
    return trend_data

def generate_cohort_average_trend(nutrient_type):
    """Generate realistic cohort average trend data over 8 weeks"""
    
    # Set seed for consistent cohort data
    random.seed(hash("cohort_" + nutrient_type))
    
    # Define baseline values for different nutrients (population averages)
    baselines = {
        "protein": 85,
        "fiber": 22,
        "vitamin_c": 72
    }
    
    baseline = baselines.get(nutrient_type, 50)
    weeks = 8
    trend_data = []
    
    # Generate cohort trend showing gradual improvement (typical intervention effect)
    for week in range(weeks):
        if week == 0:
            # Start slightly below baseline
            value = baseline * 0.92
        else:
            # Gradual improvement with some variation
            weekly_improvement = (week * 0.8)  # Gradual upward trend
            weekly_variation = random.uniform(-2, 2)  # Small random variation
            value = baseline * 0.92 + weekly_improvement + weekly_variation
        
        trend_data.append(round(max(0, value), 1))
    
    return trend_data

@router.get("/admin/analytics/patients-list")
async def get_patients_list(
    current_user: User = Depends(get_current_user)
):
    """Get list of patients for analytics dropdown"""
    # Check if user is admin
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Get real patient data from database
        patients_data = await get_all_patients()
        
        # Transform patient data to match frontend expectations
        patients_list = []
        for patient in patients_data:
            # Find associated user for last_active info
            last_active = patient.get("created_at", datetime.utcnow().isoformat())
            patient_registration_code = patient.get("registration_code") or patient.get("id")
            
            try:
                # Look for user with matching registration code to get last login
                user_query = f"SELECT * FROM c WHERE c.type = 'user' AND c.registration_code = '{patient_registration_code}'"
                users = list(user_container.query_items(query=user_query, enable_cross_partition_query=True))
                if users:
                    user = users[0]
                    last_active = user.get("last_login") or user.get("created_at") or last_active
            except Exception as user_error:
                print(f"[get_patients_list] Error finding user for patient {patient_registration_code}: {str(user_error)}")
            
            # Map database fields to frontend format
            patient_info = {
                "id": patient.get("id") or patient.get("registration_code"),
                "name": patient.get("name", "Unknown Patient"),
                "registration_code": patient.get("registration_code", patient.get("id")),
                "created_at": patient.get("created_at", datetime.utcnow().isoformat()),
                "condition": patient.get("condition", "Unknown Condition"),
                "last_active": last_active
            }
            patients_list.append(patient_info)
        
        # Sort by creation date, newest first
        patients_list.sort(key=lambda x: x["created_at"], reverse=True)
        
        print(f"[get_patients_list] Returning {len(patients_list)} patients")
        return JSONResponse(content={"patients": patients_list})
        
    except Exception as e:
        print(f"[get_patients_list] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/analytics/overview")
async def get_analytics_overview(
    patient_id: str = None,
    current_user: User = Depends(get_current_user)
):
    """Get analytics overview data for dashboard"""
    # Check if user is admin
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        if patient_id:
            # Individual patient analytics - get real data
            try:
                # Get patient information - patient_id might be registration code
                patient = await get_patient_by_id(patient_id)
                if not patient:
                    # Try by registration code
                    patient = await get_patient_by_registration_code(patient_id)
                    if not patient:
                        raise HTTPException(status_code=404, detail="Patient not found")
                
                # Find the user account for this patient to get email
                # Patient records don't have email, but user records do
                patient_email = None
                try:
                    # Look for user with matching patient_id or registration_code
                    user_query = f"SELECT * FROM c WHERE c.type = 'user' AND (c.patient_id = '{patient_id}' OR c.registration_code = '{patient_id}' OR c.registration_code = '{patient.get('registration_code', '')}')"
                    users = list(user_container.query_items(query=user_query, enable_cross_partition_query=True))
                    if users:
                        patient_email = users[0].get("email")
                        print(f"[get_analytics_overview] Found user email: {patient_email} for patient: {patient_id}")
                    else:
                        print(f"[get_analytics_overview] No user found for patient: {patient_id}")
                except Exception as user_error:
                    print(f"[get_analytics_overview] Error finding user for patient {patient_id}: {str(user_error)}")
                
                if not patient_email:
                    # If no user account found, return basic patient info without consumption data
                    print(f"[get_analytics_overview] No user account found for patient {patient_id}, returning basic info")
                    basic_patient_data = {
                        "patient_info": {
                            "id": patient_id,
                            "name": patient.get("name", "Unknown Patient"),
                            "condition": patient.get("condition", "Unknown Condition"),
                            "age": patient.get("age", 0),
                            "registration_date": patient.get("created_at", "")[:10] if patient.get("created_at") else ""
                        },
                        "metrics": {"total_meal_plans": 0, "completed_meal_plans": 0, "compliance_rate": 0, "avg_glucose_level": 0, "weight_change": 0, "last_login": "No user account"},
                        "weekly_trends": {"glucose_improvement": "0%", "weight_trend": "0kg", "compliance_trend": "0%", "activity_increase": "0%"},
                        "monthly_summary": {"avg_glucose": 0, "total_activities": 0, "meal_plans_completed": 0, "coaching_sessions": 0},
                        "recent_activity": [],
                        "glucose_trends": {"labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], "data": [0, 0, 0, 0, 0, 0, 0]},
                        "weight_progression": [0],
                        "meal_compliance": {"breakfast": 0, "lunch": 0, "dinner": 0, "snacks": 0}
                    }
                    return JSONResponse(content=basic_patient_data)
                
                # Get real consumption and meal plan data
                consumption_history = await get_user_consumption_history(patient_email, limit=100)
                meal_plans = await get_user_meal_plans(patient_email)
                consumption_analytics = await get_consumption_analytics(patient_email, days=30)
                
                # Process real data
                total_meal_plans = len(meal_plans)
                
                # Calculate completed meal plans based on consumption data
                # Consider a meal plan "completed" if there are consumption records for that day
                meal_plan_dates = set()
                for plan in meal_plans:
                    created_date = plan.get("created_at", "")[:10]  # Get date part
                    meal_plan_dates.add(created_date)
                
                consumption_dates = set()
                for record in consumption_history:
                    record_date = record.get("timestamp", "")[:10]  # Get date part
                    consumption_dates.add(record_date)
                
                completed_meal_plans = len(meal_plan_dates.intersection(consumption_dates))
                compliance_rate = (completed_meal_plans / total_meal_plans * 100) if total_meal_plans > 0 else 0
                
                # Extract glucose levels from consumption records
                glucose_readings = []
                weight_readings = []
                recent_activities = []
                
                for record in consumption_history[:30]:  # Last 30 records
                    nutritional_info = record.get("nutritional_info", {})
                    if isinstance(nutritional_info, str):
                        try:
                            nutritional_info = json.loads(nutritional_info)
                        except:
                            nutritional_info = {}
                    
                    # Extract glucose if available
                    glucose = nutritional_info.get("glucose_reading") or nutritional_info.get("blood_glucose")
                    if glucose and isinstance(glucose, (int, float)):
                        glucose_readings.append(glucose)
                    
                    # Extract weight if available
                    weight = nutritional_info.get("weight")
                    if weight and isinstance(weight, (int, float)):
                        weight_readings.append(weight)
                    
                    # Create recent activity entry
                    activity = {
                        "date": record.get("timestamp", "")[:10],
                        "action": f"Logged {record.get('food_name', 'food item')}",
                        "meal_type": record.get("meal_type", "unknown")
                    }
                    if glucose:
                        activity["glucose_reading"] = glucose
                    recent_activities.append(activity)
                
                # Calculate averages
                avg_glucose = sum(glucose_readings) / len(glucose_readings) if glucose_readings else 0
                weight_change = weight_readings[-1] - weight_readings[0] if len(weight_readings) >= 2 else 0
                
                # Generate weekly glucose trends (last 7 days with data)
                daily_glucose = defaultdict(list)
                for record in consumption_history:
                    record_date = record.get("timestamp", "")[:10]
                    nutritional_info = record.get("nutritional_info", {})
                    if isinstance(nutritional_info, str):
                        try:
                            nutritional_info = json.loads(nutritional_info)
                        except:
                            nutritional_info = {}
                    
                    glucose = nutritional_info.get("glucose_reading") or nutritional_info.get("blood_glucose")
                    if glucose and isinstance(glucose, (int, float)):
                        daily_glucose[record_date].append(glucose)
                
                # Get last 7 days with data
                glucose_trend_data = []
                glucose_trend_labels = []
                sorted_dates = sorted(daily_glucose.keys())[-7:]
                
                for date in sorted_dates:
                    avg_daily_glucose = sum(daily_glucose[date]) / len(daily_glucose[date])
                    glucose_trend_data.append(round(avg_daily_glucose, 1))
                    # Convert date to day name
                    try:
                        day_name = datetime.fromisoformat(date).strftime("%a")
                        glucose_trend_labels.append(day_name)
                    except:
                        glucose_trend_labels.append(date[-2:])  # Last 2 digits of date
                
                # Calculate meal compliance by meal type
                meal_type_counts = defaultdict(int)
                total_possible_meals = total_meal_plans * 4  # Assuming 4 meal types per plan
                
                for record in consumption_history:
                    meal_type = record.get("meal_type", "").lower()
                    if meal_type in ["breakfast", "lunch", "dinner", "snack"]:
                        meal_type_counts[meal_type] += 1
                
                meal_compliance = {
                    "breakfast": min(100, (meal_type_counts["breakfast"] / max(1, total_meal_plans)) * 100),
                    "lunch": min(100, (meal_type_counts["lunch"] / max(1, total_meal_plans)) * 100),
                    "dinner": min(100, (meal_type_counts["dinner"] / max(1, total_meal_plans)) * 100),
                    "snacks": min(100, (meal_type_counts["snack"] / max(1, total_meal_plans)) * 100)
                }
                
                # Build response with real data
                individual_data = {
                    "patient_info": {
                        "id": patient_id,
                        "name": patient.get("name", "Unknown Patient"),
                        "condition": patient.get("condition", "Unknown Condition"),
                        "age": patient.get("age", 0),
                        "registration_date": patient.get("created_at", "")[:10]
                    },
                    "metrics": {
                        "total_meal_plans": total_meal_plans,
                        "completed_meal_plans": completed_meal_plans,
                        "compliance_rate": round(compliance_rate, 1),
                        "avg_glucose_level": round(avg_glucose, 1) if avg_glucose > 0 else 0,
                        "weight_change": round(weight_change, 1),
                        "last_login": patient.get("last_login") or patient.get("created_at", "")
                    },
                    "weekly_trends": {
                        "glucose_improvement": f"{'+' if avg_glucose < 150 else '-'}{abs(round((150 - avg_glucose) / 150 * 100, 1))}%" if avg_glucose > 0 else "0%",
                        "weight_trend": f"{'+' if weight_change > 0 else ''}{weight_change}kg" if weight_change != 0 else "0kg",
                        "compliance_trend": f"{'+' if compliance_rate > 75 else ''}{round(compliance_rate - 75, 1)}%",
                        "activity_increase": f"+{len(consumption_history)}%"
                    },
                    "monthly_summary": {
                        "avg_glucose": round(avg_glucose, 1) if avg_glucose > 0 else 0,
                        "total_activities": len(consumption_history),
                        "meal_plans_completed": completed_meal_plans,
                        "coaching_sessions": 0  # Would need separate tracking
                    },
                    "recent_activity": recent_activities[:10],  # Last 10 activities
                    "glucose_trends": {
                        "labels": glucose_trend_labels or ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                        "data": glucose_trend_data or [0, 0, 0, 0, 0, 0, 0]
                    },
                    "weight_progression": weight_readings[-6:] if len(weight_readings) >= 6 else weight_readings or [0],
                    "meal_compliance": {
                        "breakfast": round(meal_compliance["breakfast"], 1),
                        "lunch": round(meal_compliance["lunch"], 1),
                        "dinner": round(meal_compliance["dinner"], 1),
                        "snacks": round(meal_compliance["snacks"], 1)
                    }
                }
                
                print(f"[get_analytics_overview] Individual analytics for patient {patient_id}: {total_meal_plans} meal plans, {len(consumption_history)} consumption records")
                return JSONResponse(content=individual_data)
                
            except HTTPException:
                raise
            except Exception as e:
                print(f"[get_analytics_overview] Error processing individual patient data: {str(e)}")
                # Return basic structure with empty data if processing fails
                basic_data = {
                    "patient_info": {"id": patient_id, "name": "Patient", "condition": "Unknown", "age": 0, "registration_date": ""},
                    "metrics": {"total_meal_plans": 0, "completed_meal_plans": 0, "compliance_rate": 0, "avg_glucose_level": 0, "weight_change": 0, "last_login": ""},
                    "weekly_trends": {"glucose_improvement": "0%", "weight_trend": "0kg", "compliance_trend": "0%", "activity_increase": "0%"},
                    "monthly_summary": {"avg_glucose": 0, "total_activities": 0, "meal_plans_completed": 0, "coaching_sessions": 0},
                    "recent_activity": [],
                    "glucose_trends": {"labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], "data": [0, 0, 0, 0, 0, 0, 0]},
                    "weight_progression": [0],
                    "meal_compliance": {"breakfast": 0, "lunch": 0, "dinner": 0, "snacks": 0}
                }
                return JSONResponse(content=basic_data)
        else:
            # Cohort analytics - aggregate real data from all patients
            try:
                # Get all patients
                all_patients = await get_all_patients()
                total_patients = len(all_patients)
                
                if total_patients == 0:
                    # Return empty cohort data if no patients
                    empty_cohort_data = {
                        "summary": {"total_patients": 0, "active_patients": 0, "new_registrations_this_month": 0, "avg_compliance_rate": 0, "total_meal_plans_generated": 0, "avg_glucose_improvement": 0},
                        "demographics": {"type_1_diabetes": 0, "type_2_diabetes": 0, "prediabetes": 0},
                        "engagement_metrics": {"daily_active_users": 0, "weekly_active_users": 0, "monthly_active_users": 0, "avg_session_duration": "0 minutes"},
                        "trends": {"registration_trends": {"labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], "data": [0]*12}, "compliance_trends": {"labels": ["Week 1", "Week 2", "Week 3", "Week 4"], "data": [0]*4}},
                        "top_performing_patients": [],
                        "patient_compliance_distribution": []
                    }
                    return JSONResponse(content=empty_cohort_data)
                
                # Aggregate data from all patients
                total_meal_plans = 0
                total_consumption_records = 0
                condition_counts = defaultdict(int)
                active_patients = 0
                new_registrations_this_month = 0
                all_glucose_readings = []
                patient_compliance_rates = []
                patient_compliance_distribution = []
                top_performers = []
                
                # Calculate current month threshold
                current_date = datetime.utcnow()
                month_start = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                
                # Process each patient
                for patient in all_patients:
                    # Count demographics first (always count all patients)
                    condition = patient.get("condition", "Unknown").lower()
                    if "type 1" in condition or "type1" in condition:
                        condition_counts["type_1_diabetes"] += 1
                    elif "type 2" in condition or "type2" in condition:
                        condition_counts["type_2_diabetes"] += 1
                    elif "prediabetes" in condition or "pre-diabetes" in condition:
                        condition_counts["prediabetes"] += 1
                    else:
                        condition_counts["type_2_diabetes"] += 1  # Default assumption
                    
                    # Find the user account for this patient to get email for consumption data
                    patient_email = None
                    patient_registration_code = patient.get("registration_code") or patient.get("id")
                    
                    try:
                        # Look for user with matching registration code
                        user_query = f"SELECT * FROM c WHERE c.type = 'user' AND c.registration_code = '{patient_registration_code}'"
                        users = list(user_container.query_items(query=user_query, enable_cross_partition_query=True))
                        if users:
                            patient_email = users[0].get("email")
                    except Exception as user_error:
                        print(f"[cohort_analytics] Error finding user for patient {patient_registration_code}: {str(user_error)}")
                    
                    if not patient_email:
                        print(f"[cohort_analytics] No user account found for patient {patient_registration_code}, skipping consumption data")
                        # Still count the patient in demographics but skip consumption analysis
                        continue
                    
                    # Check if patient registered this month
                    try:
                        created_at = patient.get("created_at", "")
                        if created_at:
                            patient_created = datetime.fromisoformat(created_at.replace('Z', ''))
                            if patient_created >= month_start:
                                new_registrations_this_month += 1
                    except:
                        pass
                    
                    try:
                        # Get patient's meal plans and consumption data
                        patient_meal_plans = await get_user_meal_plans(patient_email)
                        patient_consumption = await get_user_consumption_history(patient_email, limit=50)
                        
                        total_meal_plans += len(patient_meal_plans)
                        total_consumption_records += len(patient_consumption)
                        
                        # Check if patient is active (has consumption records in last 30 days)
                        thirty_days_ago = (current_date - timedelta(days=30)).isoformat()
                        has_recent_activity = any(
                            record.get("timestamp", "") > thirty_days_ago 
                            for record in patient_consumption
                        )
                        if has_recent_activity:
                            active_patients += 1
                        
                        # Calculate patient compliance
                        if len(patient_meal_plans) > 0:
                            meal_plan_dates = set(plan.get("created_at", "")[:10] for plan in patient_meal_plans)
                            consumption_dates = set(record.get("timestamp", "")[:10] for record in patient_consumption)
                            completed_plans = len(meal_plan_dates.intersection(consumption_dates))
                            compliance_rate = (completed_plans / len(patient_meal_plans)) * 100
                            patient_compliance_rates.append(compliance_rate)
                            
                            # Add to patient compliance distribution for visualization
                            patient_compliance_distribution.append({
                                "name": patient.get("name", "Unknown Patient"),
                                "compliance_rate": round(compliance_rate, 1),
                                "total_plans": len(patient_meal_plans),
                                "completed_plans": completed_plans,
                                "patient_id": patient_registration_code  # For potential patient selection
                            })
                            
                            # Extract glucose readings for this patient
                            patient_glucose = []
                            for record in patient_consumption:
                                nutritional_info = record.get("nutritional_info", {})
                                if isinstance(nutritional_info, str):
                                    try:
                                        nutritional_info = json.loads(nutritional_info)
                                    except:
                                        nutritional_info = {}
                                
                                glucose = nutritional_info.get("glucose_reading") or nutritional_info.get("blood_glucose")
                                if glucose and isinstance(glucose, (int, float)):
                                    patient_glucose.append(glucose)
                                    all_glucose_readings.append(glucose)
                            
                            # Calculate glucose improvement (baseline 150 mg/dL)
                            if patient_glucose:
                                avg_patient_glucose = sum(patient_glucose) / len(patient_glucose)
                                glucose_improvement = max(0, (150 - avg_patient_glucose) / 150 * 100)
                                
                                # Add to top performers list
                                top_performers.append({
                                    "name": patient.get("name", "Unknown Patient"),
                                    "compliance_rate": round(compliance_rate, 1),
                                    "glucose_improvement": round(glucose_improvement, 1)
                                })
                        else:
                            # Patient has no meal plans, add to distribution with 0% compliance
                            patient_compliance_distribution.append({
                                "name": patient.get("name", "Unknown Patient"),
                                "compliance_rate": 0,
                                "total_plans": 0,
                                "completed_plans": 0,
                                "patient_id": patient_registration_code
                            })
                    
                    except Exception as e:
                        print(f"[cohort_analytics] Error processing patient {patient_email}: {str(e)}")
                        continue
                
                # Calculate averages
                avg_compliance_rate = sum(patient_compliance_rates) / len(patient_compliance_rates) if patient_compliance_rates else 0
                avg_glucose_improvement = 0
                if all_glucose_readings:
                    avg_glucose = sum(all_glucose_readings) / len(all_glucose_readings)
                    avg_glucose_improvement = max(0, (150 - avg_glucose) / 150 * 100)
                
                # Sort top performers by compliance rate and take top 3
                top_performers.sort(key=lambda x: x["compliance_rate"], reverse=True)
                top_performers = top_performers[:3]
                
                # Generate monthly registration trends (mock data for now since we'd need historical tracking)
                # In a real implementation, you'd aggregate registration data by month
                registration_trend_data = [0] * 12
                registration_trend_data[current_date.month - 1] = new_registrations_this_month
                
                # Generate weekly compliance trends (last 4 weeks)
                compliance_trend_data = []
                for week in range(4):
                    week_start = current_date - timedelta(weeks=week+1)
                    week_end = current_date - timedelta(weeks=week)
                    
                    # This is simplified - in practice you'd need to track compliance by week
                    week_compliance = avg_compliance_rate + (week * 2)  # Slight trend
                    compliance_trend_data.insert(0, round(max(0, min(100, week_compliance)), 1))
                
                # Build cohort response
                cohort_data = {
                    "summary": {
                        "total_patients": total_patients,
                        "active_patients": active_patients,
                        "new_registrations_this_month": new_registrations_this_month,
                        "avg_compliance_rate": round(avg_compliance_rate, 1),
                        "total_meal_plans_generated": total_meal_plans,
                        "avg_glucose_improvement": round(avg_glucose_improvement, 1)
                    },
                    "demographics": {
                        "type_1_diabetes": condition_counts["type_1_diabetes"],
                        "type_2_diabetes": condition_counts["type_2_diabetes"],
                        "prediabetes": condition_counts["prediabetes"]
                    },
                    "engagement_metrics": {
                        "daily_active_users": max(1, active_patients // 3),  # Rough estimate
                        "weekly_active_users": max(1, active_patients // 2),  # Rough estimate
                        "monthly_active_users": active_patients,
                        "avg_session_duration": f"{round(total_consumption_records / max(1, active_patients) * 2.5, 1)} minutes"  # Rough estimate
                    },
                    "trends": {
                        "registration_trends": {
                            "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                            "data": registration_trend_data
                        },
                        "compliance_trends": {
                            "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
                            "data": compliance_trend_data
                        }
                    },
                    "top_performing_patients": top_performers,
                    "patient_compliance_distribution": patient_compliance_distribution
                }
                
                print(f"[get_analytics_overview] Cohort analytics: {total_patients} patients, {active_patients} active, {total_meal_plans} total meal plans")
                return JSONResponse(content=cohort_data)
                
            except Exception as e:
                print(f"[get_analytics_overview] Error processing cohort data: {str(e)}")
                # Return basic cohort structure if processing fails
                basic_cohort_data = {
                    "summary": {"total_patients": 0, "active_patients": 0, "new_registrations_this_month": 0, "avg_compliance_rate": 0, "total_meal_plans_generated": 0, "avg_glucose_improvement": 0},
                    "demographics": {"type_1_diabetes": 0, "type_2_diabetes": 0, "prediabetes": 0},
                    "engagement_metrics": {"daily_active_users": 0, "weekly_active_users": 0, "monthly_active_users": 0, "avg_session_duration": "0 minutes"},
                    "trends": {"registration_trends": {"labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], "data": [0]*12}, "compliance_trends": {"labels": ["Week 1", "Week 2", "Week 3", "Week 4"], "data": [0]*4}},
                    "top_performing_patients": [],
                    "patient_compliance_distribution": []
                }
                return JSONResponse(content=basic_cohort_data)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/analytics/nutrient-adequacy")
async def get_nutrient_adequacy_analytics(
    patient_id: str = None,
    current_user: User = Depends(get_current_user)
):
    """Get nutrient adequacy analytics for individual patient or cohort"""
    # Check if user is admin
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        if patient_id:
            # Individual patient nutrient analysis - show actual vs target intake
            # Simulate different patient data based on patient_id
            patient_variations = {
                "patient_001": {
                    "name": "John Doe",
                    "protein_intake": 95, "protein_target": 120,
                    "fiber_intake": 18, "fiber_target": 25,
                    "vitamin_d_intake": 8, "vitamin_d_target": 20,
                    "calcium_intake": 850, "calcium_target": 1000,
                    "iron_intake": 14, "iron_target": 18,
                    "vitamin_c_intake": 78, "vitamin_c_target": 90,
                    "folate_intake": 320, "folate_target": 400,
                    "magnesium_intake": 285, "magnesium_target": 420,
                    "compliance_pattern": [
                        [0.9, 0.85, 0.95, 0.88, 0.82, 0.75, 0.8],
                        [0.92, 0.87, 0.93, 0.85, 0.79, 0.78, 0.82],
                        [0.88, 0.91, 0.96, 0.90, 0.84, 0.73, 0.79],
                        [0.94, 0.89, 0.98, 0.92, 0.86, 0.71, 0.77]
                    ]
                },
                "patient_002": {
                    "name": "Sarah Wilson",
                    "protein_intake": 125, "protein_target": 120,  # Exceeding protein
                    "fiber_intake": 28, "fiber_target": 25,
                    "vitamin_d_intake": 22, "vitamin_d_target": 20,
                    "calcium_intake": 1100, "calcium_target": 1000,
                    "iron_intake": 19, "iron_target": 18,
                    "vitamin_c_intake": 95, "vitamin_c_target": 90,
                    "folate_intake": 420, "folate_target": 400,
                    "magnesium_intake": 450, "magnesium_target": 420,
                    "compliance_pattern": [
                        [0.95, 0.92, 0.98, 0.94, 0.89, 0.85, 0.91],
                        [0.97, 0.94, 0.99, 0.91, 0.88, 0.87, 0.93],
                        [0.93, 0.96, 0.98, 0.95, 0.92, 0.84, 0.89],
                        [0.96, 0.93, 0.99, 0.97, 0.90, 0.86, 0.92]
                    ]
                },
                "patient_003": {
                    "name": "Mike Johnson",
                    "protein_intake": 65, "protein_target": 120,  # Low protein
                    "fiber_intake": 12, "fiber_target": 25,
                    "vitamin_d_intake": 5, "vitamin_d_target": 20,
                    "calcium_intake": 600, "calcium_target": 1000,
                    "iron_intake": 10, "iron_target": 18,
                    "vitamin_c_intake": 45, "vitamin_c_target": 90,
                    "folate_intake": 250, "folate_target": 400,
                    "magnesium_intake": 200, "magnesium_target": 420,
                    "compliance_pattern": [
                        [0.65, 0.58, 0.72, 0.69, 0.55, 0.48, 0.62],
                        [0.68, 0.61, 0.75, 0.66, 0.52, 0.51, 0.64],
                        [0.71, 0.64, 0.68, 0.73, 0.57, 0.49, 0.67],
                        [0.69, 0.66, 0.71, 0.70, 0.59, 0.46, 0.63]
                    ]
                },
                "default": {
                    "name": "Selected Patient",
                    "protein_intake": 110, "protein_target": 120,
                    "fiber_intake": 22, "fiber_target": 25,
                    "vitamin_d_intake": 12, "vitamin_d_target": 20,
                    "calcium_intake": 750, "calcium_target": 1000,
                    "iron_intake": 16, "iron_target": 18,
                    "vitamin_c_intake": 85, "vitamin_c_target": 90,
                    "folate_intake": 380, "folate_target": 400,
                    "magnesium_intake": 320, "magnesium_target": 420,
                    "compliance_pattern": [
                        [0.85, 0.78, 0.92, 0.89, 0.76, 0.68, 0.75],
                        [0.88, 0.81, 0.95, 0.87, 0.73, 0.71, 0.79],
                        [0.91, 0.84, 0.88, 0.93, 0.77, 0.69, 0.82],
                        [0.89, 0.86, 0.91, 0.90, 0.79, 0.66, 0.78]
                    ]
                }
            }
            
            # Map real patient IDs to test variations for demo purposes
            # In production, this would be replaced with actual patient data from database
            patient_mapping = {
                "patient_001": "patient_001",
                "patient_002": "patient_002", 
                "patient_003": "patient_003"
            }
            
            # For any other patient ID, cycle through the variations
            if patient_id not in patient_mapping:
                variations_list = ["patient_001", "patient_002", "patient_003"]
                # Use hash of patient_id to consistently assign to a variation
                variation_index = hash(patient_id) % len(variations_list)
                mapped_variation = variations_list[variation_index]
                patient_mapping[patient_id] = mapped_variation
            
            variation_key = patient_mapping.get(patient_id, "default")
            patient_data = patient_variations.get(variation_key, patient_variations["default"])
            
            # Update name to include the actual patient ID for clarity
            if variation_key != "default":
                original_name = patient_data["name"]
                patient_data = patient_data.copy()
                patient_data["name"] = f"{original_name} (ID: {patient_id})"
            
            print(f"[get_nutrient_adequacy_analytics] Individual patient analysis for patient_id: {patient_id}, mapped to variation: {variation_key}, using data for: {patient_data['name']}")
            
            # Calculate RDA achievement as actual vs target percentages for this patient
            rda_achievement = {
                "protein": min(100, round((patient_data["protein_intake"] / patient_data["protein_target"]) * 100, 1)),
                "fiber": min(100, round((patient_data["fiber_intake"] / patient_data["fiber_target"]) * 100, 1)),
                "vitamin_d": min(100, round((patient_data["vitamin_d_intake"] / patient_data["vitamin_d_target"]) * 100, 1)),
                "calcium": min(100, round((patient_data["calcium_intake"] / patient_data["calcium_target"]) * 100, 1)),
                "iron": min(100, round((patient_data["iron_intake"] / patient_data["iron_target"]) * 100, 1)),
                "vitamin_c": min(100, round((patient_data["vitamin_c_intake"] / patient_data["vitamin_c_target"]) * 100, 1)),
                "folate": min(100, round((patient_data["folate_intake"] / patient_data["folate_target"]) * 100, 1)),
                "magnesium": min(100, round((patient_data["magnesium_intake"] / patient_data["magnesium_target"]) * 100, 1))
            }
            
            # Individual patient deficiencies (not percentages of patients, but actual deficits)
            deficiencies = []
            nutrients = [
                ("Protein", patient_data["protein_intake"], patient_data["protein_target"], "g"),
                ("Fiber", patient_data["fiber_intake"], patient_data["fiber_target"], "g"),
                ("Vitamin D", patient_data["vitamin_d_intake"], patient_data["vitamin_d_target"], "μg"),
                ("Calcium", patient_data["calcium_intake"], patient_data["calcium_target"], "mg"),
                ("Iron", patient_data["iron_intake"], patient_data["iron_target"], "mg"),
                ("Vitamin C", patient_data["vitamin_c_intake"], patient_data["vitamin_c_target"], "mg"),
                ("Folate", patient_data["folate_intake"], patient_data["folate_target"], "μg"),
                ("Magnesium", patient_data["magnesium_intake"], patient_data["magnesium_target"], "mg")
            ]
            
            for name, intake, target, unit in nutrients:
                if intake < target:
                    deficit = target - intake
                    deficit_percentage = round(((target - intake) / target) * 100, 1)
                    severity = "severe" if deficit_percentage > 40 else "moderate" if deficit_percentage > 20 else "mild"
                    deficiencies.append({
                        "name": f"Low {name}",
                        "deficit": f"{deficit:.1f} {unit}",
                        "deficit_percentage": deficit_percentage,
                        "current_intake": f"{intake:.1f} {unit}",
                        "target_intake": f"{target:.1f} {unit}",
                        "severity": severity
                    })
            
            # Sort by deficit percentage and take top 5
            deficiencies.sort(key=lambda x: x["deficit_percentage"], reverse=True)
            top_deficiencies = deficiencies[:5]
            
            mock_individual_nutrients = {
                "patient_info": {
                    "id": patient_id,
                    "name": patient_data["name"]
                },
                "mode": "individual",  # Flag to help frontend distinguish
                # For individual patients: show actual intake vs target achievement
                "rda_achievement": rda_achievement,
                "nutrient_details": {
                    "protein": {"intake": patient_data["protein_intake"], "target": patient_data["protein_target"], "unit": "g"},
                    "fiber": {"intake": patient_data["fiber_intake"], "target": patient_data["fiber_target"], "unit": "g"},
                    "vitamin_d": {"intake": patient_data["vitamin_d_intake"], "target": patient_data["vitamin_d_target"], "unit": "μg"},
                    "calcium": {"intake": patient_data["calcium_intake"], "target": patient_data["calcium_target"], "unit": "mg"},
                    "iron": {"intake": patient_data["iron_intake"], "target": patient_data["iron_target"], "unit": "mg"},
                    "vitamin_c": {"intake": patient_data["vitamin_c_intake"], "target": patient_data["vitamin_c_target"], "unit": "mg"},
                    "folate": {"intake": patient_data["folate_intake"], "target": patient_data["folate_target"], "unit": "μg"},
                    "magnesium": {"intake": patient_data["magnesium_intake"], "target": patient_data["magnesium_target"], "unit": "mg"}
                },
                "top_deficiencies": top_deficiencies,
                "daily_compliance_heatmap": patient_data["compliance_pattern"],
                # Chart-ready data formats based on this patient's actual data
                "macronutrients": [25, 45, 30],  # For pie chart [Protein, Carbs, Fats]
                "targets": [
                    patient_data["protein_target"], patient_data["fiber_target"], patient_data["vitamin_d_target"], 
                    patient_data["calcium_target"], patient_data["iron_target"], patient_data["vitamin_c_target"]
                ],
                "achieved": [
                    patient_data["protein_intake"], patient_data["fiber_intake"], patient_data["vitamin_d_intake"], 
                    patient_data["calcium_intake"], patient_data["iron_intake"], patient_data["vitamin_c_intake"]
                ],
                "trendLabels": ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6', 'Week 7', 'Week 8'],
                # Generate realistic trends based on patient profile
                "proteinTrend": generate_realistic_trend(patient_data["protein_intake"], patient_id, "protein"),
                "fiberTrend": generate_realistic_trend(patient_data["fiber_intake"], patient_id, "fiber"),
                "vitaminCTrend": generate_realistic_trend(patient_data["vitamin_c_intake"], patient_id, "vitamin_c"),
                # Legacy format for backward compatibility
                "macronutrient_distribution": {
                    "protein": 25,
                    "carbohydrates": 45,
                    "fats": 30
                },
                "daily_targets": {
                    "protein_target": patient_data["protein_target"],
                    "protein_achieved": patient_data["protein_intake"],
                    "carb_target": 200,  # Can add to patient data if needed
                    "carb_achieved": 185,
                    "fat_target": 80,
                    "fat_achieved": 75,
                    "fiber_target": patient_data["fiber_target"],
                    "fiber_achieved": patient_data["fiber_intake"]
                },
                # Calculate overall adequacy score based on RDA achievement
                "nutrient_adequacy_score": round(sum(rda_achievement.values()) / len(rda_achievement), 1),
                "dietary_compliance": {
                    "meal_timing": 92,
                    "portion_control": 78,
                    "food_variety": 85,
                    "hydration": 90
                },
                "weekly_trends": {
                    "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                    "protein": [85, 90, 78, 95, 88, 92, 87],
                    "carbs": [88, 92, 85, 90, 87, 93, 89],
                    "fats": [75, 80, 78, 85, 82, 88, 80]
                },
                "deficiency_alerts": [
                    {"nutrient": "Vitamin D", "level": "Below recommended", "severity": "moderate"},
                    {"nutrient": "Fiber", "level": "80% of target", "severity": "mild"}
                ]
            }
            return JSONResponse(content=mock_individual_nutrients)
        else:
            # Cohort nutrient analysis - enhanced with RDA tracking and deficiency analysis
            mock_cohort_nutrients = {
                "mode": "cohort",  # Flag to help frontend distinguish
                "rda_achievement": {
                    "protein": 85,
                    "fiber": 45,
                    "vitamin_d": 32,
                    "calcium": 67,
                    "iron": 71,
                    "vitamin_c": 89,
                    "folate": 58,
                    "magnesium": 63
                },
                "top_deficiencies": [
                    {"name": "Low Fiber", "percentage": 35, "patients_affected": 28},
                    {"name": "Insufficient Vitamin D", "percentage": 25, "patients_affected": 20},
                    {"name": "Excess Sodium", "percentage": 20, "patients_affected": 16},
                    {"name": "Low Iron", "percentage": 12, "patients_affected": 10},
                    {"name": "Other", "percentage": 8, "patients_affected": 6}
                ],
                "daily_compliance_heatmap": [
                    [0.8, 0.75, 0.9, 0.85, 0.78, 0.65, 0.7],   # Week 1: Mon-Sun
                    [0.82, 0.77, 0.88, 0.83, 0.76, 0.68, 0.72], # Week 2
                    [0.85, 0.79, 0.91, 0.87, 0.74, 0.63, 0.69], # Week 3
                    [0.87, 0.81, 0.93, 0.89, 0.72, 0.61, 0.67]  # Week 4
                ],
                # Legacy data structure for nutrient trends (keep existing functionality)
                "cohort_summary": {
                    "avg_nutrient_score": 82.5,
                    "patients_meeting_targets": 78,
                    "common_deficiencies": ["Vitamin D", "Fiber", "Omega-3"],
                    "avg_macros": {
                        "protein": 22,
                        "carbohydrates": 48,
                        "fats": 30
                    }
                },
                "compliance_by_condition": {
                    "type_1_diabetes": 85,
                    "type_2_diabetes": 79,
                    "prediabetes": 88
                },
                "nutrient_trends": {
                    "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                    "avg_scores": [75, 78, 82, 85, 83, 87]
                },
                "top_performers": [
                    {"name": "Sarah Wilson", "score": 95, "condition": "Type 2"},
                    {"name": "Mike Johnson", "score": 92, "condition": "Prediabetes"},
                    {"name": "David Brown", "score": 90, "condition": "Type 1"}
                ],
                # Enhanced nutrient trends data for time series charts - cohort averages
                "trendLabels": ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6', 'Week 7', 'Week 8'],
                "proteinTrend": generate_cohort_average_trend("protein"),
                "fiberTrend": generate_cohort_average_trend("fiber"),
                "vitaminCTrend": generate_cohort_average_trend("vitamin_c")
            }
            return JSONResponse(content=mock_cohort_nutrients)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/analytics/clinical-alerts")
async def get_clinical_alerts(
    current_user: User = Depends(get_current_user)
):
    """Get clinical alerts for outlier detection and intervention needs"""
    # Check if user is admin
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        import statistics
        from datetime import datetime, timedelta
        current_date = datetime.utcnow()
        
        print("[get_clinical_alerts] Starting real data analysis...")
        
        # Get all patients
        all_patients = await get_all_patients()
        if not all_patients:
            print("[get_clinical_alerts] No patients found")
            return JSONResponse(content={
                "summary": {"total_active_alerts": 0, "extreme_intake_patients": 0, "nutrient_spike_alerts": 0, "resolved_this_week": 0},
                "calorie_outliers": {"boxplot_data": {"min": 0, "q1": 0, "median": 0, "q3": 0, "max": 0, "outliers": []}},
                "nutrient_spikes": [],
                "active_alerts": []
            })
        
        print(f"[get_clinical_alerts] Analyzing {len(all_patients)} patients")
        
        # Collect all daily consumption data
        daily_calories = []
        calorie_outliers = []
        nutrient_spikes = []
        active_alerts = []
        patients_with_data = 0
        
        # Define nutrient RDA limits (per day)
        nutrient_limits = {
            "carbs": 225,      # grams (45-65% of 2000 cal diet)
            "protein": 50,     # grams (10-35% of 2000 cal diet)
            "sodium": 2300,    # mg (recommended daily limit)
            "sugar": 50,       # grams (added sugars limit)
            "fiber": 25,       # grams (daily recommendation)
            "fat": 65          # grams (20-35% of 2000 cal diet)
        }
        
        # Analyze each patient's consumption data
        for patient in all_patients:
            try:
                # Find user account for this patient
                patient_registration_code = patient.get("registration_code") or patient.get("id")
                patient_email = None
                
                try:
                    user_query = f"SELECT * FROM c WHERE c.type = 'user' AND c.registration_code = '{patient_registration_code}'"
                    users = list(user_container.query_items(query=user_query, enable_cross_partition_query=True))
                    if users:
                        patient_email = users[0].get("email")
                except Exception as user_error:
                    print(f"[get_clinical_alerts] Error finding user for patient {patient_registration_code}: {str(user_error)}")
                    continue
                
                if not patient_email:
                    continue
                
                # Get consumption history (last 30 days)
                consumption_history = await get_user_consumption_history(patient_email, limit=100)
                if not consumption_history:
                    continue
                
                patients_with_data += 1
                print(f"[get_clinical_alerts] Analyzing {len(consumption_history)} consumption records for {patient.get('name', 'Unknown')}")
                
                # Group consumption by date and calculate daily totals
                daily_totals = defaultdict(lambda: {
                    "calories": 0, "carbs": 0, "protein": 0, "sodium": 0, 
                    "sugar": 0, "fiber": 0, "fat": 0, "record_count": 0
                })
                
                for record in consumption_history:
                    record_date = record.get("timestamp", "")[:10]  # Get date part
                    
                    # Parse nutritional info
                    nutritional_info = record.get("nutritional_info", {})
                    if isinstance(nutritional_info, str):
                        try:
                            nutritional_info = json.loads(nutritional_info)
                        except:
                            nutritional_info = {}
                    
                    # Extract nutrients
                    calories = nutritional_info.get("calories", 0) or 0
                    carbs = nutritional_info.get("carbohydrates", 0) or nutritional_info.get("carbs", 0) or 0
                    protein = nutritional_info.get("protein", 0) or 0
                    sodium = nutritional_info.get("sodium", 0) or 0
                    sugar = nutritional_info.get("sugar", 0) or nutritional_info.get("sugars", 0) or 0
                    fiber = nutritional_info.get("fiber", 0) or nutritional_info.get("dietary_fiber", 0) or 0
                    fat = nutritional_info.get("fat", 0) or nutritional_info.get("total_fat", 0) or 0
                    
                    # Add to daily totals
                    if isinstance(calories, (int, float)) and calories > 0:
                        daily_totals[record_date]["calories"] += calories
                        daily_totals[record_date]["carbs"] += carbs if isinstance(carbs, (int, float)) else 0
                        daily_totals[record_date]["protein"] += protein if isinstance(protein, (int, float)) else 0
                        daily_totals[record_date]["sodium"] += sodium if isinstance(sodium, (int, float)) else 0
                        daily_totals[record_date]["sugar"] += sugar if isinstance(sugar, (int, float)) else 0
                        daily_totals[record_date]["fiber"] += fiber if isinstance(fiber, (int, float)) else 0
                        daily_totals[record_date]["fat"] += fat if isinstance(fat, (int, float)) else 0
                        daily_totals[record_date]["record_count"] += 1
                
                # Analyze daily totals for outliers and spikes
                for date, totals in daily_totals.items():
                    if totals["record_count"] == 0:
                        continue
                    
                    calories = totals["calories"]
                    
                    # Add to overall calorie distribution
                    if calories > 0:
                        daily_calories.append(calories)
                    
                    # Check for calorie outliers (outside normal ranges)
                    if calories > 3000 or calories < 800:
                        severity = "critical" if (calories > 3500 or calories < 600) else "warning"
                        calorie_outliers.append({
                            "patient_id": patient_registration_code,
                            "patient_name": patient.get("name", "Unknown Patient"),
                            "value": round(calories, 0),
                            "date": date,
                            "severity": severity
                        })
                    
                    # Check for nutrient spikes (>300% of RDA)
                    for nutrient, limit in nutrient_limits.items():
                        value = totals.get(nutrient, 0)
                        if value > 0:
                            rda_percent = (value / limit) * 100
                            
                            if rda_percent > 300:  # >3x RDA
                                severity = "critical" if rda_percent > 500 else "warning"
                                nutrient_spikes.append({
                                    "patient_id": patient_registration_code,
                                    "patient_name": patient.get("name", "Unknown Patient"),
                                    "nutrient": nutrient,
                                    "value": round(value, 1),
                                    "rda_percent": round(rda_percent, 0),
                                    "date": date,
                                    "severity": severity,
                                    "rda_limit": limit
                                })
            
            except Exception as patient_error:
                print(f"[get_clinical_alerts] Error processing patient {patient.get('name', 'Unknown')}: {str(patient_error)}")
                continue
        
        print(f"[get_clinical_alerts] Processed {patients_with_data} patients with consumption data")
        print(f"[get_clinical_alerts] Found {len(daily_calories)} daily calorie records")
        print(f"[get_clinical_alerts] Found {len(calorie_outliers)} calorie outliers")
        print(f"[get_clinical_alerts] Found {len(nutrient_spikes)} nutrient spikes")
        
        # Calculate box plot statistics from real data
        if daily_calories:
            sorted_calories = sorted(daily_calories)
            n = len(sorted_calories)
            q1 = sorted_calories[n//4] if n > 4 else sorted_calories[0]
            median = sorted_calories[n//2] if n > 2 else sorted_calories[0]
            q3 = sorted_calories[3*n//4] if n > 4 else sorted_calories[-1]
            min_cal = min(sorted_calories)
            max_cal = max(sorted_calories)
        else:
            # Fallback if no data
            q1, median, q3, min_cal, max_cal = 1800, 2100, 2400, 1200, 2800
        
        # Generate active alerts from outliers and spikes
        for outlier in calorie_outliers:
            if outlier["value"] > 3000:
                alert_type = "Extreme Calories"
                description = f"Daily intake {round((outlier['value'] - 2100) / 2100 * 100, 1)}% above recommended maximum"
                action = "Immediate consultation recommended"
            else:  # Under-eating
                alert_type = "Under-eating"
                description = f"Daily intake {round((1800 - outlier['value']) / 1800 * 100, 1)}% below recommended minimum"
                action = "Nutritional assessment needed"
            
            active_alerts.append({
                "id": f"alert_cal_{outlier['patient_id']}_{outlier['date']}",
                "patient_id": outlier["patient_id"],
                "patient_name": outlier["patient_name"],
                "alert_type": alert_type,
                "severity": outlier["severity"],
                "date": outlier["date"],
                "value": f"{outlier['value']} cal",
                "description": description,
                "action_needed": action
            })
        
        for spike in nutrient_spikes:
            nutrient_name = {
                "carbs": "Carb Spike",
                "sodium": "Sodium Excess",
                "protein": "Protein Excess",
                "sugar": "Sugar Excess",
                "fat": "Fat Excess"
            }.get(spike["nutrient"], "Nutrient Spike")
            
            unit = "mg" if spike["nutrient"] in ["sodium"] else "g"
            
            active_alerts.append({
                "id": f"alert_nut_{spike['patient_id']}_{spike['nutrient']}_{spike['date']}",
                "patient_id": spike["patient_id"],
                "patient_name": spike["patient_name"],
                "alert_type": nutrient_name,
                "severity": spike["severity"],
                "date": spike["date"],
                "value": f"{spike['value']}{unit} ({spike['rda_percent']}% RDA)",
                "description": f"{spike['nutrient'].title()} intake {spike['rda_percent']}% of recommended daily allowance",
                "action_needed": "Review dietary plan and portion sizes"
            })
        
        # Sort alerts by severity and date (most critical and recent first)
        severity_order = {"critical": 3, "warning": 2, "info": 1}
        active_alerts.sort(key=lambda x: (severity_order.get(x["severity"], 0), x["date"]), reverse=True)
        
        # Calculate summary statistics
        total_active_alerts = len(active_alerts)
        extreme_intake_patients = len(set(alert["patient_id"] for alert in active_alerts if alert["alert_type"] in ["Extreme Calories", "Under-eating"]))
        nutrient_spike_alerts = len([alert for alert in active_alerts if "Spike" in alert["alert_type"] or "Excess" in alert["alert_type"]])
        
        # Mock resolved alerts for now (would require tracking in database)
        resolved_this_week = max(0, total_active_alerts // 2)  # Assume half were resolved
        
        # Build response with real data
        clinical_alerts_data = {
            "summary": {
                "total_active_alerts": total_active_alerts,
                "extreme_intake_patients": extreme_intake_patients,
                "nutrient_spike_alerts": nutrient_spike_alerts,
                "resolved_this_week": resolved_this_week
            },
            "calorie_outliers": {
                "boxplot_data": {
                    "min": round(min_cal, 0),
                    "q1": round(q1, 0),
                    "median": round(median, 0),
                    "q3": round(q3, 0),
                    "max": round(max_cal, 0),
                    "outliers": calorie_outliers
                }
            },
            "nutrient_spikes": nutrient_spikes,
            "active_alerts": active_alerts
        }
        
        print(f"[get_clinical_alerts] Generated {total_active_alerts} real active alerts with {extreme_intake_patients} extreme intake patients")
        return JSONResponse(content=clinical_alerts_data)
        
    except Exception as e:
        print(f"[get_clinical_alerts] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/analytics/review-alert")
async def review_clinical_alert(
    review_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Submit a review for a clinical alert"""
    # Check if user is admin
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        from datetime import datetime
        
        # Extract review data
        alert_id = review_data.get("alert_id")
        action = review_data.get("action")
        notes = review_data.get("notes")
        reviewed_by = review_data.get("reviewed_by", "admin")
        reviewed_at = review_data.get("reviewed_at", datetime.utcnow().isoformat())
        
        if not alert_id or not action or not notes:
            raise HTTPException(status_code=400, detail="Missing required fields: alert_id, action, notes")
        
        # In a production system, you would save this to a database
        # For now, we'll create a mock review record
        review_record = {
            "id": f"review_{alert_id}_{int(datetime.utcnow().timestamp())}",
            "alert_id": alert_id,
            "action": action,
            "notes": notes,
            "reviewed_by": reviewed_by,
            "reviewed_at": reviewed_at,
            "type": "alert_review"
        }
        
        # TODO: Save to database
        # In a real implementation, you would:
        # 1. Save the review to a reviews collection/table
        # 2. Update the original alert status
        # 3. Potentially trigger notifications or escalations
        
        print(f"[review_clinical_alert] Alert {alert_id} reviewed with action: {action}")
        print(f"[review_clinical_alert] Review notes: {notes}")
        print(f"[review_clinical_alert] Reviewed by: {reviewed_by} at {reviewed_at}")
        
        # Return success response
        response_data = {
            "success": True,
            "message": f"Alert {alert_id} successfully reviewed",
            "review_id": review_record["id"],
            "action_taken": action,
            "next_steps": get_next_steps_for_action(action)
        }
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[review_clinical_alert] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process alert review: {str(e)}")

def get_next_steps_for_action(action: str) -> List[str]:
    """Get recommended next steps based on the review action"""
    next_steps = {
        "resolved": [
            "Alert marked as resolved",
            "Patient has been contacted and issue addressed",
            "No further action required at this time"
        ],
        "monitoring": [
            "Alert remains active for continued monitoring",
            "Schedule follow-up in 3-5 days",
            "Monitor patient's next consumption entries"
        ],
        "escalated": [
            "Alert escalated to physician for immediate review",
            "Patient should be contacted within 24 hours",
            "Consider scheduling urgent consultation"
        ],
        "dismissed": [
            "Alert dismissed as not clinically significant",
            "Alert removed from active monitoring",
            "Documentation retained for audit trail"
        ]
    }
    
    return next_steps.get(action, ["Review completed"])

@router.get("/admin/analytics/engagement-metrics")
async def get_engagement_metrics(
    patient_id: str = None,
    current_user: User = Depends(get_current_user)
):
    """Get user engagement metrics for individual patient or cohort"""
    # Check if user is admin
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        if patient_id:
            # Individual patient engagement
            mock_individual_engagement = {
                "patient_info": {
                    "id": patient_id,
                    "name": "John Doe" if patient_id == "patient_001" else "Selected Patient"
                },
                # Chart-ready data formats
                "loginLabels": ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6', 'Week 7', 'Week 8'],
                "loginFrequency": [3, 5, 4, 6, 7, 5, 6, 8],
                "sessionDuration": [15, 18, 12, 22, 25, 20, 18, 28],
                "mealLogging": [3, 3, 2, 3, 3, 2, 2],  # Daily meal logs for the week
                "activityHeatmap": [2, 4, 1, 3, 4, 2, 1, 3, 4, 2, 3, 1, 4, 2, 3, 4, 1, 2, 3, 4, 2, 1, 3, 4, 2, 3, 1, 4, 2, 3],
                "featureUsage": [35, 25, 20, 12, 8],  # Meal Plans, AI Coach, Progress, Recipes, Shopping
                "scoreLabels": ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6'],
                "engagementScore": [65, 70, 68, 75, 80, 82],
                # Legacy format for backward compatibility
                "login_frequency": {
                    "daily_logins_last_week": 6,
                    "avg_session_duration": "18.5 minutes",
                    "total_sessions_this_month": 24,
                    "streak_days": 5
                },
                "meal_logging": {
                    "consistency_score": 85,
                    "meals_logged_this_week": 18,
                    "missed_logs": 3,
                    "avg_log_time": "2.5 minutes"
                },
                "app_usage_patterns": {
                    "most_active_time": "07:00-09:00",
                    "preferred_features": ["Meal Plans", "AI Coach", "Progress Tracking"],
                    "feature_usage": {
                        "meal_plans": 95,
                        "ai_coach": 75,
                        "progress_tracking": 68,
                        "recipes": 45,
                        "shopping_lists": 38
                    }
                },
                "engagement_trends": {
                    "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
                    "sessions": [8, 6, 7, 9],
                    "duration": [15.2, 18.5, 16.8, 19.2]
                },
                "coaching_interaction": {
                    "total_sessions": 12,
                    "avg_session_length": "12.5 minutes",
                    "satisfaction_score": 4.5,
                    "most_discussed_topics": ["Meal Planning", "Blood Sugar Management", "Exercise"]
                }
            }
            return JSONResponse(content=mock_individual_engagement)
        else:
            # Cohort engagement metrics
            mock_cohort_engagement = {
                "overview": {
                    "daily_active_users": 45,
                    "weekly_active_users": 78,
                    "monthly_active_users": 98,
                    "avg_session_duration": "15.8 minutes",
                    "user_retention_rate": 82
                },
                "login_patterns": {
                    "peak_hours": ["07:00-09:00", "12:00-13:00", "18:00-20:00"],
                    "avg_sessions_per_user": 3.2,
                    "weekly_login_consistency": 76
                },
                "feature_popularity": {
                    "meal_plans": 95,
                    "ai_coach": 68,
                    "progress_tracking": 72,
                    "recipes": 54,
                    "shopping_lists": 41,
                    "export_data": 23
                },
                "engagement_by_condition": {
                    "type_1_diabetes": {"sessions": 4.2, "duration": 18.5},
                    "type_2_diabetes": {"sessions": 3.8, "duration": 16.2},
                    "prediabetes": {"sessions": 2.9, "duration": 14.8}
                },
                "churn_analysis": {
                    "at_risk_users": 12,
                    "inactive_7_days": 8,
                    "inactive_30_days": 15,
                    "reactivation_rate": 65
                },
                "trends": {
                    "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                    "active_users": [85, 88, 92, 95, 93, 98],
                    "avg_duration": [12.5, 14.2, 15.8, 16.5, 15.9, 17.2]
                }
            }
            return JSONResponse(content=mock_cohort_engagement)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))