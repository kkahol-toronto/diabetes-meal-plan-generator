from __future__ import annotations

"""Compatibility endpoints required by the current React dashboard.

These handlers return *minimal* data structures so that the UI can render
without throwing runtime errors.  Replace them with real implementations once
business logic is ported from the legacy monolith.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from ..services.auth import get_current_user
from ..models.user import User

router = APIRouter()

# ---------------------------------------------------------------------------
# Coach namespace
# ---------------------------------------------------------------------------

@router.get("/coach/notifications")
async def get_notifications(current_user: User = Depends(get_current_user)) -> List[Dict[str, Any]]:  # type: ignore[type-var]
    """Return an empty list – the React UI expects an array, not an object."""

    return []


@router.get("/coach/daily-insights")
async def get_daily_insights(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Dummy motivational text for the home page card."""

    return {
        "insights": [
            {
                "title": "Stay hydrated!",
                "message": "Drinking water before meals can help control blood sugar spikes.",
                "created_at": datetime.utcnow().isoformat(),
            },
        ]
    }


@router.get("/coach/todays-meal-plan")
async def get_todays_meal_plan(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Return an empty meal plan skeleton so the UI still functions."""

    return {
        "date": datetime.utcnow().date().isoformat(),
        "meals": [],
    }

# ---------------------------------------------------------------------------
# Consumption namespace
# ---------------------------------------------------------------------------

_DEFAULT_NUTRITION: Dict[str, int] = {
    "calories": 0,
    "protein": 0,
    "carbohydrates": 0,
    "fat": 0,
    "fiber": 0,
    "sugar": 0,
    "sodium": 0,
}

@router.get("/consumption/analytics")
async def get_consumption_analytics(days: int = 30, current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Return zeroed analytics so charts render with empty data instead of null."""

    return {
        "total_meals": 0,
        "date_range": {
            "start_date": (datetime.utcnow() - timedelta(days=days)).date().isoformat(),
            "end_date": datetime.utcnow().date().isoformat(),
        },
        "daily_averages": _DEFAULT_NUTRITION,
        "weekly_trends": {
            "calories": [],
            "protein": [],
            "carbohydrates": [],
            "fat": [],
        },
        "meal_distribution": {
            "breakfast": 0,
            "lunch": 0,
            "dinner": 0,
            "snack": 0,
        },
        "top_foods": [],
        "adherence_stats": {
            "diabetes_suitable_percentage": 0,
            "calorie_goal_adherence": 0,
            "protein_goal_adherence": 0,
            "carb_goal_adherence": 0,
        },
        "daily_nutrition_history": [],
    }


@router.get("/consumption/progress")
async def get_consumption_progress(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Return default progress values (all zeros)."""

    today = datetime.utcnow().date().isoformat()
    return {
        "date": today,
        "targets": _DEFAULT_NUTRITION,
        "consumed": _DEFAULT_NUTRITION,
    }

# ---------------------------------------------------------------------------
# User namespace
# ---------------------------------------------------------------------------

@router.get("/user/profile")
async def get_user_profile(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Return empty profile placeholder."""

    return {} 