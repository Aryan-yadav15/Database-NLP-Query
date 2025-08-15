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
) -> VisualizationService:
    """
    Provides the visualization service for generating database relationship diagrams.
    
    The visualization service creates JSON-based graph data for frontend
    rendering of database schemas, table relationships, and entity diagrams.
    
    Dependencies:
        llm_service: For entity extraction and schema analysis
        
    Returns:
        VisualizationService: Configured visualization service
        
    Features:
    - Database schema introspection and analysis
    - Entity relationship diagram generation
    - JSON graph format for frontend visualization libraries
    - Semantic entity extraction from natural language queries
    
    Design Note:
        This service is effectively singleton since it only depends on
        the LLM service, but we don't use @lru_cache to maintain
        flexibility for future request-specific customizations.
    """
    return VisualizationService(llm_service=llm_service)

def get_langchain_streaming_service(
    request: Request,
    settings: Settings = Depends(get_settings),
    llm_svc: BaseLLMService = Depends(get_llm_service),
    dq_manager: DQRuleManager = Depends(get_dq_rule_manager),
    visualization_svc: VisualizationService = Depends(get_visualization_service),
    token_tracker: RequestTokenTracker = Depends(get_token_tracker)
) -> LangChainStreamingService:
    """
    Factory for the main LangChain streaming service - the orchestrator of all AI operations.
    
    This is the primary service that coordinates all AI capabilities including:
    - SQL query generation and execution
    - Data quality rule application
    - Visualization generation
    - Token usage tracking
    - Streaming response delivery
    
    Dependencies:
        request: For accessing cached database schema
        settings: Application configuration
        llm_svc: Core LLM capabilities
        dq_manager: Data quality rule management
        visualization_svc: Database visualization
        token_tracker: Request-scoped token usage tracking
        
    Returns:
        LangChainStreamingService: Fully configured orchestration service
        
    Architecture:
        This service implements the Orchestrator pattern, coordinating
        multiple specialized services to deliver complex AI-powered
        business capabilities through a unified streaming interface.
        
    Performance Notes:
        - Database schema is cached in app.state during startup
        - Service initialization is lightweight (dependency injection)
        - Heavy lifting done by injected service dependencies
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
        visualization_service=visualization_svc,  # Database diagram generation
        token_tracker=token_tracker       # Request-scoped usage tracking
    )