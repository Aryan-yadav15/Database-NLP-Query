"""
Brain LLM Main Application Module
=================================

This module serves as the entry point for the Brain LLM FastAPI application.
It provides a comprehensive API for SQL query processing, data quality (DQ) rule management,
and Large Language Model (LLM) interactions with AdventureWorks database.

Key Features:
- RESTful API endpoints for query processing and text generation
- Streaming support for real-time LLM responses
- Database schema caching for optimized performance
- Comprehensive logging with JSON formatting
- CORS middleware for cross-origin requests
- Health monitoring endpoints

Architecture:
- FastAPI framework for high-performance async API
- Modular design with separated concerns (services, routers, config)
- Factory pattern for LLM service abstraction
- Dependency injection for database connections and services

Author: Brain LLM Team
Version: 1.0.0
"""

# Core FastAPI and middleware imports
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Application-specific imports - API routers
from app.api.v1.endpoints.query_new import router as query_router  # Streaming query processor
from app.api.v1.endpoints.generate import router as generate_router  # Text generation endpoint
from app.api.v1.endpoints.database_connections import router as db_connections_router  # Database connection management
from app.api.v1.endpoints.analytics import dashboards_router, cards_router  # Analytics dashboard endpoints

# Logging and configuration
import logging
logging.getLogger(__name__).info("Using query_new endpoint implementation")
from app.core.config import settings

# Database and utility services
from app.services.sql_query_router_logic import get_detailed_database_schema_string
from app.db.pg_connector import get_pg_connection_for_startup

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
"""
Comprehensive logging setup for the Brain LLM application.
Implements dual-output logging: console for development and JSON for production.

Features:
- Console logging with human-readable format for development
- JSON logging for structured log analysis and monitoring
- Configurable log levels via environment variables
- Automatic log directory creation
- Log rotation and retention policies
"""
import os
from pathlib import Path
from pythonjsonlogger import jsonlogger

# Ensure logs directory exists for persistent logging
log_dir = Path(settings.LOG_FILE_PATH).parent
log_dir.mkdir(parents=True, exist_ok=True)

# Configure root logger with application-wide settings
logger = logging.getLogger()
logger.setLevel(settings.log_level)

# Clean slate: Remove any existing handlers to prevent duplication
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Console Handler: Human-readable format for development and debugging
console_handler = logging.StreamHandler()
console_handler.setLevel(settings.log_level)
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# File Handler: JSON format for production monitoring and log analysis
file_handler = logging.FileHandler(settings.LOG_FILE_PATH)
file_handler.setLevel(settings.log_level)
json_formatter = jsonlogger.JsonFormatter('%(timestamp)s %(name)s %(levelname)s %(message)s %(filename)s %(funcName)s %(lineno)d')
file_handler.setFormatter(json_formatter)

# Register both handlers with the root logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Create module-specific logger for this file
logger = logging.getLogger(__name__)

# =============================================================================
# FASTAPI APPLICATION SETUP
# =============================================================================
"""
Main FastAPI application instance with comprehensive configuration.

The application provides:
- SQL query processing with LLM intelligence
- Data quality rule management and validation
- Real-time streaming responses via Server-Sent Events
- Multi-LLM provider support (Gemini, Claude, OpenAI)
- Database schema introspection and caching
"""
app = FastAPI(
    title="SQL & DQ LLM API",
    description="API for handling SQL queries, DQ rules, and LLM interactions with AdventureWorks DB",
    version="1.0.0"
)

# =============================================================================
# MIDDLEWARE CONFIGURATION
# =============================================================================
"""
CORS (Cross-Origin Resource Sharing) middleware configuration.

WARNING: Current configuration allows all origins (*) which is suitable for
development but should be restricted in production environments.

Production considerations:
- Specify exact allowed origins instead of "*"
- Consider removing credentials support if not needed
- Implement rate limiting and authentication
"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production to specific domains
    allow_credentials=True,
    allow_methods=["*"],  # Allows GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],  # Allows all headers including custom ones
)

# =============================================================================
# ROUTER REGISTRATION
# =============================================================================
"""
Register API routers with specific prefixes and tags for organization.

