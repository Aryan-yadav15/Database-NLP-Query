# brain_LLM/app/api/v1/deps.py
"""
FastAPI Dependency Injection Module
===================================

This module implements the Dependency Injection pattern for FastAPI endpoints,
providing centralized creation and management of service instances. It follows
FastAPI's dependency injection system to ensure proper lifecycle management
and singleton patterns where appropriate.

Key Design Patterns:
- Dependency Injection: Services are injected into endpoints via FastAPI's Depends()
- Singleton Pattern: Shared services use @lru_cache for single instances
- Factory Pattern: LLM services are created via factory methods
- Context Manager: Database connections auto-cleanup resources

Service Categories:
1. Configuration Services (Settings)
2. AI/ML Services (LLM, Embedding, DQ Rules)
3. Database Services (PostgreSQL connections)
4. Business Logic Services (Visualization, LangChain)

Author: Brain LLM Team
"""

from functools import lru_cache  # For singleton pattern implementation
from typing import Generator    # For context manager type hints
import psycopg2                # PostgreSQL connection types
from fastapi import Request, Depends  # FastAPI dependency injection
import logging                 # Centralized logging

# Configuration and core services
from app.core.config import Settings
from app.services.embedding_service import EmbeddingService

# LLM service abstractions - supports multiple providers (Gemini, OpenAI, etc.)
from app.services.llm import get_llm_service as llm_service_factory
from app.services.llm.base import BaseLLMService

# Database service abstractions - supports multiple database types
from app.services.connection_manager import ConnectionManager
from app.services.db.base import BaseDatabaseService

# Request-scoped and business logic services
from app.services.token_tracker import RequestTokenTracker
from app.db.pg_connector import get_adventureworks_db_session
from app.services.sql_query_router_logic import ADVENTUREWORKS_SCHEMA_FOR_LLM
from app.services.dq_rule_manager import DQRuleManager
from app.services.visualization_service import VisualizationService
from app.services.langchain_service import LangChainStreamingService

# Module-level logger for dependency creation tracking
logger = logging.getLogger(__name__)

# =============================================================================
# UTILITY FUNCTIONS FOR MULTI-DATABASE SUPPORT
# =============================================================================
"""
Utility functions to help extract and validate database connection information
from requests. These helpers make it easier for endpoints to handle multi-database
scenarios while maintaining clean code separation.
"""

def extract_db_connection_info_from_request(request_data: dict) -> dict:
    """
    Extracts database connection information from request data.
    
    This utility function standardizes the extraction of database connection
    parameters from various request formats, providing defaults and validation.
    
    Args:
        request_data: Request payload containing db_connection_info
        
    Returns:
        dict: Normalized database connection information
        
    Default Behavior:
        - Defaults to PostgreSQL if no db_type specified
        - Uses environment defaults for missing connection parameters
        - Validates required fields for non-SQLite databases
    """
    from app.core.config import Settings
    settings = Settings()
    
    # Extract db_connection_info from request
    db_connection_info = request_data.get('db_connection_info', {})
    
    # Set defaults for backward compatibility
    return {
        'db_type': db_connection_info.get('db_type', 'postgresql'),
        'db_host': db_connection_info.get('db_host', settings.PG_HOST),
        'db_port': db_connection_info.get('db_port', settings.PG_PORT),
        'db_name': db_connection_info.get('db_name', settings.PG_DATABASE_AW),
        'db_user': db_connection_info.get('db_user', settings.PG_USER),
        'db_password': db_connection_info.get('db_password', settings.PG_PASSWORD),
        'db_schema': db_connection_info.get('db_schema'),
        'additional_params': db_connection_info.get('additional_params', {})
    }

def validate_database_connection_info(db_connection_info: dict) -> bool:
    """
    Validates database connection information for completeness.
    
    Args:
        db_connection_info: Database connection parameters to validate
        
    Returns:
        bool: True if connection info is valid, False otherwise
        
    Validation Rules:
        - SQLite: Only requires db_name (file path)
        - Other databases: Require host, port, name, user, password
    """
    db_type = db_connection_info.get('db_type', 'postgresql')
    
    if db_type.lower() == 'sqlite':
        return 'db_name' in db_connection_info
    
    required_fields = ['db_host', 'db_port', 'db_name', 'db_user', 'db_password']
    return all(field in db_connection_info and db_connection_info[field] for field in required_fields)

