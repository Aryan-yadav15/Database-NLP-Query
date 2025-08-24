"""
LangChain Service Module - LangGraph Migration Wrapper
=====================================================

MIGRATION NOTICE: This module has been migrated to use the new LangGraph-powered
analytics dashboard service while maintaining backward compatibility for existing
integrations.

This module now serves as a compatibility wrapper that delegates to the advanced
LangGraph implementation while preserving the original LangChain service interface.

Architecture:
- WRAPPER: LangChainStreamingService (this module) - backward compatibility
- CORE: LangGraphAnalyticsService - advanced analytics with state management
- COMPATIBILITY: Maintains original stream_query interface

Migration Strategy:
- Phase 1: Dual implementation (LangGraph + LangChain wrapper) ✓
- Phase 2: Gradual migration of all callers to LangGraph service
- Phase 3: Deprecation of LangChain wrapper (future)

Key Features (Delegated to LangGraph):
1. Multi-step analytics workflows with state persistence
2. Conditional routing based on query intent and data characteristics
3. Advanced chart generation and dashboard assembly
4. Predictive analytics and statistical analysis
5. Real-time streaming with progress updates
6. Intelligent error recovery and retry mechanisms
7. Comprehensive token usage tracking

Analytics Pipeline (LangGraph-powered):
1. Query Intent Analysis → Classify analysis type and complexity
2. Smart SQL Generation → Context-aware SQL with retry logic
3. Data Execution → Robust query execution with connection management
4. Statistical Analysis → Comprehensive data analysis and insights
5. Chart Generation → Optimal visualization selection based on data
6. Dashboard Assembly → Interactive dashboard layout generation

Streaming Events (Enhanced via LangGraph):
- status_update: Detailed progress through analytics pipeline
- sql_generated: Generated SQL with validation status
- structured_response: Complete dashboard with charts and insights
- token_usage: Comprehensive token tracking across all nodes
- error: Enhanced error context and recovery suggestions

Author: Brain LLM Team - LangGraph Migration Wrapper
"""

import logging
import json
import asyncio
from functools import partial
from typing import Dict, List, Optional, Any, AsyncGenerator, Union

# Import the new LangGraph implementation
from .langgraph_analytics_service import LangGraphAnalyticsService, LangChainStreamingService as LangGraphLangChainWrapper

# Legacy imports maintained for compatibility
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import AgentExecutor, create_react_agent
from langchain.agents.agent import AgentOutputParser
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.language_models.chat_models import BaseChatModel

# Application services and utilities
from app.services.llm import get_llm_service as llm_service_factory
from app.services.llm import get_llm_service
from app.services.llm.base import BaseLLMService, TokenUsage
from app.services.token_tracker import RequestTokenTracker
from app.services.dq_rule_manager import DQRuleManager
from app.services.visualization_service import VisualizationService
from app.services.connection_manager import connection_manager
from app.core.config import Settings
from app.db.pg_connector import get_adventureworks_db_session

# SQL processing utilities
from .sql_query_router_logic import (
    generate_sql_via_llm, execute_sql_query_pg, execute_sql_query_unified, format_sql_results_via_llm,
    generate_sql_and_entities_for_dq_rule_sync
)

# Module-level logger for service operations
logger = logging.getLogger(__name__)

def format_sse(event_name: str, data: Dict[str, Any]) -> str:
    """
    Format data as Server-Sent Events (SSE) for real-time streaming to clients.
    
    Converts Python dictionaries to SSE format for browser EventSource API consumption.
    Each event includes a type and JSON-serialized data payload.
    
    Args:
        event_name: Type of event (e.g., 'status_update', 'structured_response')
        data: Dictionary containing the event payload
        
    Returns:
        str: Formatted SSE string with event type and data
        
    Example:
        format_sse("status_update", {"message": "Processing query..."})
        # Returns: "event: status_update\ndata: {\"message\": \"Processing query...\"}\n\n"
    """
    json_data = json.dumps(data, default=str)  # default=str handles non-serializable objects like datetime
    return f"event: {event_name}\ndata: {json_data}\n\n"

