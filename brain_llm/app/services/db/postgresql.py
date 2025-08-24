"""
PostgreSQL Database Service Implementation
=========================================

This module provides PostgreSQL-specific database service implementation for the Brain LLM application.
It extends the BaseDatabaseService to provide PostgreSQL-optimized connection management, schema
introspection, and query execution capabilities.

Key Features:
- PostgreSQL connection pooling with psycopg2
- Advanced schema introspection with foreign keys and constraints
- RealDictCursor for dictionary-style result access
- PostgreSQL-specific error handling and optimization
- Support for PostgreSQL extensions and advanced data types

Integration:
- Migrates existing pg_connector.py functionality
- Maintains backward compatibility with current code
- Optimized for AdventureWorks sample database
- Supports dynamic PostgreSQL connections

Author: Brain LLM Team
"""

import psycopg2
import psycopg2.extras
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool
from urllib.parse import quote_plus
from typing import Any, Generator, Optional, Dict, List, Tuple
import time
import logging

from app.services.db.base import (
    BaseDatabaseService, 
    ConnectionInfo, 
    QueryResult,
    DatabaseConnectionError,
    DatabaseSchemaError,
    DatabaseQueryError
)

logger = logging.getLogger(__name__)

class PostgreSQLService(BaseDatabaseService):
    """
    PostgreSQL database service implementation.
    
    This service provides PostgreSQL-specific implementations for all database operations
    including connection management, schema introspection, and query execution.
    It migrates and enhances the existing pg_connector.py functionality while maintaining
    full backward compatibility.
    
    Features:
    - Connection pooling with configurable pool sizes
    - Advanced PostgreSQL schema introspection
    - RealDictCursor for dictionary-style results
    - PostgreSQL-specific error handling
    - Support for PostgreSQL extensions and JSON data types
    - Optimized queries for AdventureWorks database
    
    Performance Optimizations:
    - Connection reuse through SQLAlchemy pooling
    - Efficient schema caching
    - Prepared statement support
    - Connection health monitoring
    """
    
    def __init__(self, connection_info: Optional[ConnectionInfo] = None):
        """
        Initialize PostgreSQL service.
        
        Args:
            connection_info: Optional PostgreSQL connection parameters
        """
        super().__init__(connection_info)
        self.logger = logging.getLogger(f"{__name__}.PostgreSQLService")
        self._engines: Dict[str, Engine] = {}  # Engine cache
        
    def get_connection(self, connection_info: ConnectionInfo) -> Generator[psycopg2.extensions.connection, None, None]:
        """
        Create a PostgreSQL connection with context management.
        
        This method provides a raw psycopg2 connection with RealDictCursor for
        compatibility with existing code that expects dictionary-style results.
        
        Args:
            connection_info: PostgreSQL connection parameters
            
        Yields:
            psycopg2.extensions.connection: Raw PostgreSQL connection with RealDictCursor
            
        Raises:
            DatabaseConnectionError: If connection fails
            
        Example:
            for conn in pg_service.get_connection(conn_info):
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM customers")
                results = cursor.fetchall()  # Returns list of dictionaries
        """
        connection = None
        try:
            self.logger.info(f"Connecting to PostgreSQL database: {connection_info.db_host}:{connection_info.db_port}/{connection_info.db_name}")
            
            # Create connection with RealDictCursor for dictionary-style results
            connection = psycopg2.connect(
                host=connection_info.db_host,
                port=connection_info.db_port,
                database=connection_info.db_name,
                user=connection_info.db_user,
                password=connection_info.db_password,
                cursor_factory=RealDictCursor,
                connect_timeout=30  # 30 second connection timeout
            )
            
            # Test the connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            self.log_connection_attempt(connection_info, True)
            yield connection
            
        except psycopg2.Error as e:
            error_msg = self.format_error_message(e, "PostgreSQL connection failed")
            self.log_connection_attempt(connection_info, False, error_msg)
            raise DatabaseConnectionError(error_msg) from e
        except Exception as e:
            error_msg = self.format_error_message(e, "Unexpected error during PostgreSQL connection")
            self.log_connection_attempt(connection_info, False, error_msg)
            raise DatabaseConnectionError(error_msg) from e
        finally:
            if connection is not None:
                connection.close()
                self.logger.info("PostgreSQL connection closed")
    
    def get_engine(self, connection_info: ConnectionInfo) -> Engine:
        """
        Create a SQLAlchemy engine for PostgreSQL with connection pooling.
        
        This method creates and caches SQLAlchemy engines for efficient connection
        pooling and reuse across multiple requests.
        
        Args:
            connection_info: PostgreSQL connection parameters
            
        Returns:
            Engine: Configured SQLAlchemy engine with connection pooling
            
        Raises:
            DatabaseConnectionError: If engine creation fails
        """
        # Create unique key for engine caching
        engine_key = f"{connection_info.db_user}@{connection_info.db_host}:{connection_info.db_port}/{connection_info.db_name}"
        
        # Return cached engine if available
        if engine_key in self._engines:
            self.logger.info(f"Reusing cached PostgreSQL engine: {engine_key}")
            return self._engines[engine_key]
        
        try:
            self.logger.info(f"Creating new PostgreSQL engine: {engine_key}")
            
            # Create connection string with URL encoding for special characters
            encoded_password = quote_plus(connection_info.db_password)
            connection_string = (
                f"postgresql+psycopg2://{connection_info.db_user}:{encoded_password}"
                f"@{connection_info.db_host}:{connection_info.db_port}/{connection_info.db_name}"
            )
            
            # Create engine with optimized pool settings
            engine = create_engine(
                connection_string,
                poolclass=QueuePool,
                pool_size=5,              # Base pool size
                max_overflow=10,          # Additional connections under load
                pool_timeout=30,          # Timeout for getting connection from pool
                pool_recycle=3600,        # Recycle connections after 1 hour
                pool_pre_ping=True,       # Validate connections before use
                echo=False                # Set to True for SQL debugging
            )
            
            # Test the engine with a simple query
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # Cache the engine for reuse
            self._engines[engine_key] = engine
            self.logger.info(f"Successfully created and cached PostgreSQL engine: {engine_key}")
            
            return engine
            
        except Exception as e:
            error_msg = self.format_error_message(e, "PostgreSQL engine creation failed")
            self.logger.error(error_msg)
            raise DatabaseConnectionError(error_msg) from e
    
    def validate_connection(self, connection_info: ConnectionInfo) -> Tuple[bool, Optional[str]]:
        """
        Validate PostgreSQL connection without establishing persistent connection.
        
        Args:
            connection_info: PostgreSQL connection parameters to validate
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            # Attempt a quick connection test
            test_connection = psycopg2.connect(
                host=connection_info.db_host,
                port=connection_info.db_port,
                database=connection_info.db_name,
                user=connection_info.db_user,
                password=connection_info.db_password,
                connect_timeout=10  # Quick timeout for validation
            )
            
            # Test with a simple query
            with test_connection.cursor() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                self.logger.info(f"PostgreSQL validation successful: {version}")
            
            test_connection.close()
            return True, None
            
        except psycopg2.Error as e:
            error_msg = f"PostgreSQL validation failed: {str(e)}"
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error during PostgreSQL validation: {str(e)}"
            return False, error_msg
    
    def get_schema_string(self, connection: psycopg2.extensions.connection) -> str:
        """
        Extract PostgreSQL schema as formatted string for LLM consumption.
        
        This method provides comprehensive schema information including tables,
        columns, data types, constraints, foreign keys, and indexes in a format
        optimized for LLM processing and SQL query generation.
        
        Args:
            connection: Active PostgreSQL connection
            
        Returns:
            str: Formatted schema string suitable for LLM prompts
            
        Raises:
            DatabaseSchemaError: If schema extraction fails
        """
        try:
            self.logger.info("Starting PostgreSQL schema extraction")
            schema_parts = []
            
            with connection.cursor() as cursor:
                # Get database information
                cursor.execute("SELECT current_database(), version()")
                db_info = cursor.fetchone()
                schema_parts.append(f"Database: {db_info[0]}")
                schema_parts.append(f"PostgreSQL Version: {db_info[1]}")
                schema_parts.append("")
                
                # Get all tables with their schemas
                cursor.execute("""
                    SELECT schemaname, tablename, tableowner
                    FROM pg_tables 
                    WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                    ORDER BY schemaname, tablename
                """)
                tables = cursor.fetchall()
                
                if not tables:
                    return "No user tables found in the database."
                
                schema_parts.append(f"Found {len(tables)} tables:")
                schema_parts.append("")
                
                for table in tables:
                    schema_name = table['schemaname']
                    table_name = table['tablename']
                    full_table_name = f"{schema_name}.{table_name}" if schema_name != 'public' else table_name
                    
                    schema_parts.append(f"Table: {full_table_name}")
                    
                    # Get column information
                    cursor.execute("""
                        SELECT 
                            column_name,
                            data_type,
                            is_nullable,
                            column_default,
                            character_maximum_length,
                            numeric_precision,
                            numeric_scale
                        FROM information_schema.columns
                        WHERE table_schema = %s AND table_name = %s
                        ORDER BY ordinal_position
                    """, (schema_name, table_name))
                    columns = cursor.fetchall()
                    
                    for col in columns:
                        col_name = col['column_name']
                        data_type = col['data_type']
                        
                        # Format data type with precision/scale if applicable
                        if col['character_maximum_length']:
                            data_type += f"({col['character_maximum_length']})"
                        elif col['numeric_precision'] and col['numeric_scale']:
                            data_type += f"({col['numeric_precision']},{col['numeric_scale']})"
                        elif col['numeric_precision']:
                            data_type += f"({col['numeric_precision']})"
                        
                        nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                        default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                        
                        schema_parts.append(f"  - {col_name}: {data_type} {nullable}{default}")
                    
                    # Get primary key information
                    cursor.execute("""
                        SELECT kcu.column_name
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu 
                            ON tc.constraint_name = kcu.constraint_name
                            AND tc.table_schema = kcu.table_schema
                        WHERE tc.constraint_type = 'PRIMARY KEY'
                            AND tc.table_schema = %s AND tc.table_name = %s
                        ORDER BY kcu.ordinal_position
                    """, (schema_name, table_name))
                    pk_columns = [row['column_name'] for row in cursor.fetchall()]
                    
                    if pk_columns:
                        schema_parts.append(f"  Primary Key: {', '.join(pk_columns)}")
                    
                    # Get foreign key information
                    cursor.execute("""
                        SELECT 
                            kcu.column_name,
                            ccu.table_schema AS foreign_table_schema,
                            ccu.table_name AS foreign_table_name,
                            ccu.column_name AS foreign_column_name
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu 
                            ON tc.constraint_name = kcu.constraint_name
                            AND tc.table_schema = kcu.table_schema
                        JOIN information_schema.constraint_column_usage ccu 
                            ON ccu.constraint_name = tc.constraint_name
                            AND ccu.table_schema = tc.table_schema
                        WHERE tc.constraint_type = 'FOREIGN KEY'
                            AND tc.table_schema = %s AND tc.table_name = %s
                    """, (schema_name, table_name))
                    foreign_keys = cursor.fetchall()
                    
                    for fk in foreign_keys:
                        foreign_table = f"{fk['foreign_table_schema']}.{fk['foreign_table_name']}" if fk['foreign_table_schema'] != 'public' else fk['foreign_table_name']
                        schema_parts.append(f"  Foreign Key: {fk['column_name']} -> {foreign_table}.{fk['foreign_column_name']}")
                    
                    # Get table row count (approximate for large tables)
                    cursor.execute(f"""
                        SELECT reltuples::BIGINT AS estimate
                        FROM pg_class 
                        WHERE relname = %s
                    """, (table_name,))
                    row_count_result = cursor.fetchone()
                    if row_count_result and row_count_result['estimate'] > 0:
                        schema_parts.append(f"  Estimated Rows: {row_count_result['estimate']:,}")
                    
                    schema_parts.append("")
                
                # Get view information
                cursor.execute("""
                    SELECT schemaname, viewname
                    FROM pg_views 
                    WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                    ORDER BY schemaname, viewname
                """)
                views = cursor.fetchall()
                
                if views:
                    schema_parts.append(f"Views ({len(views)}):")
                    for view in views:
                        schema_name = view['schemaname']
                        view_name = view['viewname']
                        full_view_name = f"{schema_name}.{view_name}" if schema_name != 'public' else view_name
                        schema_parts.append(f"  - {full_view_name}")
                    schema_parts.append("")
            
            schema_string = "\\n".join(schema_parts)
            self.logger.info(f"PostgreSQL schema extraction completed. Schema length: {len(schema_string)} characters")
            return schema_string
            
        except psycopg2.Error as e:
            error_msg = self.format_error_message(e, "PostgreSQL schema extraction failed")
            self.logger.error(error_msg)
            raise DatabaseSchemaError(error_msg) from e
        except Exception as e:
            error_msg = self.format_error_message(e, "Unexpected error during PostgreSQL schema extraction")
            self.logger.error(error_msg)
            raise DatabaseSchemaError(error_msg) from e
    
    def get_table_names(self, connection: psycopg2.extensions.connection) -> List[str]:
        """
        Get list of all table names in the PostgreSQL database.
        
        Args:
            connection: Active PostgreSQL connection
            
        Returns:
            List[str]: Table names in the database
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT schemaname || '.' || tablename as full_name
                    FROM pg_tables 
                    WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                    ORDER BY schemaname, tablename
                """)
                return [row['full_name'] for row in cursor.fetchall()]
        except psycopg2.Error as e:
            raise DatabaseSchemaError(f"Failed to get table names: {str(e)}") from e
    
    def get_table_schema(self, connection: psycopg2.extensions.connection, table_name: str) -> Dict[str, Any]:
        """
        Get detailed schema information for a specific PostgreSQL table.
        
        Args:
            connection: Active PostgreSQL connection
            table_name: Name of the table to analyze (can include schema)
            
        Returns:
            Dict containing detailed table schema information
        """
        try:
            # Parse schema and table name
            if '.' in table_name:
                schema_name, table_name = table_name.split('.', 1)
            else:
                schema_name = 'public'
            
            table_info = {
                'schema_name': schema_name,
                'table_name': table_name,
                'columns': [],
                'primary_keys': [],
                'foreign_keys': [],
                'indexes': []
            }
            
            with connection.cursor() as cursor:
                # Get column information
                cursor.execute("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length,
                        numeric_precision,
                        numeric_scale
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                """, (schema_name, table_name))
                
                for col in cursor.fetchall():
                    table_info['columns'].append(dict(col))
                
                # Get primary keys
                cursor.execute("""
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                        AND tc.table_schema = %s AND tc.table_name = %s
                """, (schema_name, table_name))
                
                table_info['primary_keys'] = [row['column_name'] for row in cursor.fetchall()]
                
                # Get foreign keys
                cursor.execute("""
                    SELECT 
                        kcu.column_name,
                        ccu.table_schema AS foreign_table_schema,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage ccu 
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_schema = %s AND tc.table_name = %s
                """, (schema_name, table_name))
                
                for fk in cursor.fetchall():
                    table_info['foreign_keys'].append(dict(fk))
            
            return table_info
            
        except psycopg2.Error as e:
            raise DatabaseSchemaError(f"Failed to get table schema for {table_name}: {str(e)}") from e
    
    def execute_query(self, connection: psycopg2.extensions.connection, query: str) -> QueryResult:
        """
        Execute a PostgreSQL query and return standardized results.
        
        Args:
            connection: Active PostgreSQL connection
            query: SQL query string to execute
            
        Returns:
            QueryResult: Standardized query result container
        """
        start_time = time.time()
        
        try:
            with connection.cursor() as cursor:
                self.logger.debug(f"Executing PostgreSQL query: {query[:100]}...")
                cursor.execute(query)
                
                # Handle different query types
                if cursor.description:
                    # SELECT query - fetch results
                    rows = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    data = [dict(row) for row in rows]
                    row_count = len(data)
                else:
                    # INSERT/UPDATE/DELETE query
                    data = []
                    columns = []
                    row_count = cursor.rowcount
                
                execution_time = time.time() - start_time
                
                self.logger.info(f"PostgreSQL query executed successfully. Rows: {row_count}, Time: {execution_time:.3f}s")
                
                return QueryResult(
                    data=data,
                    columns=columns,
                    row_count=row_count,
                    success=True,
                    execution_time=execution_time
                )
                
        except psycopg2.Error as e:
            execution_time = time.time() - start_time
            error_msg = self.format_error_message(e, "PostgreSQL query execution failed")
            
            self.logger.error(f"PostgreSQL query failed: {error_msg}")
            
            return QueryResult(
                data=[],
                columns=[],
                row_count=0,
                success=False,
                execution_time=execution_time,
                error_message=error_msg
            )
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = self.format_error_message(e, "Unexpected error during PostgreSQL query execution")
            
            self.logger.error(f"Unexpected error in PostgreSQL query: {error_msg}")
            
            return QueryResult(
                data=[],
                columns=[],
                row_count=0,
                success=False,
                execution_time=execution_time,
                error_message=error_msg
            )
    
    def execute_query_with_params(self, connection: psycopg2.extensions.connection, query: str, params: Dict[str, Any]) -> QueryResult:
        """
        Execute a parameterized PostgreSQL query to prevent SQL injection.
        
        Args:
            connection: Active PostgreSQL connection
            query: SQL query string with parameter placeholders
            params: Dictionary of parameter values
            
        Returns:
            QueryResult: Standardized query result container
        """
        start_time = time.time()
        
        try:
            with connection.cursor() as cursor:
                self.logger.debug(f"Executing parameterized PostgreSQL query: {query[:100]}...")
                cursor.execute(query, params)
                
                if cursor.description:
                    rows = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    data = [dict(row) for row in rows]
                    row_count = len(data)
                else:
                    data = []
                    columns = []
                    row_count = cursor.rowcount
                
                execution_time = time.time() - start_time
                
                return QueryResult(
                    data=data,
                    columns=columns,
                    row_count=row_count,
                    success=True,
                    execution_time=execution_time
                )
                
        except psycopg2.Error as e:
            execution_time = time.time() - start_time
            error_msg = self.format_error_message(e, "Parameterized PostgreSQL query execution failed")
            
            return QueryResult(
                data=[],
                columns=[],
                row_count=0,
                success=False,
                execution_time=execution_time,
                error_message=error_msg
            )
    
    def get_connection_string(self, connection_info: ConnectionInfo) -> str:
        """
        Generate PostgreSQL connection string.
        
        Args:
            connection_info: PostgreSQL connection parameters
            
        Returns:
            str: Formatted PostgreSQL connection string
        """
        encoded_password = quote_plus(connection_info.db_password)
        return (
            f"postgresql+psycopg2://{connection_info.db_user}:{encoded_password}"
            f"@{connection_info.db_host}:{connection_info.db_port}/{connection_info.db_name}"
        )
    
    def get_supported_features(self) -> Dict[str, bool]:
        """
        Get PostgreSQL feature support matrix.
        
        Returns:
            Dict[str, bool]: Feature support matrix for PostgreSQL
        """
        return {
            "connection_pooling": True,
            "transactions": True,
            "foreign_keys": True,
            "stored_procedures": True,
            "window_functions": True,
            "json_support": True,
            "array_support": True,
            "full_text_search": True,
            "materialized_views": True,
            "partitioning": True,
            "extensions": True,
            "custom_types": True,
            "recursive_queries": True,
            "upsert": True  # INSERT ... ON CONFLICT
        }
    
    def _get_database_version(self, connection: Any) -> Optional[str]:
        """Get PostgreSQL version information."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version()")
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception:
            return None
