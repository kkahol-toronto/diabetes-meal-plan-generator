"""
Test Endpoints Router
Contains all testing and development endpoints for debugging and validation.
These endpoints are used for development, testing, and debugging purposes.
"""

from fastapi import APIRouter, HTTPException, Depends, Request as FastAPIRequest
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from models import User
from routers.auth import get_current_user
from database import (
    get_user_by_email, create_patient, create_user, save_consumption_record,
    get_user_consumption_history, get_recent_chat_history, get_user_meal_plans,
    format_chat_history_for_prompt, interactions_container, user_container
)
from utils import get_password_hash, get_today_utc_boundaries, get_user_timezone_boundaries

router = APIRouter()

@router.get("/test/profile-persistence")
async def test_profile_persistence(current_user: User = Depends(get_current_user)):
    """
    Test endpoint to diagnose profile persistence issues.
    Returns detailed information about profile storage and retrieval.
    """
    try:
        user_email = current_user["email"]
        
        # Get user document
        user_doc = await get_user_by_email(user_email)
        if not user_doc:
            return {
                "status": "error",
                "message": "User not found",
                "user_email": user_email
            }
        
        # Get profile from user document
        profile_in_user_doc = user_doc.get("profile", {})
        
        # Get separate profile record
        separate_profile = {}
        try:
            # Check if there's a separate profile document
            profile_query = f"c.type = 'profile' AND c.user_email = '{user_email}'"
            profile_items = list(user_container.query_items(
                query=profile_query,
                enable_cross_partition_query=True
            ))
            
            if profile_items:
                separate_profile = profile_items[0]
        except Exception as profile_error:
            separate_profile = {"error": str(profile_error)}
        
        return {
            "status": "success",
            "user_email": user_email,
            "user_doc_has_profile": bool(profile_in_user_doc),
            "profile_in_user_doc": profile_in_user_doc,
            "separate_profile_exists": bool(separate_profile and "error" not in separate_profile),
            "separate_profile": separate_profile,
            "profile_fields_in_user_doc": list(profile_in_user_doc.keys()) if profile_in_user_doc else [],
            "recommendations": [
                "Profile should be stored in the user document under 'profile' field",
                "Separate profile documents are deprecated",
                "Use save_user_profile endpoint to update profile"
            ]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Test failed: {str(e)}",
            "user_email": current_user.get("email", "Unknown")
        }

@router.post("/test/create-sample-data")
async def create_sample_data():
    """Create sample consumption data for testing"""
    try:
        # Sample consumption records for the last 7 days
        sample_foods = [
            {
                "food_name": "Grilled Chicken Breast with Vegetables",
                "nutritional_info": {
                    "calories": 350,
                    "protein": 45,
                    "carbohydrates": 15,
                    "fat": 12,
                    "fiber": 5,
                    "sugar": 8,
                    "sodium": 450
                },
                "medical_rating": {
                    "diabetes_suitability": "high",
                    "hypertension_suitability": "high",
                    "heart_disease_suitability": "high",
                    "cholesterol_suitability": "high",
                    "overall_health_score": 85
                }
            },
            {
                "food_name": "Greek Yogurt with Berries",
                "nutritional_info": {
                    "calories": 180,
                    "protein": 15,
                    "carbohydrates": 20,
                    "fat": 5,
                    "fiber": 3,
                    "sugar": 15,
                    "sodium": 80
                },
                "medical_rating": {
                    "diabetes_suitability": "medium",
                    "hypertension_suitability": "high",
                    "heart_disease_suitability": "high", 
                    "cholesterol_suitability": "high",
                    "overall_health_score": 78
                }
            },
            {
                "food_name": "Brown Rice with Lentils",
                "nutritional_info": {
                    "calories": 280,
                    "protein": 12,
                    "carbohydrates": 50,
                    "fat": 3,
                    "fiber": 8,
                    "sugar": 4,
                    "sodium": 200
                },
                "medical_rating": {
                    "diabetes_suitability": "medium",
                    "hypertension_suitability": "high",
                    "heart_disease_suitability": "high",
                    "cholesterol_suitability": "high",
                    "overall_health_score": 80
                }
            }
        ]
        
        # Create sample records for the test user over the last 7 days
        test_user_email = "test@example.com"
        records_created = 0
        
        for day_offset in range(7):
            for food in sample_foods:
                # Create timestamp for this day
                record_date = datetime.utcnow() - timedelta(days=day_offset)
                
                consumption_record = {
                    "id": f"test_{test_user_email}_{record_date.strftime('%Y%m%d')}_{food['food_name'].replace(' ', '_')}",
                    "user_email": test_user_email,
                    "timestamp": record_date.isoformat(),
                    "food_name": food["food_name"],
                    "estimated_portion": "1 serving",
                    "nutritional_info": food["nutritional_info"],
                    "medical_rating": food["medical_rating"],
                    "type": "consumption",
                    "source": "test_data_creation",
                    "confidence_score": 0.9,
                    "created_at": datetime.utcnow().isoformat()
                }
                
                try:
                    await save_consumption_record(consumption_record)
                    records_created += 1
                except Exception as save_error:
                    print(f"Error saving record: {save_error}")
                    continue
        
        return {
            "status": "success",
            "message": f"Created {records_created} sample consumption records",
            "test_user_email": test_user_email,
            "foods_included": [food["food_name"] for food in sample_foods],
            "days_covered": 7
        }
        
    except Exception as e:
        print(f"[create_sample_data] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create sample data: {str(e)}")

