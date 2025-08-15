"""
Brain LLM API Version 1 Package
==============================

This package contains Version 1 of the Brain LLM REST API, implementing
comprehensive natural language database querying and AI text generation
capabilities with modern FastAPI patterns.

Components:
- endpoints/: HTTP endpoint implementations with streaming support
- schemas/: Pydantic models for request/response validation
- deps.py: Dependency injection for service management

Version 1 Features:
- Streaming query processing with real-time updates
- Comprehensive error handling and validation
- Token usage tracking and cost monitoring
- Multi-provider LLM support (Google Gemini, extensible)
- Database schema visualization and relationship mapping

API Design:
- RESTful principles with proper HTTP status codes
- JSON request/response format with Pydantic validation
- Server-Sent Events for streaming capabilities
- OpenAPI 3.0 compatible with automatic documentation

Future Versions:
- Version 2 may include GraphQL support
- Enhanced authentication and authorization
- Advanced analytics and monitoring endpoints

Author: Brain LLM Team
"""