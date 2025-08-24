"""
Analytics Dashboard Models

This module contains Pydantic models for the analytics dashboard feature.
These models provide type validation, serialization, and API documentation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, validator


class DashboardBase(BaseModel):
    """Base dashboard model with common fields"""
    name: str = Field(..., min_length=1, max_length=255, description="Dashboard name")
    description: Optional[str] = Field(None, description="Dashboard description")


class DashboardCreate(DashboardBase):
    """Model for creating a new dashboard"""
    layout_config: Optional[Dict[str, Any]] = Field(
        default={
            "breakpoints": {"lg": 1200, "md": 996, "sm": 768, "xs": 480, "xxs": 0},
            "cols": {"lg": 12, "md": 10, "sm": 6, "xs": 4, "xxs": 2}
        },
        description="Grid layout configuration"
    )
    sharing_config: Optional[Dict[str, Any]] = Field(
        default={"public": False, "permissions": []},
        description="Dashboard sharing settings"
    )


class DashboardUpdate(BaseModel):
    """Model for updating an existing dashboard"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    layout_config: Optional[Dict[str, Any]] = None
    sharing_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class Dashboard(DashboardBase):
    """Complete dashboard model"""
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID = Field(..., description="Owner user ID")
    layout_config: Dict[str, Any] = Field(default_factory=dict)
    sharing_config: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    
    # Related data
    cards: Optional[List['InsightCard']] = None
    
    class Config:
        from_attributes = True


class InsightCardBase(BaseModel):
    """Base insight card model"""
    title: str = Field(..., min_length=1, max_length=255, description="Card title")
    query_text: str = Field(..., min_length=1, description="Original natural language query")
    generated_sql: str = Field(..., min_length=1, description="Generated SQL query")
    database_type: str = Field(default="postgresql", description="Database type")
    database_config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Database connection config")


class InsightCardCreate(InsightCardBase):
    """Model for creating a new insight card"""
    dashboard_id: UUID = Field(..., description="Parent dashboard ID")
    visualization_type: str = Field(default="table", description="Chart type: table, bar, line, pie, etc.")
    visualization_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    position_config: Optional[Dict[str, Any]] = Field(
        default={"x": 0, "y": 0, "w": 6, "h": 4},
        description="Grid position and size"
    )
    refresh_frequency: str = Field(default="manual", description="Refresh frequency: manual, hourly, daily, weekly")
    auto_refresh_enabled: bool = Field(default=False, description="Enable automatic refresh")


class InsightCardUpdate(BaseModel):
    """Model for updating an existing insight card"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    query_text: Optional[str] = None
    generated_sql: Optional[str] = None
    database_type: Optional[str] = None
    database_config: Optional[Dict[str, Any]] = None
    visualization_type: Optional[str] = None
    visualization_config: Optional[Dict[str, Any]] = None
    position_config: Optional[Dict[str, Any]] = None
    refresh_frequency: Optional[str] = None
    auto_refresh_enabled: Optional[bool] = None
    is_active: Optional[bool] = None


class InsightCard(InsightCardBase):
    """Complete insight card model"""
    id: UUID = Field(default_factory=uuid4)
    dashboard_id: UUID
    visualization_type: str = "table"
    visualization_config: Dict[str, Any] = Field(default_factory=dict)
    position_config: Dict[str, Any] = Field(default_factory=dict)
    refresh_frequency: str = "manual"
    auto_refresh_enabled: bool = False
    last_refreshed: Optional[datetime] = None
    last_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    
    # Related data
    comments: Optional[List['DashboardComment']] = None
    
    class Config:
        from_attributes = True


class DashboardCommentBase(BaseModel):
    """Base comment model"""
    comment_text: str = Field(..., min_length=1, description="Comment content")


class DashboardCommentCreate(DashboardCommentBase):
    """Model for creating a new comment"""
    card_id: UUID = Field(..., description="Target card ID")
    user_id: UUID = Field(..., description="Comment author ID")


class DashboardCommentUpdate(BaseModel):
    """Model for updating a comment"""
    comment_text: Optional[str] = Field(None, min_length=1)
    is_resolved: Optional[bool] = None


class DashboardComment(DashboardCommentBase):
    """Complete comment model"""
    id: UUID = Field(default_factory=uuid4)
    card_id: UUID
    user_id: UUID
    is_resolved: bool = False
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DashboardShareBase(BaseModel):
    """Base sharing model"""
    permission_level: Literal["view", "edit", "admin"] = Field(default="view", description="Access level")


class DashboardShareCreate(DashboardShareBase):
    """Model for creating a sharing link"""
    dashboard_id: UUID = Field(..., description="Dashboard to share")
    shared_with_user_id: Optional[UUID] = Field(None, description="Specific user ID (None for public)")
    expires_at: Optional[datetime] = Field(None, description="Link expiration time")


class DashboardShare(DashboardShareBase):
    """Complete sharing model"""
    id: UUID = Field(default_factory=uuid4)
    dashboard_id: UUID
    shared_with_user_id: Optional[UUID] = None
    access_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime
    
    class Config:
        from_attributes = True


class DashboardWithCards(Dashboard):
    """Dashboard model with loaded cards"""
    cards: List[InsightCard] = Field(default_factory=list)


class DashboardListResponse(BaseModel):
    """Response model for dashboard listing"""
    dashboards: List[Dashboard]
    total: int
    page: int
    page_size: int


class CardExecutionResult(BaseModel):
    """Result of executing a card's query"""
    card_id: UUID
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    last_refreshed: datetime


class DashboardExecutionResult(BaseModel):
    """Result of executing all cards in a dashboard"""
    dashboard_id: UUID
    results: List[CardExecutionResult]
    total_execution_time: float
    success_count: int
    error_count: int


# Refresh frequency options
REFRESH_FREQUENCIES = [
    "manual",
    "every_5_minutes", 
    "every_15_minutes",
    "every_30_minutes",
    "hourly",
    "daily",
    "weekly",
    "monthly"
]

# Visualization types
VISUALIZATION_TYPES = [
    "table",
    "bar_chart",
    "line_chart", 
    "pie_chart",
    "scatter_plot",
    "area_chart",
    "kpi_card",
    "text_card"
]

# Update forward references
Dashboard.model_rebuild()
InsightCard.model_rebuild()
