"""
API Endpoints Package
====================

This package contains the HTTP endpoint implementations for the Brain LLM API,
providing RESTful interfaces for natural language processing, query execution,
and AI-powered database interactions.

Endpoints:
- generate.py: Simple text generation for summarization and content creation
- query_new.py: Advanced streaming query processing with multi-step workflows

Endpoint Features:
- FastAPI async/await patterns for high performance
- Pydantic request/response validation for type safety
- Comprehensive error handling with appropriate HTTP status codes
- Dependency injection for service management and testing
- OpenAPI documentation generation for client integration

Design Patterns:
- RESTful API design with proper HTTP methods and status codes
- Streaming responses via Server-Sent Events for real-time updates
- Dependency injection for loose coupling and testability
- Comprehensive logging for monitoring and debugging

Author: Brain LLM Team
"""