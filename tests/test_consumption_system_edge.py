"""Edge-case tests for :pymod:`backend.consumption_system`"""

from __future__ import annotations

import sys
from unittest import mock

import importlib.util
import pathlib
import pytest

# patch dependencies
sys.modules.setdefault("database", mock.MagicMock())

ROOT = pathlib.Path(__file__).resolve().parents[1]
consumption_path = ROOT / "backend" / "consumption_system.py"

spec = importlib.util.spec_from_file_location("cons", consumption_path)
cons = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
sys.modules[spec.name] = cons  # type: ignore[arg-type]
assert spec.loader
spec.loader.exec_module(cons)  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_get_ai_nutrition_analysis_fallback(monkeypatch):
    """If OpenAI client is *not* initialised, tracker should return fallback data."""

    tracker = cons.ConsumptionTracker()
    # Ensure no client
    tracker.client = None

    result = await tracker._get_ai_nutrition_analysis("mystery dish", "small")
    assert result["food_name"] == "mystery dish"
    assert result["nutritional_info"]["calories"] == 200  # from fallback template 