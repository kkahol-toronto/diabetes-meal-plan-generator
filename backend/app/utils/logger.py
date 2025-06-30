from __future__ import annotations

"""Shared logger for backend components.

Import this module instead of configuring ``logging`` in every file to avoid
duplicate handlers and inconsistent formats.
"""

import logging
import sys
from types import ModuleType
from typing import Any

__all__ = ["logger"]

_NAME = "diabetes-meal-plan"
logger = logging.getLogger(_NAME)

if not logger.handlers:
    # Root logger configuration is performed once – subsequent imports are
    # idempotent thanks to the "handlers" check.
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)

    # Avoid duplicate log propagation to the root logger.
    logger.propagate = False

# Expose a stub for typing completeness in test suites that monkey-patch
# ``backend.app.utils.logger`` before import time.

def __getattr__(name: str) -> Any:  # pragma: no cover
    if name == "logger":
        return logger
    raise AttributeError(name) 