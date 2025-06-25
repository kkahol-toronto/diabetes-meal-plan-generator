"""Tests for :pymod:`backend.consumption_system`.

These tests focus on *pure* helper methods and the public coroutine
``quick_log_food``.  External I/O (OpenAI & Cosmos DB) is stubbed using
``unittest.mock`` so that tests run quickly and deterministically.
"""

from __future__ import annotations

from datetime import datetime
from types import ModuleType
from typing import Generator
from unittest import mock

import importlib.util
import pathlib
import sys

import pytest


# --------------------------------------------------------------------------------------
# Module import with dependency stubs
# --------------------------------------------------------------------------------------

# Ensure external dependencies that appear at *import time* are stubbed out first.
sys.modules.setdefault("database", mock.MagicMock())
sys.modules.setdefault("openai", mock.MagicMock())

ROOT_DIR = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "backend" / "consumption_system.py"

spec = importlib.util.spec_from_file_location("consumption_system", MODULE_PATH)
consumption_system = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
sys.modules[spec.name] = consumption_system  # type: ignore[arg-type]
assert spec.loader is not None
spec.loader.exec_module(consumption_system)  # type: ignore[attr-defined]

ConsumptionTracker = consumption_system.ConsumptionTracker  # alias for brevity


# --------------------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------------------


@pytest.fixture()
def tracker() -> Generator[consumption_system.ConsumptionTracker, None, None]:
    """Return a fresh :class:`~backend.consumption_system.ConsumptionTracker` instance."""

    yield ConsumptionTracker()


# --------------------------------------------------------------------------------------
# Helper-method unit tests
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "hour,expected",
    [
        (6, "breakfast"),
        (12, "lunch"),
        (18, "dinner"),
        (2, "snack"),  # edge case – outside standard meal windows
    ],
)
def test_determine_meal_type(tracker: consumption_system.ConsumptionTracker, hour: int, expected: str) -> None:
    """``_determine_meal_type`` should resolve the correct meal-type string."""

    fake_dt = datetime(2024, 1, 1, hour=hour)
    assert tracker._determine_meal_type(fake_dt) == expected


def test_determine_meal_type_none(tracker: consumption_system.ConsumptionTracker) -> None:
    """Passing *None* returns ``"unknown"`` (early-return guard)."""

    assert tracker._determine_meal_type(None) == "unknown"  # type: ignore[arg-type]


def test_empty_analytics_response_structure(tracker: consumption_system.ConsumptionTracker) -> None:
    """Verify keys and zero counts of the placeholder analytics structure."""

    response = tracker._empty_analytics_response("2024-01-01")  # type: ignore[attr-defined]

    mandatory = {
        "total_meals",
        "date_range",
        "daily_averages",
        "weekly_trends",
        "meal_distribution",
        "top_foods",
        "adherence_stats",
        "daily_nutrition_history",
    }
    assert mandatory.issubset(response)
    assert response["total_meals"] == 0


def test_process_consumption_analytics_basic(tracker: consumption_system.ConsumptionTracker) -> None:
    """With sample records, analytics should compute simple averages correctly."""

    sample_records = [
        {
            "logged_at": "2024-01-01T12:00:00Z",
            "nutritional_info": {
                "calories": 200,
                "carbohydrates": 30,
                "protein": 10,
                "fat": 5,
            },
        },
        {
            "logged_at": "2024-01-02T12:00:00Z",
            "nutritional_info": {
                "calories": 100,
                "carbohydrates": 15,
                "protein": 5,
                "fat": 2,
            },
        },
    ]

    days = 2
    analytics = tracker._process_consumption_analytics(sample_records, days, "2024-01-01")  # type: ignore[attr-defined]
    assert analytics["total_meals"] == 2
    # Average calories should be (200 + 100) / 2 = 150
    assert analytics["daily_averages"]["calories"] == pytest.approx(150)


# --------------------------------------------------------------------------------------
# Public coroutine tests
# --------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_quick_log_food_success(tracker: consumption_system.ConsumptionTracker) -> None:
    """Happy-path: all internal helpers succeed and a success dict is returned."""

    with (
        mock.patch.object(tracker, "_get_ai_nutrition_analysis", return_value={
            "food_name": "banana",
            "estimated_portion": "1",
            "nutritional_info": {
                "calories": 100,
                "carbohydrates": 25,
                "protein": 1,
                "fat": 0,
            },
            "medical_rating": {"diabetes_suitability": "low"},
            "analysis_notes": "mocked notes",
        }),
        mock.patch.object(tracker, "_create_consumption_record", return_value={"id": "rec_123"}),
    ):
        result = await tracker.quick_log_food("user123", "banana")

    assert result == {
        "success": True,
        "record_id": "rec_123",
        "food_name": "banana",
        "nutritional_summary": {
            "calories": 100,
            "carbohydrates": 25,
            "protein": 1,
            "fat": 0,
        },
        "diabetes_rating": "low",
        "message": "Successfully logged banana",
    }


@pytest.mark.asyncio
async def test_quick_log_food_failure(tracker: consumption_system.ConsumptionTracker) -> None:
    """Failure path: internal helper raises and the coroutine propagates an error."""

    class SentinalError(RuntimeError):
        """Unique exception type for test clarity."""

    with mock.patch.object(tracker, "_get_ai_nutrition_analysis", side_effect=SentinalError):
        with pytest.raises(Exception):
            await tracker.quick_log_food("user", "item") 