"""
Database Service Factory
========================

This module acts as the central factory for all database services within the Brain LLM application.
It implements the **Factory Design Pattern** to decouple the rest of the application from the 
specific implementation details of any given database provider, similar to the multi-LLM service factory.

Core Concepts:
--------------
1.  **Abstraction**: The application interacts with a generic `BaseDatabaseService` interface,
    not with a concrete `PostgreSQLService` or `MySQLService`.
2.  **Decoupling**: The main application logic (e.g., `LangChainStreamingService`) does
    not need to be changed when adding, removing, or modifying a database provider.
3.  **Centralized Registration**: The `_database_services` dictionary acts as a single,
    authoritative registry of all available database services.

How to Add a New Database Service (e.g., for 'Oracle'):
-------------------------------------------------------
To add support for a new database provider, follow these three simple steps:

1.  **Create the Service Class**:
    -   In the `app/services/db/` directory, create a new file (e.g., `oracle.py`).
    -   Inside this file, define a new class (e.g., `OracleService`) that inherits
        from `BaseDatabaseService`.
    -   Implement all the abstract methods defined in `BaseDatabaseService`.

2.  **Import the New Service Class**:
    -   In *this* file (`__init__.py`), add an import statement for your new class.
        ```python
        from .oracle import OracleService
        ```

3.  **Register the Service**:
    -   Add a new entry to the `_database_services` dictionary below. The key should be a
        simple, lowercase string that will be used to request the service (e.g., via
        an API parameter `db_type=oracle`).
        ```python
        "oracle": OracleService
        ```

After these steps, the new database can be invoked throughout the application by
referencing its key (e.g., calling the API with `"db_type": "oracle"`).

Supported Database Types:
------------------------
- PostgreSQL: "postgresql", "postgres", "pg" (aliases)
- MySQL: "mysql", "mariadb" (aliases)
- SQLite: "sqlite", "sqlite3" (aliases) 
- Snowflake: "snowflake" (future implementation)

Architecture Benefits:
---------------------
- **Zero Coupling**: Application logic is independent of database implementation
- **Hot Swapping**: Change database providers without code modifications
- **Easy Extension**: Add new databases with minimal changes
- **Type Safety**: Consistent interface across all database providers
- **Error Handling**: Centralized validation and error reporting

Author: Brain LLM Team
"""

from typing import Type, Optional, Dict, Any, List, Tuple
from app.services.db.base import BaseDatabaseService, ConnectionInfo

# --- Step 1: Import all available database service implementations ---
# Each new database service class must be imported here to be discoverable by the factory.

# PostgreSQL service - primary database for the application
from .postgresql import PostgreSQLService

# MySQL service - enterprise database support
from .mysql import MySQLService

# SQLite service - lightweight database for development and small applications
from .sqlite import SQLiteService

# Future database services (will be implemented in subsequent phases)
# from .snowflake import SnowflakeService

# Example for a future Oracle service:
# from .oracle import OracleService


# --- Step 2: Register the imported services in the dictionary ---
# This dictionary maps a simple, lowercase string identifier (the "key") to the
# corresponding service class. This is the central registry for the factory.
_database_services: Dict[str, Type[BaseDatabaseService]] = {
    # PostgreSQL with aliases
    "postgresql": PostgreSQLService,
    "postgres": PostgreSQLService,  # Common alias
    "pg": PostgreSQLService,        # Short alias
    
    # MySQL with aliases
    "mysql": MySQLService,
    "mariadb": MySQLService,        # Compatible with MySQL
    
    # SQLite with aliases
    "sqlite": SQLiteService,
    "sqlite3": SQLiteService,       # Alternative name
    
    # Future database services (commented out until implemented)
    # "snowflake": SnowflakeService,
    
    # Example for a future Oracle service:
    # "oracle": OracleService,
}


def get_database_service(db_type: str, connection_info: Optional[ConnectionInfo] = None) -> BaseDatabaseService:
    """
    Factory function to instantiate and return a specific database service.

    This function is the single entry point for the rest of the application to
    obtain a concrete database service instance without needing to know about the
    specific implementation classes. It looks up the requested service by its
    string key and returns an initialized object.

    Args:
        db_type: The string identifier for the desired database service. This key
                must exist in the `_database_services` dictionary. The lookup is
                case-insensitive.
        connection_info: Optional connection information to initialize the service with.
                        If None, service will be created without initial connection info.

    Returns:
        An initialized instance of the requested database service class, which
        conforms to the `BaseDatabaseService` interface.

    Raises:
        ValueError: If the provided `db_type` does not correspond to any
                   registered service in the `_database_services` dictionary.
                   
    Example:
        # Get PostgreSQL service
        pg_service = get_database_service("postgresql")
        
        # Get MySQL service with connection info
        mysql_conn_info = ConnectionInfo(
            db_type="mysql",
            db_host="localhost", 
            db_port=3306,
            db_name="sakila",
            db_user="root",
            db_password="password"
        )
        mysql_service = get_database_service("mysql", mysql_conn_info)
    """
    # Use .lower() to ensure the lookup is case-insensitive.
    service_class = _database_services.get(db_type.lower())
    if not service_class:
        supported_types = list(_database_services.keys())
        raise ValueError(
            f"Unsupported database type: '{db_type}'. "
            f"Supported database types are: {supported_types}"
        )
    
    # Instantiate the service with optional connection info
    return service_class(connection_info=connection_info)


