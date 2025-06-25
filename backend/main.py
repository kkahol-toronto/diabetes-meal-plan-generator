"""Application entry point for the Diabetes Meal-Plan Generator API.

This slim module *only* creates the :class:`fastapi.FastAPI` instance and
registers modular routers.  Business logic lives in ``backend/services`` and
route handlers in ``backend/routers``.
"""

from fastapi import FastAPI

# Routers – import paths must resolve quickly, so keep heavy deps in their own
# modules, **not** at top-level of this file.
from backend.app.routers.coach import router as coach_router  # existing router

app = FastAPI(title="Diabetes Meal-Plan API")

# Mount routers under versioned prefix for future evolution.
API_PREFIX = "/api/v1"

auth_prefix = f"{API_PREFIX}/coach"
app.include_router(coach_router, prefix=auth_prefix, tags=["coach"])


@app.get(f"{API_PREFIX}/health", tags=["misc"])
async def health_check() -> dict[str, str]:
    """Simple uptime probe for load-balancers and monitoring."""

    return {"status": "ok"} 