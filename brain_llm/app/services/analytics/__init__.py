"""
Analytics Services Package

This package contains all business logic services for the analytics dashboard feature.
Services follow clean architecture principles and are organized by domain responsibility.

Service Architecture:
- DashboardService: Dashboard CRUD and management
- InsightCardService: Card operations and execution
- QueryExecutionService: Database query execution (to be implemented)
- SharingService: Dashboard sharing and permissions (to be implemented)

Design Principles:
- Single Responsibility: Each service has one clear purpose
- Dependency Injection: Services receive their dependencies
- Error Handling: Comprehensive exception handling
- Type Safety: Full type hints and validation
- Performance: Caching, parallel execution, and optimization
"""

from .dashboard_service import DashboardService
from .card_service import InsightCardService

__all__ = [
    "DashboardService",
    "InsightCardService",
]
