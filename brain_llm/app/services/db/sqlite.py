"""
SQLite Database Service Implementation
=====================================

This module provides SQLite-specific database service implementation for the Brain LLM application.
It extends the BaseDatabaseService to provide SQLite-optimized connection management, schema
introspection, and query execution capabilities.

Key Features:
- SQLite connection management with file-based databases
- Advanced schema introspection with foreign keys and constraints
- Dictionary-style result access for consistency
- SQLite-specific error handling and optimization
- Support for in-memory and file-based databases

Integration:
- Follows the same pattern as PostgreSQL and MySQL services
- Maintains compatibility with multi-database architecture
- Optimized for SQLite limitations and strengths
- Supports dynamic SQLite database files

SQLite Considerations:
- No connection pooling (SQLite is file-based)
- Limited concurrent write access
- No stored procedures or complex data types
- Excellent for development and lightweight applications

Author: Brain LLM Team
"""

import sqlite3
from sqlite3 import Row, Error as SQLiteError
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from urllib.parse import quote_plus
from typing import Any, Generator, Optional, Dict, List, Tuple
import time
import logging
import os
from pathlib import Path

from app.services.db.base import (
    BaseDatabaseService, 
    ConnectionInfo, 
    QueryResult,
    DatabaseConnectionError,
    DatabaseSchemaError,
    DatabaseQueryError
)

logger = logging.getLogger(__name__)

