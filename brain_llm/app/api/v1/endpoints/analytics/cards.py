"""
Insight Cards API Endpoints

RESTful API endpoints for insight card management including:
- Card CRUD operations
- Card query execution and refresh
- Card positioning and layout updates
- Pin queries to dashboards

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
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from fastapi.responses import JSONResponse

from app.models.analytics import (
    InsightCard,
    InsightCardCreate,
    InsightCardUpdate,
    CardExecutionResult,
)
from app.services.analytics import InsightCardService
from app.core.database import get_database_connection
import asyncpg

router = APIRouter(prefix="/cards", tags=["Analytics - Cards"])


async def get_card_service(
    db: asyncpg.Connection = Depends(get_database_connection)
) -> InsightCardService:
    """Dependency to get card service instance"""
    return InsightCardService(db)


# Mock user ID for now - replace with actual authentication
MOCK_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


@router.post(
    "/",
    response_model=InsightCard,
    status_code=201,
    summary="Create Card",
    description="Create a new insight card"
)
async def create_card(
    card_data: InsightCardCreate,
    service: InsightCardService = Depends(get_card_service)
) -> InsightCard:
    """
    Create a new insight card
    
    - **dashboard_id**: Target dashboard ID (required)
    - **title**: Card title (required)
    - **query_text**: Original natural language query (required)
    - **generated_sql**: Generated SQL query (required)
    - **database_type**: Database type (postgresql, mysql, sqlite, etc.)
    - **visualization_type**: Chart type (table, bar, line, pie, etc.)
    - **position_config**: Grid position and size
    - **refresh_frequency**: Auto-refresh frequency
    """
    try:
        card = await service.create_card(card_data, MOCK_USER_ID)
        return card
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{card_id}",
    response_model=InsightCard,
    summary="Get Card",
    description="Get insight card by ID"
)
async def get_card(
    card_id: UUID = Path(..., description="Card ID"),
    service: InsightCardService = Depends(get_card_service)
) -> InsightCard:
    """
    Get insight card by ID
    
    Returns the card if the user has access to its dashboard.
    """
    card = await service.get_card(card_id, MOCK_USER_ID)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return card


@router.put(
    "/{card_id}",
    response_model=InsightCard,
    summary="Update Card",
    description="Update insight card properties"
)
async def update_card(
    card_id: UUID = Path(..., description="Card ID"),
    updates: InsightCardUpdate = ...,
    service: InsightCardService = Depends(get_card_service)
) -> InsightCard:
    """
    Update insight card
    
    Users with edit permission on the dashboard can update cards.
    """
    card = await service.update_card(card_id, updates, MOCK_USER_ID)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found or no permission")
    return card


@router.delete(
    "/{card_id}",
    status_code=204,
    summary="Delete Card",
    description="Delete insight card (soft delete)"
)
async def delete_card(
    card_id: UUID = Path(..., description="Card ID"),
    service: InsightCardService = Depends(get_card_service)
):
    """
    Delete insight card
    
    Users with edit permission on the dashboard can delete cards.
    This is a soft delete - the card is marked as inactive.
    """
    success = await service.delete_card(card_id, MOCK_USER_ID)
    if not success:
        raise HTTPException(status_code=404, detail="Card not found or no permission")
    return JSONResponse(status_code=204, content=None)


@router.post(
    "/{card_id}/execute",
    response_model=CardExecutionResult,
    summary="Execute Card",
    description="Execute the card's query and return results"
)
async def execute_card(
    card_id: UUID = Path(..., description="Card ID"),
    service: InsightCardService = Depends(get_card_service)
) -> CardExecutionResult:
    """
    Execute card query
    
    Runs the card's SQL query against the configured database and returns the results.
    """
    card = await service.get_card(card_id, MOCK_USER_ID)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    result = await service.execute_card_query(card)
    return result


@router.post(
    "/{card_id}/refresh",
    response_model=CardExecutionResult,
    summary="Refresh Card",
    description="Refresh card data by re-executing its query"
)
async def refresh_card(
    card_id: UUID = Path(..., description="Card ID"),
    service: InsightCardService = Depends(get_card_service)
) -> CardExecutionResult:
    """
    Refresh card data
    
    Re-executes the card's query and updates the stored results.
    This is the same as execute_card but emphasizes the refresh action.
    """
    return await execute_card(card_id, service)


@router.post(
    "/pin-query",
    response_model=InsightCard,
    status_code=201,
    summary="Pin Query to Dashboard",
    description="Create a card from a chat query result"
)
async def pin_query_to_dashboard(
    pin_data: dict = Body(..., example={
        "dashboard_id": "123e4567-e89b-12d3-a456-426614174000",
        "title": "Monthly Sales Report",
        "query_text": "Show me the monthly sales for this year",
        "generated_sql": "SELECT DATE_TRUNC('month', order_date) as month, SUM(total) as sales FROM orders WHERE order_date >= '2024-01-01' GROUP BY month ORDER BY month",
        "database_type": "postgresql",
        "visualization_type": "bar_chart",
        "position": {"x": 0, "y": 0, "w": 6, "h": 4}
    }),
    service: InsightCardService = Depends(get_card_service)
) -> InsightCard:
    """
    Pin a query result to a dashboard
    
    This endpoint is designed to be called from the chat interface when users
    click "Pin to Dashboard" on a query result.
    
    Expected request body:
    - **dashboard_id**: Target dashboard ID
    - **title**: Card title
    - **query_text**: Original natural language query
    - **generated_sql**: Generated SQL query
    - **database_type**: Database type used
    - **visualization_type**: Preferred visualization
    - **position**: Optional grid position
    """
    try:
        # Convert the pin_data to InsightCardCreate model
        card_create_data = InsightCardCreate(
            dashboard_id=UUID(pin_data["dashboard_id"]),
            title=pin_data["title"],
            query_text=pin_data["query_text"],
            generated_sql=pin_data["generated_sql"],
            database_type=pin_data.get("database_type", "postgresql"),
            visualization_type=pin_data.get("visualization_type", "table"),
            position_config=pin_data.get("position", {"x": 0, "y": 0, "w": 6, "h": 4}),
        )
        
        card = await service.create_card(card_create_data, MOCK_USER_ID)
        
        # Immediately execute the card to populate it with data
        await service.execute_card_query(card)
        
        # Return the updated card
        updated_card = await service.get_card(card.id, MOCK_USER_ID)
        return updated_card
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing required field: {str(e)}")


@router.put(
    "/{card_id}/position",
    response_model=InsightCard,
    summary="Update Card Position",
    description="Update card position and size in the dashboard grid"
)
async def update_card_position(
    card_id: UUID = Path(..., description="Card ID"),
    position: dict = Body(..., example={"x": 6, "y": 0, "w": 6, "h": 4}),
    service: InsightCardService = Depends(get_card_service)
) -> InsightCard:
    """
    Update card position in dashboard grid
    
    This endpoint is called when users drag and resize cards in the dashboard.
    
    Position format:
    - **x**: Grid column position (0-based)
    - **y**: Grid row position (0-based) 
    - **w**: Width in grid columns
    - **h**: Height in grid rows
    """
    updates = InsightCardUpdate(position_config=position)
    card = await service.update_card(card_id, updates, MOCK_USER_ID)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found or no permission")
    return card


@router.get(
    "/{card_id}/data",
    summary="Get Card Data",
    description="Get the cached data for a card"
)
async def get_card_data(
    card_id: UUID = Path(..., description="Card ID"),
    service: InsightCardService = Depends(get_card_service)
):
    """
    Get cached card data
    
    Returns the last execution result for the card without re-executing the query.
    """
    card = await service.get_card(card_id, MOCK_USER_ID)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    return {
        "card_id": card_id,
        "title": card.title,
        "last_refreshed": card.last_refreshed,
        "data": card.last_result,
        "error": card.error_message,
        "visualization_type": card.visualization_type,
        "visualization_config": card.visualization_config
    }
