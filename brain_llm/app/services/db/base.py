"""
Database Service Abstraction Module
===================================

This module defines the abstract base class for database services in the Brain LLM application.
It implements the Strategy Pattern to provide a unified interface for different database providers,
similar to the multi-LLM service architecture.

Key Components:
- BaseDatabaseService: Abstract base class defining the database service interface
- ConnectionInfo: Data class for database connection parameters
- QueryResult: Data class for standardized query results

Design Patterns:
- Strategy Pattern: Allows swapping database providers without code changes
- Factory Pattern: Used in conjunction with database service factory
- Template Method: Defines common interface while allowing provider-specific implementations

Supported Database Providers:
- PostgreSQL (via postgresql.py)
- MySQL (via mysql.py) 
- SQLite (via sqlite.py)
- Snowflake (via snowflake.py)
- Extensible for additional providers

Author: Brain LLM Team
"""

from abc import ABC, abstractmethod
from typing import Any, Generator, Optional, Dict, List, Tuple
from dataclasses import dataclass
from sqlalchemy.engine import Engine
import logging

logger = logging.getLogger(__name__)

@dataclass
class ConnectionInfo:
    """
    Data structure for database connection parameters.
    
    This class provides a standardized way to pass database connection
    information across different database providers, enabling consistent
    connection management regardless of the underlying database type.
    
    Attributes:
        db_type (str): Database type identifier (postgresql, mysql, sqlite, snowflake)
        db_host (str): Database server hostname or IP address
        db_port (int): Database server port number
        db_name (str): Database/schema name
        db_user (str): Database username for authentication
        db_password (str): Database password for authentication
        db_schema (Optional[str]): Pre-provided schema string to avoid fetching
        additional_params (Dict[str, Any]): Database-specific additional parameters
        
    Usage:
        # PostgreSQL connection
        pg_info = ConnectionInfo(
            db_type="postgresql",
            db_host="localhost",
            db_port=5432,
            db_name="adventureworks",
            db_user="postgres",
            db_password="password"
        )
        
        # Snowflake connection with additional parameters
        sf_info = ConnectionInfo(
            db_type="snowflake",
            db_host="account.snowflakecomputing.com",
            db_port=443,
            db_name="DATABASE",
            db_user="user",
            db_password="password",
            additional_params={
                "warehouse": "COMPUTE_WH",
                "role": "ACCOUNTADMIN",
                "schema": "PUBLIC"
            }
        )
    """
    db_type: str
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    db_schema: Optional[str] = None
    additional_params: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize additional_params as empty dict if None"""
        if self.additional_params is None:
            self.additional_params = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert ConnectionInfo to dictionary for serialization.
        
        Returns:
            dict: Dictionary representation suitable for JSON serialization
        """
        return {
            "db_type": self.db_type,
            "db_host": self.db_host,
            "db_port": self.db_port,
            "db_name": self.db_name,
            "db_user": self.db_user,
            "db_password": "***",  # Mask password for security
            "db_schema": self.db_schema,
            "additional_params": self.additional_params
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConnectionInfo':
        """
        Create ConnectionInfo from dictionary.
        
        Args:
            data: Dictionary containing connection parameters
            
        Returns:
            ConnectionInfo: Validated connection info instance
        """
        return cls(
            db_type=data.get('db_type', 'postgresql'),
            db_host=data['db_host'],
            db_port=data['db_port'],
            db_name=data['db_name'],
            db_user=data['db_user'],
            db_password=data['db_password'],
            db_schema=data.get('db_schema'),
            additional_params=data.get('additional_params', {})
        )

@dataclass
class QueryResult:
    """
    Standardized query result container.
    
    This class provides a consistent interface for query results across
    different database providers, enabling uniform result processing
    regardless of the underlying database type.
    
    Attributes:
        data (List[Dict[str, Any]]): Query result rows as list of dictionaries
        columns (List[str]): Column names in order
        row_count (int): Number of rows returned
        execution_time (Optional[float]): Query execution time in seconds
        error_message (Optional[str]): Error message if query failed
        success (bool): Whether query executed successfully
        
    Usage:
        # Successful query result
        result = QueryResult(
            data=[{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}],
            columns=["id", "name"],
            row_count=2,
            execution_time=0.045,
            success=True
        )
        
        # Failed query result
        error_result = QueryResult(
            data=[],
            columns=[],
            row_count=0,
            success=False,
            error_message="Syntax error in SQL query"
        )
    """
    data: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    success: bool = True
    execution_time: Optional[float] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert QueryResult to dictionary for API responses.
        
        Returns:
            dict: Dictionary representation suitable for JSON serialization
        """
        return {
            "data": self.data,
            "columns": self.columns,
            "row_count": self.row_count,
            "success": self.success,
            "execution_time": self.execution_time,
            "error_message": self.error_message
        }

class BaseDatabaseService(ABC):
    """
    Abstract base class defining the interface for database services.
    
    This class implements the Strategy Pattern, allowing the application to work
    with different database providers (PostgreSQL, MySQL, SQLite, Snowflake)
    through a unified interface, similar to the multi-LLM service architecture.
    
    Key Responsibilities:
    1. Connection management (context managers, pooling)
    2. Schema introspection and caching
    3. Query execution with error handling
    4. Database-specific optimizations
    5. Connection string generation
    
    Design Benefits:
    - Database independence: Switch database providers without code changes
    - Consistent error handling across all providers
    - Standardized connection management
    - Type safety through abstract method definitions
    
    Implementation Notes:
    - All concrete implementations must override abstract methods
    - Connection parameters are provided per-request for multi-tenant support
    - Schema caching is implemented at the service level
    - Error handling should be comprehensive and informative
    """
    
    def __init__(self, connection_info: Optional[ConnectionInfo] = None):
        """
        Initialize the database service with optional connection info.
        
        Args:
            connection_info: Database connection parameters. If None,
                           implementation should use default configuration.
        """
        self.connection_info = connection_info
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    # =============================================================================
    # CORE CONNECTION MANAGEMENT METHODS
    # =============================================================================
    
    @abstractmethod
    def get_connection(self, connection_info: ConnectionInfo) -> Generator[Any, None, None]:
        """
        Create a database connection with context management.
        
        This method should return a context manager that automatically handles
        connection lifecycle including cleanup in case of exceptions.
        
        Args:
            connection_info: Database connection parameters
            
        Yields:
            Connection object specific to the database provider
            
        Raises:
            DatabaseConnectionError: If connection fails
            
        Example:
            for conn in db_service.get_connection(conn_info):
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM table")
                results = cursor.fetchall()
        """
        pass
    
    @abstractmethod
    def get_engine(self, connection_info: ConnectionInfo) -> Engine:
        """
        Create a SQLAlchemy engine for the database connection.
        
        This method should return a configured SQLAlchemy engine with
        appropriate connection pooling and database-specific settings.
        
        Args:
            connection_info: Database connection parameters
            
        Returns:
            SQLAlchemy Engine configured for the specific database
            
        Raises:
            DatabaseConnectionError: If engine creation fails
            
        Example:
            engine = db_service.get_engine(conn_info)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
        """
        pass
    
    @abstractmethod
    def validate_connection(self, connection_info: ConnectionInfo) -> Tuple[bool, Optional[str]]:
        """
        Validate database connection without establishing persistent connection.
        
        This method performs a quick connection test to verify that the
        provided connection parameters are valid and the database is accessible.
        
        Args:
            connection_info: Database connection parameters to validate
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
            
        Example:
            is_valid, error = db_service.validate_connection(conn_info)
            if not is_valid:
                logger.error(f"Connection validation failed: {error}")
        """
        pass
    
    def test_connection(self, **kwargs) -> Dict[str, Any]:
        """
        Test database connection and return detailed information.
        
        This method provides a higher-level interface for connection testing
        that returns structured information suitable for API responses.
        
        Args:
            **kwargs: Database connection parameters (varies by database type)
            
        Returns:
            Dict containing connection test results:
            {
                "success": bool,
                "error": Optional[str],
                "version": Optional[str],
                "tables_count": Optional[int],
                "connection_info": Optional[Dict]
            }
        """
        try:
            # Build connection info from kwargs
            connection_info = self._build_connection_info_from_kwargs(**kwargs)
            
            # Validate connection
            is_valid, error_message = self.validate_connection(connection_info)
            
            if not is_valid:
                return {
                    "success": False,
                    "error": error_message
                }
            
            # Get additional connection details
            with self.get_connection(connection_info) as conn:
                try:
                    tables = self.get_table_names(conn)
                    version_info = self._get_database_version(conn)
                    
                    return {
                        "success": True,
                        "version": version_info,
                        "tables_count": len(tables),
                        "connection_info": {
                            "database_type": self.get_database_type(),
                            "host": getattr(connection_info, 'db_host', None),
                            "database": connection_info.db_name,
                            "schema": getattr(connection_info, 'db_schema', None)
                        }
                    }
                except Exception as e:
                    # Connection works but schema introspection failed
                    return {
                        "success": True,
                        "error": f"Connected but schema access failed: {str(e)}",
                        "connection_info": {
                            "database_type": self.get_database_type(),
                            "host": getattr(connection_info, 'db_host', None),
                            "database": connection_info.db_name
                        }
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_connection_info_from_kwargs(self, **kwargs) -> ConnectionInfo:
        """
        Build ConnectionInfo from keyword arguments.
        
        This method handles the conversion from API parameters to the
        standardized ConnectionInfo structure, with database-specific
        parameter mapping.
        """
        # Default values
        connection_params = {
            'db_type': self.get_database_type(),
            'db_host': kwargs.get('host', 'localhost'),
            'db_port': kwargs.get('port', 5432),
            'db_name': kwargs.get('database', ''),
            'db_user': kwargs.get('username', ''),
            'db_password': kwargs.get('password', ''),
            'db_schema': kwargs.get('schema', None),
            'additional_params': {}
        }
        
        # Handle database-specific parameters
        if 'account' in kwargs:  # Snowflake
            connection_params['additional_params']['account'] = kwargs['account']
        if 'warehouse' in kwargs:  # Snowflake
            connection_params['additional_params']['warehouse'] = kwargs['warehouse']
            
        return ConnectionInfo(**connection_params)
    
    def _get_database_version(self, connection: Any) -> Optional[str]:
        """
        Get database version information.
        
        This method should be overridden by concrete implementations
        to provide database-specific version queries.
        """
        try:
            # Default SQL that works for most databases
            result = self.execute_query(connection, "SELECT VERSION()")
            if result.success and result.data:
                return result.data[0].get('version', 'Unknown')
        except:
            pass
        return None
    
    # =============================================================================
    # SCHEMA INTROSPECTION METHODS
    # =============================================================================
    
    @abstractmethod
    def get_schema_string(self, connection: Any) -> str:
        """
        Extract database schema as a formatted string for LLM consumption.
        
        This method should return a comprehensive schema description including
        tables, columns, data types, relationships, and constraints in a format
        optimized for LLM processing and SQL query generation.
        
        Args:
            connection: Active database connection object
            
        Returns:
            str: Formatted schema string suitable for LLM prompts
            
        Raises:
            DatabaseSchemaError: If schema extraction fails
            
        Example:
            schema = db_service.get_schema_string(connection)
            # Returns formatted string like:
            # "Table: customers (id INTEGER PRIMARY KEY, name VARCHAR(100), ...)"
        """
        pass
    
    @abstractmethod
    def get_table_names(self, connection: Any) -> List[str]:
        """
        Get list of all table names in the database.
        
        Args:
            connection: Active database connection object
            
        Returns:
            List[str]: Table names in the database
            
        Raises:
            DatabaseSchemaError: If table listing fails
        """
        pass
    
    @abstractmethod
    def get_table_schema(self, connection: Any, table_name: str) -> Dict[str, Any]:
        """
        Get detailed schema information for a specific table.
        
        Args:
            connection: Active database connection object
            table_name: Name of the table to analyze
            
        Returns:
            Dict containing table schema details (columns, types, constraints)
            
        Raises:
            DatabaseSchemaError: If table schema extraction fails
        """
        pass
    
    # =============================================================================
    # QUERY EXECUTION METHODS
    # =============================================================================
    
    @abstractmethod
    def execute_query(self, connection: Any, query: str) -> QueryResult:
        """
        Execute a SQL query and return standardized results.
        
        This method should handle query execution, result formatting, and
        error handling in a consistent manner across all database providers.
        
        Args:
            connection: Active database connection object
            query: SQL query string to execute
            
        Returns:
            QueryResult: Standardized query result container
            
        Example:
            result = db_service.execute_query(conn, "SELECT * FROM customers")
            if result.success:
                for row in result.data:
                    print(row)
            else:
                print(f"Query failed: {result.error_message}")
        """
        pass
    
    @abstractmethod
    def execute_query_with_params(self, connection: Any, query: str, params: Dict[str, Any]) -> QueryResult:
        """
        Execute a parameterized SQL query to prevent SQL injection.
        
        Args:
            connection: Active database connection object
            query: SQL query string with parameter placeholders
            params: Dictionary of parameter values
            
        Returns:
            QueryResult: Standardized query result container
        """
        pass
    
    # =============================================================================
    # CONNECTION STRING AND CONFIGURATION METHODS
    # =============================================================================
    
    @abstractmethod
    def get_connection_string(self, connection_info: ConnectionInfo) -> str:
        """
        Generate database-specific connection string.
        
        This method should create a properly formatted connection string
        for the specific database provider, handling URL encoding and
        database-specific connection parameters.
        
        Args:
            connection_info: Database connection parameters
            
        Returns:
            str: Formatted connection string for the database provider
            
        Note:
            Connection strings with passwords should be handled securely
            and never logged in their complete form.
            
        Example:
            # PostgreSQL: postgresql://user:pass@host:port/db
            # MySQL: mysql+pymysql://user:pass@host:port/db
            # SQLite: sqlite:///path/to/database.db
        """
        pass
    
    @abstractmethod
    def get_supported_features(self) -> Dict[str, bool]:
        """
        Get dictionary of supported database features.
        
        Returns:
            Dict[str, bool]: Feature support matrix for this database
            
        Example:
            {
                "connection_pooling": True,
                "transactions": True,
                "foreign_keys": True,
                "stored_procedures": True,
                "window_functions": True,
                "json_support": True
            }
        """
        pass
    
    # =============================================================================
    # UTILITY AND HELPER METHODS
    # =============================================================================
    
    def get_database_type(self) -> str:
        """
        Get the database type identifier for this service.
        
        Returns:
            str: Database type (postgresql, mysql, sqlite, snowflake)
        """
        return self.__class__.__name__.lower().replace('service', '')
    
    def format_error_message(self, original_error: Exception, context: str = "") -> str:
        """
        Format database error messages in a user-friendly way.
        
        Args:
            original_error: The original database exception
            context: Additional context about what operation failed
            
        Returns:
            str: Formatted, user-friendly error message
        """
        error_type = type(original_error).__name__
        base_message = str(original_error)
        
        if context:
            return f"{context}: {error_type} - {base_message}"
        return f"{error_type}: {base_message}"
    
    def log_connection_attempt(self, connection_info: ConnectionInfo, success: bool, error: Optional[str] = None):
        """
        Log connection attempts for monitoring and debugging.
        
        Args:
            connection_info: Connection parameters (passwords will be masked)
            success: Whether the connection was successful
            error: Error message if connection failed
        """
        masked_info = connection_info.to_dict()  # Already masks password
        
        if success:
            self.logger.info(f"Successfully connected to {masked_info['db_type']} database: "
                           f"{masked_info['db_host']}:{masked_info['db_port']}/{masked_info['db_name']}")
        else:
            self.logger.error(f"Failed to connect to {masked_info['db_type']} database: "
                            f"{masked_info['db_host']}:{masked_info['db_port']}/{masked_info['db_name']} - {error}")

# =============================================================================
# CUSTOM EXCEPTIONS
# =============================================================================

class DatabaseServiceError(Exception):
    """Base exception for database service errors."""
    pass

class DatabaseConnectionError(DatabaseServiceError):
    """Exception raised when database connection fails."""
    pass

class DatabaseSchemaError(DatabaseServiceError):
    """Exception raised when schema introspection fails."""
    pass

class DatabaseQueryError(DatabaseServiceError):
    """Exception raised when query execution fails."""
    pass
