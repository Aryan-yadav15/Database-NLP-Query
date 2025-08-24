"""
Analytics Models Package

This package contains all Pydantic models for the analytics dashboard feature.
Models are organized by domain to maintain clean separation of concerns.
"""

from .dashboard import (
    # Dashboard models
    Dashboard,
    DashboardBase,
    DashboardCreate,
    DashboardUpdate,
    DashboardWithCards,
    DashboardListResponse,
    
    # Insight card models
    InsightCard,
    InsightCardBase,
    InsightCardCreate,
    InsightCardUpdate,
    
    # Comment models
    DashboardComment,
    DashboardCommentBase,
    DashboardCommentCreate,
    DashboardCommentUpdate,
    
    # Sharing models
    DashboardShare,
    DashboardShareBase,
    DashboardShareCreate,
    
    # Execution result models
    CardExecutionResult,
    DashboardExecutionResult,
    
    # Constants
    REFRESH_FREQUENCIES,
    VISUALIZATION_TYPES,
)

__all__ = [
    # Dashboard models
    "Dashboard",
    "DashboardBase", 
    "DashboardCreate",
    "DashboardUpdate",
    "DashboardWithCards",
    "DashboardListResponse",
    
    # Insight card models
    "InsightCard",
    "InsightCardBase",
    "InsightCardCreate", 
    "InsightCardUpdate",
    
    # Comment models
    "DashboardComment",
    "DashboardCommentBase",
    "DashboardCommentCreate",
    "DashboardCommentUpdate",
    
    # Sharing models
    "DashboardShare",
    "DashboardShareBase",
    "DashboardShareCreate",
    
    # Execution result models
    "CardExecutionResult",
    "DashboardExecutionResult",
    
    # Constants
    "REFRESH_FREQUENCIES",
    "VISUALIZATION_TYPES",
]
