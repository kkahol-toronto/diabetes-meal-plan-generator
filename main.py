"""Convenience ASGI entrypoint.

Running `uvicorn main:app` from the project root now works; it simply
re-exports the FastAPI `app` instance defined in `backend/main.py`.
"""
import sys
import os

# Ensure the project root is on sys.path (it should be already, but be safe)
PROJECT_ROOT = os.path.dirname(__file__)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.main import app  # noqa: E402 