"""
Dashboard Service

This service handles all dashboard-related operations including:
- Dashboard CRUD operations
- Dashboard sharing and permissions
- Dashboard execution and refresh
- Dashboard analytics and metrics

Clean architecture principles:
- Single responsibility: Only handles dashboard logic
- Dependency injection: Database connection passed in
- Error handling: Comprehensive exception handling
- Type safety: Full type hints and validation
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
import asyncpg

from app.models.analytics import (
    Dashboard,
    DashboardCreate,
    DashboardUpdate,
    DashboardWithCards,
    DashboardListResponse,
    DashboardExecutionResult,
    CardExecutionResult,
)

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for managing dashboards and dashboard execution"""
    
    def __init__(self, db_connection: asyncpg.Connection):
        """Initialize with database connection"""
        self.db = db_connection
    
    async def create_dashboard(
        self, 
        dashboard_data: DashboardCreate, 
        user_id: UUID
    ) -> Dashboard:
        """
        Create a new dashboard
        
        Args:
            dashboard_data: Dashboard creation data
            user_id: Owner user ID
            
        Returns:
            Created dashboard
            
        Raises:
            ValueError: If dashboard data is invalid
            RuntimeError: If database operation fails
        """
        try:
            query = """
                INSERT INTO dashboards (user_id, name, description, layout_config, sharing_config)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, user_id, name, description, layout_config, sharing_config, 
                         is_active, created_at, updated_at
            """
            
            row = await self.db.fetchrow(
                query,
                user_id,
                dashboard_data.name,
                dashboard_data.description,
                json.dumps(dashboard_data.layout_config) if dashboard_data.layout_config else None,
                json.dumps(dashboard_data.sharing_config) if dashboard_data.sharing_config else None,
            )
            
            if not row:
                raise RuntimeError("Failed to create dashboard")
            
            # Convert database row to Dashboard model
            dashboard_dict = dict(row)
            dashboard_dict['layout_config'] = json.loads(dashboard_dict['layout_config'] or '{}')
            dashboard_dict['sharing_config'] = json.loads(dashboard_dict['sharing_config'] or '{}')
            
            logger.info(f"Created dashboard {row['id']} for user {user_id}")
            return Dashboard(**dashboard_dict)
            
        except Exception as e:
            logger.error(f"Error creating dashboard: {str(e)}")
            raise RuntimeError(f"Failed to create dashboard: {str(e)}")
    
    async def get_dashboard(self, dashboard_id: UUID, user_id: UUID) -> Optional[Dashboard]:
        """
        Get dashboard by ID with user permission check
        
        Args:
            dashboard_id: Dashboard ID
            user_id: Requesting user ID
            
        Returns:
            Dashboard if found and accessible, None otherwise
        """
        try:
            query = """
                SELECT d.id, d.user_id, d.name, d.description, d.layout_config, 
                       d.sharing_config, d.is_active, d.created_at, d.updated_at
                FROM dashboards d
                WHERE d.id = $1 
                  AND d.is_active = true
                  AND (d.user_id = $2 
                       OR EXISTS (
                           SELECT 1 FROM dashboard_shares ds 
                           WHERE ds.dashboard_id = d.id 
                             AND ds.shared_with_user_id = $2 
                             AND ds.is_active = true
                       )
                       OR (d.sharing_config->>'public')::boolean = true)
            """
            
            row = await self.db.fetchrow(query, dashboard_id, user_id)
            
            if not row:
                return None
            
            dashboard_dict = dict(row)
            dashboard_dict['layout_config'] = json.loads(dashboard_dict['layout_config'] or '{}')
            dashboard_dict['sharing_config'] = json.loads(dashboard_dict['sharing_config'] or '{}')
            
            return Dashboard(**dashboard_dict)
            
        except Exception as e:
            logger.error(f"Error getting dashboard {dashboard_id}: {str(e)}")
            return None
    
    async def get_dashboard_with_cards(
        self, 
        dashboard_id: UUID, 
        user_id: UUID
    ) -> Optional[DashboardWithCards]:
        """
        Get dashboard with all its cards loaded
        
        Args:
            dashboard_id: Dashboard ID
            user_id: Requesting user ID
            
        Returns:
            Dashboard with cards if found and accessible
        """
        dashboard = await self.get_dashboard(dashboard_id, user_id)
        if not dashboard:
            return None
        
        try:
            # Get all cards for this dashboard
            cards_query = """
                SELECT id, dashboard_id, title, query_text, generated_sql, 
                       database_type, database_config, visualization_type, 
                       visualization_config, position_config, refresh_frequency, 
                       auto_refresh_enabled, last_refreshed, last_result, 
                       error_message, is_active, created_at, updated_at
                FROM insight_cards
                WHERE dashboard_id = $1 AND is_active = true
                ORDER BY created_at ASC
            """
            
            card_rows = await self.db.fetch(cards_query, dashboard_id)
            
            # Convert cards to models
            cards = []
            for row in card_rows:
                card_dict = dict(row)
                card_dict['database_config'] = json.loads(card_dict['database_config'] or '{}')
                card_dict['visualization_config'] = json.loads(card_dict['visualization_config'] or '{}')
                card_dict['position_config'] = json.loads(card_dict['position_config'] or '{}')
                card_dict['last_result'] = json.loads(card_dict['last_result'] or 'null')
                
                from app.models.analytics import InsightCard
                cards.append(InsightCard(**card_dict))
            
            dashboard_dict = dashboard.dict()
            dashboard_dict['cards'] = cards
            
            return DashboardWithCards(**dashboard_dict)
            
        except Exception as e:
            logger.error(f"Error getting dashboard with cards {dashboard_id}: {str(e)}")
            return None
    
    async def list_user_dashboards(
        self, 
        user_id: UUID, 
        page: int = 1, 
        page_size: int = 20
    ) -> DashboardListResponse:
        """
        List dashboards accessible to user with pagination
        
        Args:
            user_id: User ID
            page: Page number (1-based)
            page_size: Items per page
            
        Returns:
            Paginated dashboard list
        """
        try:
            offset = (page - 1) * page_size
            
            # Get total count
            count_query = """
                SELECT COUNT(DISTINCT d.id)
                FROM dashboards d
                LEFT JOIN dashboard_shares ds ON d.id = ds.dashboard_id
                WHERE d.is_active = true
                  AND (d.user_id = $1 
                       OR (ds.shared_with_user_id = $1 AND ds.is_active = true)
                       OR (d.sharing_config->>'public')::boolean = true)
            """
            
            total = await self.db.fetchval(count_query, user_id)
            
            # Get dashboards
            dashboards_query = """
                SELECT DISTINCT d.id, d.user_id, d.name, d.description, 
                       d.layout_config, d.sharing_config, d.is_active, 
                       d.created_at, d.updated_at
                FROM dashboards d
                LEFT JOIN dashboard_shares ds ON d.id = ds.dashboard_id
                WHERE d.is_active = true
                  AND (d.user_id = $1 
                       OR (ds.shared_with_user_id = $1 AND ds.is_active = true)
                       OR (d.sharing_config->>'public')::boolean = true)
                ORDER BY d.updated_at DESC
                LIMIT $2 OFFSET $3
            """
            
            rows = await self.db.fetch(dashboards_query, user_id, page_size, offset)
            
            dashboards = []
            for row in rows:
                dashboard_dict = dict(row)
                dashboard_dict['layout_config'] = json.loads(dashboard_dict['layout_config'] or '{}')
                dashboard_dict['sharing_config'] = json.loads(dashboard_dict['sharing_config'] or '{}')
                dashboards.append(Dashboard(**dashboard_dict))
            
            return DashboardListResponse(
                dashboards=dashboards,
                total=total or 0,
                page=page,
                page_size=page_size
            )
            
        except Exception as e:
            logger.error(f"Error listing user dashboards: {str(e)}")
            return DashboardListResponse(dashboards=[], total=0, page=page, page_size=page_size)
    
    async def update_dashboard(
        self, 
        dashboard_id: UUID, 
        updates: DashboardUpdate, 
        user_id: UUID
    ) -> Optional[Dashboard]:
        """
        Update dashboard (owner only)
        
        Args:
            dashboard_id: Dashboard ID
            updates: Update data
            user_id: Requesting user ID
            
        Returns:
            Updated dashboard if successful
        """
        try:
            # Check ownership
            ownership_check = await self.db.fetchval(
                "SELECT user_id FROM dashboards WHERE id = $1 AND is_active = true",
                dashboard_id
            )
            
            if not ownership_check or ownership_check != user_id:
                return None
            
            # Build update query dynamically
            update_fields = []
            values = []
            param_count = 1
            
            if updates.name is not None:
                update_fields.append(f"name = ${param_count}")
                values.append(updates.name)
                param_count += 1
                
            if updates.description is not None:
                update_fields.append(f"description = ${param_count}")
                values.append(updates.description)
                param_count += 1
                
            if updates.layout_config is not None:
                update_fields.append(f"layout_config = ${param_count}")
                values.append(json.dumps(updates.layout_config))
                param_count += 1
                
            if updates.sharing_config is not None:
                update_fields.append(f"sharing_config = ${param_count}")
                values.append(json.dumps(updates.sharing_config))
                param_count += 1
                
            if updates.is_active is not None:
                update_fields.append(f"is_active = ${param_count}")
                values.append(updates.is_active)
                param_count += 1
            
            if not update_fields:
                # No updates to apply
                return await self.get_dashboard(dashboard_id, user_id)
            
            # Add dashboard_id to values
            values.append(dashboard_id)
            
            query = f"""
                UPDATE dashboards 
                SET {', '.join(update_fields)}
                WHERE id = ${param_count}
                RETURNING id, user_id, name, description, layout_config, 
                         sharing_config, is_active, created_at, updated_at
            """
            
            row = await self.db.fetchrow(query, *values)
            
            if not row:
                return None
            
            dashboard_dict = dict(row)
            dashboard_dict['layout_config'] = json.loads(dashboard_dict['layout_config'] or '{}')
            dashboard_dict['sharing_config'] = json.loads(dashboard_dict['sharing_config'] or '{}')
            
            logger.info(f"Updated dashboard {dashboard_id}")
            return Dashboard(**dashboard_dict)
            
        except Exception as e:
            logger.error(f"Error updating dashboard {dashboard_id}: {str(e)}")
            return None
    
    async def delete_dashboard(self, dashboard_id: UUID, user_id: UUID) -> bool:
        """
        Soft delete dashboard (owner only)
        
        Args:
            dashboard_id: Dashboard ID
            user_id: Requesting user ID
            
        Returns:
            True if deleted successfully
        """
        try:
            result = await self.db.fetchval(
                """
                UPDATE dashboards 
                SET is_active = false 
                WHERE id = $1 AND user_id = $2 AND is_active = true
                RETURNING id
                """,
                dashboard_id,
                user_id
            )
            
            success = result is not None
            if success:
                logger.info(f"Deleted dashboard {dashboard_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting dashboard {dashboard_id}: {str(e)}")
            return False
