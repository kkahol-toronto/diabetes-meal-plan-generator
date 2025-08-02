from fastapi import APIRouter, Depends, HTTPException
from typing import List
from models import User
from routers.auth import get_current_user
from database import (
    get_user_consumption_history,
    get_consumption_analytics,
    interactions_container
)
from datetime import datetime, timedelta
import traceback
import sys
from collections import defaultdict

router = APIRouter()

@router.get("/consumption/history")
async def get_consumption_history(
    limit: int = 50,
    force_refresh: bool = False,
    current_user: User = Depends(get_current_user)
):
    """Get consumption history - FIXED USER ID CONSISTENCY with cache bypass option"""
    try:
        print(f"[get_consumption_history] *** CRITICAL DEBUG *** Getting history for user {current_user['email']}")
        print(f"[get_consumption_history] *** CRITICAL DEBUG *** Force refresh: {force_refresh}")
        print(f"[get_consumption_history] *** CRITICAL DEBUG *** current_user keys: {list(current_user.keys())}")
        print(f"[get_consumption_history] *** CRITICAL DEBUG *** current_user['email']: {current_user.get('email')}")
        print(f"[get_consumption_history] *** CRITICAL DEBUG *** current_user['id']: {current_user.get('id')}")
        
        # If force_refresh is requested, clear cache first
        if force_refresh:
            print(f"[get_consumption_history] Force refresh requested - clearing cache for {current_user['email']}")
            from services.cache_service import invalidate_consumption_cache
            invalidate_consumption_cache(current_user["email"])
        
        # Use the original database function with EMAIL (consistent with how we save)
        history = await get_user_consumption_history(current_user["email"], limit)
        print(f"[get_consumption_history] *** CRITICAL DEBUG *** Retrieved {len(history)} records for {current_user['email']}")
        
        # Log sample record if exists
        if history:
            sample = history[0]
            print(f"[get_consumption_history] *** SAMPLE RECORD *** {sample.get('food_name')} at {sample.get('timestamp')}")
        else:
            print(f"[get_consumption_history] *** NO RECORDS FOUND *** for user {current_user['email']}")
        
        return history
        
    except Exception as e:
        print(f"[get_consumption_history] Error: {str(e)}")
        print(f"[get_consumption_history] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get consumption history: {str(e)}")

