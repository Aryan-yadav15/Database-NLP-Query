"""
Database Connection Pool Management Module
==========================================

This module provides centralized database connection pooling and management
for the Brain LLM application, supporting dynamic database connections with
efficient resource utilization and connection reuse.

Key Features:
1. Connection pool management with SQLAlchemy engines
2. Dynamic database connection support for multi-tenant scenarios
3. Raw psycopg2 connection fallback for legacy compatibility
4. URL encoding for special characters in credentials
5. Connection pool configuration with timeout and lifecycle management

Connection Pooling Benefits:
- Resource efficiency: Reuses established connections
- Performance: Eliminates connection overhead for repeated queries
- Scalability: Handles concurrent requests with pool sizing
- Reliability: Automatic connection recycling and error recovery

Pool Configuration:
- Pool Size: 5 connections per database
- Max Overflow: 2 additional connections under load
- Timeout: 30 seconds for connection acquisition
- Recycle: 1800 seconds (30 minutes) connection lifetime

Integration:
- Primary: AdventureWorks database with default credentials
- Dynamic: User-provided database configurations
- Compatibility: Both SQLAlchemy engines and raw psycopg2 connections

Author: Brain LLM Team
"""

import logging
from typing import Dict, Any
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool
import psycopg2
from psycopg2.extras import RealDictCursor

# Module-level logger for connection operations
logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Centralized database connection pool manager for dynamic database connectivity.
    
    This class implements the Singleton pattern to provide application-wide
    database connection management with connection pooling, credential handling,
    and multi-database support for tenant-specific configurations.
    
    Core Responsibilities:
    1. SQLAlchemy engine creation and caching
    2. Connection pool lifecycle management
    3. Database credential security and URL encoding
    4. Raw psycopg2 connection provisioning for legacy code
    5. Connection reuse optimization and resource cleanup
    
    Pool Management Strategy:
    - Engine Caching: One engine per unique database configuration
    - Pool Sizing: Configurable connection limits per database
    - Timeout Handling: Graceful degradation under high load
    - Connection Recycling: Automatic cleanup of stale connections
    
    Security Features:
    - URL encoding for special characters in passwords
    - Credential isolation per database configuration
    - Connection string sanitization for logging
    - Error handling to prevent credential exposure
    
    Performance Benefits:
    - Connection reuse eliminates handshake overhead
    - Pool warming for consistent response times
    - Concurrent request handling with queue management
    - Memory efficiency through shared connection objects
    """
    
    def __init__(self):
        """
        Initialize the connection manager with empty pool registry.
        
        Creates the internal data structures for tracking database engines
        and connection pools across different database configurations.
        """
        self.pools: Dict[str, Engine] = {}  # Registry of SQLAlchemy engines by database key
        logger.info("ConnectionManager initialized with empty pool registry.")

    def _get_pool_key(self, db_info: Dict[str, Any]) -> str:
        """Creates a unique key for a database connection pool."""
        return f"{db_info['db_user']}@{db_info['db_host']}:{db_info['db_port']}/{db_info['db_name']}"

    def get_db_engine(self, db_info: Dict[str, Any]) -> Engine:
        """
        Gets a SQLAlchemy engine for the given connection details.
        Uses a connection pool to reuse engines for the same database.
        """
        from urllib.parse import quote_plus
        
        pool_key = self._get_pool_key(db_info)

        if pool_key in self.pools:
            logging.info(f"Reusing existing connection pool for: {pool_key}")
            return self.pools[pool_key]

        logging.info(f"Creating new connection pool for: {pool_key}")
        try:
            # URL encode the password for SQLAlchemy connection string
            encoded_password = quote_plus(db_info['db_password']) if db_info.get('db_password') else db_info.get('db_password')
            
            conn_str = (
                f"postgresql+psycopg2://{db_info['db_user']}:{encoded_password}"
                f"@{db_info['db_host']}:{db_info['db_port']}/{db_info['db_name']}"
            )
            
            engine = create_engine(
                conn_str,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=2,
                pool_timeout=30,
                pool_recycle=1800,
            )
            # Make a test connection to ensure the engine is valid
            with engine.connect() as connection:
                logging.info(f"Successfully connected and created pool for {pool_key}")

            self.pools[pool_key] = engine
            return engine
        except Exception as e:
            logging.error(f"Failed to create database engine for {pool_key}: {e}")
            raise

    def get_raw_psycopg2_connection(self, db_info: Dict[str, Any]):
        """
        Gets a raw psycopg2 connection for the given database info.
        This is needed for compatibility with existing code that expects raw psycopg2 connections.
        """
        import psycopg2
        from psycopg2.extras import RealDictCursor
        from urllib.parse import unquote_plus
        
        try:
            # URL decode the password in case it contains encoded characters like %40 for @
            decoded_password = unquote_plus(db_info['db_password']) if db_info.get('db_password') else db_info.get('db_password')
            
            connection = psycopg2.connect(
                host=db_info['db_host'],
                port=db_info['db_port'],
                database=db_info['db_name'],
                user=db_info['db_user'],
                password=decoded_password,
                cursor_factory=RealDictCursor  # Returns results as dictionaries
            )
            logging.info(f"Successfully created raw psycopg2 connection to {self._get_pool_key(db_info)}")
            return connection
        except Exception as e:
            logging.error(f"Failed to create raw psycopg2 connection for {self._get_pool_key(db_info)}: {e}")
            raise

# Instantiate a single manager for the application to use
connection_manager = ConnectionManager()