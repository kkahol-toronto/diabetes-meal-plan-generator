"""Application entry point for the Diabetes Meal-Plan Generator API.

This slim module *only* creates the :class:`fastapi.FastAPI` instance and
registers modular routers.  Business logic lives in ``backend/services`` and
route handlers in ``backend/routers``.
"""

import os, sys

# Allow running `uvicorn main:app` from inside the backend/ directory.
# When launched that way, Python needs the project root on sys.path so that
# absolute imports like ``backend.app...`` resolve correctly.
_CURRENT_DIR = os.path.dirname(__file__)
_PARENT_DIR = os.path.dirname(_CURRENT_DIR)
if _PARENT_DIR not in sys.path:
    sys.path.insert(0, _PARENT_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Routers – import paths must resolve quickly, so keep heavy deps in their own
# modules, **not** at top-level of this file.
from backend.app.routers.coach import router as coach_router  # existing router
from backend.app.routers.auth import router as auth_router  # login router
from backend.app.routers.compat import router as compat_router  # legacy fallbacks
from backend.app.routers.consumption import router as consumption_router  # consumption analytics
from backend.app.routers.meal_plans import router as meal_plans_router  # meal plans management

app = FastAPI(title="Diabetes Meal-Plan API")

# ---------------------------------------------------------------------------
# CORS (React dev-server runs on 3000, API on 8000)
# ---------------------------------------------------------------------------

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers under versioned prefix for future evolution.
API_PREFIX = "/api/v1"

auth_prefix = f"{API_PREFIX}/coach"
app.include_router(coach_router, prefix=auth_prefix, tags=["coach"])
app.include_router(coach_router, prefix="/coach", tags=["coach-root"])

# Expose login both at root and under the versioned prefix so frontend paths
# remain stable.
app.include_router(auth_router, tags=["auth"])
app.include_router(auth_router, prefix=API_PREFIX, tags=["auth-v1"])

# Mount legacy compatibility router first (no prefix) so its paths are available
app.include_router(compat_router, tags=["compat"])

# Mount consumption router for nutrition analytics
consumption_prefix = f"{API_PREFIX}/consumption"
app.include_router(consumption_router, prefix=consumption_prefix, tags=["consumption"])
app.include_router(consumption_router, prefix="/consumption", tags=["consumption-root"])

# Mount meal plans router for meal plan management
meal_plans_prefix = f"{API_PREFIX}/meal_plans"
app.include_router(meal_plans_router, prefix=meal_plans_prefix, tags=["meal-plans"])
app.include_router(meal_plans_router, prefix="/meal_plans", tags=["meal-plans-root"])

@app.get(f"{API_PREFIX}/health", tags=["misc"])
async def health_check() -> dict[str, str]:
    """Simple uptime probe for load-balancers and monitoring."""

    return {"status": "ok"} 