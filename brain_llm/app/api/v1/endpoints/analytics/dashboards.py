"""
Dashboard API Endpoints

RESTful API endpoints for dashboard management including:
- Dashboard CRUD operations
- Dashboard listing and search
- Dashboard sharing and permissions
- Dashboard execution and refresh

API Design:
- RESTful conventions
- Proper HTTP status codes
- Comprehensive error handling
- Input validation
- Documentation with OpenAPI
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.responses import JSONResponse

from app.models.analytics import (
    Dashboard,
    DashboardCreate,
    DashboardUpdate,
    DashboardWithCards,
    DashboardListResponse,
    DashboardExecutionResult,
)
from app.services.analytics import DashboardService, InsightCardService
from app.core.database import get_database_connection
import asyncpg

router = APIRouter(prefix="/dashboards", tags=["Analytics - Dashboards"])


async def get_dashboard_service(
    db: asyncpg.Connection = Depends(get_database_connection)
) -> DashboardService:
    """Dependency to get dashboard service instance"""
    return DashboardService(db)


async def get_card_service(
    db: asyncpg.Connection = Depends(get_database_connection)
) -> InsightCardService:
    """Dependency to get card service instance"""
    return InsightCardService(db)


# Mock user ID for now - replace with actual authentication
MOCK_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


@router.post(
    "/",
    response_model=Dashboard,
    status_code=201,
    summary="Create Dashboard",
    description="Create a new analytics dashboard"
)
async def create_dashboard(
    dashboard_data: DashboardCreate,
    service: DashboardService = Depends(get_dashboard_service)
) -> Dashboard:
    """
    Create a new dashboard
    
    - **name**: Dashboard name (required)
    - **description**: Optional description
    - **layout_config**: Grid layout configuration
    - **sharing_config**: Sharing and permissions settings
    """
    try:
        dashboard = await service.create_dashboard(dashboard_data, MOCK_USER_ID)
        return dashboard
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/",
    response_model=DashboardListResponse,
    summary="List Dashboards",
    description="Get paginated list of dashboards accessible to user"
)
async def list_dashboards(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    service: DashboardService = Depends(get_dashboard_service)
) -> DashboardListResponse:
    """
    List dashboards with pagination
    
    Returns dashboards that the user owns, has been shared with, or are public.
    """
    return await service.list_user_dashboards(MOCK_USER_ID, page, page_size)


@router.get(
    "/{dashboard_id}",
    response_model=Dashboard,
    summary="Get Dashboard",
    description="Get dashboard by ID"
)
async def get_dashboard(
    dashboard_id: UUID = Path(..., description="Dashboard ID"),
    service: DashboardService = Depends(get_dashboard_service)
) -> Dashboard:
    """
    Get dashboard by ID
    
    Returns the dashboard if the user has access to it.
    """
    dashboard = await service.get_dashboard(dashboard_id, MOCK_USER_ID)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.get(
    "/{dashboard_id}/full",
    response_model=DashboardWithCards,
    summary="Get Dashboard with Cards",
    description="Get dashboard with all its cards loaded"
)
async def get_dashboard_with_cards(
    dashboard_id: UUID = Path(..., description="Dashboard ID"),
    service: DashboardService = Depends(get_dashboard_service)
) -> DashboardWithCards:
    """
    Get dashboard with all cards loaded
    
    Returns the dashboard with all its insight cards included.
    """
    dashboard = await service.get_dashboard_with_cards(dashboard_id, MOCK_USER_ID)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.put(
    "/{dashboard_id}",
    response_model=Dashboard,
    summary="Update Dashboard",
    description="Update dashboard properties"
)
async def update_dashboard(
    dashboard_id: UUID = Path(..., description="Dashboard ID"),
    updates: DashboardUpdate = ...,
    service: DashboardService = Depends(get_dashboard_service)
) -> Dashboard:
    """
    Update dashboard
    
    Only the dashboard owner can update the dashboard.
    """
    dashboard = await service.update_dashboard(dashboard_id, updates, MOCK_USER_ID)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found or no permission")
    return dashboard


@router.delete(
    "/{dashboard_id}",
    status_code=204,
    summary="Delete Dashboard",
    description="Delete dashboard (soft delete)"
)
async def delete_dashboard(
    dashboard_id: UUID = Path(..., description="Dashboard ID"),
    service: DashboardService = Depends(get_dashboard_service)
):
    """
    Delete dashboard
    
    Only the dashboard owner can delete the dashboard.
    This is a soft delete - the dashboard is marked as inactive.
    """
    success = await service.delete_dashboard(dashboard_id, MOCK_USER_ID)
    if not success:
        raise HTTPException(status_code=404, detail="Dashboard not found or no permission")
    return JSONResponse(status_code=204, content=None)


@router.post(
    "/{dashboard_id}/refresh",
    response_model=DashboardExecutionResult,
    summary="Refresh Dashboard",
    description="Execute all cards in the dashboard"
)
async def refresh_dashboard(
    dashboard_id: UUID = Path(..., description="Dashboard ID"),
    card_service: InsightCardService = Depends(get_card_service)
) -> DashboardExecutionResult:
    """
    Refresh all cards in the dashboard
    
    Executes all active cards in parallel and returns the results.
    """
    result = await card_service.refresh_dashboard_cards(dashboard_id, MOCK_USER_ID)
    if not result:
        raise HTTPException(status_code=404, detail="Dashboard not found or no cards")
    return result


@router.get(
    "/{dashboard_id}/status",
    summary="Dashboard Status",
    description="Get dashboard execution status and statistics"
)
async def get_dashboard_status(
    dashboard_id: UUID = Path(..., description="Dashboard ID"),
    service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get dashboard status and statistics
    
    Returns information about the dashboard's cards, last refresh times, etc.
    """
    dashboard = await service.get_dashboard_with_cards(dashboard_id, MOCK_USER_ID)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    total_cards = len(dashboard.cards) if dashboard.cards else 0
    active_cards = len([c for c in dashboard.cards if c.is_active]) if dashboard.cards else 0
    cards_with_data = len([c for c in dashboard.cards if c.last_result]) if dashboard.cards else 0
    cards_with_errors = len([c for c in dashboard.cards if c.error_message]) if dashboard.cards else 0
    
    last_refresh = None
    if dashboard.cards:
        last_refreshed_cards = [c for c in dashboard.cards if c.last_refreshed]
        if last_refreshed_cards:
            last_refresh = max(c.last_refreshed for c in last_refreshed_cards)
    
    return {
        "dashboard_id": dashboard_id,
        "name": dashboard.name,
        "total_cards": total_cards,
        "active_cards": active_cards,
        "cards_with_data": cards_with_data,
        "cards_with_errors": cards_with_errors,
        "last_refresh": last_refresh,
        "created_at": dashboard.created_at,
        "updated_at": dashboard.updated_at
    }
