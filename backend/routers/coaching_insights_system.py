from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import Counter
from models import User
from routers.auth import get_current_user
from database import get_user_by_email
from services.coaching_system import (
    get_consumption_progress_data,
    get_daily_coaching_insights_data,
    get_nutrition_score_breakdown_data
)
import traceback

router = APIRouter()

@router.get("/consumption/progress")
async def get_consumption_progress(current_user: User = Depends(get_current_user)):
    """
    Returns user's daily calorie/macro goals, today's progress, and weekly/monthly averages.
    Always returns a valid set of goals, using smart defaults if needed.
    """
    # 1. Get user profile (for goals)
    user_doc = await get_user_by_email(current_user["email"])
    if not user_doc or "profile" not in user_doc:
        raise HTTPException(status_code=404, detail="User profile not found")
    profile = user_doc["profile"]
    
    # Use the extracted coaching system function
    return await get_consumption_progress_data(current_user["email"], profile)

@router.get("/coach/daily-insights")
async def get_daily_coaching_insights(current_user: User = Depends(get_current_user)):
    """Get daily insights - USING ORIGINAL LOGIC with better integration"""
    try:
        # Get user profile
        profile = current_user.get("profile", {})
        
        # Use the extracted coaching system function
        return await get_daily_coaching_insights_data(current_user["email"], profile)
    except Exception as e:
        print(f"[get_daily_insights] Error: {str(e)}")
        print(f"[get_daily_insights] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get daily insights: {str(e)}")

@router.get("/coach/nutrition-score-breakdown")
async def get_nutrition_score_breakdown(current_user: User = Depends(get_current_user)):
    """
    Get detailed nutrition score breakdown for UI transparency.
    Shows users exactly how their score was calculated.
    """
    try:
        # Get the daily insights which contains the score breakdown
        insights = await get_daily_coaching_insights(current_user)
        score_breakdown = insights.get("score_breakdown", {})
        
        # Add additional explanation for UI
        breakdown_with_explanations = {
            "current_score": insights.get("diabetes_adherence", 0),
            "breakdown": {
                "base_score": {
                    "value": score_breakdown.get("base_score", 0),
                    "explanation": "Based on the diabetes-suitability of your recent meals",
                    "icon": "📊"
                },
                "today_boost": {
                    "value": score_breakdown.get("today_boost", 0),
                    "explanation": "Bonus for healthy choices made today",
                    "icon": "⚡",
                    "is_positive": True
                },
                "healthy_bonus": {
                    "value": score_breakdown.get("healthy_bonus", 0),
                    "explanation": "Reward for high-fiber, low-glycemic food choices",
                    "icon": "🥬",
                    "is_positive": True
                },
                "carb_penalty": {
                    "value": -score_breakdown.get("carb_penalty", 0),
                    "explanation": "Reduction for high-carb meals (>45g carbs)",
                    "icon": "🍞",
                    "is_positive": False
                },
                "sugar_penalty": {
                    "value": -score_breakdown.get("sugar_penalty", 0),
                    "explanation": "Reduction for high-sugar meals (>15g sugar)",
                    "icon": "🍭",
                    "is_positive": False
                },
                "processed_penalty": {
                    "value": -score_breakdown.get("processed_penalty", 0),
                    "explanation": "Reduction for high-sodium processed foods (>800mg)",
                    "icon": "🥫",
                    "is_positive": False
                },
                "consistency_penalty": {
                    "value": -score_breakdown.get("consistency_penalty", 0),
                    "explanation": "Small reduction for inconsistent healthy logging",
                    "icon": "📅",
                    "is_positive": False
                }
            },
            "personalization": {
                "is_personalized": score_breakdown.get("calculation_method") == "personalized",
                "sensitivity_factor": score_breakdown.get("sensitivity_factor", 1.0),
                "explanation": "Your score is personalized based on your age, health conditions, activity level, and goals"
            },
            "tips": []
        }
        
        # Generate actionable tips based on the breakdown
        if score_breakdown.get("carb_penalty", 0) > 5:
            breakdown_with_explanations["tips"].append({
                "type": "carbs",
                "message": "Try choosing lower-carb alternatives like cauliflower rice or zucchini noodles",
                "icon": "💡"
            })
        
        if score_breakdown.get("sugar_penalty", 0) > 5:
            breakdown_with_explanations["tips"].append({
                "type": "sugar",
                "message": "Opt for naturally sweet foods like berries instead of processed desserts",
                "icon": "🫐"
            })
        
        if score_breakdown.get("processed_penalty", 0) > 3:
            breakdown_with_explanations["tips"].append({
                "type": "processed",
                "message": "Choose fresh, whole foods and cook at home when possible",
                "icon": "🍳"
            })
        
        if score_breakdown.get("today_boost", 0) > 10:
            breakdown_with_explanations["tips"].append({
                "type": "positive",
                "message": "Great job with today's healthy choices! Keep up the excellent work!",
                "icon": "🌟"
            })
        elif score_breakdown.get("today_boost", 0) == 0:
            breakdown_with_explanations["tips"].append({
                "type": "encouragement",
                "message": "Log some healthy meals today to boost your score!",
                "icon": "🎯"
            })
        
        return breakdown_with_explanations
        
    except Exception as e:
        print(f"[nutrition_score_breakdown] Error: {str(e)}")
        print(f"[nutrition_score_breakdown] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get score breakdown: {str(e)}")

