"""Tests for the `get_meal_suggestion` route in :pymod:`backend.app.routers.coach`."""

from __future__ import annotations

import sys
from unittest import mock

import pytest
from fastapi import HTTPException

# Stub heavy service modules before import
for module in [
    "backend.app.services.meal_service",
    "backend.app.services.auth",
    "backend.app.services.ai_service",
    "backend.app.utils.logger",
]:
    sys.modules.setdefault(module, mock.MagicMock())

from backend.app.routers import coach  # noqa: E402  # import after stubs


@pytest.mark.asyncio
async def test_get_meal_suggestion_success(monkeypatch):
    """Route returns success=True when downstream service responds."""

    # Arrange mocks
    current_user = mock.MagicMock(email="test@example.com")
    monkeypatch.setattr(coach, "get_current_user", lambda: current_user)

    meal_profile = {"dietary_restrictions": ["vegan"], "health_conditions": []}
    meal_history = []

    coach.get_user_profile = mock.AsyncMock(return_value=meal_profile)  # type: ignore[attr-defined]
    coach.get_user_meal_history = mock.AsyncMock(return_value=meal_history)  # type: ignore[attr-defined]
    coach.get_ai_suggestion = mock.AsyncMock(return_value={"text": "Mock meal"})  # type: ignore[attr-defined]

    payload = {"meal_type": "dinner", "remaining_calories": 500}

    response = await coach.get_meal_suggestion(payload, current_user)

    assert response["success"] is True
    assert "suggestion" in response


@pytest.mark.asyncio
async def test_get_meal_suggestion_handles_error(monkeypatch):
    """If internal logic raises, route should return success=False"""

    current_user = mock.MagicMock(email="test@example.com")
    monkeypatch.setattr(coach, "get_current_user", lambda: current_user)

    # Force get_user_profile to raise
    coach.get_user_profile = mock.AsyncMock(side_effect=RuntimeError("db down"))  # type: ignore[attr-defined]

    payload = {}
    resp = await coach.get_meal_suggestion(payload, current_user)
    assert resp["success"] is False
    assert "error" in resp 