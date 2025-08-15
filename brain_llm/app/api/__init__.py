"""
Brain LLM API Package
====================

This package contains the RESTful API implementation for the Brain LLM system,
providing HTTP endpoints for natural language query processing, text generation,
and AI-powered database interactions.

API Structure:
- v1/: Version 1 API endpoints and schemas
  - endpoints/: HTTP endpoint implementations
  - schemas/: Request/response data models
  - deps.py: FastAPI dependency injection

API Features:
- Streaming query processing with Server-Sent Events
- Real-time LLM responses for better user experience
- Comprehensive request validation using Pydantic
- Token usage tracking for cost monitoring
- Multi-model LLM support with provider abstraction

Endpoints:
- /api/v1/query/stream: Streaming natural language query processing
- /api/v1/generate/text: Simple text generation for summarization

Author: Brain LLM Team
"""