@router.post("/test/create-user")
async def create_test_user():
    """Create a test user for development purposes"""
    try:
        # Create a test patient first with comprehensive health conditions
        patient_data = {
            "id": "TEST123",  # Use registration code as ID for consistency
            "name": "Test Patient",
            "phone": "1234567890",
            "condition": "Type 2 Diabetes",
            "medical_conditions": ["Type 2 Diabetes", "Hypertension", "High Cholesterol", "PCOS"],
            "medications": ["Metformin", "Lisinopril", "Atorvastatin", "Spironolactone"],
            "allergies": ["Shellfish", "Tree Nuts"],
            "dietary_restrictions": ["Low Sodium", "Low Glycemic Index"],
            "registration_code": "TEST123",
            "type": "patient",  # Add type field
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Save patient to database
        await create_patient(patient_data)
        
        # Create corresponding user account
        user_data = {
            "email": "test@example.com",
            "password": get_password_hash("testpassword123"),
            "profile": {
                "name": patient_data["name"],
                "age": 35,
                "gender": "female",
                "weight": 75,
                "height": 165,
                "activityLevel": "moderate",
                "medicalConditions": patient_data["medical_conditions"],
                "currentMedications": patient_data["medications"],
                "allergies": patient_data["allergies"],
                "dietaryPreferences": ["vegetarian"],
                "calorieGoal": 1800,
                "macroGoals": {
                    "carbs": 45,
                    "protein": 25,
                    "fat": 30
                },
                "timezone": "UTC",
                "registration_code": "TEST123"
            },
            "registration_code": "TEST123",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Create user
        result = await create_user(user_data)
        
        return {
            "status": "success",
            "message": "Test user created successfully",
            "user_email": "test@example.com",
            "password": "testpassword123",
            "registration_code": "TEST123",
            "patient_profile": patient_data,
            "user_id": result.get("id") if result else None
        }
        
    except Exception as e:
        print(f"[create_test_user] Error: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to create test user: {str(e)}"
        }

@router.post("/test/quick-log")
async def test_quick_log_food(food_data: dict):
    """Test quick food logging without authentication"""
    try:
        print(f"[test_quick_log_food] Testing quick log with data: {food_data}")
        
        # Extract required data
        test_user_email = "test@example.com"  # Use fixed test user
        food_name = food_data.get("food_name", "Test Food")
        portion = food_data.get("portion", "1 serving")
        
        # Create mock nutritional info if not provided
        nutritional_info = food_data.get("nutritional_info", {
            "calories": 200,
            "protein": 10,
            "carbohydrates": 25,
            "fat": 8,
            "fiber": 3,
            "sugar": 5,
            "sodium": 300
        })
        
        # Create mock medical rating
        medical_rating = food_data.get("medical_rating", {
            "diabetes_suitability": "medium",
            "hypertension_suitability": "medium",
            "heart_disease_suitability": "medium",
            "cholesterol_suitability": "medium",
            "overall_health_score": 75,
            "overall_rating": 4
        })
        
        # Create consumption record
        consumption_record = {
            "id": f"test_{test_user_email}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "user_email": test_user_email,
            "timestamp": datetime.utcnow().isoformat(),
            "food_name": food_name,
            "estimated_portion": portion,
            "nutritional_info": nutritional_info,
            "medical_rating": medical_rating,
            "type": "consumption",
            "source": "test_quick_log",
            "confidence_score": 0.95,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Save to database
        result = await save_consumption_record(consumption_record)
        
        return {
            "status": "success",
            "message": "Test food logged successfully",
            "record_id": consumption_record["id"],
            "food_name": food_name,
            "calories": nutritional_info.get("calories"),
            "medical_score": medical_rating.get("overall_health_score"),
            "user_email": test_user_email,
            "timestamp": consumption_record["timestamp"]
        }
        
    except Exception as e:
        print(f"[test_quick_log_food] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to log test food: {str(e)}")

@router.get("/test/consumption/history")
async def test_get_consumption_history(limit: int = 50):
    """Test getting consumption history without authentication"""
    try:
        test_user_email = "test@example.com"
        history = await get_user_consumption_history(test_user_email, limit=limit)
        return {"status": "success", "count": len(history), "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get test consumption history: {str(e)}")

@router.get("/test/consumption/analytics")
async def test_get_consumption_analytics(days: int = 7):
    """Test getting consumption analytics without authentication"""
    try:
        test_user_email = "test@example.com"
        # Mock analytics data for testing
        return {
            "status": "success", 
            "user_email": test_user_email, 
            "days": days,
            "total_calories": 1800,
            "avg_daily_calories": 257,
            "total_meals": 21
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get test analytics: {str(e)}")

@router.get("/test/coach/daily-insights")
async def test_get_daily_insights():
    """Test getting daily coaching insights without authentication"""
    try:
        print(f"[test_get_daily_insights] Getting daily insights for test user")
        
        # Create a mock user for testing
        mock_user = {
            "email": "test@example.com",
            "id": "test@example.com"
        }
        
        # Import the actual function to test
        from main import get_daily_coaching_insights
        
        # Call the actual function with mock user
        return await get_daily_coaching_insights(mock_user)
        
    except Exception as e:
        print(f"[test_get_daily_insights] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get daily insights: {str(e)}")

@router.get("/test/coach/notifications")
async def test_get_notifications():
    """Test getting notifications without authentication"""
    try:
        print(f"[test_get_notifications] Getting notifications for test user")
        
        # Create a mock user for testing
        mock_user = {
            "email": "test@example.com",
            "id": "test@example.com"
        }
        
        # Import the actual function to test
        from main import get_notifications
        
        return await get_notifications(mock_user)
        
    except Exception as e:
        print(f"[test_get_notifications] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get notifications: {str(e)}")

@router.get("/test/coach/todays-meal-plan")
async def test_get_todays_meal_plan():
    """Test today's meal plan without authentication"""
    try:
        print(f"[test_get_todays_meal_plan] Getting today's meal plan for test user")
        
        # Create a mock user for testing
        mock_user = {
            "email": "test@example.com",
            "id": "test@example.com"
        }
        
        # Import the actual function to test
        from main import get_todays_meal_plan
        
        return await get_todays_meal_plan(mock_user)
        
    except Exception as e:
        print(f"[test_get_todays_meal_plan] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get today's meal plan: {str(e)}")