class LangChainStreamingService:
    """
    Backward Compatibility Wrapper for LangGraph Analytics Service.
    
    This class provides the same interface as the original LangChain service
    but delegates to the advanced LangGraph implementation internally.
    
    Migration Strategy:
    - Maintains existing stream_query interface for backward compatibility
    - Delegates all processing to the new LangGraph analytics pipeline
    - Preserves token tracking and error handling behavior
    - Provides seamless upgrade path for existing integrations
    
    Key Benefits of Migration:
    - Advanced analytics workflows with state persistence
    - Conditional routing based on query intent
    - Sophisticated chart generation and dashboard assembly
    - Enhanced error recovery and retry mechanisms
    - Better streaming progress updates
    
    Compatibility Notes:
    - All existing callers can use this service without changes
    - Enhanced analytics capabilities are automatically available
    - Token usage tracking is preserved and enhanced
    - Error handling is improved while maintaining error event format
    """
    
    def __init__(self, llm_service: BaseLLMService, settings: Settings, db_schema: str,
                 dq_rule_manager: DQRuleManager, visualization_service: VisualizationService,
                 token_tracker: RequestTokenTracker):
        """
        Initialize the compatibility wrapper with all required dependencies.
        
        Creates the underlying LangGraph analytics service while preserving
        the same initialization interface as the original LangChain service.
        
        Args:
            llm_service: Default LLM service for requests without specific provider
            settings: Application configuration including model names and API keys
            db_schema: Cached database schema string for SQL generation
            dq_rule_manager: Service for data quality rule discovery and validation
            visualization_service: Service for generating database schema visualizations
            token_tracker: Request-scoped token usage tracker (injected via FastAPI)
        """
        # Initialize the new LangGraph service internally
        self.langgraph_service = LangGraphAnalyticsService(
            llm_service=llm_service,
            settings=settings,
            db_schema=db_schema,
            dq_rule_manager=dq_rule_manager,
            visualization_service=visualization_service,
            token_tracker=token_tracker
        )
        
        # Store dependencies for compatibility with legacy code
        self.settings = settings
        self.db_schema = db_schema
        self.token_tracker = token_tracker
        
        # Legacy state tracking (maintained for compatibility)
        self.default_llm_service = llm_service
        self.dq_rule_manager = dq_rule_manager
        self.visualization_service = visualization_service
        
        logger.info("LangChain service initialized as wrapper for LangGraph analytics service")
    
    async def stream_query(self, query: str, model_name: Optional[str] = None,
                          temperature: Optional[float] = 0.0, api_key: Optional[str] = None,
                          chat_history: Optional[List[Dict[str, str]]] = None,
                          short_term_memory: Optional[List[str]] = None,
                          db_connection_info: Optional[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        """
        Main query processing method with backward compatible interface.
        
        This method maintains the exact same interface as the original LangChain
        service but delegates to the advanced LangGraph analytics pipeline.
        
        Migration Benefits:
        - Advanced analytics workflows with state management
        - Sophisticated query intent analysis and routing
        - Enhanced chart generation and dashboard assembly
        - Improved error recovery and retry logic
        - Better statistical analysis and insights
        
        Args:
            query: Natural language query from the user
            model_name: Optional LLM model specification (e.g., "gemini-1.5-flash")
            temperature: Optional temperature for LLM generation (0.0-1.0)
            api_key: Optional API key for per-request LLM service override
            chat_history: Optional conversation context for follow-up questions
            short_term_memory: Optional recent context for query understanding
            db_connection_info: Optional dynamic database connection parameters
            
        Yields:
            str: Server-Sent Events formatted as "event: type\ndata: {json}\n\n"
            
        Event Types Emitted (Enhanced by LangGraph):
            - status_update: Enhanced progress through analytics pipeline
            - sql_generated: Generated SQL with validation and context
            - structured_response: Advanced dashboard with charts and insights
            - token_usage: Comprehensive token tracking across all workflow nodes
            - error: Improved error messages with recovery suggestions
            
        Compatibility Notes:
            - Maintains exact same method signature as original service
            - All existing callers work without modification
            - Enhanced analytics capabilities are automatically available
            - Token tracking behavior is preserved and improved
        """
        try:
            logger.info(f"Processing query via LangGraph analytics pipeline: '{query[:100]}...'")
            
            # Delegate to the advanced LangGraph analytics service
            async for event in self.langgraph_service.stream_analytics_query(
                query=query,
                model_name=model_name,
                temperature=temperature,
                api_key=api_key,
                chat_history=chat_history,
                short_term_memory=short_term_memory,
                db_connection_info=db_connection_info
            ):
                yield event
                
        except Exception as e:
            logger.error(f"Error in LangGraph analytics pipeline: {e}", exc_info=True)
            # Ensure compatibility with existing error handling
            error_event = f"event: error\ndata: {json.dumps({'message': f'Analytics service error: {str(e)}'})}\n\n"
            yield error_event