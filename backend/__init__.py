"""Backend package initialization.

This file ensures that auxiliary endpoint modules such as `admin_profile_endpoints` are
imported when the backend package is loaded, so their routes are registered with the
FastAPI application defined in `backend.main`.
"""

# Import side-effect modules that register additional routers
from . import admin_profile_endpoints  # noqa: F401 