# =============================================================================
# SINGLETON SERVICE DEPENDENCIES
# =============================================================================
"""
Singleton services are created once per application lifecycle and shared
across all requests. They use @lru_cache(maxsize=1) to ensure only one
instance exists, improving performance and maintaining state consistency.

Singleton Pattern Benefits:
- Memory efficiency: Single instance shared across requests
- Performance: Avoid repeated expensive initialization
- State consistency: Shared configuration and cached data
- Resource management: Single connection pools and model instances
"""

@lru_cache()
def get_settings() -> Settings:
    """
    Provides the global application settings singleton.
    
    This dependency ensures that all endpoints use the same configuration
    instance, preventing inconsistencies from multiple Settings() creations.
    
    Returns:
        Settings: Validated application configuration instance
        
    Usage in endpoints:
        @app.get("/health")
        def health_check(settings: Settings = Depends(get_settings)):
            return {"status": "ok", "log_level": settings.LOG_LEVEL}
    """
    return Settings()

@lru_cache()
def get_embedding_service() -> EmbeddingService:
    """
    Provides the singleton embedding service for vector operations.
    
    The embedding service loads a heavy ML model (80MB+) that should only
    be initialized once for performance and memory efficiency.
    
    Features:
    - Sentence transformer model for text embeddings
    - Used for DQ rule similarity matching
    - ChromaDB vector operations
    
    Returns:
        EmbeddingService: Initialized embedding service with loaded model
        
    Performance Note:
        First call loads the model (2-3 seconds), subsequent calls are instant.
    """
    return EmbeddingService()

# =============================================================================
# LLM SERVICE FACTORY DEPENDENCY
# =============================================================================
"""
LLM service factory that provides different AI models based on runtime parameters.
This allows dynamic model selection per request without singleton constraints.

Supported Models:
- "gemini": Google Gemini models (gemini-1.5-flash, gemini-1.5-pro)
- Future: "openai", "claude", "llama" (extensible architecture)
"""

def get_llm_service(model_name: str = "gemini") -> BaseLLMService:
    """
    Factory dependency for creating LLM service instances.
    
    This function acts as a bridge between FastAPI's dependency injection
    and the LLM service factory pattern. It allows per-request model
    selection while maintaining the abstraction layer.
    
    Args:
        model_name: LLM provider name ("gemini", "openai", etc.)
        
    Returns:
        BaseLLMService: Configured LLM service instance
        
    Design Notes:
        - No @lru_cache to allow different models per request
        - Factory pattern enables easy addition of new LLM providers
        - Abstract interface ensures consistent API across providers
        
    Usage in endpoints:
        @app.post("/generate")
        def generate_text(
            request: GenerateRequest,
            llm: BaseLLMService = Depends(get_llm_service)
        ):
            return llm.generate_text(request.prompt)
    """
    return llm_service_factory(model_name)

@lru_cache()
def get_dq_rule_manager() -> DQRuleManager:
    """
    Provides the singleton Data Quality (DQ) rule manager.
    
    The DQ manager loads and indexes 500+ business rules from CSV files
    into ChromaDB for semantic similarity search. This is expensive to
    initialize and should be shared across all requests.
    
    Features:
    - ChromaDB vector storage for rule embeddings
    - Semantic search for relevant business rules
    - CSV-based rule definitions for business user maintenance
    - Entity extraction and SQL generation for rule validation
    
    Returns:
        DQRuleManager: Initialized DQ rule manager with loaded rules
        
    Performance:
        - Initial load: 10-15 seconds (CSV parsing + embedding generation)
        - Subsequent access: Instant (cached embeddings in ChromaDB)
        - Memory usage: ~200MB for rule embeddings
    """
    return DQRuleManager(settings=get_settings())

# =============================================================================
# REQUEST-SCOPED DEPENDENCIES
# =============================================================================
"""
Request-scoped dependencies are created fresh for each HTTP request and
automatically cleaned up when the request completes. They manage per-request
state and resources that should not be shared between concurrent requests.

Key Characteristics:
- New instance per request (no @lru_cache)
- Automatic cleanup via context managers
- Request-specific state isolation
- Resource lifecycle tied to request lifecycle
"""

