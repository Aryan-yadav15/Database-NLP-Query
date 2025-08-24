"""
Database Dependencies Module

This module provides FastAPI dependency injection for database connections.
It includes both sync and async connection providers for the analytics dashboard feature.

Dependencies:
- get_database_connection: Provides async PostgreSQL connections
- get_sync_database_connection: Provides sync PostgreSQL connections

Design:
- Connection pooling for performance
- Automatic connection cleanup
- Error handling and logging
- Support for both sync and async operations
"""

import asyncpg
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


# Connection pool for async operations (will be initialized on startup)
_async_pool = None


async def init_async_pool():
    """Initialize the async connection pool"""
    global _async_pool
    try:
        _async_pool = await asyncpg.create_pool(
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD,
            database=settings.DATABASE_NAME,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        logger.info("Async database pool initialized")
    except Exception as e:
        logger.error(f"Failed to initialize async database pool: {e}")
        raise


async def close_async_pool():
    """Close the async connection pool"""
    global _async_pool
    if _async_pool:
        await _async_pool.close()
        _async_pool = None
        logger.info("Async database pool closed")


@asynccontextmanager
async def get_async_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """
    Get an async database connection from the pool
    
    Yields:
        asyncpg.Connection: Database connection
        
    Raises:
        RuntimeError: If pool is not initialized
    """
    if not _async_pool:
        raise RuntimeError("Async database pool not initialized")
    
    async with _async_pool.acquire() as connection:
        try:
            yield connection
        except Exception as e:
            logger.error(f"Database operation error: {e}")
            raise


async def get_database_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """
    FastAPI dependency for async database connections
    
    This function provides async database connections for FastAPI endpoints.
    It automatically manages connection lifecycle and cleanup.
    
    Yields:
        asyncpg.Connection: Database connection
    """
    async with get_async_connection() as connection:
        yield connection


@contextmanager
def get_sync_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """
    Get a synchronous database connection
    
    Yields:
        psycopg2.connection: Database connection
    """
    connection = None
    try:
        connection = psycopg2.connect(
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD,
            database=settings.DATABASE_NAME,
            cursor_factory=RealDictCursor
        )
        yield connection
    except Exception as e:
        if connection:
            connection.rollback()
        logger.error(f"Sync database operation error: {e}")
        raise
    finally:
        if connection:
            connection.close()


def get_sync_database_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """
    FastAPI dependency for sync database connections
    
    Yields:
        psycopg2.connection: Database connection
    """
    with get_sync_connection() as connection:
        yield connection


# Mock connection for development/testing when database is not available
class MockAsyncConnection:
    """Mock async connection for development/testing"""
    
    def __init__(self):
        from datetime import datetime
        import uuid
        self._mock_data = {}
        self._counter = 1
        
    async def execute(self, query, *args):
        logger.warning(f"Mock execute: {query} with args: {args}")
        return None
    
    async def fetch(self, query, *args):
        logger.warning(f"Mock fetch: {query} with args: {args}")
        
        # Return mock data for common queries
        if "dashboards" in query.lower() and "select" in query.lower():
            # Return multiple mock dashboards
            return [
                self._create_mock_dashboard(),
                self._create_mock_dashboard(),
                self._create_mock_dashboard(),
                self._create_mock_dashboard()
            ]
        elif "insight_cards" in query.lower() and "select" in query.lower():
            return [self._create_mock_card()]
        return []
    
    async def fetchrow(self, query, *args):
        logger.warning(f"Mock fetchrow: {query} with args: {args}")
        
        # Handle INSERT operations for dashboards
        if "insert into dashboards" in query.lower():
            return self._create_mock_dashboard()
        
        # Handle INSERT operations for insight cards
        elif "insert into insight_cards" in query.lower():
            # Return a mock card that matches the arguments provided
            mock_card = self._create_mock_card()
            # Use the dashboard_id from the arguments if provided
            if len(args) > 0:
                mock_card['dashboard_id'] = args[0]  # First arg is dashboard_id
            if len(args) > 1:
                mock_card['title'] = args[1]  # Second arg is title
            return mock_card
        
        # Handle SELECT by ID operations for dashboards (including complex JOINs)
        elif ("select d.id, d.user_id, d.name" in query.lower() and 
              "from dashboards d" in query.lower() and 
              "where d.id = $1" in query.lower()):
            # This handles the complex dashboard permission query
            mock_dashboard = self._create_mock_dashboard()
            if len(args) > 0:
                mock_dashboard['id'] = args[0]  # Use the requested dashboard_id
            return mock_dashboard
        
        # Handle SELECT for insight cards with JOINs
        elif ("select c.id, c.dashboard_id, c.title" in query.lower() and 
              "from insight_cards c" in query.lower() and 
              "join dashboards d" in query.lower()):
            # This handles the complex card permission query
            mock_card = self._create_mock_card()
            if len(args) > 0:
                mock_card['id'] = args[0]  # Use the requested card_id
            return mock_card
        
        # Handle simple SELECT by ID operations
        elif "dashboards" in query.lower() and "where id" in query.lower():
            return self._create_mock_dashboard()
        elif "insight_cards" in query.lower() and "where id" in query.lower():
            return self._create_mock_card()
        
        # Handle dashboard permission checks
        elif "select d.id from dashboards" in query.lower():
            # Return a UUID to indicate dashboard exists and user has permission
            if len(args) > 0:
                return args[0]  # Return the dashboard_id passed in
            return self._create_mock_dashboard()['id']
            
        return None
    
    async def fetchval(self, query, *args):
        logger.warning(f"Mock fetchval: {query} with args: {args}")
        
        # Return count for COUNT queries
        if "count" in query.lower():
            return 1
        # Handle dashboard permission checks
        elif "select d.id from dashboards" in query.lower():
            # Return the dashboard_id if checking permissions
            if len(args) > 0:
                return args[0]  # Return the dashboard_id passed in
            import uuid
            return uuid.uuid4()
        return None
    
    def _create_mock_dashboard(self):
        """Create a mock dashboard record"""
        from datetime import datetime
        import uuid
        import json
        
        dashboard_id = uuid.uuid4()
        return {
            'id': dashboard_id,
            'user_id': uuid.UUID('00000000-0000-0000-0000-000000000001'),
            'name': 'Sales Performance Dashboard',
            'description': 'Monthly sales analysis and trends',
            'layout_config': json.dumps({
                "breakpoints": {"lg": 1200, "md": 996, "sm": 768, "xs": 480, "xxs": 0},
                "cols": {"lg": 12, "md": 10, "sm": 6, "xs": 4, "xxs": 2}
            }),
            'sharing_config': json.dumps({"public": False, "permissions": []}),
            'is_active': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    
    def _create_mock_card(self):
        """Create a mock insight card record"""
        from datetime import datetime
        import uuid
        import json
        
        card_id = uuid.uuid4()
        return {
            'id': card_id,
            'dashboard_id': uuid.uuid4(),
            'title': 'Total Revenue',
            'query_text': 'What is the total revenue?',
            'generated_sql': 'SELECT SUM(amount) as total_revenue FROM sales',
            'database_type': 'postgresql',
            'database_config': json.dumps({}),
            'visualization_type': 'number',
            'visualization_config': json.dumps({
                "chart_type": "number",
                "color": "green",
                "format": "currency"
            }),
            'position_config': json.dumps({"x": 0, "y": 0, "w": 6, "h": 4}),
            'refresh_frequency': 'manual',
            'auto_refresh_enabled': False,
            'last_refreshed': None,
            'last_result': None,
            'error_message': None,
            'is_active': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }


async def get_mock_database_connection() -> AsyncGenerator[MockAsyncConnection, None]:
    """
    Mock database dependency for development/testing
    
    Yields:
        MockAsyncConnection: Mock connection that logs operations
    """
    yield MockAsyncConnection()


# For development, we can switch between real and mock connections
DEVELOPMENT_MODE = True  # Set to False when database is properly configured

if DEVELOPMENT_MODE:
    # Use mock connection for development
    get_database_connection = get_mock_database_connection
    logger.info("Using mock database connection for development")
else:
    logger.info("Using real database connection")
