"""
API Schema Models Package
========================

This package contains Pydantic data models for request and response validation
in the Brain LLM API. These schemas ensure type safety, automatic validation,
and comprehensive API documentation generation.

Schema Files:
- query.py: Models for query processing requests and responses

Schema Features:
- Comprehensive field validation with custom validators
- Optional fields for flexible client integration
- Nested data structures for complex response types
- Automatic OpenAPI schema generation for documentation
- Type-safe serialization and deserialization

Data Models:
- QueryRequest: Natural language query with context and parameters
- QueryResponse: Comprehensive response with text, tables, and visualizations
- TableData: Structured tabular data for frontend rendering
- RetrievedSource: Document source attribution for fact verification

Validation Features:
- Custom field validators for data integrity
- Automatic type conversion and coercion
- Error messages for invalid input data
- JSON schema generation for client validation

Author: Brain LLM Team
"""