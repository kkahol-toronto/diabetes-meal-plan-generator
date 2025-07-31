"""
Pia's Corner Admin Analytics Router
Provides analytics dashboard functionality for administrators.
Requires admin authentication for all endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
from datetime import datetime, timedelta

from models import User
from routers.auth import get_current_user

router = APIRouter()

@router.get("/admin/analytics/patients-list")
async def get_patients_list(
    current_user: User = Depends(get_current_user)
):
    """Get list of patients for analytics dropdown"""
    # Check if user is admin
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Mock patient data for now
        mock_patients = [
            {
                "id": "patient_001",
                "name": "John Doe",
                "registration_code": "REG001",
                "created_at": "2024-01-15T10:00:00Z",
                "condition": "Type 2 Diabetes",
                "last_active": "2024-12-20T15:30:00Z"
            },
            {
                "id": "patient_002", 
                "name": "Jane Smith",
                "registration_code": "REG002",
                "created_at": "2024-02-01T09:15:00Z",
                "condition": "Type 1 Diabetes",
                "last_active": "2024-12-19T14:20:00Z"
            },
            {
                "id": "patient_003",
                "name": "Mike Johnson",
                "registration_code": "REG003", 
                "created_at": "2024-03-10T11:30:00Z",
                "condition": "Prediabetes",
                "last_active": "2024-12-18T16:45:00Z"
            },
            {
                "id": "patient_004",
                "name": "Sarah Wilson",
                "registration_code": "REG004",
                "created_at": "2024-04-05T08:45:00Z",
                "condition": "Type 2 Diabetes",
                "last_active": "2024-12-21T10:15:00Z"
            },
            {
                "id": "patient_005",
                "name": "David Brown",
                "registration_code": "REG005",
                "created_at": "2024-05-20T13:20:00Z",
                "condition": "Type 1 Diabetes", 
                "last_active": "2024-12-20T12:00:00Z"
            }
        ]
        
        return JSONResponse(content={"patients": mock_patients})
        
    except Exception as e:
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
            # Individual patient analytics
            mock_individual_data = {
                "patient_info": {
                    "id": patient_id,
                    "name": "John Doe" if patient_id == "patient_001" else "Selected Patient",
                    "condition": "Type 2 Diabetes",
                    "age": 45,
                    "registration_date": "2024-01-15"
                },
                "metrics": {
                    "total_meal_plans": 24,
                    "completed_meal_plans": 20,
                    "compliance_rate": 83.3,
                    "avg_glucose_level": 145,
                    "weight_change": -2.5,
                    "last_login": "2024-12-20T15:30:00Z"
                },
                "weekly_trends": {
                    "glucose_improvement": "+2.3%",
                    "weight_trend": "-0.2kg",
                    "compliance_trend": "+5%",
                    "activity_increase": "+12%"
                },
                "monthly_summary": {
                    "avg_glucose": 142,
                    "total_activities": 85,
                    "meal_plans_completed": 20,
                    "coaching_sessions": 8
                },
                "recent_activity": [
                    {
                        "date": "2024-12-20",
                        "action": "Completed breakfast meal plan",
                        "glucose_reading": 142
                    },
                    {
                        "date": "2024-12-19", 
                        "action": "Updated weight measurement",
                        "weight": 78.5
                    },
                    {
                        "date": "2024-12-18",
                        "action": "Chat session with AI coach",
                        "duration": "15 minutes"
                    }
                ],
                "glucose_trends": {
                    "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                    "data": [148, 142, 151, 139, 145, 152, 140]
                },
                "weight_progression": [82.5, 82.2, 81.8, 81.5, 81.0, 80.0],
                "meal_compliance": {
                    "breakfast": 90,
                    "lunch": 75,
                    "dinner": 85,
                    "snacks": 70
                }
            }
            return JSONResponse(content=mock_individual_data)
        else:
            # Cohort analytics
            mock_cohort_data = {
                "summary": {
                    "total_patients": 125,
                    "active_patients": 98,
                    "new_registrations_this_month": 12,
                    "avg_compliance_rate": 78.5,
                    "total_meal_plans_generated": 2847,
                    "avg_glucose_improvement": 8.2
                },
                "demographics": {
                    "type_1_diabetes": 35,
                    "type_2_diabetes": 67,
                    "prediabetes": 23
                },
                "engagement_metrics": {
                    "daily_active_users": 45,
                    "weekly_active_users": 78,
                    "monthly_active_users": 98,
                    "avg_session_duration": "12.5 minutes"
                },
                "trends": {
                    "registration_trends": {
                        "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                        "data": [8, 12, 15, 18, 22, 19, 25, 28, 24, 21, 17, 12]
                    },
                    "compliance_trends": {
                        "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
                        "data": [75, 78, 82, 79]
                    }
                },
                "top_performing_patients": [
                    {
                        "name": "Sarah Wilson",
                        "compliance_rate": 95,
                        "glucose_improvement": 15.2
                    },
                    {
                        "name": "David Brown", 
                        "compliance_rate": 92,
                        "glucose_improvement": 12.8
                    },
                    {
                        "name": "Mike Johnson",
                        "compliance_rate": 89,
                        "glucose_improvement": 11.5
                    }
                ]
            }
            return JSONResponse(content=mock_cohort_data)
            
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
            # Individual patient nutrient analysis
            mock_individual_nutrients = {
                "patient_info": {
                    "id": patient_id,
                    "name": "John Doe" if patient_id == "patient_001" else "Selected Patient"
                },
                # Chart-ready data formats
                "macronutrients": [25, 45, 30],  # For pie chart [Protein, Carbs, Fats]
                "targets": [50, 25, 20, 1000, 18, 90],  # For bar chart comparison
                "achieved": [42, 22, 15, 850, 16, 75],  # For bar chart comparison
                "trendLabels": ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6', 'Week 7', 'Week 8'],
                "proteinTrend": [45, 48, 42, 50, 47, 52, 49, 51],
                "fiberTrend": [20, 22, 18, 25, 23, 27, 24, 26],
                "vitaminCTrend": [65, 70, 62, 75, 68, 78, 72, 76],
                # Legacy format for backward compatibility
                "macronutrient_distribution": {
                    "protein": 25,
                    "carbohydrates": 45,
                    "fats": 30
                },
                "daily_targets": {
                    "protein_target": 120,
                    "protein_achieved": 110,
                    "carb_target": 200,
                    "carb_achieved": 185,
                    "fat_target": 80,
                    "fat_achieved": 75,
                    "fiber_target": 35,
                    "fiber_achieved": 28
                },
                "nutrient_adequacy_score": 87,
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
            # Cohort nutrient analysis
            mock_cohort_nutrients = {
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
                ]
            }
            return JSONResponse(content=mock_cohort_nutrients)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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