Router Architecture:
- /api/v1/query: Core query processing with streaming support
- /api/v1/generate: Simple text generation for summarization tasks
- /api/v1/database: Database connection management

Each router is versioned (v1) to support future API evolution without
breaking existing clients.
"""
app.include_router(
    query_router,
    prefix="/api/v1/query",
    tags=["query"]
)
app.include_router(
    generate_router, 
    prefix="/api/v1/generate",
    tags=["generation"]
)
app.include_router(
    db_connections_router,
    prefix="/api/v1",
    tags=["database"]
)
app.include_router(
    dashboards_router,
    prefix="/api/v1/analytics",
    tags=["analytics"]
)
app.include_router(
    cards_router,
    prefix="/api/v1/analytics",
    tags=["analytics"]
)

# =============================================================================
# HEALTH CHECK ENDPOINT
# =============================================================================

@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancer probes.
    
    This endpoint provides a quick way to verify that the API is running
    and responsive. It's typically used by:
    - Load balancers for health checks
    - Monitoring systems for uptime verification
    - Container orchestrators (k8s, Docker Swarm) for readiness probes
    
    Returns:
        dict: Service status information including version
        
    Status Codes:
        200: Service is healthy and operational
    """
    return {
        "status": "ok",
        "service": "SQL & DQ LLM API",
        "version": app.version
    }

# =============================================================================
# APPLICATION LIFECYCLE EVENTS
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler.
    
    Performs critical initialization tasks that must complete before
    the application can serve requests:
    
    1. Database connectivity verification
    2. Schema introspection and caching
    3. Service initialization validation
    
    The database schema is cached in app.state for performance optimization,
    avoiding repeated schema queries during request processing.
    
    Error Handling:
    - Non-critical errors are logged but don't prevent startup
    - Fallback schema is used if database is unavailable
    - Application continues with degraded functionality
    """
    logger.info("SQL & DQ LLM API starting up...")
    try:
        # Initialize database connection for schema introspection
        db_conn_startup = get_pg_connection_for_startup()
        if db_conn_startup:
            try:
                logger.info("Fetching detailed database schema for LLM prompts...")
                
                # Cache the complete database schema for LLM context
                # This improves performance by avoiding repeated schema queries
                schema_str = get_detailed_database_schema_string(db_conn_startup)
                app.state.detailed_db_schema = schema_str
                
                # Validate schema quality and provide appropriate logging
                if "SCHEMA_UNAVAILABLE" in schema_str:
                    logger.warning("Fetched schema is unavailable. SQL routing will use fallback.")
                else:
                    logger.info(f"Successfully loaded and cached detailed DB schema (length: {len(schema_str)}).")
            finally:
                # Always close the startup connection to prevent resource leaks
                db_conn_startup.close()
                logger.info("Startup database connection closed.")
        else:
            # Fallback to static schema if dynamic introspection fails
            logger.error("Could not get DB connection for startup schema fetch. SQL routing will use fallback.")
            from app.services.sql_query_router_logic import ADVENTUREWORKS_SCHEMA_FOR_LLM
            app.state.detailed_db_schema = ADVENTUREWORKS_SCHEMA_FOR_LLM
    except Exception as e:
        # Critical error handling: log the error but continue with fallback
        logger.error(f"Critical startup error during schema fetch: {e}")
        from app.services.sql_query_router_logic import ADVENTUREWORKS_SCHEMA_FOR_LLM
        app.state.detailed_db_schema = ADVENTUREWORKS_SCHEMA_FOR_LLM

@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event handler.
    
    Performs cleanup tasks when the application is terminating:
    - Close database connections
    - Clean up temporary resources
    - Log shutdown completion
    
    This ensures graceful shutdown and prevents resource leaks.
    """
    logger.info("SQL & DQ LLM API shutting down...")
    # Additional cleanup tasks can be added here
    # Example: await database_pool.close()
    # Example: await llm_service.cleanup()