@router.get("/consumption/analytics")
async def get_consumption_analytics_endpoint(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get consumption analytics - USING ORIGINAL FUNCTION with better error handling"""
    try:
        print(f"[get_consumption_analytics] Getting analytics for user {current_user['id']} for {days} days")
        
        # Get user's timezone from profile
        user_timezone = current_user.get("profile", {}).get("timezone", "UTC")
        print(f"[get_consumption_analytics] Using timezone: {user_timezone}")
        
        # Use the original database function with timezone
        analytics = await get_consumption_analytics(current_user["email"], days, user_timezone)
        print(f"[get_consumption_analytics] Generated analytics successfully")
        
        return analytics
        
    except Exception as e:
        print(f"[get_consumption_analytics] Error: {str(e)}")
        print(f"[get_consumption_analytics] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get consumption analytics: {str(e)}")

@router.get("/consumption/meal-analytics")
async def get_meal_level_analytics(
    days: int = 1,
    current_user: User = Depends(get_current_user)
):
    """Get meal-level nutritional breakdown analytics - REAL DATA FOR CHARTS"""
    try:
        print(f"[get_meal_level_analytics] Getting meal analytics for user {current_user['email']} for {days} days")
        
        # Get user's timezone from profile
        user_timezone = current_user.get("profile", {}).get("timezone", "UTC")
        
        # Calculate date threshold
        threshold_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        query = f"""
        SELECT * FROM c 
        WHERE c.type = 'consumption_record' 
        AND c.user_id = '{current_user['email']}' 
        AND c.timestamp >= '{threshold_date}' 
        ORDER BY c.timestamp DESC
        """
        
        records = list(interactions_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        if not records:
            return {
                "meal_breakdown": {
                    "breakfast": {"calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0, "fiber": 0, "sugar": 0, "sodium": 0},
                    "lunch": {"calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0, "fiber": 0, "sugar": 0, "sodium": 0},
                    "dinner": {"calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0, "fiber": 0, "sugar": 0, "sodium": 0},
                    "snack": {"calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0, "fiber": 0, "sugar": 0, "sodium": 0}
                },
                "daily_totals": {"calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0, "fiber": 0, "sugar": 0, "sodium": 0},
                "total_records": 0
            }
        
        # Initialize meal breakdown
        meal_breakdown = {
            "breakfast": {"calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0, "fiber": 0, "sugar": 0, "sodium": 0},
            "lunch": {"calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0, "fiber": 0, "sugar": 0, "sodium": 0},
            "dinner": {"calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0, "fiber": 0, "sugar": 0, "sodium": 0},
            "snack": {"calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0, "fiber": 0, "sugar": 0, "sodium": 0}
        }
        
        daily_totals = {"calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0, "fiber": 0, "sugar": 0, "sodium": 0}
        
        # Process each record
        for record in records:
            nutritional_info = record.get("nutritional_info", {})
            meal_type = record.get("meal_type", "snack")
            timestamp = record.get("timestamp", "")
            
            # If meal_type is empty, determine based on time
            if not meal_type or meal_type == "":
                try:
                    record_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    hour = record_time.hour
                    if 5 <= hour < 11:
                        meal_type = "breakfast"
                    elif 11 <= hour < 16:
                        meal_type = "lunch"
                    elif 16 <= hour < 22:
                        meal_type = "dinner"
                    else:
                        meal_type = "snack"
                except:
                    meal_type = "snack"
            
            # Extract nutrition values
            calories = nutritional_info.get("calories", 0)
            protein = nutritional_info.get("protein", 0)
            carbohydrates = nutritional_info.get("carbohydrates", nutritional_info.get("carbs", 0))
            fat = nutritional_info.get("fat", 0)
            fiber = nutritional_info.get("fiber", 0)
            sugar = nutritional_info.get("sugar", 0)
            sodium = nutritional_info.get("sodium", 0)
            
            # Add to meal breakdown
            if meal_type in meal_breakdown:
                meal_breakdown[meal_type]["calories"] += calories
                meal_breakdown[meal_type]["protein"] += protein
                meal_breakdown[meal_type]["carbohydrates"] += carbohydrates
                meal_breakdown[meal_type]["fat"] += fat
                meal_breakdown[meal_type]["fiber"] += fiber
                meal_breakdown[meal_type]["sugar"] += sugar
                meal_breakdown[meal_type]["sodium"] += sodium
            
            # Add to daily totals
            daily_totals["calories"] += calories
            daily_totals["protein"] += protein
            daily_totals["carbohydrates"] += carbohydrates
            daily_totals["fat"] += fat
            daily_totals["fiber"] += fiber
            daily_totals["sugar"] += sugar
            daily_totals["sodium"] += sodium
        
        print(f"[get_meal_level_analytics] Processed {len(records)} records")
        print(f"[get_meal_level_analytics] Meal breakdown: {meal_breakdown}")
        
        return {
            "meal_breakdown": meal_breakdown,
            "daily_totals": daily_totals,
            "total_records": len(records)
        }
        
    except Exception as e:
        print(f"[get_meal_level_analytics] Error: {str(e)}")
        print(f"[get_meal_level_analytics] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get meal-level analytics: {str(e)}")

@router.post("/consumption/fix-meal-types")
async def fix_meal_types(current_user: User = Depends(get_current_user)):
    """Fix meal types for existing consumption records based on timestamp"""
    try:
        print(f"[fix_meal_types] Starting meal type fix for user {current_user['email']}")
        
        # Get all consumption records for the user
        query = f"""
        SELECT * FROM c 
        WHERE c.type = 'consumption_record' 
        AND c.user_id = '{current_user['email']}' 
        ORDER BY c.timestamp DESC
        """
        
        records = list(interactions_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        print(f"[fix_meal_types] Found {len(records)} consumption records")
        
        updated_count = 0
        
        for record in records:
            timestamp = record.get("timestamp", "")
            current_meal_type = record.get("meal_type", "")
            
            # Only update if meal_type is empty or "snack" (likely incorrect)
            if not current_meal_type or current_meal_type == "" or current_meal_type == "snack":
                try:
                    # Determine correct meal type based on timestamp
                    record_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    hour = record_time.hour
                    
                    if 5 <= hour < 11:
                        correct_meal_type = "breakfast"
                    elif 11 <= hour < 16:
                        correct_meal_type = "lunch"
                    elif 16 <= hour < 22:
                        correct_meal_type = "dinner"
                    else:
                        correct_meal_type = "snack"
                    
                    # Only update if the meal type actually changed
                    if current_meal_type != correct_meal_type:
                        record["meal_type"] = correct_meal_type
                        interactions_container.upsert_item(body=record)
                        updated_count += 1
                        print(f"[fix_meal_types] Updated record {record['id']}: {current_meal_type} -> {correct_meal_type}")
                    
                except Exception as e:
                    print(f"[fix_meal_types] Error processing record {record.get('id', 'unknown')}: {str(e)}")
                    continue
        
        return {
            "success": True,
            "message": f"Fixed meal types for {updated_count} consumption records",
            "total_records": len(records),
            "updated_records": updated_count
        }
        
    except Exception as e:
        print(f"[fix_meal_types] Error: {str(e)}")
        print(f"[fix_meal_types] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to fix meal types: {str(e)}") 