class SQLiteService(BaseDatabaseService):
    """
    SQLite database service implementation.
    
    This service provides SQLite-specific implementations for all database operations
    including connection management, schema introspection, and query execution.
    It handles SQLite's unique characteristics including file-based storage,
    limited concurrency, and simplified feature set.
    
    Features:
    - File-based database management
    - In-memory database support (:memory:)
    - Advanced SQLite schema introspection
    - Dictionary-style result access for consistency
    - SQLite-specific error handling
    - WAL mode support for better concurrency
    
    SQLite Limitations:
    - No connection pooling (file-based, single writer)
    - No stored procedures
    - Limited data types (TEXT, INTEGER, REAL, BLOB)
    - No user management or authentication
    - Limited concurrent write operations
    
    Performance Optimizations:
    - WAL mode for better read concurrency
    - Efficient schema caching
    - Proper transaction handling
    - Foreign key constraint enforcement
    """
    
    def __init__(self, connection_info: Optional[ConnectionInfo] = None):
        """
        Initialize SQLite service.
        
        Args:
            connection_info: Optional SQLite connection parameters
        """
        super().__init__(connection_info)
        self.logger = logging.getLogger(f"{__name__}.SQLiteService")
        self._engines: Dict[str, Engine] = {}  # Engine cache
        
    def get_connection(self, connection_info: ConnectionInfo) -> Generator[sqlite3.Connection, None, None]:
        """
        Create a SQLite connection with context management.
        
        This method provides a raw sqlite3 connection with Row factory for
        dictionary-style access, maintaining consistency with other database services.
        
        Args:
            connection_info: SQLite connection parameters
                           - db_name should be the database file path or ":memory:"
                           - other fields are ignored for SQLite
            
        Yields:
            sqlite3.Connection: Raw SQLite connection with Row factory
            
        Raises:
            DatabaseConnectionError: If connection fails
            
        Example:
            for conn in sqlite_service.get_connection(conn_info):
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM customers")
                results = cursor.fetchall()  # Returns list of Row objects (dict-like)
        """
        connection = None
        db_path = connection_info.db_name
        
        try:
            # Handle special case for in-memory database
            if db_path == ":memory:":
                self.logger.info("Connecting to SQLite in-memory database")
            else:
                # Convert to absolute path and ensure directory exists
                if not os.path.isabs(db_path):
                    db_path = os.path.abspath(db_path)
                
                # Create directory if it doesn't exist
                db_dir = os.path.dirname(db_path)
                if db_dir and not os.path.exists(db_dir):
                    os.makedirs(db_dir, exist_ok=True)
                    self.logger.info(f"Created directory for SQLite database: {db_dir}")
                
                self.logger.info(f"Connecting to SQLite database: {db_path}")
            
            # Create connection with optimized settings
            connection = sqlite3.connect(
                db_path,
                timeout=30.0,  # 30 second timeout for lock contention
                check_same_thread=False,  # Allow connection sharing across threads
                isolation_level=None  # Autocommit mode
            )
            
            # Set Row factory for dictionary-like access
            connection.row_factory = sqlite3.Row
            
            # Configure SQLite for better performance and consistency
            cursor = connection.cursor()
            
            # Enable foreign key constraints (disabled by default in SQLite)
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Use WAL mode for better concurrency (if not in-memory)
            if db_path != ":memory:":
                cursor.execute("PRAGMA journal_mode = WAL")
            
            # Set cache size (negative value = KB, positive = pages)
            cursor.execute("PRAGMA cache_size = -64000")  # 64MB cache
            
            # Synchronous mode for better performance (still safe with WAL)
            cursor.execute("PRAGMA synchronous = NORMAL")
            
            # Enable query planner optimizations
            cursor.execute("PRAGMA optimize")
            
            # Test the connection
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()[0]
            self.logger.info(f"Connected to SQLite version: {version}")
            
            cursor.close()
            self.log_connection_attempt(connection_info, True)
            yield connection
            
        except SQLiteError as e:
            error_msg = self.format_error_message(e, "SQLite connection failed")
            self.log_connection_attempt(connection_info, False, error_msg)
            raise DatabaseConnectionError(error_msg) from e
        except Exception as e:
            error_msg = self.format_error_message(e, "Unexpected error during SQLite connection")
            self.log_connection_attempt(connection_info, False, error_msg)
            raise DatabaseConnectionError(error_msg) from e
        finally:
            if connection is not None:
                connection.close()
                self.logger.info("SQLite connection closed")
    
    def get_engine(self, connection_info: ConnectionInfo) -> Engine:
        """
        Create a SQLAlchemy engine for SQLite.
        
        Note: SQLite doesn't support connection pooling in the traditional sense
        since it's file-based. Each connection is independent.
        
        Args:
            connection_info: SQLite connection parameters
            
        Returns:
            Engine: Configured SQLAlchemy engine for SQLite
            
        Raises:
            DatabaseConnectionError: If engine creation fails
        """
        # Create unique key for engine caching
        db_path = connection_info.db_name
        if not os.path.isabs(db_path) and db_path != ":memory:":
            db_path = os.path.abspath(db_path)
        
        engine_key = f"sqlite://{db_path}"
        
        # Return cached engine if available
        if engine_key in self._engines:
            self.logger.info(f"Reusing cached SQLite engine: {engine_key}")
            return self._engines[engine_key]
        
        try:
            self.logger.info(f"Creating new SQLite engine: {engine_key}")
            
            # Create connection string
            if db_path == ":memory:":
                connection_string = "sqlite:///:memory:"
            else:
                # Ensure directory exists
                db_dir = os.path.dirname(db_path)
                if db_dir and not os.path.exists(db_dir):
                    os.makedirs(db_dir, exist_ok=True)
                
                # SQLite URL format
                connection_string = f"sqlite:///{db_path}"
            
            # Create engine with SQLite-specific settings
            engine = create_engine(
                connection_string,
                echo=False,  # Set to True for SQL debugging
                pool_pre_ping=True,  # Validate connections before use
                pool_timeout=30,
                connect_args={
                    'timeout': 30,
                    'check_same_thread': False,
                }
            )
            
            # Test the engine and configure SQLite settings
            with engine.connect() as conn:
                # Test connection
                result = conn.execute(text("SELECT sqlite_version()"))
                version = result.fetchone()[0]
                self.logger.info(f"SQLite engine connected, version: {version}")
                
                # Configure SQLite settings
                conn.execute(text("PRAGMA foreign_keys = ON"))
                if db_path != ":memory:":
                    conn.execute(text("PRAGMA journal_mode = WAL"))
                conn.execute(text("PRAGMA cache_size = -64000"))
                conn.execute(text("PRAGMA synchronous = NORMAL"))
                conn.commit()
            
            # Cache the engine for reuse
            self._engines[engine_key] = engine
            self.logger.info(f"Successfully created and cached SQLite engine: {engine_key}")
            
            return engine
            
        except Exception as e:
            error_msg = self.format_error_message(e, "SQLite engine creation failed")
            self.logger.error(error_msg)
            raise DatabaseConnectionError(error_msg) from e
    
    def validate_connection(self, connection_info: ConnectionInfo) -> Tuple[bool, Optional[str]]:
        """
        Validate SQLite connection without establishing persistent connection.
        
        Args:
            connection_info: SQLite connection parameters to validate
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            db_path = connection_info.db_name
            
            # Handle in-memory database
            if db_path == ":memory:":
                # In-memory databases are always valid
                return True, None
            
            # Convert to absolute path
            if not os.path.isabs(db_path):
                db_path = os.path.abspath(db_path)
            
            # Check if directory exists or can be created
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                try:
                    os.makedirs(db_dir, exist_ok=True)
                except OSError as e:
                    return False, f"Cannot create directory for SQLite database: {str(e)}"
            
            # Test connection
            test_connection = sqlite3.connect(db_path, timeout=10.0)
            cursor = test_connection.cursor()
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()[0]
            cursor.close()
            test_connection.close()
            
            self.logger.info(f"SQLite validation successful: {version}")
            return True, None
            
        except SQLiteError as e:
            error_msg = f"SQLite validation failed: {str(e)}"
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error during SQLite validation: {str(e)}"
            return False, error_msg
    
    def get_schema_string(self, connection: sqlite3.Connection) -> str:
        """
        Extract SQLite schema as formatted string for LLM consumption.
        
        This method provides comprehensive schema information including tables,
        columns, data types, constraints, foreign keys, and indexes in a format
        optimized for LLM processing and SQL query generation.
        
        Args:
            connection: Active SQLite connection
            
        Returns:
            str: Formatted schema string suitable for LLM prompts
            
        Raises:
            DatabaseSchemaError: If schema extraction fails
        """
        try:
            self.logger.info("Starting SQLite schema extraction")
            schema_parts = []
            
            cursor = connection.cursor()
            
            # Get database information
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()[0]
            
            # Get database file info
            cursor.execute("PRAGMA database_list")
            db_info = cursor.fetchone()
            db_name = db_info[1] if db_info else "main"
            db_file = db_info[2] if db_info else ":memory:"
            
            schema_parts.append(f"Database: {db_name}")
            schema_parts.append(f"SQLite Version: {version}")
            schema_parts.append(f"Database File: {db_file}")
            schema_parts.append("")
            
            # Get all tables (excluding SQLite system tables)
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            if not tables:
                cursor.close()
                return "No user tables found in the database."
            
            schema_parts.append(f"Found {len(tables)} tables:")
            schema_parts.append("")
            
            for table_name in tables:
                schema_parts.append(f"Table: {table_name}")
                
                # Get table creation SQL for detailed information
                cursor.execute("""
                    SELECT sql FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (table_name,))
                create_sql = cursor.fetchone()
                if create_sql:
                    # Parse the CREATE TABLE statement for better formatting
                    # For now, show the simplified column info
                    pass
                
                # Get column information using PRAGMA
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                for col in columns:
                    col_id, col_name, col_type, not_null, default_value, is_pk = col
                    
                    # Format column information
                    type_info = col_type if col_type else "TEXT"
                    nullable = "NOT NULL" if not_null else "NULL"
                    pk_info = " PRIMARY KEY" if is_pk else ""
                    default_info = f" DEFAULT {default_value}" if default_value is not None else ""
                    
                    schema_parts.append(f"  - {col_name}: {type_info} {nullable}{pk_info}{default_info}")
                
                # Get foreign key information
                cursor.execute(f"PRAGMA foreign_key_list({table_name})")
                foreign_keys = cursor.fetchall()
                
                for fk in foreign_keys:
                    fk_id, seq, ref_table, from_col, to_col, on_update, on_delete, match = fk
                    constraint_info = ""
                    if on_update != "NO ACTION":
                        constraint_info += f" ON UPDATE {on_update}"
                    if on_delete != "NO ACTION":
                        constraint_info += f" ON DELETE {on_delete}"
                    
                    schema_parts.append(f"  Foreign Key: {from_col} -> {ref_table}.{to_col}{constraint_info}")
                
                # Get index information
                cursor.execute(f"PRAGMA index_list({table_name})")
                indexes = cursor.fetchall()
                
                for idx in indexes:
                    seq, idx_name, unique, origin, partial = idx
                    if not idx_name.startswith("sqlite_autoindex"):  # Skip auto-indexes
                        unique_info = " UNIQUE" if unique else ""
                        schema_parts.append(f"  Index: {idx_name}{unique_info}")
                
                # Get table row count
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = cursor.fetchone()[0]
                    if row_count > 0:
                        schema_parts.append(f"  Row Count: {row_count:,}")
                except SQLiteError:
                    # Table might not be accessible
                    pass
                
                schema_parts.append("")
            
            # Get view information
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='view'
                ORDER BY name
            """)
            views = [row[0] for row in cursor.fetchall()]
            
            if views:
                schema_parts.append(f"Views ({len(views)}):")
                for view in views:
                    schema_parts.append(f"  - {view}")
                schema_parts.append("")
            
            # Get trigger information
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='trigger'
                ORDER BY name
            """)
            triggers = [row[0] for row in cursor.fetchall()]
            
            if triggers:
                schema_parts.append(f"Triggers ({len(triggers)}):")
                for trigger in triggers:
                    schema_parts.append(f"  - {trigger}")
                schema_parts.append("")
            
            # Get SQLite settings
            cursor.execute("PRAGMA foreign_keys")
            fk_enabled = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            
            schema_parts.append("SQLite Configuration:")
            schema_parts.append(f"  Foreign Keys: {'ON' if fk_enabled else 'OFF'}")
            schema_parts.append(f"  Journal Mode: {journal_mode}")
            
            cursor.close()
            
            schema_string = "\\n".join(schema_parts)
            self.logger.info(f"SQLite schema extraction completed. Schema length: {len(schema_string)} characters")
            return schema_string
            
        except SQLiteError as e:
            error_msg = self.format_error_message(e, "SQLite schema extraction failed")
            self.logger.error(error_msg)
            raise DatabaseSchemaError(error_msg) from e
        except Exception as e:
            error_msg = self.format_error_message(e, "Unexpected error during SQLite schema extraction")
            self.logger.error(error_msg)
            raise DatabaseSchemaError(error_msg) from e
    
    def get_table_names(self, connection: sqlite3.Connection) -> List[str]:
        """
        Get list of all table names in the SQLite database.
        
        Args:
            connection: Active SQLite connection
            
        Returns:
            List[str]: Table names in the database
        """
        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            return tables
        except SQLiteError as e:
            raise DatabaseSchemaError(f"Failed to get table names: {str(e)}") from e
    
    def get_table_schema(self, connection: sqlite3.Connection, table_name: str) -> Dict[str, Any]:
        """
        Get detailed schema information for a specific SQLite table.
        
        Args:
            connection: Active SQLite connection
            table_name: Name of the table to analyze
            
        Returns:
            Dict containing detailed table schema information
        """
        try:
            table_info = {
                'table_name': table_name,
                'columns': [],
                'primary_keys': [],
                'foreign_keys': [],
                'indexes': [],
                'create_sql': None
            }
            
            cursor = connection.cursor()
            
            # Get table creation SQL
            cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table_name,))
            create_result = cursor.fetchone()
            if create_result:
                table_info['create_sql'] = create_result[0]
            
            # Get column information
            cursor.execute(f"PRAGMA table_info({table_name})")
            for col in cursor.fetchall():
                col_id, col_name, col_type, not_null, default_value, is_pk = col
                
                column_info = {
                    'column_name': col_name,
                    'data_type': col_type if col_type else 'TEXT',
                    'is_nullable': not not_null,
                    'column_default': default_value,
                    'is_primary_key': bool(is_pk),
                    'column_id': col_id
                }
                
                table_info['columns'].append(column_info)
                
                # Collect primary keys
                if is_pk:
                    table_info['primary_keys'].append(col_name)
            
            # Get foreign key information
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            for fk in cursor.fetchall():
                fk_id, seq, ref_table, from_col, to_col, on_update, on_delete, match = fk
                
                table_info['foreign_keys'].append({
                    'id': fk_id,
                    'sequence': seq,
                    'column_name': from_col,
                    'referenced_table_name': ref_table,
                    'referenced_column_name': to_col,
                    'on_update': on_update,
                    'on_delete': on_delete,
                    'match': match
                })
            
            # Get index information
            cursor.execute(f"PRAGMA index_list({table_name})")
            for idx in cursor.fetchall():
                seq, idx_name, unique, origin, partial = idx
                
                # Get index columns
                cursor.execute(f"PRAGMA index_info({idx_name})")
                index_columns = []
                for idx_col in cursor.fetchall():
                    seqno, cid, col_name = idx_col
                    index_columns.append({
                        'sequence': seqno,
                        'column_id': cid,
                        'column_name': col_name
                    })
                
                table_info['indexes'].append({
                    'index_name': idx_name,
                    'is_unique': bool(unique),
                    'origin': origin,
                    'is_partial': bool(partial),
                    'columns': index_columns
                })
            
            cursor.close()
            return table_info
            
        except SQLiteError as e:
            raise DatabaseSchemaError(f"Failed to get table schema for {table_name}: {str(e)}") from e
    
    def execute_query(self, connection: sqlite3.Connection, query: str) -> QueryResult:
        """
        Execute a SQLite query and return standardized results.
        
        Args:
            connection: Active SQLite connection
            query: SQL query string to execute
            
        Returns:
            QueryResult: Standardized query result container
        """
        start_time = time.time()
        cursor = None
        
        try:
            cursor = connection.cursor()
            self.logger.debug(f"Executing SQLite query: {query[:100]}...")
            cursor.execute(query)
            
            # Handle different query types
            if cursor.description:
                # SELECT query - fetch results
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                # Convert Row objects to dictionaries for consistency
                data = [dict(row) for row in rows]
                row_count = len(data)
            else:
                # INSERT/UPDATE/DELETE query
                data = []
                columns = []
                row_count = cursor.rowcount
                
                # For INSERT operations, get the last row ID
                if cursor.lastrowid:
                    data = [{'last_insert_rowid': cursor.lastrowid}]
                    columns = ['last_insert_rowid']
            
            execution_time = time.time() - start_time
            
            self.logger.info(f"SQLite query executed successfully. Rows: {row_count}, Time: {execution_time:.3f}s")
            
            return QueryResult(
                data=data,
                columns=columns,
                row_count=row_count,
                success=True,
                execution_time=execution_time
            )
            
        except SQLiteError as e:
            execution_time = time.time() - start_time
            error_msg = self.format_error_message(e, "SQLite query execution failed")
            
            self.logger.error(f"SQLite query failed: {error_msg}")
            
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
            error_msg = self.format_error_message(e, "Unexpected error during SQLite query execution")
            
            self.logger.error(f"Unexpected error in SQLite query: {error_msg}")
            
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
    
    def execute_query_with_params(self, connection: sqlite3.Connection, query: str, params: Dict[str, Any]) -> QueryResult:
        """
        Execute a parameterized SQLite query to prevent SQL injection.
        
        Note: SQLite uses named parameters with :name syntax or ? positional parameters.
        This method converts dictionary parameters to named parameter format.
        
        Args:
            connection: Active SQLite connection
            query: SQL query string with parameter placeholders (:name format)
            params: Dictionary of parameter values
            
        Returns:
            QueryResult: Standardized query result container
        """
        start_time = time.time()
        cursor = None
        
        try:
            cursor = connection.cursor()
            self.logger.debug(f"Executing parameterized SQLite query: {query[:100]}...")
            
            # SQLite expects named parameters in :name format
            # Convert query if it uses %(name)s format to :name format
            if '%(' in query and ')s' in query:
                import re
                # Convert %(name)s to :name
                query = re.sub(r'%\\(([^)]+)\\)s', r':\\1', query)
            
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
                
                if cursor.lastrowid:
                    data = [{'last_insert_rowid': cursor.lastrowid}]
                    columns = ['last_insert_rowid']
            
            execution_time = time.time() - start_time
            
            return QueryResult(
                data=data,
                columns=columns,
                row_count=row_count,
                success=True,
                execution_time=execution_time
            )
            
        except SQLiteError as e:
            execution_time = time.time() - start_time
            error_msg = self.format_error_message(e, "Parameterized SQLite query execution failed")
            
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
        Generate SQLite connection string.
        
        Args:
            connection_info: SQLite connection parameters
                           - db_name should be the database file path or ":memory:"
            
        Returns:
            str: Formatted SQLite connection string
        """
        db_path = connection_info.db_name
        
        if db_path == ":memory:":
            return "sqlite:///:memory:"
        else:
            # Convert to absolute path if not already
            if not os.path.isabs(db_path):
                db_path = os.path.abspath(db_path)
            return f"sqlite:///{db_path}"
    
    def get_supported_features(self) -> Dict[str, bool]:
        """
        Get SQLite feature support matrix.
        
        Returns:
            Dict[str, bool]: Feature support matrix for SQLite
        """
        return {
            "connection_pooling": False,   # SQLite is file-based
            "transactions": True,
            "foreign_keys": True,          # But disabled by default
            "stored_procedures": False,    # Not supported
            "window_functions": True,      # SQLite 3.25+
            "json_support": True,          # SQLite 3.38+ JSON functions
            "array_support": False,        # Not native
            "full_text_search": True,      # FTS extension
            "materialized_views": False,   # Not supported
            "partitioning": False,         # Not supported
            "extensions": True,            # Loadable extensions
            "custom_types": False,         # Limited to 5 storage classes
            "recursive_queries": True,     # Common Table Expressions
            "upsert": True,               # INSERT OR REPLACE / ON CONFLICT
            "auto_increment": True,        # AUTOINCREMENT keyword
            "in_memory_database": True,    # :memory: databases
            "file_based": True,           # File-based storage
            "wal_mode": True,             # Write-Ahead Logging
            "attach_database": True,      # ATTACH DATABASE statement
            "virtual_tables": True,       # Virtual table mechanism
            "rtree_index": True          # R*Tree spatial index
        }
    
    def create_database_file(self, file_path: str) -> bool:
        """
        Create a new SQLite database file.
        
        Args:
            file_path: Path where to create the database file
            
        Returns:
            bool: True if database was created successfully
            
        Raises:
            DatabaseConnectionError: If database creation fails
        """
        try:
            # Convert to absolute path
            if not os.path.isabs(file_path):
                file_path = os.path.abspath(file_path)
            
            # Create directory if it doesn't exist
            db_dir = os.path.dirname(file_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                self.logger.info(f"Created directory for SQLite database: {db_dir}")
            
            # Create database file
            connection = sqlite3.connect(file_path)
            cursor = connection.cursor()
            
            # Configure the new database
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("PRAGMA journal_mode = WAL")
            cursor.execute("PRAGMA cache_size = -64000")
            cursor.execute("PRAGMA synchronous = NORMAL")
            
            connection.commit()
            cursor.close()
            connection.close()
            
            self.logger.info(f"Successfully created SQLite database: {file_path}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to create SQLite database {file_path}: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseConnectionError(error_msg) from e
