"""
Enhanced Database Connection Pool Management Module
=================================================

This module provides centralized database connection pooling and management
for the Brain LLM application, supporting multiple database types through
the new database service architecture while maintaining backward compatibility.

Key Features:
1. Multi-database support (PostgreSQL, MySQL, SQLite, Snowflake)
2. Database service factory integration
3. Connection pool management with SQLAlchemy engines
4. Dynamic database connection support for multi-tenant scenarios
5. Raw connection fallback for legacy compatibility
6. URL encoding for special characters in credentials
7. Connection pool configuration with timeout and lifecycle management

Enhanced Architecture:
- Database Service Layer: Unified interface for all database types
- Service Caching: Efficient database service reuse
- Connection Pooling: Per-database type and configuration
- Backward Compatibility: Existing code continues to work unchanged

Connection Pooling Benefits:
- Resource efficiency: Reuses established connections
- Performance: Eliminates connection overhead for repeated queries
- Scalability: Handles concurrent requests with pool sizing
- Reliability: Automatic connection recycling and error recovery

Pool Configuration:
- Pool Size: 5 connections per database
- Max Overflow: 10 additional connections under load (enhanced)
- Timeout: 30 seconds for connection acquisition
- Recycle: 3600 seconds (1 hour) connection lifetime (enhanced)

Integration:
- Primary: AdventureWorks database with default credentials
- Dynamic: User-provided database configurations for any supported database type
- Compatibility: Both SQLAlchemy engines and raw connections
- Service Layer: Database-specific optimizations through service classes

Author: Brain LLM Team
"""

import logging
from typing import Dict, Any, Generator, Optional
from urllib.parse import quote_plus, unquote_plus
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool
import psycopg2
from psycopg2.extras import RealDictCursor

# Import new database service architecture
from app.services.db.base import BaseDatabaseService, ConnectionInfo
from app.services.db import get_database_service, is_database_type_supported

