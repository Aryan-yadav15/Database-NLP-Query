"""
Brain LLM Application Package
============================

This package contains the complete Brain LLM application - an intelligent system
for natural language database querying, data quality management, and AI-powered
data analysis using Large Language Models.

Main Components:
- api/: RESTful API endpoints and request/response schemas
- core/: Configuration management and application settings
- db/: Database connectivity and connection management
- prompts/: LLM prompt templates and engineering
- services/: Business logic, AI services, and data processing

Key Features:
- Natural language to SQL conversion using Google Gemini
- Data Quality rule management with vector similarity search
- Real-time streaming responses via Server-Sent Events
- Database schema visualization and relationship mapping
- Comprehensive token usage tracking for cost monitoring

Architecture:
- FastAPI framework for high-performance async API
- Dependency injection for service management
- Factory pattern for LLM provider abstraction
- Modular design with clear separation of concerns

Author: Brain LLM Team
Version: 1.0.0
"""