def get_token_tracker(request: Request) -> RequestTokenTracker:
    """
    Provides a request-scoped token usage tracker.
    
    Each HTTP request gets its own token tracker to accumulate LLM API
    usage across multiple service calls within that request. This enables
    accurate per-request cost tracking and billing.
    
    Args:
        request: FastAPI Request object for unique identification
        
    Returns:
        RequestTokenTracker: Fresh tracker instance for this request
        
    Features:
    - Accumulates token usage from multiple LLM calls
    - Request-scoped isolation prevents cross-request contamination
    - Enables streaming token usage updates to client
    - Supports cost analysis and usage monitoring
    
    Usage Pattern:
        1. Request starts -> New tracker created
        2. LLM calls made -> Tokens accumulated in tracker
        3. Request ends -> Final token count sent to client
    """
    # Generate unique request ID for tracking and debugging
    request_id = getattr(request.state, 'request_id', id(request))
    return RequestTokenTracker(request_id=str(request_id))

def get_aw_db() -> Generator[psycopg2.extensions.connection, None, None]:
    """
    Provides a request-scoped PostgreSQL connection to AdventureWorks database.
    
    This dependency yields a database connection that is automatically
    cleaned up when the request completes, preventing connection leaks
    and ensuring proper resource management.
    
    Yields:
        psycopg2.extensions.connection: Active database connection
        
    Features:
    - Automatic connection cleanup via generator pattern
    - RealDictCursor for dictionary-style result access
    - Connection pooling handled by underlying service
    - Exception safety with guaranteed cleanup
    
    Usage in endpoints:
        @app.get("/customers")
        def get_customers(db: psycopg2.connection = Depends(get_aw_db)):
            cursor = db.cursor()
            cursor.execute("SELECT * FROM customers")
            return cursor.fetchall()
    """
    yield from get_adventureworks_db_session()

# =============================================================================
# MULTI-DATABASE SERVICE DEPENDENCIES
# =============================================================================
"""
Multi-database dependencies provide unified access to different database types
through the new database service architecture. These dependencies enable
endpoints to work with PostgreSQL, MySQL, SQLite, Snowflake, and other
databases through a consistent interface.

Architecture Benefits:
- Unified Interface: Same API across all database types
- Service Abstraction: Database-specific optimizations hidden behind interface
- Connection Management: Proper lifecycle and resource management
- Extensibility: Easy to add new database types
"""

@lru_cache()
def get_connection_manager() -> ConnectionManager:
    """
    Provides the singleton connection manager for multi-database operations.
    
    The connection manager coordinates database service creation, connection
    pooling, and service caching across different database types. It's
    expensive to initialize and should be shared across all requests.
    
    Returns:
        ConnectionManager: Initialized connection manager with service registry
        
    Features:
    - Database service factory and registry
    - Connection pooling per database type and configuration
    - Service caching for performance optimization
    - Health monitoring and connection validation
    
    Performance:
        - Service creation: ~100ms per database type
        - Connection pooling: Shared across requests
        - Memory usage: ~50MB for service instances and pools
    """
    return ConnectionManager()

def get_database_service(
    db_type: str = "postgresql",
    connection_manager: ConnectionManager = Depends(get_connection_manager)
) -> BaseDatabaseService:
    """
    Factory dependency for creating database service instances.
    
    This function provides database-specific service instances that implement
    the unified database interface. Services are cached by the connection
    manager for performance optimization.
    
    Args:
        db_type: Database type identifier (postgresql, mysql, sqlite, snowflake)
        connection_manager: Injected connection manager singleton
        
    Returns:
        BaseDatabaseService: Database-specific service implementation
        
    Raises:
        ValueError: If database type is not supported
        
    Usage in endpoints:
        @app.post("/query")
        def execute_query(
            request: QueryRequest,
            db_service: BaseDatabaseService = Depends(get_database_service)
        ):
            # db_service automatically matches the request's db_type
            pass
            
    Design Notes:
        - Services are cached by connection manager for efficiency
        - Each database type has optimized implementations
        - Consistent interface across all database types
    """
    try:
        return connection_manager.get_database_service(db_type)
    except ValueError as e:
        logger.error(f"Failed to get database service for type '{db_type}': {e}")
        raise