def get_supported_database_types() -> List[str]:
    """
    Get list of all supported database types.
    
    Returns:
        List[str]: All registered database type identifiers
        
    Example:
        supported = get_supported_database_types()
        print(f"Supported databases: {', '.join(supported)}")
        # Output: "Supported databases: postgresql, postgres, pg, mysql, sqlite, snowflake"
    """
    return list(_database_services.keys())


def is_database_type_supported(db_type: str) -> bool:
    """
    Check if a database type is supported by the factory.
    
    Args:
        db_type: Database type identifier to check
        
    Returns:
        bool: True if database type is supported, False otherwise
        
    Example:
        if is_database_type_supported("postgresql"):
            service = get_database_service("postgresql")
        else:
            print("PostgreSQL not supported")
    """
    return db_type.lower() in _database_services


def get_database_service_info() -> Dict[str, Dict[str, Any]]:
    """
    Get detailed information about all registered database services.
    
    Returns:
        Dict containing service information for each database type
        
    Example:
        info = get_database_service_info()
        for db_type, details in info.items():
            print(f"{db_type}: {details['class_name']}")
    """
    service_info = {}
    
    for db_type, service_class in _database_services.items():
        service_info[db_type] = {
            "class_name": service_class.__name__,
            "module": service_class.__module__,
            "supported_features": service_class().get_supported_features() if hasattr(service_class, 'get_supported_features') else {}
        }
    
    return service_info


def validate_database_connection_info(connection_info: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate database connection information for any supported database type.
    
    Args:
        connection_info: Dictionary containing database connection parameters
        
    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
        
    Example:
        conn_data = {
            "db_type": "postgresql",
            "db_host": "localhost",
            "db_port": 5432,
            "db_name": "test",
            "db_user": "user",
            "db_password": "pass"
        }
        is_valid, error = validate_database_connection_info(conn_data)
    """
    try:
        # Check required fields
        required_fields = ['db_type', 'db_host', 'db_port', 'db_name', 'db_user', 'db_password']
        missing_fields = [field for field in required_fields if field not in connection_info]
        
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        # Check if database type is supported
        db_type = connection_info.get('db_type')
        if not is_database_type_supported(db_type):
            supported = get_supported_database_types()
            return False, f"Unsupported database type '{db_type}'. Supported types: {', '.join(supported)}"
        
        # Validate port is numeric
        try:
            port = int(connection_info['db_port'])
            if port <= 0 or port > 65535:
                return False, "Port must be between 1 and 65535"
        except (ValueError, TypeError):
            return False, "Port must be a valid integer"
        
        # Create ConnectionInfo object to validate structure
        try:
            conn_info = ConnectionInfo.from_dict(connection_info)
        except Exception as e:
            return False, f"Invalid connection info structure: {str(e)}"
        
        return True, None
        
    except Exception as e:
        return False, f"Validation error: {str(e)}"


# =============================================================================
# FACTORY UTILITIES AND HELPERS
# =============================================================================

class DatabaseServiceFactory:
    """
    Alternative factory class interface for database services.
    
    This class provides a more object-oriented interface to the database service
    factory, useful for dependency injection scenarios or when you need to maintain
    factory state.
    
    Example:
        factory = DatabaseServiceFactory()
        pg_service = factory.create("postgresql")
        mysql_service = factory.create("mysql", conn_info)
    """
    
    def __init__(self):
        """Initialize the database service factory."""
        self._services_cache: Dict[str, BaseDatabaseService] = {}
    
    def create(self, db_type: str, connection_info: Optional[ConnectionInfo] = None) -> BaseDatabaseService:
        """
        Create a database service instance.
        
        Args:
            db_type: Database type identifier
            connection_info: Optional connection information
            
        Returns:
            BaseDatabaseService: Database service instance
        """
        return get_database_service(db_type, connection_info)
    
    def create_with_caching(self, db_type: str, connection_info: Optional[ConnectionInfo] = None) -> BaseDatabaseService:
        """
        Create a database service instance with caching.
        
        Note: Caching is based on db_type only, not connection_info.
        Use with caution in multi-tenant scenarios.
        
        Args:
            db_type: Database type identifier
            connection_info: Optional connection information
            
        Returns:
            BaseDatabaseService: Database service instance (cached if available)
        """
        if db_type not in self._services_cache:
            self._services_cache[db_type] = get_database_service(db_type, connection_info)
        return self._services_cache[db_type]
    
    def get_supported_types(self) -> List[str]:
        """Get list of supported database types."""
        return get_supported_database_types()
    
    def is_supported(self, db_type: str) -> bool:
        """Check if database type is supported."""
        return is_database_type_supported(db_type)
    
    def clear_cache(self):
        """Clear the service cache."""
        self._services_cache.clear()


# Create a default factory instance for convenience
default_factory = DatabaseServiceFactory()
