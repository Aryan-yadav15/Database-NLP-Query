"""
MySQL Database Service Implementation
====================================

This module provides MySQL-specific database service implementation for the Brain LLM application.
It extends the BaseDatabaseService to provide MySQL-optimized connection management, schema
introspection, and query execution capabilities.

Key Features:
- MySQL connection pooling with mysql-connector-python
- Advanced schema introspection with foreign keys and constraints
- Dictionary-style result access for consistency
- MySQL-specific error handling and optimization
- Support for MySQL-specific data types and features

Integration:
- Follows the same pattern as PostgreSQL service
- Maintains compatibility with multi-database architecture
- Optimized for common MySQL configurations
- Supports dynamic MySQL connections

Author: Brain LLM Team
"""

import mysql.connector
from mysql.connector import pooling, Error as MySQLError
from mysql.connector.cursor import MySQLCursorDict
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

class MySQLService(BaseDatabaseService):
    """
    MySQL database service implementation.
    
    This service provides MySQL-specific implementations for all database operations
    including connection management, schema introspection, and query execution.
    It follows the same patterns as the PostgreSQL service while handling
    MySQL-specific requirements and optimizations.
    
    Features:
    - Connection pooling with configurable pool sizes
    - Advanced MySQL schema introspection
    - Dictionary-style cursor results for consistency
    - MySQL-specific error handling
    - Support for MySQL data types and storage engines
    - Optimized for common MySQL use cases
    
    Performance Optimizations:
    - Connection reuse through SQLAlchemy pooling
    - Efficient schema caching
    - Connection health monitoring
    - MySQL-specific query optimizations
    """
    
    def __init__(self, connection_info: Optional[ConnectionInfo] = None):
        """
        Initialize MySQL service.
        
        Args:
            connection_info: Optional MySQL connection parameters
        """
        super().__init__(connection_info)
        self.logger = logging.getLogger(f"{__name__}.MySQLService")
        self._engines: Dict[str, Engine] = {}  # Engine cache
        self._connection_pools: Dict[str, pooling.MySQLConnectionPool] = {}  # Pool cache
        
    def get_connection(self, connection_info: ConnectionInfo) -> Generator[mysql.connector.MySQLConnection, None, None]:
        """
        Create a MySQL connection with context management.
        
        This method provides a raw mysql-connector-python connection with dictionary cursor
        for compatibility and consistency with other database services.
        
        Args:
            connection_info: MySQL connection parameters
            
        Yields:
            mysql.connector.MySQLConnection: Raw MySQL connection with dictionary cursor
            
        Raises:
            DatabaseConnectionError: If connection fails
            
        Example:
            for conn in mysql_service.get_connection(conn_info):
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM customers")
                results = cursor.fetchall()  # Returns list of dictionaries
        """
        connection = None
        try:
            self.logger.info(f"Connecting to MySQL database: {connection_info.db_host}:{connection_info.db_port}/{connection_info.db_name}")
            
            # Create connection configuration
            config = {
                'host': connection_info.db_host,
                'port': connection_info.db_port,
                'database': connection_info.db_name,
                'user': connection_info.db_user,
                'password': connection_info.db_password,
                'autocommit': True,
                'connection_timeout': 30,  # 30 second connection timeout
                'charset': 'utf8mb4',  # Full UTF-8 support
                'collation': 'utf8mb4_unicode_ci',
                'sql_mode': 'TRADITIONAL',  # Strict mode for better data integrity
                'raise_on_warnings': True
            }
            
            # Add any additional MySQL-specific parameters
            if connection_info.additional_params:
                config.update(connection_info.additional_params)
            
            # Create connection
            connection = mysql.connector.connect(**config)
            
            # Test the connection
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT 1 as test")
            test_result = cursor.fetchone()
            cursor.close()
            
            if not test_result or test_result.get('test') != 1:
                raise MySQLError("Connection test failed")
            
            self.log_connection_attempt(connection_info, True)
            yield connection
            
        except MySQLError as e:
            error_msg = self.format_error_message(e, "MySQL connection failed")
            self.log_connection_attempt(connection_info, False, error_msg)
            raise DatabaseConnectionError(error_msg) from e
        except Exception as e:
            error_msg = self.format_error_message(e, "Unexpected error during MySQL connection")
            self.log_connection_attempt(connection_info, False, error_msg)
            raise DatabaseConnectionError(error_msg) from e
        finally:
            if connection is not None and connection.is_connected():
                connection.close()
                self.logger.info("MySQL connection closed")
    
    def get_engine(self, connection_info: ConnectionInfo) -> Engine:
        """
        Create a SQLAlchemy engine for MySQL with connection pooling.
        
        This method creates and caches SQLAlchemy engines for efficient connection
        pooling and reuse across multiple requests.
        
        Args:
            connection_info: MySQL connection parameters
            
        Returns:
            Engine: Configured SQLAlchemy engine with connection pooling
            
        Raises:
            DatabaseConnectionError: If engine creation fails
        """
        # Create unique key for engine caching
        engine_key = f"{connection_info.db_user}@{connection_info.db_host}:{connection_info.db_port}/{connection_info.db_name}"
        
        # Return cached engine if available
        if engine_key in self._engines:
            self.logger.info(f"Reusing cached MySQL engine: {engine_key}")
            return self._engines[engine_key]
        
        try:
            self.logger.info(f"Creating new MySQL engine: {engine_key}")
            
            # Create connection string with URL encoding for special characters
            encoded_password = quote_plus(connection_info.db_password)
            connection_string = (
                f"mysql+mysqlconnector://{connection_info.db_user}:{encoded_password}"
                f"@{connection_info.db_host}:{connection_info.db_port}/{connection_info.db_name}"
                f"?charset=utf8mb4&collation=utf8mb4_unicode_ci"
            )
            
            # Create engine with optimized pool settings for MySQL
            engine = create_engine(
                connection_string,
                poolclass=QueuePool,
                pool_size=5,              # Base pool size
                max_overflow=10,          # Additional connections under load
                pool_timeout=30,          # Timeout for getting connection from pool
                pool_recycle=3600,        # Recycle connections after 1 hour
                pool_pre_ping=True,       # Validate connections before use
                echo=False,               # Set to True for SQL debugging
                connect_args={
                    'charset': 'utf8mb4',
                    'autocommit': True,
                    'connection_timeout': 30,
                    'sql_mode': 'TRADITIONAL'
                }
            )
            
            # Test the engine with a simple query
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # Cache the engine for reuse
            self._engines[engine_key] = engine
            self.logger.info(f"Successfully created and cached MySQL engine: {engine_key}")
            
            return engine
            
        except Exception as e:
            error_msg = self.format_error_message(e, "MySQL engine creation failed")
            self.logger.error(error_msg)
            raise DatabaseConnectionError(error_msg) from e
    
    def validate_connection(self, connection_info: ConnectionInfo) -> Tuple[bool, Optional[str]]:
        """
        Validate MySQL connection without establishing persistent connection.
        
        Args:
            connection_info: MySQL connection parameters to validate
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            # Attempt a quick connection test
            config = {
                'host': connection_info.db_host,
                'port': connection_info.db_port,
                'database': connection_info.db_name,
                'user': connection_info.db_user,
                'password': connection_info.db_password,
                'connection_timeout': 10,  # Quick timeout for validation
                'autocommit': True
            }
            
            test_connection = mysql.connector.connect(**config)
            
            # Test with a simple query
            cursor = test_connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            cursor.close()
            
            self.logger.info(f"MySQL validation successful: {version}")
            test_connection.close()
            return True, None
            
        except MySQLError as e:
            error_msg = f"MySQL validation failed: {str(e)}"
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error during MySQL validation: {str(e)}"
            return False, error_msg
    
    def get_schema_string(self, connection: mysql.connector.MySQLConnection) -> str:
        """
        Extract MySQL schema as formatted string for LLM consumption.
        
        This method provides comprehensive schema information including tables,
        columns, data types, constraints, foreign keys, and indexes in a format
        optimized for LLM processing and SQL query generation.
        
        Args:
            connection: Active MySQL connection
            
        Returns:
            str: Formatted schema string suitable for LLM prompts
            
        Raises:
            DatabaseSchemaError: If schema extraction fails
        """
        try:
            self.logger.info("Starting MySQL schema extraction")
            schema_parts = []
            
            cursor = connection.cursor(dictionary=True)
            
            # Get database information
            cursor.execute("SELECT DATABASE() as current_db, VERSION() as version")
            db_info = cursor.fetchone()
            schema_parts.append(f"Database: {db_info['current_db']}")
            schema_parts.append(f"MySQL Version: {db_info['version']}")
            schema_parts.append("")
            
            # Get all tables
            cursor.execute("SHOW TABLES")
            tables = [row[f"Tables_in_{db_info['current_db']}"] for row in cursor.fetchall()]
            
            if not tables:
                cursor.close()
                return "No tables found in the database."
            
            schema_parts.append(f"Found {len(tables)} tables:")
            schema_parts.append("")
            
            for table_name in tables:
                schema_parts.append(f"Table: {table_name}")
                
                # Get column information
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                
                for col in columns:
                    col_name = col['Field']
                    data_type = col['Type']
                    nullable = "NULL" if col['Null'] == 'YES' else "NOT NULL"
                    key_info = f" {col['Key']}" if col['Key'] else ""
                    default = f" DEFAULT {col['Default']}" if col['Default'] is not None else ""
                    extra = f" {col['Extra']}" if col['Extra'] else ""
                    
                    schema_parts.append(f"  - {col_name}: {data_type} {nullable}{key_info}{default}{extra}")
                
                # Get foreign key information
                cursor.execute(f"""
                    SELECT 
                        COLUMN_NAME,
                        REFERENCED_TABLE_NAME,
                        REFERENCED_COLUMN_NAME
                    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA = DATABASE()
                        AND TABLE_NAME = '{table_name}'
                        AND REFERENCED_TABLE_NAME IS NOT NULL
                """)
                foreign_keys = cursor.fetchall()
                
                for fk in foreign_keys:
                    schema_parts.append(f"  Foreign Key: {fk['COLUMN_NAME']} -> {fk['REFERENCED_TABLE_NAME']}.{fk['REFERENCED_COLUMN_NAME']}")
                
                # Get table row count
                cursor.execute(f"SELECT COUNT(*) as row_count FROM {table_name}")
                row_count_result = cursor.fetchone()
                if row_count_result and row_count_result['row_count'] > 0:
                    schema_parts.append(f"  Row Count: {row_count_result['row_count']:,}")
                
                # Get table engine and other info
                cursor.execute(f"""
                    SELECT ENGINE, TABLE_COLLATION, AUTO_INCREMENT
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = '{table_name}'
                """)
                table_info = cursor.fetchone()
                if table_info:
                    if table_info['ENGINE']:
                        schema_parts.append(f"  Engine: {table_info['ENGINE']}")
                    if table_info['TABLE_COLLATION']:
                        schema_parts.append(f"  Collation: {table_info['TABLE_COLLATION']}")
                    if table_info['AUTO_INCREMENT']:
                        schema_parts.append(f"  Auto Increment: {table_info['AUTO_INCREMENT']}")
                
                schema_parts.append("")
            
            # Get view information
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.VIEWS 
                WHERE TABLE_SCHEMA = DATABASE()
                ORDER BY TABLE_NAME
            """)
            views = cursor.fetchall()
            
            if views:
                schema_parts.append(f"Views ({len(views)}):")
                for view in views:
                    schema_parts.append(f"  - {view['TABLE_NAME']}")
                schema_parts.append("")
            
            # Get stored procedures
            cursor.execute("""
                SELECT ROUTINE_NAME, ROUTINE_TYPE
                FROM INFORMATION_SCHEMA.ROUTINES
                WHERE ROUTINE_SCHEMA = DATABASE()
                ORDER BY ROUTINE_NAME
            """)
            routines = cursor.fetchall()
            
            if routines:
                schema_parts.append(f"Stored Procedures/Functions ({len(routines)}):")
                for routine in routines:
                    schema_parts.append(f"  - {routine['ROUTINE_NAME']} ({routine['ROUTINE_TYPE']})")
                schema_parts.append("")
            
            cursor.close()
            
            schema_string = "\\n".join(schema_parts)
            self.logger.info(f"MySQL schema extraction completed. Schema length: {len(schema_string)} characters")
            return schema_string
            
        except MySQLError as e:
            error_msg = self.format_error_message(e, "MySQL schema extraction failed")
            self.logger.error(error_msg)
            raise DatabaseSchemaError(error_msg) from e
        except Exception as e:
            error_msg = self.format_error_message(e, "Unexpected error during MySQL schema extraction")
            self.logger.error(error_msg)
            raise DatabaseSchemaError(error_msg) from e
    
    def get_table_names(self, connection: mysql.connector.MySQLConnection) -> List[str]:
        """
        Get list of all table names in the MySQL database.
        
        Args:
            connection: Active MySQL connection
            
        Returns:
            List[str]: Table names in the database
        """
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SHOW TABLES")
            
            # Get the column name dynamically (it includes the database name)
            db_name = connection.database
            column_name = f"Tables_in_{db_name}"
            
            tables = [row[column_name] for row in cursor.fetchall()]
            cursor.close()
            return tables
        except MySQLError as e:
            raise DatabaseSchemaError(f"Failed to get table names: {str(e)}") from e
    
    def get_table_schema(self, connection: mysql.connector.MySQLConnection, table_name: str) -> Dict[str, Any]:
        """
        Get detailed schema information for a specific MySQL table.
        
        Args:
            connection: Active MySQL connection
            table_name: Name of the table to analyze
            
        Returns:
            Dict containing detailed table schema information
        """
        try:
            table_info = {
                'database_name': connection.database,
                'table_name': table_name,
                'columns': [],
                'primary_keys': [],
                'foreign_keys': [],
                'indexes': [],
                'engine': None,
                'collation': None
            }
            
            cursor = connection.cursor(dictionary=True)
            
            # Get column information
            cursor.execute(f"DESCRIBE {table_name}")
            for col in cursor.fetchall():
                table_info['columns'].append({
                    'column_name': col['Field'],
                    'data_type': col['Type'],
                    'is_nullable': col['Null'] == 'YES',
                    'column_default': col['Default'],
                    'key': col['Key'],
                    'extra': col['Extra']
                })
                
                # Collect primary keys
                if col['Key'] == 'PRI':
                    table_info['primary_keys'].append(col['Field'])
            
            # Get foreign key information
            cursor.execute(f"""
                SELECT 
                    COLUMN_NAME,
                    REFERENCED_TABLE_NAME,
                    REFERENCED_COLUMN_NAME,
                    CONSTRAINT_NAME
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = '{table_name}'
                    AND REFERENCED_TABLE_NAME IS NOT NULL
            """)
            
            for fk in cursor.fetchall():
                table_info['foreign_keys'].append({
                    'column_name': fk['COLUMN_NAME'],
                    'referenced_table_name': fk['REFERENCED_TABLE_NAME'],
                    'referenced_column_name': fk['REFERENCED_COLUMN_NAME'],
                    'constraint_name': fk['CONSTRAINT_NAME']
                })
            
            # Get index information
            cursor.execute(f"SHOW INDEX FROM {table_name}")
            for idx in cursor.fetchall():
                table_info['indexes'].append({
                    'index_name': idx['Key_name'],
                    'column_name': idx['Column_name'],
                    'non_unique': idx['Non_unique'] == 1,
                    'seq_in_index': idx['Seq_in_index']
                })
            
            # Get table metadata
            cursor.execute(f"""
                SELECT ENGINE, TABLE_COLLATION, AUTO_INCREMENT, TABLE_ROWS
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = '{table_name}'
            """)
            metadata = cursor.fetchone()
            if metadata:
                table_info['engine'] = metadata['ENGINE']
                table_info['collation'] = metadata['TABLE_COLLATION']
                table_info['auto_increment'] = metadata['AUTO_INCREMENT']
                table_info['estimated_rows'] = metadata['TABLE_ROWS']
            
            cursor.close()
            return table_info
            
        except MySQLError as e:
            raise DatabaseSchemaError(f"Failed to get table schema for {table_name}: {str(e)}") from e
    
    def execute_query(self, connection: mysql.connector.MySQLConnection, query: str) -> QueryResult:
        """
        Execute a MySQL query and return standardized results.
        
        Args:
            connection: Active MySQL connection
            query: SQL query string to execute
            
        Returns:
            QueryResult: Standardized query result container
        """
        start_time = time.time()
        cursor = None
        
        try:
            cursor = connection.cursor(dictionary=True)
            self.logger.debug(f"Executing MySQL query: {query[:100]}...")
            cursor.execute(query)
            
            # Handle different query types
            if cursor.description:
                # SELECT query - fetch results
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                data = rows  # Already in dictionary format
                row_count = len(data)
            else:
                # INSERT/UPDATE/DELETE query
                data = []
                columns = []
                row_count = cursor.rowcount
                
                # For INSERT operations, try to get the last insert ID
                if cursor.lastrowid:
                    data = [{'last_insert_id': cursor.lastrowid}]
                    columns = ['last_insert_id']
            
            execution_time = time.time() - start_time
            
            self.logger.info(f"MySQL query executed successfully. Rows: {row_count}, Time: {execution_time:.3f}s")
            
            return QueryResult(
                data=data,
                columns=columns,
                row_count=row_count,
                success=True,
                execution_time=execution_time
            )
            
        except MySQLError as e:
            execution_time = time.time() - start_time
            error_msg = self.format_error_message(e, "MySQL query execution failed")
            
            self.logger.error(f"MySQL query failed: {error_msg}")
            
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
            error_msg = self.format_error_message(e, "Unexpected error during MySQL query execution")
            
            self.logger.error(f"Unexpected error in MySQL query: {error_msg}")
            
            return QueryResult(
                data=[],
                columns=[],
                row_count=0,
                success=False,
                execution_time=execution_time,
                error_message=error_msg
            )
        finally:
            if cursor:
                cursor.close()
    
    def execute_query_with_params(self, connection: mysql.connector.MySQLConnection, query: str, params: Dict[str, Any]) -> QueryResult:
        """
        Execute a parameterized MySQL query to prevent SQL injection.
        
        Args:
            connection: Active MySQL connection
            query: SQL query string with parameter placeholders (%(name)s format)
            params: Dictionary of parameter values
            
        Returns:
            QueryResult: Standardized query result container
        """
        start_time = time.time()
        cursor = None
        
        try:
            cursor = connection.cursor(dictionary=True)
            self.logger.debug(f"Executing parameterized MySQL query: {query[:100]}...")
            cursor.execute(query, params)
            
            if cursor.description:
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                data = rows
                row_count = len(data)
            else:
                data = []
                columns = []
                row_count = cursor.rowcount
                
                if cursor.lastrowid:
                    data = [{'last_insert_id': cursor.lastrowid}]
                    columns = ['last_insert_id']
            
            execution_time = time.time() - start_time
            
            return QueryResult(
                data=data,
                columns=columns,
                row_count=row_count,
                success=True,
                execution_time=execution_time
            )
            
        except MySQLError as e:
            execution_time = time.time() - start_time
            error_msg = self.format_error_message(e, "Parameterized MySQL query execution failed")
            
            return QueryResult(
                data=[],
                columns=[],
                row_count=0,
                success=False,
                execution_time=execution_time,
                error_message=error_msg
            )
        finally:
            if cursor:
                cursor.close()
    
    def get_connection_string(self, connection_info: ConnectionInfo) -> str:
        """
        Generate MySQL connection string.
        
        Args:
            connection_info: MySQL connection parameters
            
        Returns:
            str: Formatted MySQL connection string
        """
        encoded_password = quote_plus(connection_info.db_password)
        return (
            f"mysql+mysqlconnector://{connection_info.db_user}:{encoded_password}"
            f"@{connection_info.db_host}:{connection_info.db_port}/{connection_info.db_name}"
        )
    
    def get_supported_features(self) -> Dict[str, bool]:
        """
        Get MySQL feature support matrix.
        
        Returns:
            Dict[str, bool]: Feature support matrix for MySQL
        """
        return {
            "connection_pooling": True,
            "transactions": True,
            "foreign_keys": True,
            "stored_procedures": True,
            "window_functions": True,  # MySQL 8.0+
            "json_support": True,      # MySQL 5.7+
            "array_support": False,    # Not native in MySQL
            "full_text_search": True,
            "materialized_views": False,  # Not supported
            "partitioning": True,
            "extensions": False,       # Not like PostgreSQL
            "custom_types": False,     # Limited support
            "recursive_queries": True, # MySQL 8.0+ CTE
            "upsert": True,           # INSERT ... ON DUPLICATE KEY UPDATE
            "auto_increment": True,
            "multiple_storage_engines": True,
            "replication": True
        }
