"""
Analytics API Package

This package contains all API endpoints for the analytics dashboard feature.
Endpoints are organized by domain to maintain clean separation of concerns.

API Structure:
- dashboards.py: Dashboard CRUD and management endpoints
- cards.py: Insight card operations and execution endpoints
- sharing.py: Dashboard sharing and permissions (to be implemented)

Design Principles:
- RESTful conventions
- Proper HTTP status codes
- Comprehensive error handling
- Input validation with Pydantic
- OpenAPI documentation
- Clean separation of concerns
"""

from .dashboards import router as dashboards_router
from .cards import router as cards_router

__all__ = [
    "dashboards_router",
    "cards_router",
]
