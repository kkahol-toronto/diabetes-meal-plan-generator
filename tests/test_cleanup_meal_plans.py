"""Tests for :pymod:`backend.cleanup_meal_plans`.

We validate both *happy* and *failure* paths of the fallback-deletion logic. All
Azure Cosmos calls are replaced with :pyclass:`unittest.mock.Mock` objects so
no network access occurs during testing.
"""

from __future__ import annotations

from unittest import mock

import importlib
import sys

# Create a dummy azure.cosmos module so that runtime import in the target module succeeds
sys.modules.setdefault("azure", mock.MagicMock())
sys.modules.setdefault("azure.cosmos", mock.MagicMock())
sys.modules.setdefault("azure.cosmos.exceptions", mock.MagicMock())

MODULE_NAME = "backend.cleanup_meal_plans"

cleanup_meal_plans = importlib.import_module(MODULE_NAME)

def _make_mock_container(delete_side_effects):
    """Utility: returns a mock container with configured side effects."""
    container = mock.Mock()
    container.query_items.return_value = [{
        "id": "doc1",
        "session_id": "sess1",
        "user_id": cleanup_meal_plans.USER_EMAIL,
        "type": "meal_plan",
    }]
    # The function under test calls delete_item up to three times per doc.
    container.delete_item.side_effect = delete_side_effects
    return container


def test_main_deletes_with_fallbacks() -> None:
    """Happy path: second partition_key succeeds after first raises NotFound."""

    # Simulate the CosmosResourceNotFoundError using a simple Exception subclass.
    class FakeNotFound(Exception):
        """Stand-in for CosmosResourceNotFoundError."""

    # Patch the module's exception reference so that the except block works
    cleanup_meal_plans.exceptions.CosmosResourceNotFoundError = FakeNotFound

    delete_effects = [FakeNotFound(), None]
    mock_container = _make_mock_container(delete_effects)

    with mock.patch.object(cleanup_meal_plans, "CosmosClient") as mock_client_class, \
         mock.patch.object(cleanup_meal_plans, "print"):
        # Wire up mock database + container chain
        mock_client = mock_client_class.from_connection_string.return_value
        mock_db = mock_client.get_database_client.return_value
        mock_db.get_container_client.return_value = mock_container

        cleanup_meal_plans.main()

    # Expect delete_item called at least twice with different partition keys
    assert mock_container.delete_item.call_count >= 2
    first_pk = mock_container.delete_item.call_args_list[0].kwargs["partition_key"]
    second_pk = mock_container.delete_item.call_args_list[1].kwargs["partition_key"]
    assert first_pk == "sess1"
    assert second_pk == "doc1"


# --------------------------------------------------------------------------------------
# Failure-path: item never deleted despite fallbacks
# --------------------------------------------------------------------------------------


def test_main_unable_to_delete(monkeypatch):
    """When *all* delete attempts raise, function should continue gracefully."""

    class FakeNotFound(Exception):
        """Stand-in for the Cosmos *not found* error."""

    # Ensure cleanup_meal_plans catches our fake error type
    cleanup_meal_plans.exceptions.CosmosResourceNotFoundError = FakeNotFound

    # Every delete attempt raises FakeNotFound
    mock_container = _make_mock_container([FakeNotFound(), FakeNotFound(), FakeNotFound()])

    # Patch CosmosClient path and silence prints
    with mock.patch.object(cleanup_meal_plans, "CosmosClient") as mock_client_class, \
         mock.patch.object(cleanup_meal_plans, "print"):
        mock_client = mock_client_class.from_connection_string.return_value
        mock_db = mock_client.get_database_client.return_value
        mock_db.get_container_client.return_value = mock_container

        # Should not raise even though nothing could be deleted
        cleanup_meal_plans.main()

    # Three attempts for each of three strategies = 3 calls
    assert mock_container.delete_item.call_count == 3 