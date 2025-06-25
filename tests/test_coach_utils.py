"""Tests for helper utilities in :pymod:`backend.app.routers.coach`."""

from __future__ import annotations

# Stub *heavy* dependencies required at import time to keep the coach module lightweight.
import sys
from unittest import mock

for _module in [
    "backend.app.services.meal_service",
    "backend.app.services.auth",
    "backend.app.services.ai_service",
    "backend.app.utils.logger",
]:
    sys.modules.setdefault(_module, mock.MagicMock())

# Now that stubs are in place we can safely import the real module.
from backend.app.routers.coach import analyze_meal_patterns, build_meal_suggestion_prompt


def test_analyze_meal_patterns_frequency_accumulates() -> None:
    """Repeated foods should have their frequency incremented."""
    history = [
        {"meal_type": "breakfast", "food_name": "oatmeal", "timestamp": "2024-01-01"},
        {"meal_type": "breakfast", "food_name": "oatmeal", "timestamp": "2024-01-02"},
        {"meal_type": "lunch", "food_name": "salad", "timestamp": "2024-01-01"},
    ]

    patterns = analyze_meal_patterns(history)
    oatmeal_entry = next(m for m in patterns["breakfast"] if m["name"] == "oatmeal")
    assert oatmeal_entry["frequency"] == 2
    # Meal types with no data should still exist as keys for downstream UI tables.
    assert set(patterns) == {"breakfast", "lunch", "dinner", "snack"}


def test_build_meal_suggestion_prompt_contains_key_info() -> None:
    """Prompt should embed calories, restrictions, and preferences text."""

    prompt = build_meal_suggestion_prompt(
        meal_type="dinner",
        remaining_calories=600,
        meal_patterns={},
        dietary_restrictions=["gluten"],
        health_conditions=["diabetes"],
        context={"query_context": "I want something light"},
        preferences="high protein"
    )

    assert "600" in prompt
    assert "gluten" in prompt
    assert "diabetes" in prompt
    assert "high protein" in prompt


def test_build_meal_suggestion_prompt_late_meal_flag() -> None:
    """When context indicates a *late meal* the prompt should reflect it."""

    prompt = build_meal_suggestion_prompt(
        meal_type="snack",
        remaining_calories=200,
        meal_patterns={},
        dietary_restrictions=[],
        health_conditions=[],
        context={"is_late_meal": True, "query_context": "just a quick bite"},
        preferences="",
    )

    assert "lighter option" in prompt.lower() or "light" in prompt.lower() 