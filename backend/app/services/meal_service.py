"""Compatibility layer: exposes helpers expected by routers.

Some branches import `backend.app.services.meal_service`.  That module was
removed but the router is still importing it, causing runtime crashes.  We
provide lightweight wrappers that delegate to the real implementations in
`backend.database`.  This avoids touching every router file.
"""
from typing import Any, Dict, List

from backend.app import database as db

__all__ = [
    "get_user_meal_history",
    "get_user_profile",
]


async def get_user_meal_history(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Return recent meal history for a user."""
    if hasattr(db, "get_user_meal_history"):
        return await db.get_user_meal_history(user_id, limit)  # type: ignore[arg-type]

    # Fallback: return empty list to keep application functional even when
    # the actual database implementation is not wired up.  This should be
    # replaced once the Cosmos-DB helpers land in `backend/app/database`.
    return []


async def get_user_profile(email: str) -> Dict[str, Any] | None:
    """Return user profile by email (partition key/id)."""
    if hasattr(db, "get_user_by_email"):
        return await db.get_user_by_email(email)  # type: ignore[arg-type]

    # Fallback: return basic empty profile
    return {"dietary_restrictions": [], "health_conditions": []} 