"""
Routers package for FastAPI application
"""
from . import auth
from . import admin
from . import analyze
from . import health  # ✅ health router'ını da ekleyin

__all__ = ["auth", "admin", "analyze", "health"]