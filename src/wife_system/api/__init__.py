"""FastAPI boundary for the wife-system service."""

from wife_system.api.app import app, create_app

__all__ = ["app", "create_app"]
