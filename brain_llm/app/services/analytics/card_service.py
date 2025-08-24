"""
Insight Card Service

This service handles all insight card operations including:
- Card CRUD operations
- Card query execution and refresh
- Card positioning and layout management
- Card data caching and performance optimization

Clean architecture principles:
- Single responsibility: Only handles card logic
- Dependency injection: Database connection and query service passed in
- Error handling: Comprehensive exception handling
- Performance: Caching and parallel execution
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
import asyncpg

from app.models.analytics import (
    InsightCard,
    InsightCardCreate,
    InsightCardUpdate,
    CardExecutionResult,
    DashboardExecutionResult,
)

logger = logging.getLogger(__name__)


class InsightCardService:
    """Service for managing insight cards and card execution"""
    
    def __init__(self, db_connection: asyncpg.Connection):
        """Initialize with database connection"""
        self.db = db_connection
    
    async def create_card(
        self, 
        card_data: InsightCardCreate, 
        user_id: UUID
    ) -> Optional[InsightCard]:
        """
        Create a new insight card
        
        Args:
            card_data: Card creation data
            user_id: User creating the card
            
        Returns:
            Created card if successful
            
        Raises:
            ValueError: If card data is invalid
            RuntimeError: If database operation fails
        """
        try:
            # Verify user has access to dashboard
            dashboard_check = await self.db.fetchval(
                """
                SELECT d.id FROM dashboards d
                LEFT JOIN dashboard_shares ds ON d.id = ds.dashboard_id
                WHERE d.id = $1 
                  AND d.is_active = true
                  AND (d.user_id = $2 
                       OR (ds.shared_with_user_id = $2 AND ds.is_active = true AND ds.permission_level IN ('edit', 'admin'))
                       OR (d.sharing_config->>'public')::boolean = true)
                """,
                card_data.dashboard_id,
                user_id
            )
            
            if not dashboard_check:
                raise ValueError("Dashboard not found or no edit permission")
            
            query = """
                INSERT INTO insight_cards (
                    dashboard_id, title, query_text, generated_sql, database_type,
                    database_config, visualization_type, visualization_config,
                    position_config, refresh_frequency, auto_refresh_enabled
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING id, dashboard_id, title, query_text, generated_sql, 
                         database_type, database_config, visualization_type, 
                         visualization_config, position_config, refresh_frequency, 
                         auto_refresh_enabled, last_refreshed, last_result, 
                         error_message, is_active, created_at, updated_at
            """
            
            row = await self.db.fetchrow(
                query,
                card_data.dashboard_id,
                card_data.title,
                card_data.query_text,
                card_data.generated_sql,
                card_data.database_type,
                json.dumps(card_data.database_config) if card_data.database_config else None,
                card_data.visualization_type,
                json.dumps(card_data.visualization_config) if card_data.visualization_config else None,
                json.dumps(card_data.position_config) if card_data.position_config else None,
                card_data.refresh_frequency,
                card_data.auto_refresh_enabled,
            )
            
            if not row:
                raise RuntimeError("Failed to create card")
            
            card_dict = dict(row)
            card_dict['database_config'] = json.loads(card_dict['database_config'] or '{}')
            card_dict['visualization_config'] = json.loads(card_dict['visualization_config'] or '{}')
            card_dict['position_config'] = json.loads(card_dict['position_config'] or '{}')
            card_dict['last_result'] = json.loads(card_dict['last_result'] or 'null')
            
            logger.info(f"Created card {row['id']} for dashboard {card_data.dashboard_id}")
            return InsightCard(**card_dict)
            
        except Exception as e:
            logger.error(f"Error creating card: {str(e)}")
            raise RuntimeError(f"Failed to create card: {str(e)}")
    
    async def get_card(self, card_id: UUID, user_id: UUID) -> Optional[InsightCard]:
        """
        Get card by ID with user permission check
        
        Args:
            card_id: Card ID
            user_id: Requesting user ID
            
        Returns:
            Card if found and accessible
        """
        try:
            query = """
                SELECT c.id, c.dashboard_id, c.title, c.query_text, c.generated_sql, 
                       c.database_type, c.database_config, c.visualization_type, 
                       c.visualization_config, c.position_config, c.refresh_frequency, 
                       c.auto_refresh_enabled, c.last_refreshed, c.last_result, 
                       c.error_message, c.is_active, c.created_at, c.updated_at
                FROM insight_cards c
                JOIN dashboards d ON c.dashboard_id = d.id
                LEFT JOIN dashboard_shares ds ON d.id = ds.dashboard_id
                WHERE c.id = $1 
                  AND c.is_active = true
                  AND d.is_active = true
                  AND (d.user_id = $2 
                       OR (ds.shared_with_user_id = $2 AND ds.is_active = true)
                       OR (d.sharing_config->>'public')::boolean = true)
            """
            
            row = await self.db.fetchrow(query, card_id, user_id)
            
            if not row:
                return None
            
            card_dict = dict(row)
            card_dict['database_config'] = json.loads(card_dict['database_config'] or '{}')
            card_dict['visualization_config'] = json.loads(card_dict['visualization_config'] or '{}')
            card_dict['position_config'] = json.loads(card_dict['position_config'] or '{}')
            card_dict['last_result'] = json.loads(card_dict['last_result'] or 'null')
            
            return InsightCard(**card_dict)
            
        except Exception as e:
            logger.error(f"Error getting card {card_id}: {str(e)}")
            return None
    
    async def update_card(
        self, 
        card_id: UUID, 
        updates: InsightCardUpdate, 
        user_id: UUID
    ) -> Optional[InsightCard]:
        """
        Update card (with permission check)
        
        Args:
            card_id: Card ID
            updates: Update data
            user_id: Requesting user ID
            
        Returns:
            Updated card if successful
        """
        try:
            # Check permission
            permission_check = await self.db.fetchval(
                """
                SELECT d.user_id FROM insight_cards c
                JOIN dashboards d ON c.dashboard_id = d.id
                LEFT JOIN dashboard_shares ds ON d.id = ds.dashboard_id
                WHERE c.id = $1 
                  AND c.is_active = true
                  AND d.is_active = true
                  AND (d.user_id = $2 
                       OR (ds.shared_with_user_id = $2 AND ds.is_active = true AND ds.permission_level IN ('edit', 'admin')))
                """,
                card_id,
                user_id
            )
            
            if not permission_check:
                return None
            
            # Build update query dynamically
            update_fields = []
            values = []
            param_count = 1
            
            if updates.title is not None:
                update_fields.append(f"title = ${param_count}")
                values.append(updates.title)
                param_count += 1
                
            if updates.query_text is not None:
                update_fields.append(f"query_text = ${param_count}")
                values.append(updates.query_text)
                param_count += 1
                
            if updates.generated_sql is not None:
                update_fields.append(f"generated_sql = ${param_count}")
                values.append(updates.generated_sql)
                param_count += 1
                
            if updates.database_type is not None:
                update_fields.append(f"database_type = ${param_count}")
                values.append(updates.database_type)
                param_count += 1
                
            if updates.database_config is not None:
                update_fields.append(f"database_config = ${param_count}")
                values.append(json.dumps(updates.database_config))
                param_count += 1
                
            if updates.visualization_type is not None:
                update_fields.append(f"visualization_type = ${param_count}")
                values.append(updates.visualization_type)
                param_count += 1
                
            if updates.visualization_config is not None:
                update_fields.append(f"visualization_config = ${param_count}")
                values.append(json.dumps(updates.visualization_config))
                param_count += 1
                
            if updates.position_config is not None:
                update_fields.append(f"position_config = ${param_count}")
                values.append(json.dumps(updates.position_config))
                param_count += 1
                
            if updates.refresh_frequency is not None:
                update_fields.append(f"refresh_frequency = ${param_count}")
                values.append(updates.refresh_frequency)
                param_count += 1
                
            if updates.auto_refresh_enabled is not None:
                update_fields.append(f"auto_refresh_enabled = ${param_count}")
                values.append(updates.auto_refresh_enabled)
                param_count += 1
                
            if updates.is_active is not None:
                update_fields.append(f"is_active = ${param_count}")
                values.append(updates.is_active)
                param_count += 1
            
            if not update_fields:
                return await self.get_card(card_id, user_id)
            
            # Add card_id to values
            values.append(card_id)
            
            query = f"""
                UPDATE insight_cards 
                SET {', '.join(update_fields)}
                WHERE id = ${param_count}
                RETURNING id, dashboard_id, title, query_text, generated_sql, 
                         database_type, database_config, visualization_type, 
                         visualization_config, position_config, refresh_frequency, 
                         auto_refresh_enabled, last_refreshed, last_result, 
                         error_message, is_active, created_at, updated_at
            """
            
            row = await self.db.fetchrow(query, *values)
            
            if not row:
                return None
            
            card_dict = dict(row)
            card_dict['database_config'] = json.loads(card_dict['database_config'] or '{}')
            card_dict['visualization_config'] = json.loads(card_dict['visualization_config'] or '{}')
            card_dict['position_config'] = json.loads(card_dict['position_config'] or '{}')
            card_dict['last_result'] = json.loads(card_dict['last_result'] or 'null')
            
            logger.info(f"Updated card {card_id}")
            return InsightCard(**card_dict)
            
        except Exception as e:
            logger.error(f"Error updating card {card_id}: {str(e)}")
            return None
    
    async def delete_card(self, card_id: UUID, user_id: UUID) -> bool:
        """
        Soft delete card (with permission check)
        
        Args:
            card_id: Card ID
            user_id: Requesting user ID
            
        Returns:
            True if deleted successfully
        """
        try:
            result = await self.db.fetchval(
                """
                UPDATE insight_cards 
                SET is_active = false 
                WHERE id = $1 
                  AND EXISTS (
                      SELECT 1 FROM dashboards d
                      LEFT JOIN dashboard_shares ds ON d.id = ds.dashboard_id
                      WHERE d.id = insight_cards.dashboard_id 
                        AND d.is_active = true
                        AND (d.user_id = $2 
                             OR (ds.shared_with_user_id = $2 AND ds.is_active = true AND ds.permission_level IN ('edit', 'admin')))
                  )
                  AND is_active = true
                RETURNING id
                """,
                card_id,
                user_id
            )
            
            success = result is not None
            if success:
                logger.info(f"Deleted card {card_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting card {card_id}: {str(e)}")
            return False
    
    async def execute_card_query(self, card: InsightCard) -> CardExecutionResult:
        """
        Execute a card's query and return the result
        
        Args:
            card: Card to execute
            
        Returns:
            Execution result with data or error
        """
        start_time = datetime.now()
        
        try:
            # This will be implemented when we integrate with the query service
            # For now, return a mock successful result
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Mock data for now
            mock_data = {
                "columns": ["id", "name", "value"],
                "rows": [
                    [1, "Sample Data", 100],
                    [2, "Test Record", 200],
                    [3, "Example Row", 300]
                ],
                "total_rows": 3
            }
            
            # Update card's last_refreshed and result
            await self.db.execute(
                """
                UPDATE insight_cards 
                SET last_refreshed = $1, last_result = $2, error_message = NULL
                WHERE id = $3
                """,
                start_time,
                json.dumps(mock_data),
                card.id
            )
            
            return CardExecutionResult(
                card_id=card.id,
                success=True,
                data=mock_data,
                execution_time=execution_time,
                last_refreshed=start_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_message = str(e)
            
            # Update card with error
            await self.db.execute(
                """
                UPDATE insight_cards 
                SET error_message = $1, last_refreshed = $2
                WHERE id = $3
                """,
                error_message,
                start_time,
                card.id
            )
            
            logger.error(f"Error executing card {card.id}: {error_message}")
            
            return CardExecutionResult(
                card_id=card.id,
                success=False,
                error=error_message,
                execution_time=execution_time,
                last_refreshed=start_time
            )
    
    async def refresh_dashboard_cards(
        self, 
        dashboard_id: UUID, 
        user_id: UUID
    ) -> Optional[DashboardExecutionResult]:
        """
        Execute all cards in a dashboard in parallel
        
        Args:
            dashboard_id: Dashboard ID
            user_id: Requesting user ID
            
        Returns:
            Dashboard execution result
        """
        try:
            # Get all active cards for the dashboard
            cards_query = """
                SELECT id, dashboard_id, title, query_text, generated_sql, 
                       database_type, database_config, visualization_type, 
                       visualization_config, position_config, refresh_frequency, 
                       auto_refresh_enabled, last_refreshed, last_result, 
                       error_message, is_active, created_at, updated_at
                FROM insight_cards c
                JOIN dashboards d ON c.dashboard_id = d.id
                LEFT JOIN dashboard_shares ds ON d.id = ds.dashboard_id
                WHERE c.dashboard_id = $1 
                  AND c.is_active = true
                  AND d.is_active = true
                  AND (d.user_id = $2 
                       OR (ds.shared_with_user_id = $2 AND ds.is_active = true)
                       OR (d.sharing_config->>'public')::boolean = true)
                ORDER BY c.created_at ASC
            """
            
            card_rows = await self.db.fetch(cards_query, dashboard_id, user_id)
            
            if not card_rows:
                return None
            
            # Convert to InsightCard objects
            cards = []
            for row in card_rows:
                card_dict = dict(row)
                card_dict['database_config'] = json.loads(card_dict['database_config'] or '{}')
                card_dict['visualization_config'] = json.loads(card_dict['visualization_config'] or '{}')
                card_dict['position_config'] = json.loads(card_dict['position_config'] or '{}')
                card_dict['last_result'] = json.loads(card_dict['last_result'] or 'null')
                cards.append(InsightCard(**card_dict))
            
            # Execute all cards in parallel
            start_time = datetime.now()
            tasks = [self.execute_card_query(card) for card in cards]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            execution_results = []
            success_count = 0
            error_count = 0
            
            for result in results:
                if isinstance(result, Exception):
                    error_count += 1
                    execution_results.append(
                        CardExecutionResult(
                            card_id=cards[len(execution_results)].id,
                            success=False,
                            error=str(result),
                            execution_time=0,
                            last_refreshed=datetime.now()
                        )
                    )
                else:
                    execution_results.append(result)
                    if result.success:
                        success_count += 1
                    else:
                        error_count += 1
            
            total_execution_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Refreshed {len(cards)} cards for dashboard {dashboard_id}")
            
            return DashboardExecutionResult(
                dashboard_id=dashboard_id,
                results=execution_results,
                total_execution_time=total_execution_time,
                success_count=success_count,
                error_count=error_count
            )
            
        except Exception as e:
            logger.error(f"Error refreshing dashboard cards {dashboard_id}: {str(e)}")
            return None
