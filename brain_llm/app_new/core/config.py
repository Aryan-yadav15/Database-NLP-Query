"""
Core configuration module for Brain LLM platform
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    APP_NAME: str = "Brain LLM - AI Business Intelligence"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: Optional[str] = None
    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    
    # Redis Cache
    REDIS_URL: Optional[str] = "redis://localhost:6379"
    
    # LLM APIs
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    
    # External Data APIs
    SERPER_API_KEY: Optional[str] = None
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    NEWS_API_KEY: Optional[str] = None
    WEATHER_API_KEY: Optional[str] = None
    
    # File Storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_FILE_TYPES: list = [".csv", ".xlsx", ".xls", ".json", ".parquet"]
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Analytics
    ENABLE_EXTERNAL_DATA: bool = True
    CACHE_INSIGHTS: bool = True
    MAX_DATASET_ROWS: int = 1000000
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