# Module-level logger for connection operations
logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Enhanced centralized database connection pool manager for multi-database connectivity.
    
    This class has been enhanced to support multiple database types through the new
    database service architecture while maintaining full backward compatibility with
    existing PostgreSQL-specific code.
    
    New Features:
    1. Multi-database type support (PostgreSQL, MySQL, SQLite, Snowflake)
    2. Database service factory integration for type-specific optimizations
    3. Service caching for improved performance
    4. Enhanced connection pooling with better configuration
    5. Comprehensive error handling and logging
    6. Connection validation and health monitoring
    
    Legacy Compatibility:
    - All existing methods continue to work unchanged
    - PostgreSQL-specific methods maintained for backward compatibility
    - Raw psycopg2 connections still supported for legacy code
    
    Core Responsibilities:
    1. Database service creation and caching
    2. SQLAlchemy engine creation and caching 
    3. Connection pool lifecycle management
    4. Database credential security and URL encoding
    5. Raw connection provisioning for legacy code
    6. Multi-database type support and routing
    7. Connection reuse optimization and resource cleanup
    
    Pool Management Strategy:
    - Service Caching: One service instance per database type
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
    - Service reuse eliminates instantiation overhead
    - Connection reuse eliminates handshake overhead
    - Pool warming for consistent response times
    - Concurrent request handling with queue management
    - Memory efficiency through shared connection objects
    """
    
    def __init__(self):
        """
        Initialize the enhanced connection manager.
        
        Creates the internal data structures for tracking database engines,
        connection pools, and database services across different database
        configurations and types.
        """
        # Legacy compatibility - maintain existing structure
        self.pools: Dict[str, Engine] = {}  # Registry of SQLAlchemy engines by database key
        
        # New multi-database support
        self.database_services: Dict[str, BaseDatabaseService] = {}  # Service cache by database type
        self.service_pools: Dict[str, Dict[str, Engine]] = {}  # Nested pools: {db_type: {pool_key: engine}}
        
        logger.info("Enhanced ConnectionManager initialized with multi-database support")
    
    def _get_pool_key(self, db_info: Dict[str, Any]) -> str:
        """
        Creates a unique key for a database connection pool.
        
        Enhanced to include database type for multi-database support.
        """
        db_type = db_info.get('db_type', 'postgresql')
        return f"{db_type}://{db_info['db_user']}@{db_info['db_host']}:{db_info['db_port']}/{db_info['db_name']}"
    
    def _get_legacy_pool_key(self, db_info: Dict[str, Any]) -> str:
        """Legacy pool key format for backward compatibility."""
        return f"{db_info['db_user']}@{db_info['db_host']}:{db_info['db_port']}/{db_info['db_name']}"
    
    def get_database_service(self, db_type: str) -> BaseDatabaseService:
        """
        Get or create a database service for the specified database type.
        
        Services are cached for performance and reused across requests.
        
        Args:
            db_type: Database type identifier (postgresql, mysql, sqlite, snowflake)
            
        Returns:
            BaseDatabaseService: Database service instance
            
        Raises:
            ValueError: If database type is not supported
        """
        db_type = db_type.lower()
        
        if db_type in self.database_services:
            logger.debug(f"Reusing cached database service: {db_type}")
            return self.database_services[db_type]
        
        if not is_database_type_supported(db_type):
            supported_types = ", ".join(["postgresql", "mysql", "sqlite", "snowflake"])  # Will be dynamic once implemented
            raise ValueError(f"Unsupported database type '{db_type}'. Supported types: {supported_types}")
        
        logger.info(f"Creating new database service: {db_type}")
        service = get_database_service(db_type)
        self.database_services[db_type] = service
        
        return service
    
    def get_connection_via_service(self, db_info: Dict[str, Any]) -> Generator[Any, None, None]:
        """
        Get database connection using the new database service architecture.
        
        This method provides a unified interface for connecting to any supported
        database type through the appropriate database service.
        
        Args:
            db_info: Database connection information including db_type
            
        Yields:
            Database connection object specific to the database type
            
        Example:
            db_info = {
                "db_type": "postgresql",
                "db_host": "localhost",
                "db_port": 5432,
                "db_name": "test",
                "db_user": "user",
                "db_password": "pass"
            }
            
            for conn in connection_manager.get_connection_via_service(db_info):
                # Use connection (automatically closed when generator exits)
                pass
        """
        db_type = db_info.get('db_type', 'postgresql')
        
        try:
            # Get appropriate database service
            db_service = self.get_database_service(db_type)
            
            # Create ConnectionInfo object
            connection_info = ConnectionInfo.from_dict(db_info)
            
            # Use service to get connection
            yield from db_service.get_connection(connection_info)
            
        except Exception as e:
            logger.error(f"Failed to get connection via service for {db_type}: {e}")
            raise
    
    def get_engine_via_service(self, db_info: Dict[str, Any]) -> Engine:
        """
        Get SQLAlchemy engine using the new database service architecture.
        
        This method provides a unified interface for creating engines for any
        supported database type through the appropriate database service.
        
        Args:
            db_info: Database connection information including db_type
            
        Returns:
            Engine: SQLAlchemy engine for the specified database
        """
        db_type = db_info.get('db_type', 'postgresql')
        pool_key = self._get_pool_key(db_info)
        
        # Initialize service pool structure if needed
        if db_type not in self.service_pools:
            self.service_pools[db_type] = {}
        
        # Check if engine already exists in service pool
        if pool_key in self.service_pools[db_type]:
            logger.info(f"Reusing existing {db_type} engine: {pool_key}")
            return self.service_pools[db_type][pool_key]
        
        try:
            # Get appropriate database service
            db_service = self.get_database_service(db_type)
            
            # Create ConnectionInfo object
            connection_info = ConnectionInfo.from_dict(db_info)
            
            # Use service to get engine
            engine = db_service.get_engine(connection_info)
            
            # Cache the engine
            self.service_pools[db_type][pool_key] = engine
            logger.info(f"Created and cached new {db_type} engine: {pool_key}")
            
            return engine
            
        except Exception as e:
            logger.error(f"Failed to get engine via service for {db_type}: {e}")
            raise
    
    def validate_connection_info(self, db_info: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate database connection information using appropriate service.
        
        Args:
            db_info: Database connection information including db_type
            
        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        try:
            db_type = db_info.get('db_type', 'postgresql')
            
            # Get appropriate database service
            db_service = self.get_database_service(db_type)
            
            # Create ConnectionInfo object
            connection_info = ConnectionInfo.from_dict(db_info)
            
            # Use service to validate connection
            return db_service.validate_connection(connection_info)
            
        except Exception as e:
            return False, f"Connection validation error: {str(e)}"

    
    # =============================================================================
    # LEGACY COMPATIBILITY METHODS
    # =============================================================================
    # These methods maintain backward compatibility with existing code
    
    def get_db_engine(self, db_info: Dict[str, Any]) -> Engine:
        """
        Legacy method: Gets a SQLAlchemy engine for PostgreSQL connections.
        
        This method maintains backward compatibility with existing code.
        For new code, consider using get_engine_via_service() for multi-database support.
        
        Args:
            db_info: Database connection information (assumes PostgreSQL)
            
        Returns:
            Engine: SQLAlchemy engine for PostgreSQL
        """
        # Ensure db_type is set for PostgreSQL (backward compatibility)
        if 'db_type' not in db_info:
            db_info = db_info.copy()  # Don't modify original dict
            db_info['db_type'] = 'postgresql'
        
        # Use legacy pool key for existing code compatibility
        legacy_pool_key = self._get_legacy_pool_key(db_info)
        
        if legacy_pool_key in self.pools:
            logging.info(f"Reusing existing legacy connection pool for: {legacy_pool_key}")
            return self.pools[legacy_pool_key]

        logging.info(f"Creating new legacy connection pool for: {legacy_pool_key}")
        try:
            # Legacy PostgreSQL connection string creation
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
            
            # Test the engine
            with engine.connect() as connection:
                logging.info(f"Successfully connected and created legacy pool for {legacy_pool_key}")

            self.pools[legacy_pool_key] = engine
            return engine
            
        except Exception as e:
            logging.error(f"Failed to create legacy database engine for {legacy_pool_key}: {e}")
            raise

    def get_raw_psycopg2_connection(self, db_info: Dict[str, Any]):
        """
        Legacy method: Gets a raw psycopg2 connection for PostgreSQL.
        
        This method maintains backward compatibility with existing code that
        expects raw psycopg2 connections with RealDictCursor.
        
        Args:
            db_info: Database connection information (assumes PostgreSQL)
            
        Returns:
            psycopg2.extensions.connection: Raw PostgreSQL connection
        """
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
            logging.info(f"Successfully created raw psycopg2 connection to {self._get_legacy_pool_key(db_info)}")
            return connection
        except Exception as e:
            logging.error(f"Failed to create raw psycopg2 connection for {self._get_legacy_pool_key(db_info)}: {e}")
            raise
    
    # =============================================================================
    # UTILITY AND MANAGEMENT METHODS  
    # =============================================================================
    
    def clear_service_cache(self):
        """Clear the database service cache."""
        self.database_services.clear()
        logger.info("Database service cache cleared")
    
    def clear_engine_cache(self, db_type: Optional[str] = None):
        """
        Clear engine cache for specific database type or all types.
        
        Args:
            db_type: Optional database type to clear. If None, clears all.
        """
        if db_type:
            if db_type in self.service_pools:
                self.service_pools[db_type].clear()
                logger.info(f"Engine cache cleared for {db_type}")
        else:
            self.service_pools.clear()
            self.pools.clear()  # Legacy pools
            logger.info("All engine caches cleared")
    
    def get_connection_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about current connections and pools.
        
        Returns:
            Dict containing connection pool statistics
        """
        stats = {
            "database_services_cached": len(self.database_services),
            "service_pools": {},
            "legacy_pools": len(self.pools),
            "total_engines": len(self.pools)
        }
        
        for db_type, pools in self.service_pools.items():
            stats["service_pools"][db_type] = len(pools)
            stats["total_engines"] += len(pools)
        
        return stats
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all cached connections.
        
        Returns:
            Dict containing health check results
        """
        health_status = {
            "healthy": True,
            "services_checked": 0,
            "engines_checked": 0,
            "failed_checks": [],
            "timestamp": None
        }
        
        import time
        health_status["timestamp"] = time.time()
        
        # Check service pools
        for db_type, pools in self.service_pools.items():
            health_status["services_checked"] += 1
            
            for pool_key, engine in pools.items():
                health_status["engines_checked"] += 1
                
                try:
                    # Quick connection test
                    with engine.connect() as conn:
                        from sqlalchemy import text
                        conn.execute(text("SELECT 1"))
                    logger.debug(f"Health check passed for {pool_key}")
                    
                except Exception as e:
                    health_status["healthy"] = False
                    health_status["failed_checks"].append({
                        "pool_key": pool_key,
                        "db_type": db_type,
                        "error": str(e)
                    })
                    logger.warning(f"Health check failed for {pool_key}: {e}")
        
        return health_status

# Instantiate a single manager for the application to use
connection_manager = ConnectionManager()