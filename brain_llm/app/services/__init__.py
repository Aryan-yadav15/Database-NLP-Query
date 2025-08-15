"""
Business Logic Services Package
===============================

This package contains the core business logic and service implementations
for the Brain LLM application, providing AI-powered data processing,
database connectivity, and intelligent query handling capabilities.

Service Categories:

1. **AI & ML Services:**
   - llm/: Large Language Model service abstractions and implementations
   - embedding_service.py: Text-to-vector conversion using SentenceTransformers
   - langchain_service.py: Complex multi-step AI workflows with streaming

2. **Data Services:**
   - chroma_service.py: Vector database operations for similarity search
   - dq_rule_manager.py: Data Quality rule management and validation
   - sql_query_router_logic.py: Natural language to SQL conversion

3. **Infrastructure Services:**
   - connection_manager.py: Database connection pooling and management
   - token_tracker.py: LLM API usage tracking and cost monitoring
   - visualization_service.py: Database schema visualization and graph generation

4. **Utility Services:**
   - result_formatter.py: Optimized SQL result formatting without LLM calls

Design Patterns:
- Dependency injection for loose coupling and testability
- Factory pattern for LLM service abstraction
- Singleton pattern for shared resources (connection pools, models)
- Strategy pattern for different processing approaches

Integration:
- Services are injected via FastAPI dependency system
- Centralized configuration through settings
- Comprehensive logging for monitoring and debugging
- Error handling with graceful degradation

Author: Brain LLM Team
"""