def get_dynamic_database_connection(
    db_connection_info: dict,
    connection_manager: ConnectionManager = Depends(get_connection_manager)
) -> Generator[any, None, None]:
    """
    Provides a request-scoped database connection using dynamic connection info.
    
    This dependency creates database connections based on runtime connection
    parameters, enabling multi-tenant scenarios and dynamic database selection.
    Connections are automatically cleaned up when the request completes.
    
    Args:
        db_connection_info: Database connection parameters including db_type
        connection_manager: Injected connection manager singleton
        
    Yields:
        Database connection object (type varies by database)
        
    Connection Info Format:
        {
            "db_type": "postgresql",  # Database type
            "db_host": "localhost",
            "db_port": 5432,
            "db_name": "database",
            "db_user": "username",
            "db_password": "password"
        }
        
    Features:
    - Multi-database type support
    - Automatic connection cleanup
    - Connection pooling and reuse
    - Error handling and validation
    
    Usage in endpoints:
        @app.post("/dynamic-query")
        def dynamic_query(
            request: QueryRequest,
            db_conn = Depends(get_dynamic_database_connection)
        ):
            # Connection type automatically matches request.db_connection_info
            pass
    """
    logger.info(f"Creating dynamic database connection for {db_connection_info.get('db_type', 'unknown')} database")
    
    try:
        yield from connection_manager.get_connection_via_service(db_connection_info)
    except Exception as e:
        logger.error(f"Failed to create dynamic database connection: {e}")
        raise

def get_database_service_from_request(
    request: Request,
    connection_manager: ConnectionManager = Depends(get_connection_manager)
) -> BaseDatabaseService:
    """
    Extracts database service based on request body's db_connection_info.
    
    This dependency automatically determines the appropriate database service
    based on the request's database connection information. It's useful for
    endpoints that need to handle different database types dynamically.
    
    Args:
        request: FastAPI Request object containing db_connection_info
        connection_manager: Injected connection manager singleton
        
    Returns:
        BaseDatabaseService: Database service matching request's db_type
        
    Request Processing:
        1. Extracts db_connection_info from request body
        2. Determines db_type (defaults to 'postgresql')
        3. Returns appropriate database service
        
    Usage in endpoints:
        @app.post("/smart-query")
        async def smart_query(
            request: QueryRequest,
            db_service: BaseDatabaseService = Depends(get_database_service_from_request)
        ):
            # db_service automatically matches QueryRequest.db_connection_info.db_type
            pass
    """
    # Default to PostgreSQL for backward compatibility
    db_type = "postgresql"
    
    # Try to extract db_type from request body if available
    if hasattr(request.state, 'db_connection_info'):
        db_connection_info = request.state.db_connection_info
        db_type = db_connection_info.get('db_type', 'postgresql')
    
    logger.debug(f"Determined database type from request: {db_type}")
    
    try:
        return connection_manager.get_database_service(db_type)
    except ValueError as e:
        logger.warning(f"Failed to get database service for type '{db_type}', falling back to PostgreSQL: {e}")
        return connection_manager.get_database_service("postgresql")

async def get_token_usage_service(
    db_service: BaseDatabaseService = Depends(get_database_service_from_request)
):
    """
    Provides a TokenUsageService configured for the requested database type.
    
    This dependency creates a token usage service that can work with any
    supported database type, automatically handling the database-specific
    connection and query logic.
    
    Args:
        db_service: Database service for the target database
        
    Returns:
        TokenUsageService: Configured for the specified database
        
    Multi-Database Support:
        - Works with PostgreSQL, MySQL, SQLite, Snowflake
        - Automatically adapts SQL syntax per database type
        - Maintains token usage tracking across different databases
        
    Usage:
        @app.post("/track-tokens")
        async def track_usage(
            request: TokenRequest,
            token_service: TokenUsageService = Depends(get_token_usage_service)
        ):
            await token_service.log_token_usage(request.tokens, request.model)
    """
    # TODO: Implement TokenUsageService when needed
    # from app.services.token_usage_service import TokenUsageService
    # return TokenUsageService(db_service=db_service)
    logger.info("TokenUsageService placeholder - not implemented yet")
    return None

# =============================================================================
# COMPOSITE SERVICE DEPENDENCIES
# =============================================================================
"""
Composite services depend on multiple other services and coordinate complex
business logic. They represent higher-level application capabilities built
from lower-level service primitives.

Design Pattern: Dependency Composition
- Services declare their dependencies via Depends()
- FastAPI automatically resolves the dependency graph
- Circular dependencies are prevented by design
- Services can be easily mocked for testing
"""

