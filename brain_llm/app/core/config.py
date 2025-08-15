"""
Brain LLM Configuration Management Module
========================================

This module provides centralized configuration management for the Brain LLM application
using Pydantic Settings for type safety, validation, and environment variable handling.

Key Features:
- Type-safe configuration with automatic validation
- Environment variable support with prefixing
- Database connection string generation
- LLM provider configuration (Google Gemini)
- Logging configuration with multiple output formats
- Data Quality (DQ) service configuration

Environment Variables:
- All configuration can be overridden via environment variables
- Prefix: API2_ (e.g., API2_PG_HOST, API2_GEMINI_API_KEY)
- Supports .env file loading for development

Security Considerations:
- API keys should never be hardcoded
- Use environment variables or secure vaults for sensitive data
- Database passwords should be encrypted in production

Author: Brain LLM Team
"""

from pydantic_settings import BaseSettings
from typing import Optional
import logging

class Settings(BaseSettings):
    """
    Application configuration settings using Pydantic for validation and type safety.
    
    This class centralizes all configuration parameters and provides:
    - Automatic type conversion and validation
    - Environment variable support with the API2_ prefix
    - Default values for development environments
    - Property methods for computed configurations
    
    Configuration Categories:
    1. Database settings (PostgreSQL)
    2. AI/ML model configurations
    3. Data Quality (DQ) settings
    4. Google Gemini LLM settings
    5. Logging and monitoring
    """
    
    # =============================================================================
    # DATABASE CONFIGURATION
    # =============================================================================
    """
    PostgreSQL database connection settings for AdventureWorks sample database.
    
    Security Note: In production, these values should be provided via environment
    variables or secure configuration management systems.
    """
    PG_HOST: str = "localhost"                    # Database server hostname/IP - supports Docker containers
    PG_PORT: int = 5432                          # PostgreSQL default port - standard TCP port
    PG_DATABASE_AW: str = "Adventureworks"       # AdventureWorks database name - Microsoft sample DB
    PG_USER: str = "postgres"                    # Database username - superuser for development
    PG_PASSWORD: str = "aryanyadav@deloitte"     # Database password - MUST be env var in production
    
    # =============================================================================
    # EMBEDDING MODEL CONFIGURATION
    # =============================================================================
    """
    Sentence transformer model for vector embeddings used in:
    - Data Quality rule matching and similarity scoring
    - Semantic search in ChromaDB vector database
    - Document similarity and retrieval ranking
    
    Model Choice: all-MiniLM-L6-v2 provides good balance of speed vs accuracy
    """
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"  # 384-dimensional embeddings, 80MB model

    # =============================================================================
    # DATA QUALITY (DQ) SETTINGS
    # =============================================================================
    """
    Configuration for Data Quality rule management system.
    Uses ChromaDB for vector storage and similarity search of business rules.
    
    Architecture:
    - Rules stored as embeddings for semantic matching
    - CSV file provides rule definitions and metadata
    - Cache file optimizes database schema lookups
    """
    DQ_CHROMA_PATH: str = "chroma_db_dq_rules"        # ChromaDB persistence directory - local storage
    DQ_COLLECTION_NAME: str = "dq_rulebook_collection" # ChromaDB collection name - namespace for rules
    DQ_RULES_FILE: str = "dqrules.csv"                # CSV file containing DQ rules - human-readable format
    DQ_SCHEMA_CACHE_FILE: str = "db_schema.txt"       # Cached database schema file - performance optimization
    DQ_MAX_SUGGESTIONS: int = 3                       # Maximum DQ suggestions per query - UI/UX constraint
    
    # =============================================================================
    # GOOGLE GEMINI LLM CONFIGURATION
    # =============================================================================
    """
    Google Gemini AI configuration for text generation and SQL query processing.
    
    Model Selection Strategy:
    - RAG Model: Gemini-1.5-flash for general Q&A and context understanding
    - SQL Model: Gemini-1.5-flash for SQL generation and database interactions
    
    Performance Characteristics:
    - Flash models: ~2-3 second response time, cost-effective
    - Pro models: Higher accuracy but 5-10 second response time
    
    Safety Settings: Configured for business environments with minimal restrictions
    """
    GEMINI_API_KEY: str                                   # Required: Google AI API key - obtain from Google AI Studio
    GEMINI_RAG_MODEL_NAME: str = "gemini-1.5-flash"      # Fast model for RAG tasks - balanced speed/quality
    GEMINI_SQL_MODEL_NAME: str = "gemini-1.5-flash"      # Fast model for SQL generation - specialized for code
    
    # Safety settings for business use - minimal restrictions for professional content
    GEMINI_SAFETY_SETTINGS: dict = {
        "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",         # Allow business discussions
        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",        # Allow competitive analysis
        "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",  # Allow medical/scientific terms
        "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE"   # Allow security discussions
    }

    # =============================================================================
    # LOGGING AND MONITORING CONFIGURATION
    # =============================================================================
    """
    Comprehensive logging configuration supporting both development and production.
    
    Features:
    - Multi-format logging (JSON for production, text for development)
    - Configurable verbosity levels
    - File rotation and retention policies
    - Structured logging for monitoring systems
    
    Log Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
    """
    LOG_LEVEL: str = "INFO"                    # Logging verbosity level - INFO balances detail/performance  
    LOG_FILE_PATH: str = "logs/app.json"       # JSON log file location - structured for log aggregation
    LOG_FORMAT: str = "json"                   # Log format: "json" (production) or "text" (development)
    LOG_RETENTION_DAYS: int = 30               # Log file retention period - compliance requirement
    
    # =============================================================================
    # COMPUTED PROPERTIES
    # =============================================================================
    
    @property
    def log_level(self) -> int:
        """
        Convert string log level to logging module integer constant.
        
        This property provides type-safe access to Python's logging levels,
        converting user-friendly string values to the integers required by
        the logging module.
        
        Returns:
            int: Logging level constant (e.g., logging.INFO=20, logging.DEBUG=10)
            
        Example:
            settings.log_level returns 20 for "INFO" level
            
        Supported Levels:
            - DEBUG (10): Detailed diagnostic information
            - INFO (20): General operational information  
            - WARNING (30): Warning messages for potential issues
            - ERROR (40): Error conditions that don't stop execution
            - CRITICAL (50): Critical errors that may stop execution
        """
        return getattr(logging, self.LOG_LEVEL.upper())

    @property
    def database_url(self) -> str:
        """
        Generate PostgreSQL connection URL for SQLAlchemy and other database tools.
        
        Constructs a standard PostgreSQL connection string using the configured
        database parameters. This URL is compatible with SQLAlchemy, psycopg2,
        and other PostgreSQL clients.
        
        Returns:
            str: Complete PostgreSQL connection string in standard format
            
        Format:
            postgresql://username:password@host:port/database
            
        Example:
            postgresql://postgres:password@localhost:5432/Adventureworks
            
        Security Note:
            This URL contains credentials and should be handled securely:
            - Never log the complete URL
            - Use environment variables for credentials
            - Consider connection pooling for production
            
        Usage:
            engine = create_engine(settings.database_url)
            conn = psycopg2.connect(settings.database_url)
        """
        return f"postgresql://{self.PG_USER}:{self.PG_PASSWORD}@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DATABASE_AW}"

    # =============================================================================
    # PYDANTIC CONFIGURATION
    # =============================================================================
    
    class Config:
        """
        Pydantic configuration for environment variable handling and validation.
        
        Features:
        - Automatic .env file loading for development
        - Environment variable prefix (API2_) for namespace isolation
        - Extra field handling for forward compatibility
        """
        env_file = ".env"                    # Load from .env file if present
        env_prefix = "API2_"                 # Prefix for environment variables
        extra = "ignore"                     # Ignore unknown environment variables

# =============================================================================
# GLOBAL CONFIGURATION INSTANCE
# =============================================================================
"""
Global settings instance for application-wide configuration access.

This singleton pattern ensures consistent configuration across all modules
and provides a single point of configuration management.

Usage in other modules:
    from app.core.config import settings
    database_url = settings.database_url
    api_key = settings.GEMINI_API_KEY
"""
settings = Settings()
