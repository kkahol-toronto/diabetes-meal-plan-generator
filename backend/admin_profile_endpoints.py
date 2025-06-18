from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import TYPE_CHECKING
from fastapi.security import OAuth2PasswordBearer

from database import get_user_by_email, user_container

# Lazy import utilities from backend.main inside endpoint functions to avoid circular imports
if TYPE_CHECKING:
    # Only for type hints to avoid runtime circular imports
    from main import User  # noqa: F401

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def _current_user(token: str = Depends(oauth2_scheme)):
    # Import at runtime to avoid circular ref
    from main import get_current_user  # type: ignore
    return await get_current_user(token)

def _get_auth_dependencies():
    """Import get_current_user and User at runtime to avoid circular import issues."""
    from main import get_current_user, User  # type: ignore
    return get_current_user, User

router = APIRouter(prefix="/admin", tags=["Admin Profile"])

class AdminProfileUpdateRequest(BaseModel):
    """Schema for admin profile update payloads"""
    profile: dict

# Helper to fetch a user either by email or linked patient_id
async def _get_user_by_identifier(identifier: str):
    # Try primary key (email)
    user = await get_user_by_email(identifier)
    if user:
        return user
    # Fallback: query by patient_id linkage
    query = f"SELECT * FROM c WHERE c.type = 'user' AND c.patient_id = '{identifier}'"
    items = list(user_container.query_items(query=query, enable_cross_partition_query=True))
    return items[0] if items else None

@router.get("/profile/{identifier}")
async def admin_get_user_profile(identifier: str, current_user=Depends(_current_user)):
    """Retrieve any user's profile given their email or patient_id (admin only)."""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    user_doc = await _get_user_by_identifier(identifier)
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    return {"profile": user_doc.get("profile", {})}

@router.post("/profile/{identifier}")
async def admin_update_user_profile(identifier: str, payload: AdminProfileUpdateRequest, current_user=Depends(_current_user)):
    """Create or update a user's profile (admin only)."""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    user_doc = await _get_user_by_identifier(identifier)
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    existing_profile = user_doc.get("profile", {})
    updated_profile = {**existing_profile, **payload.profile}
    user_doc["profile"] = updated_profile
    user_container.replace_item(item=user_doc["id"], body=user_doc)
    return {"message": "Profile updated successfully", "profile": updated_profile} 