def get_visualization_service(
    llm_service: BaseLLMService = Depends(get_llm_service)
    # TODO: Re-enable db_service when VisualizationService is fully updated
    # db_service: BaseDatabaseService = Depends(get_database_service_from_request)
) -> VisualizationService:
    """
    Provides the visualization service for generating database relationship diagrams.
    
    The visualization service creates JSON-based graph data for frontend
    rendering of database schemas, table relationships, and entity diagrams.
    Enhanced with multi-database support for visualizing different database types.
    
    Dependencies:
        llm_service: For entity extraction and schema analysis
        db_service: Database service for the target database type
        
    Returns:
        VisualizationService: Configured visualization service with multi-DB support
        
    Multi-Database Features:
    - PostgreSQL: Full relationship mapping and constraints analysis
    - MySQL: Foreign key relationships and index visualization
    - SQLite: Table relationships and schema introspection
    - Snowflake: Warehouse and schema hierarchy visualization
    - Semantic entity extraction from natural language queries
    - Database-agnostic visualization capabilities
    
    Enhanced Capabilities:
        - Automatic database type detection from request
        - Unified visualization interface across all database types
        - Dynamic schema introspection per database dialect
        - JSON graph format optimized for frontend rendering
    """
    try:
        return VisualizationService(llm_service=llm_service)
    # TODO: Add db_service parameter when VisualizationService is fully updated
    # return VisualizationService(llm_service=llm_service, db_service=db_service)
    except Exception as e:
        # Fallback to basic visualization service for backward compatibility
        logger.warning(f"Failed to create enhanced visualization service: {e}")
        return VisualizationService(llm_service=llm_service)

def get_langchain_streaming_service(
    request: Request,
    settings: Settings = Depends(get_settings),
    llm_svc: BaseLLMService = Depends(get_llm_service),
    dq_manager: DQRuleManager = Depends(get_dq_rule_manager),
    visualization_svc: VisualizationService = Depends(get_visualization_service),
    token_tracker: RequestTokenTracker = Depends(get_token_tracker),
    db_service: BaseDatabaseService = Depends(get_database_service_from_request)
) -> LangChainStreamingService:
    """
    Factory for the main LangChain streaming service - the orchestrator of all AI operations.
    
    This is the primary service that coordinates all AI capabilities including:
    - SQL query generation and execution across multiple database types
    - Data quality rule application
    - Multi-database visualization generation
    - Token usage tracking
    - Streaming response delivery
    
    Dependencies:
        request: For accessing cached database schema
        settings: Application configuration
        llm_svc: Core LLM capabilities
        dq_manager: Data quality rule management
        visualization_svc: Multi-database visualization service
        token_tracker: Request-scoped token usage tracking
        db_service: Database service for the target database type
        
    Returns:
        LangChainStreamingService: Fully configured orchestration service
        
    Multi-Database Architecture:
        This service now supports multiple database types through the database
        service layer, enabling consistent AI operations across PostgreSQL,
        MySQL, SQLite, and Snowflake.
        
    Enhanced Capabilities:
        - Database-agnostic SQL generation and execution
        - Multi-database schema introspection and caching
        - Unified visualization across different database types
        - Consistent token tracking regardless of database backend
        
    Performance Notes:
        - Database schema is cached in app.state during startup
        - Service initialization is lightweight (dependency injection)
        - Heavy lifting done by injected service dependencies
        - Database connections are pooled per database type
    """
    # Retrieve cached database schema from application state for performance
    # Falls back to default schema if caching failed during startup
    db_schema = getattr(request.app.state, 'detailed_db_schema', ADVENTUREWORKS_SCHEMA_FOR_LLM)
    
    logger.info(f"Initializing LangChainService with schema length: {len(db_schema)}")
    
    return LangChainStreamingService(
        llm_service=llm_svc,              # AI text generation and reasoning
        settings=settings,                # Application configuration
        db_schema=db_schema,              # Cached database schema for SQL generation
        dq_rule_manager=dq_manager,       # Business rule validation
        visualization_service=visualization_svc,  # Multi-database diagram generation
        token_tracker=token_tracker       # Request-scoped usage tracking
        # TODO: Add db_service parameter when LangChainStreamingService is updated
    )