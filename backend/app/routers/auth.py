from __future__ import annotations

"""Authentication endpoints (login)."""

from datetime import datetime, timedelta
from typing import Any

import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt

from ..models.user import User
from ..utils.logger import logger

router = APIRouter()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
async def _authenticate_user(username: str, password: str) -> User | None:  # noqa: D401
    """Very naive credential check.

    In production this must be replaced by a real password verification against
    stored password hashes.  For development/demo purposes any non-empty
    credentials are accepted.
    """

    if username and password:
        return User(email=username)  # type: ignore[arg-type]
    return None


def _create_access_token(data: dict[str, Any], *, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):  # noqa: D401
    """Return an OAuth2 compatible *bearer* access token.

    This endpoint works with FastAPI's ``OAuth2PasswordBearer`` dependency used
    in :pyfunc:`backend.app.services.auth.get_current_user`.
    """

    user = await _authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.info("Failed login attempt for %s", form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = _create_access_token({"sub": user["email"]})
    logger.debug("User %s authenticated, token issued", user["email"])
    return {"access_token": access_token, "token_type": "bearer"} 