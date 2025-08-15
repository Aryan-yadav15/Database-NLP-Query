"""
PostgreSQL Database Connector Module
====================================

This module provides robust PostgreSQL database connectivity for the Brain LLM application.
It offers both direct connections and FastAPI-compatible dependency injection patterns.

Key Features:
- Connection pooling and resource management
- Automatic connection cleanup using context managers
- RealDictCursor for dictionary-style result access
- Separate functions for startup vs. request-scoped connections
- Comprehensive error handling and logging

Database Integration:
- Primary database: AdventureWorks sample database
- Connection parameters sourced from centralized configuration
- Supports both synchronous and asynchronous operations

Author: Brain LLM Team
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Generator
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def get_pg_connection_for_startup():
    """
    Create a direct PostgreSQL connection for application startup operations.
    
    This function is specifically designed for one-time startup tasks such as:
    - Database schema introspection
    - Initial data validation
    - Configuration verification
    
    Unlike request-scoped connections, this returns a raw connection object
    that must be manually closed by the caller.
    
    Returns:
        psycopg2.extensions.connection: Direct database connection or None if failed
        
    Error Handling:
        - Logs connection errors but returns None instead of raising exceptions
        - Allows application to continue with fallback configurations
        
    Usage:
        conn = get_pg_connection_for_startup()
        if conn:
            try:
                # Perform startup operations
                cursor = conn.cursor()
                # ... database operations ...
            finally:
                conn.close()  # Always close the connection
    """
    try:
        connection = psycopg2.connect(
            host=settings.PG_HOST,
            port=settings.PG_PORT,
            database=settings.PG_DATABASE_AW,
            user=settings.PG_USER,
            password=settings.PG_PASSWORD
        )
        return connection
    except psycopg2.Error as e:
        logger.error(f"Error connecting to PostgreSQL during startup: {e}")
        return None

def get_aw_db_conn() -> Generator[psycopg2.extensions.connection, None, None]:
    """
    Create a request-scoped PostgreSQL connection to the AdventureWorks database.
    
    This function implements a context manager pattern that automatically handles
    connection lifecycle management including cleanup in case of exceptions.
    
    Features:
    - Automatic connection cleanup via generator pattern
    - RealDictCursor for dictionary-style result access
    - Comprehensive error handling and logging
    - Resource leak prevention through guaranteed cleanup
    
    Returns:
        Generator[psycopg2.extensions.connection]: Database connection context manager
        
    Yields:
        psycopg2.extensions.connection: Active database connection with RealDictCursor
        
    Raises:
        psycopg2.Error: Re-raised after logging for upstream error handling
        
    Example Usage:
        for connection in get_aw_db_conn():
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM customers")
            results = cursor.fetchall()  # Returns list of dictionaries
            
    Note:
        The connection is automatically closed when the generator exits,
        even if an exception occurs during database operations.
    """
    try:
        # Establish connection with dictionary cursor for easier data access
        connection = psycopg2.connect(
            host=settings.PG_HOST,
            port=settings.PG_PORT,
            database=settings.PG_DATABASE_AW,
            user=settings.PG_USER,
            password=settings.PG_PASSWORD,
            cursor_factory=RealDictCursor  # Returns results as dictionaries instead of tuples
        )
        logger.info("Successfully connected to AdventureWorks database")
        yield connection
    except psycopg2.Error as e:
        logger.error(f"Error connecting to AdventureWorks database: {e}")
        raise  # Re-raise for upstream error handling
    finally:
        # Guaranteed cleanup: close connection even if exceptions occur
        if 'connection' in locals() and connection is not None:
            connection.close()
            logger.info("Database connection closed")

def get_adventureworks_db_session() -> Generator[psycopg2.extensions.connection, None, None]:
    """
    FastAPI dependency-compatible database session provider.
    
    This function serves as an alias for get_aw_db_conn() with a more descriptive
    name that clearly indicates its intended use as a FastAPI dependency.
    
    The function name follows FastAPI naming conventions for dependency injection
    and makes the codebase more readable when used in endpoint definitions.
    
    Returns:
        Generator[psycopg2.extensions.connection]: Database connection context manager
        
    Usage in FastAPI endpoints:
        @router.post("/query")
        async def process_query(
            request: QueryRequest,
            db: psycopg2.extensions.connection = Depends(get_adventureworks_db_session)
        ):
            # Use db connection for query processing
            cursor = db.cursor()
            # ... database operations ...
            
    Note:
        This is functionally identical to get_aw_db_conn() but provides
        semantic clarity when used as a dependency injection provider.
    """
    yield from get_aw_db_conn()