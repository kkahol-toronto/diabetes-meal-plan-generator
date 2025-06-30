from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
import os

# Re-use database connection & models from the primary backend
try:
    from backend.app.database.dependencies import get_db  # type: ignore
    from backend.app.models.user import User              # type: ignore
except ModuleNotFoundError:
    # Fallback stubs when backend package is not importable (e.g. during CI linting)
    def get_db():
        yield None

    class User(dict):
        pass


ADMIN_PORTAL_TITLE = "Diabetes Diet Manager – Admin Portal"
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

app = FastAPI(title=ADMIN_PORTAL_TITLE, docs_url="/docs", redoc_url="/redoc")

# Mount static assets (CSS / JS)
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)


@app.get("/", response_class=HTMLResponse, tags=["Admin Panel"])
async def admin_panel(request: Request, db=Depends(get_db)):
    """Render the main admin panel table with all registered users."""

    # TODO: Replace this stub with real user retrieval logic from Cosmos DB
    users: List[User]
    if db:
        # Example when using an ORM: users = db.query(User).all()
        users = []  # pragma: no cover
    else:
        # Stub data for development without a database connection
        users = [
            User(id="1", name="Alice", phone="1234567890", condition="Diabetes", code="ABC123", created="2025-05-14 12:46:16"),
            User(id="2", name="Bob", phone="0987654321", condition="Diabetes", code="XYZ987", created="2025-05-26 18:21:23"),
        ]

    return templates.TemplateResponse("admin_panel.html", {"request": request, "users": users, "title": ADMIN_PORTAL_TITLE})


@app.get("/users/{user_id}", response_class=HTMLResponse, tags=["Admin Panel"])
async def user_profile(user_id: str, request: Request, db=Depends(get_db)):
    """Display (and eventually edit) the comprehensive health profile for a single user."""

    # TODO: Fetch the real user document/profile from the database
    user: User | None
    if db:
        # Example ORM style; adjust for Cosmos DB SDK as needed
        user = None  # pragma: no cover
    else:
        # Stub profile matching the meal-plan generation form fields (simplified)
        user = User(
            id=user_id,
            full_name="John Doe",
            date_of_birth="2005-11-10",
            age=19,
            sex="Male",
            height_cm=175,
            weight_kg=63,
            bmi="20.6 (Normal)",
            waist_cm=56,
            bp_systolic=120,
            bp_diastolic=77,
            heart_rate=72,
        )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return templates.TemplateResponse("profile.html", {"request": request, "user": user, "title": ADMIN_PORTAL_TITLE}) 