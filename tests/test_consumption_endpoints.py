"""Tests for :pymod:`backend.consumption_endpoints` endpoints.

These unit tests call the standalone async endpoint functions directly while
mocking out the heavy tracker and authentication dependencies so that no I/O
occurs.
"""

from __future__ import annotations

import sys
from unittest import mock

import importlib
import pytest
from fastapi import HTTPException
import importlib.util, pathlib

MODULE_PATH = "backend.consumption_endpoints"

# Patch external modules before first import
sys.modules.setdefault("database", mock.MagicMock())  # used in fallback logic

# Ensure the relative import in the target module resolves
ROOT_DIR = pathlib.Path(__file__).resolve().parents[1]
cs_path = ROOT_DIR / "backend" / "consumption_system.py"
_spec = importlib.util.spec_from_file_location("backend.consumption_system", cs_path)
cons_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules[_spec.name] = cons_mod  # type: ignore[arg-type]
sys.modules.setdefault("consumption_system", cons_mod)  # alias for bare import
assert _spec.loader
_spec.loader.exec_module(cons_mod)  # type: ignore[attr-defined]

ce = importlib.import_module(MODULE_PATH)


class _DummyTracker:
    """Simple fake tracker with canned return values."""

    async def quick_log_food(self, user_id: str, food_name: str, portion: str = "medium"):
        return {"success": True, "record_id": "abc"}

    async def get_consumption_history(self, user_id: str, limit: int = 50):
        return [
            {"id": "r1", "food_name": "apple"},
            {"id": "r2", "food_name": "banana"},
        ]

    async def get_consumption_analytics(self, user_id: str, days: int = 30):
        return {"total_meals": 2}


@pytest.fixture(autouse=True)
def _patch_tracker(monkeypatch):
    """Globally patch ``get_tracker`` to return the dummy tracker."""

    monkeypatch.setattr(ce, "get_tracker", lambda: _DummyTracker())
    yield


@pytest.fixture()
def _user():
    return {"id": "user123"}


# -------------------------- quick_log_food_endpoint --------------------------


@pytest.mark.asyncio
async def test_quick_log_food_success(monkeypatch, _user):
    """Endpoint returns tracker result when input is valid."""

    monkeypatch.setattr(ce, "get_current_user", lambda _: _user)
    data = {"food_name": "apple", "portion": "small"}

    result = await ce.quick_log_food_endpoint(data, _user)  # type: ignore[arg-type]
    assert result["success"] is True
    assert result["record_id"] == "abc"


@pytest.mark.asyncio
async def test_quick_log_food_missing_name(monkeypatch, _user):
    """Missing food_name should raise 400 HTTPException."""

    monkeypatch.setattr(ce, "get_current_user", lambda _: _user)
    with pytest.raises(HTTPException) as exc:
        await ce.quick_log_food_endpoint({}, _user)  # type: ignore[arg-type]

    assert exc.value.status_code == 400


# ------------------- get_consumption_history / analytics --------------------


@pytest.mark.asyncio
async def test_consumption_history(monkeypatch, _user):
    monkeypatch.setattr(ce, "get_current_user", lambda _: _user)
    history = await ce.get_consumption_history_endpoint(50, _user)  # type: ignore[arg-type]

    assert len(history) == 2
    assert history[0]["food_name"] == "apple"


@pytest.mark.asyncio
async def test_consumption_analytics(monkeypatch, _user):
    monkeypatch.setattr(ce, "get_current_user", lambda _: _user)
    analytics = await ce.get_consumption_analytics_endpoint(7, _user)  # type: ignore[arg-type]

    assert analytics["total_meals"] == 2 