def detect_food_exploitation(user_email: str, today_consumption: list, new_food_name: str) -> dict:
    """
    Detect if user is trying to exploit the scoring system by logging the same food repeatedly.
    Returns exploitation status and adjusted scoring.
    """
    try:
        # Count food occurrences today
        food_counts = Counter()
        for record in today_consumption:
            food_name = record.get("food_name", "").lower().strip()
            food_counts[food_name] += 1
        
        # Add the new food being logged
        new_food_lower = new_food_name.lower().strip()
        food_counts[new_food_lower] += 1
        
        exploitation_detected = False
        score_adjustment = 0
        warnings = []
        
        # Check for repetitive logging
        for food, count in food_counts.items():
            if count > 3:  # Same food more than 3 times in one day
                exploitation_detected = True
                excess_logs = count - 3
                score_adjustment -= (excess_logs * 2)  # 2% penalty per excess log
                warnings.append(f"'{food}' logged {count} times today (max recommended: 3)")
            elif count == 3:
                warnings.append(f"'{food}' logged 3 times today - consider adding variety")
        
        # Check for suspicious patterns (only "healthy" foods logged)
        healthy_foods = ["spinach", "broccoli", "kale", "lettuce", "cucumber", "celery"]
        if len(food_counts) >= 5 and all(any(healthy in food for healthy in healthy_foods) for food in food_counts.keys()):
            exploitation_detected = True
            score_adjustment -= 5  # 5% penalty for unrealistic all-healthy pattern
            warnings.append("Diet seems unrealistically limited to only healthy foods - add variety")
        
        # Check for meal variety (encourage diverse nutrition)
        if len(food_counts) == 1 and list(food_counts.values())[0] > 2:
            warnings.append("Try adding variety to your meals for better nutrition coverage")
        
        return {
            "exploitation_detected": exploitation_detected,
            "score_adjustment": score_adjustment,
            "warnings": warnings,
            "food_counts": dict(food_counts),
            "variety_score": len(food_counts),  # Higher is better
            "recommendation": "Add more variety to your meals" if len(food_counts) < 3 else "Good meal variety!"
        }
        
    except Exception as e:
        print(f"[FOOD_EXPLOITATION] Error: {e}")
        return {
            "exploitation_detected": False,
            "score_adjustment": 0,
            "warnings": [],
            "food_counts": {},
            "variety_score": 1,
            "recommendation": "Continue logging diverse meals"
        } 