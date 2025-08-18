"""
LangChain-Powered Streaming Agent Service Module
===============================================

This module provides the core AI agent functionality for the Brain LLM system,
implementing a sophisticated ReAct (Reasoning + Acting) pattern using LangChain
to handle complex multi-step workflows with real-time streaming capabilities.

Key Features:
1. Multi-tool agent with SQL generation, DQ validation, and visualization
2. Real-time streaming of agent thoughts and actions via Server-Sent Events
3. Token usage tracking across all LLM interactions
4. Conversational memory and context management
5. Dynamic LLM service integration with multiple providers

Agent Architecture:
- ReAct Pattern: Combines reasoning and action-taking in iterative loops
- Tool System: Modular tools for SQL, DQ rules, visualization, and conversation
- Streaming: Real-time user feedback during multi-step processing
- Memory: Short-term and chat history for contextual conversations

Tools Available:
1. sql_workflow: Natural language to SQL conversion and execution
2. query_dq_rules: Data quality rule discovery and validation
3. generate_visualization: Entity relationship diagram generation
4. conversational_response: Direct conversational interactions

Streaming Events:
- status_update: Progress notifications during processing
- structured_response: Final results with SQL, tables, and visualizations
- token_usage: Accumulated token consumption across all LLM calls

Author: Brain LLM Team
"""

import logging
import json
import asyncio
from functools import partial
from typing import Dict, List, Optional, Any, AsyncGenerator, Union

# LangChain core components for agent implementation
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

# Module-level logger for agent operations
logger = logging.getLogger(__name__)

def format_sse(event_name: str, data: Dict[str, Any]) -> str:
    """
    Format data as Server-Sent Events (SSE) for real-time streaming to clients.
    
    Converts Python dictionaries to SSE format for browser EventSource API consumption.
    Each event includes a type and JSON-serialized data payload.
    
    SSE Format Specification:
    - Each event starts with "event: <event_name>"
    - Data follows as "data: <json_payload>"
    - Events are terminated with double newlines "\n\n"
    - Multiple data lines are supported for large payloads
    
    Args:
        event_name: Type of event (e.g., 'status_update', 'structured_response')
        data: Dictionary containing the event payload
        
    Returns:
        str: Formatted SSE string with event type and data
        
    Example:
        format_sse("status_update", {"message": "Processing query..."})
        # Returns: "event: status_update\ndata: {\"message\": \"Processing query...\"}\n\n"
        
    Browser Consumption:
        const eventSource = new EventSource('/api/v1/query/stream');
        eventSource.addEventListener('status_update', (event) => {
            const data = JSON.parse(event.data);
            console.log(data.message);
        });
    """
    json_data = json.dumps(data, default=str)  # default=str handles non-serializable objects like datetime
    return f"event: {event_name}\ndata: {json_data}\n\n"

class AsyncStreamingCallbackHandler(AsyncCallbackHandler):
    """
    Custom LangChain callback handler for real-time streaming of agent operations.
    
    This handler intercepts key events during agent execution and converts them
    into Server-Sent Events for real-time user feedback. It provides visibility
    into the agent's decision-making process and tool usage.
    
    Key Events Handled:
    - Chain start: When the AgentExecutor begins processing
    - Agent actions: When the agent decides to use a specific tool
    - Tool execution: During tool invocation (optional)
    
    Threading Considerations:
    - Uses asyncio.Queue for thread-safe communication
    - All callbacks are async to prevent blocking the agent
    - Queue acts as a bridge between agent and streaming response
    """
    
    def __init__(self, queue: asyncio.Queue):
        """
        Initialize the callback handler with a communication queue.
        
        Args:
            queue: Asyncio queue for sending events to the streaming response
        """
        self.queue = queue
        
    async def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any):
        """
        Called when a LangChain chain (like AgentExecutor) starts execution.
        
        Args:
            serialized: Metadata about the chain being started
            inputs: Input parameters passed to the chain
            **kwargs: Additional callback parameters
        """
        # Only send status for the main AgentExecutor, not sub-chains
        if serialized and serialized.get("name") == "AgentExecutor":
            await self.queue.put(format_sse("status_update", {"message": "Analyzing query..."}))
            
    async def on_agent_action(self, action: AgentAction, **kwargs: Any):
        """
        Called when the agent decides to take an action (use a tool).
        
        This provides real-time feedback about which tool the agent has chosen,
        helping users understand the reasoning process.
        
        Args:
            action: LangChain AgentAction object containing tool and input
            **kwargs: Additional callback parameters
        """
        # Provide user-friendly tool names for better UX
        tool_display_names = {
            "get_database_answer": "SQL database tool",
            "get_data_quality_info": "data quality analysis tool",
            "visualize_database_schema": "visualization tool", 
            "answer_from_history": "conversation tool"
        }
        
        display_name = tool_display_names.get(action.tool, action.tool)
        await self.queue.put(format_sse("status_update", {"message": f"Using the {display_name}..."}))
        
    # Additional callback methods can be added here:
    # - on_tool_start: When a tool begins execution
    # - on_tool_end: When a tool completes execution
    # - on_llm_start: When an LLM call begins
    # - on_llm_end: When an LLM call completes

class StopAfterToolOutputParser(AgentOutputParser):
    """
    Custom LangChain output parser for single-tool execution strategy.
    
    This parser implements a "one-shot" agent pattern where the agent selects
    one tool, executes it, and immediately returns the result without further
    reasoning loops. This prevents infinite loops and ensures predictable
    response times.
    
    Parsing Strategy:
    1. Extract "Thought:", "Action:", and "Action Input:" from LLM output
    2. If valid action found, return AgentAction for tool execution
    3. If "Final Answer:" found, return AgentFinish to end the process
    4. If parsing fails, gracefully return an error response
    
    Output Format Expected from LLM:
        Thought: I need to query the database for sales data
        Action: get_database_answer  
        Action Input: Show me total sales by region
    
    Benefits:
    - Prevents agent from getting stuck in reasoning loops
    - Ensures fast, predictable response times
    - Simplifies debugging and error handling
    - Reduces token consumption
    """
    
    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        """
        Parse LLM output text into either an action to take or a final answer.
        
        Args:
            text: Raw text output from the LLM
            
        Returns:
            Union[AgentAction, AgentFinish]: Either an action to execute or final response
            
        Parsing Algorithm:
        1. Split text into lines and scan for key markers
        2. Extract thought process (optional, for debugging)
        3. Extract action (tool name) - required
        4. Extract action input (tool parameters) - required
        5. Handle special case of "Final Answer:" for direct responses
        """
        # Initialize parsing variables
        thought = None
        action = None
        action_input = None
        
        # Scan through each line looking for key markers
        for line in text.strip().split('\n'):
            line = line.strip()
            if line.startswith("Thought:"):
                thought = line[len("Thought:"):].strip()
            elif line.startswith("Action:"):
                action = line[len("Action:"):].strip()
            elif line.startswith("Action Input:"):
                # Use partition to handle multi-line inputs correctly
                # This captures everything after "Action Input:" even if it spans multiple lines
                action_input = text.partition("Action Input:")[2].strip()
                break  # Stop after finding Action Input, as it's the last part we need

        # Case 1: Valid action and input found - execute the tool
        if action and action_input:
            return AgentAction(tool=action, tool_input=action_input, log=text)
            
        # Case 2: Final answer provided - return directly to user
        if "Final Answer:" in text:
            return AgentFinish(return_values={"output": text}, log=text)
            
        # Case 3: Parsing failed - log warning and return graceful error
        logger.warning(f"Could not parse LLM output into a valid action, text: {text}")
        return AgentFinish(
            return_values={"output": "Could not parse LLM output into a valid action/response."},
            log=text
        )

    @property
    def _type(self) -> str:
        """Return parser type identifier for LangChain framework."""
        return "stop-after-tool-output-parser"

class LangChainStreamingService:
    """
    Core service orchestrating multi-tool AI agent with real-time streaming capabilities.
    
    This service implements a sophisticated ReAct (Reasoning + Acting) pattern using LangChain
    to handle complex multi-step workflows. It provides a unified interface for SQL generation,
    data quality validation, schema visualization, and conversational interactions.
    
    Architecture Components:
    1. Dynamic LLM Service Selection: Support for multiple LLM providers per request
    2. Token Usage Tracking: Comprehensive monitoring across all LLM interactions  
    3. Real-time Streaming: Server-Sent Events for live progress updates
    4. Tool Orchestration: Modular tools for different data operations
    5. Connection Management: Dynamic database connections with schema caching
    
    Service State Management:
    - default_llm_service: Fallback service when no specific provider requested
    - current_request_llm_service: Per-request LLM service with custom API keys
    - current_db_connection_info: Dynamic database connection parameters
    - token_tracker: Request-scoped token usage accumulator
    
    Threading Model:
    - Async/await throughout for non-blocking operations
    - asyncio.Queue for real-time event streaming
    - Thread-safe database connection management
    """
    
    def __init__(self, llm_service: BaseLLMService, settings: Settings, db_schema: str, 
                 dq_rule_manager: DQRuleManager, visualization_service: VisualizationService, 
                 token_tracker: RequestTokenTracker):
        """
        Initialize the LangChain streaming service with all required dependencies.
        
        Args:
            llm_service: Default LLM service for requests without specific provider
            settings: Application configuration including model names and API keys
            db_schema: Cached database schema string for SQL generation
            dq_rule_manager: Service for data quality rule discovery and validation
            visualization_service: Service for generating database schema visualizations
            token_tracker: Request-scoped token usage tracker (injected via FastAPI)
        """
        # Core service dependencies - injected via FastAPI dependency system
        self.default_llm_service = llm_service          # Fallback LLM service
        self.settings = settings                        # App configuration
        self.db_schema = db_schema                      # Cached DB schema
        self.dq_rule_manager = dq_rule_manager         # DQ rules service
        self.visualization_service = visualization_service  # Visualization service
        self.token_tracker = token_tracker              # Request-scoped token tracker
        
        # Per-request state variables - reset for each new query
        self.langchain_llm: Optional[BaseChatModel] = None              # LangChain model instance
        self.last_formatted_history: str = ""                          # Formatted chat history
        self.current_request_llm_service: Optional[BaseLLMService] = None  # Per-request LLM service
        self.current_db_connection_info: Optional[Dict[str, Any]] = None   # Dynamic DB connection
        
        # Model configuration for current request - enables consistent model usage across tools
        self.current_model_name: Optional[str] = None                   # User-provided model name
        self.current_temperature: Optional[float] = None                # User-provided temperature
    
    def _accumulate_token_usage(self, usage: TokenUsage):
        """
        Accumulate token usage via the injected request-scoped token tracker.
        
        This method provides a consistent interface for all tools to report
        their token consumption. The token tracker automatically handles
        aggregation and provides final totals at the end of the request.
        
        Args:
            usage: TokenUsage object containing prompt, response, and total tokens
            
        Thread Safety:
            The token tracker is request-scoped and therefore thread-safe
            within the context of a single user request.
        """
        if usage:
            self.token_tracker.add_usage(usage)
            logger.debug(f"Added token usage: {usage.total_token_count} tokens")  # Debug logging

    # =============================================================================
    # AGENT TOOL IMPLEMENTATIONS
    # =============================================================================
    # Each tool implements a specific capability of the Brain LLM system.
    # Tools are designed to be modular, async, and provide real-time feedback.
    
    async def _answer_from_history_tool(self, queue: asyncio.Queue, query: str) -> str:
        """
        Conversational tool for handling general questions and chat history inquiries.
        
        This tool serves as the "default" option when no specialized tool is needed.
        It leverages chat history to provide contextual responses for:
        - General conversation ("Hello", "Thank you", "How are you?")
        - Questions about previous interactions ("What did you just tell me?")
        - Follow-up clarifications ("Can you explain that again?")
        
        Processing Flow:
        1. Notify user that we're processing based on conversation history
        2. Construct prompt with full chat history context
        3. Stream LLM response with token tracking
        4. Format and send structured response event
        
        Args:
            queue: Asyncio queue for sending real-time progress updates
            query: User's conversational question or follow-up
            
        Returns:
            str: Success/failure message for the agent (not shown to user)
            
        Token Efficiency:
            Uses temperature=0.2 for more focused, less creative responses
            suitable for factual conversation and clarification requests.
        """
        try:
            # Send real-time progress update to user
            await queue.put(format_sse("status_update", {"message": "Thinking based on our conversation..."}))
            
            # Construct conversational prompt with full context
            conversational_prompt = f"""You are a helpful assistant.
Based on the following conversation history, provide a direct and helpful answer to the user's latest question.
Do not try to access any external tools.

<chat_history>
{self.last_formatted_history}
</chat_history>

User's Question: "{query}"

Your Answer:
"""
            # Use streaming with usage tracking for token monitoring
            response_generator = self.current_request_llm_service.generate_text_streamed_with_usage(
                prompt=conversational_prompt,
                model_name=self.current_model_name or self.settings.GEMINI_RAG_MODEL_NAME,  # Use request model or fallback
                temperature=self.current_temperature if self.current_temperature is not None else 0.2  # Use request temp or fallback
            )
            
            # Collect streaming response chunks and track token usage
            answer_parts = []
            for chunk, usage in response_generator:
                if chunk:
                    answer_parts.append(chunk)
                if usage:
                    self._accumulate_token_usage(usage)  # Track tokens for final report
            
            answer_text = "".join(answer_parts)

            # Send structured response to client
            response_payload = {
                "answer_text": answer_text,
                "strategy_used": "CONVERSATIONAL"  # Indicates which tool was used
            }
            await queue.put(format_sse("structured_response", response_payload))
            return "Successfully provided a direct answer based on conversation history."

        except Exception as e:
            logger.error(f"Error in conversational tool: {e}", exc_info=True)
            await queue.put(format_sse("error", {"message": f"Error answering from history: {str(e)}"}))
            return f"Error: An error occurred while answering from history: {e}"
            
    async def _sql_workflow_tool(self, queue: asyncio.Queue, query: str) -> str:
        """
        Comprehensive SQL workflow tool for natural language to database query processing.
        
        This is the most complex tool, handling the complete SQL workflow from
        natural language understanding to query execution and result formatting.
        
        Workflow Stages:
        1. Schema Selection: Choose between cached, dynamic, or provided schema
        2. SQL Generation: Convert natural language to valid PostgreSQL
        3. Query Execution: Run SQL against the appropriate database
        4. Result Formatting: Convert tabular data to human-readable response
        5. Response Packaging: Structure data for frontend consumption
        
        Dynamic Connection Support:
        - Supports both default AdventureWorks and custom database connections
        - Handles schema provision vs. dynamic schema fetching
        - Ensures proper connection cleanup to prevent resource leaks
        
        Error Handling & Resilience:
        - Retry logic for SQL generation (up to 3 attempts)
        - Graceful degradation for connection failures
        - Comprehensive error logging with context
        
        Args:
            queue: Asyncio queue for real-time progress updates
            query: Natural language query from user
            
        Returns:
            str: Success/failure message for the agent
            
        Performance Optimizations:
        - Schema caching reduces database round-trips
        - Streaming LLM responses for faster user feedback
        - Connection pooling for database efficiency
        """
        try:
            await queue.put(format_sse("status_update", {"message": "Generating SQL..."}))
            
            # =================================================================
            # STAGE 1: DATABASE CONNECTION AND SCHEMA SELECTION
            # =================================================================
            pg_conn = None
            schema_to_use = self.db_schema  # Default to cached schema for performance
            
            if self.current_db_connection_info:
                # Dynamic database connection requested
                provided_schema = self.current_db_connection_info.get('db_schema')
                
                if provided_schema and provided_schema.strip():
                    # Case A: Pre-provided schema in request payload
                    logger.info("Using pre-provided schema from request payload")
                    schema_to_use = provided_schema
                    # Still need connection for query execution
                    pg_conn = connection_manager.get_raw_psycopg2_connection(self.current_db_connection_info)
                else:
                    # Case B: Dynamic connection, fetch schema from actual database
                    logger.info("Using dynamic database connection and fetching schema from database")
                    pg_conn = connection_manager.get_raw_psycopg2_connection(self.current_db_connection_info)
                    # Get fresh schema from the actual database - expensive but accurate
                    from .sql_query_router_logic import get_detailed_database_schema_string
                    schema_to_use = await asyncio.to_thread(get_detailed_database_schema_string, pg_conn)
                    logger.info(f"Dynamically fetched schema length: {len(schema_to_use)} characters")
            else:
                # Case C: Default AdventureWorks connection with cached schema
                logger.info("Using default database connection and cached schema")
                pg_conn_gen = get_adventureworks_db_session()
                pg_conn = next(pg_conn_gen)
            
            # =================================================================
            # STAGE 2: SQL GENERATION WITH RETRY LOGIC
            # =================================================================
            max_retries = 3  # Balance between reliability and response time
            sql_query = None
            
            for attempt in range(max_retries):
                try:
                    # Use streaming method with token usage tracking
                    sql_generator = self.current_request_llm_service.generate_text_streamed_with_usage(
                        prompt=f"""Given the following schema and user query, generate an appropriate SQL query.

Schema:
{schema_to_use}

User Query: {query}

Generate ONLY the SQL query without any explanation or markdown formatting. The query should be valid PostgreSQL.""",
                        model_name=self.current_model_name or self.settings.GEMINI_SQL_MODEL_NAME,  # Use request model or SQL-specialized fallback
                        temperature=self.current_temperature if self.current_temperature is not None else 0.1  # Use request temp or low fallback
                    )
                    
                    # Collect streaming chunks and track tokens
                    sql_parts = []
                    for chunk, usage in sql_generator:
                        if chunk:
                            sql_parts.append(chunk)
                        if usage:
                            self._accumulate_token_usage(usage)
                    
                    sql_text = "".join(sql_parts).strip()
                    # Parse and validate the generated SQL
                    sql_query = self.current_request_llm_service.parse_sql_from_text(sql_text)
                    
                    # Validate that we got a proper SELECT statement
                    if sql_query and sql_query.strip().upper().startswith('SELECT'):
                        break  # Success - exit retry loop
                        
                except Exception as e:
                    logger.warning(f"SQL generation attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:  # Don't sleep on final attempt
                        await asyncio.sleep(1)  # Brief delay before retry
            
            # Check if SQL generation ultimately failed
            if not sql_query: 
                raise ValueError(f"Failed to generate valid SQL after {max_retries} attempts.")
                
            # Notify user of successful SQL generation
            await queue.put(format_sse("sql_generated", {"sql": sql_query}))
            await queue.put(format_sse("status_update", {"message": "Executing query..."}))
            
            # =================================================================
            # STAGE 3: QUERY EXECUTION WITH CONNECTION MANAGEMENT
            # =================================================================
            try:
                # NEW: Use unified database query execution that supports multiple database types
                if self.current_db_connection_info:
                    # Dynamic connection - use the unified method with connection info
                    results_df, error_msg = await asyncio.to_thread(
                        execute_sql_query_unified, 
                        self.current_db_connection_info, 
                        sql_query
                    )
                    logger.info("Executed query using unified database service with dynamic connection")
                else:
                    # Default connection - fallback to legacy method for backward compatibility
                    results_df, error_msg = await asyncio.to_thread(execute_sql_query_pg, pg_conn, sql_query)
                    logger.info("Executed query using legacy PostgreSQL method with default connection")
                
                if error_msg: 
                    raise ConnectionError(f"DB error: {error_msg}")
            finally:
                # Ensure proper connection cleanup to prevent resource leaks
                if self.current_db_connection_info:
                    # Dynamic connection - close it manually (only if using legacy method)
                    if pg_conn and 'pg_conn' in locals():
                        pg_conn.close()
                        logger.info("Dynamic database connection closed")
                else:
                    # Default connection - use generator cleanup
                    try: 
                        next(pg_conn_gen)  # Trigger generator cleanup
                    except StopIteration: 
                        pass  # Expected - generator exhausted
            
            # =================================================================
            # STAGE 4: RESULT FORMATTING WITH LLM
            # =================================================================
            await queue.put(format_sse("status_update", {"message": "Interpreting results..."}))
            
            # Format results using token tracking
            format_generator = self.current_request_llm_service.generate_text_streamed_with_usage(
                prompt=f"""Format the following SQL query results into a clear, human-readable answer.

SQL Query: {sql_query}
User's Original Question: {query}
Results: {results_df.to_string(index=False) if not results_df.empty else 'No results found'}

Provide a concise and informative summary of what the data shows in response to the user's question.""",
                model_name=self.current_model_name or self.settings.GEMINI_RAG_MODEL_NAME,  # Use request model or fallback
                temperature=self.current_temperature if self.current_temperature is not None else 0.1  # Use request temp or low fallback
            )
            
            # Collect formatted response and track tokens
            format_parts = []
            for chunk, usage in format_generator:
                if chunk:
                    format_parts.append(chunk)
                if usage:
                    self._accumulate_token_usage(usage)
            
            # =================================================================
            # STAGE 5: RESPONSE PACKAGING FOR FRONTEND
            # =================================================================
            answer_text = "".join(format_parts)
            
            # Convert DataFrame to JSON-serializable format
            table_data = {
                "columns": list(results_df.columns), 
                "rows": results_df.values.tolist()
            }
            
            # Package complete response with all components
            response_payload = {
                "answer_text": answer_text,     # Human-readable summary
                "table": table_data,           # Structured data for display
                "sql": sql_query,              # Generated SQL for transparency
                "strategy_used": "SQL"         # Tool identifier
            }
            await queue.put(format_sse("structured_response", response_payload))
            return "Successfully provided a structured response for the SQL query."
            
        except Exception as e:
            logger.error(f"Error in SQL tool: {e}", exc_info=True)
            await queue.put(format_sse("error", {"message": f"Error in SQL tool: {str(e)}"}))
            return f"Error: An error occurred in the SQL workflow: {e}"

    async def _dq_workflow_tool(self, queue: asyncio.Queue, query: str) -> str:
        try:
            await queue.put(format_sse("status_update", {"message": "Searching for relevant data quality rules..."}))
            rules = await asyncio.to_thread(self.dq_rule_manager.find_relevant_rules_sync, query)
            if not rules: raise ValueError("No relevant DQ rules found.")
            await queue.put(format_sse("status_update", {"message": f"Found {len(rules)} rule(s). Generating validation queries..."}))
            rules_with_sql = []
            for rule in rules:
                rule_desc = rule.get("Description")
                if rule_desc:
                    llm_data = await asyncio.to_thread(generate_sql_and_entities_for_dq_rule_sync, rule_desc, self.current_request_llm_service, self.db_schema, 1, self.token_tracker, self.current_model_name)
                    rule['sql_query'] = llm_data.get("sql_query") if llm_data else "N/A"
                rules_with_sql.append(rule)
            await queue.put(format_sse("status_update", {"message": "Formatting DQ rules for display..."}))
            table_data = {"title": "Data Quality Rules", "columns": ["Rule ID", "Description", "Status", "SQL Code"], "rows": [[r.get('Rule_ID'), r.get('Description'), r.get('status'), r.get('sql_query')] for r in rules_with_sql]}
            answer_text = f"I found {len(rules_with_sql)} relevant data quality rule(s)."
            response_payload = {"answer_text": answer_text, "table": table_data, "dqRules": rules_with_sql, "strategy_used": "DQ_RULE"}
            await queue.put(format_sse("structured_response", response_payload))
            return "Successfully provided a structured response for the DQ query."
        except Exception as e:
            logger.error(f"Error in DQ tool: {e}", exc_info=True)
            await queue.put(format_sse("error", {"message": f"Error in DQ tool: {str(e)}"}))
            return f"Error: An error occurred in the DQ workflow: {e}"

    async def _visualize_schema_tool(self, queue: asyncio.Queue, query: str) -> str:
        try:
            await queue.put(format_sse("status_update", {"message": "Analyzing schema for visualization..."}))
            
            # Get dynamic connection and LLM service if available
            dynamic_llm_service = self.current_request_llm_service
            dynamic_db_connection = None
            provided_schema = None
            
            if self.current_db_connection_info:
                logger.info("Using dynamic database connection for visualization")
                # Check if schema is pre-provided
                provided_schema = self.current_db_connection_info.get('db_schema')
                if provided_schema and provided_schema.strip():
                    logger.info("Using pre-provided schema for visualization (no DB fetch needed)")
                else:
                    logger.info("No pre-provided schema, will fetch from database")
                dynamic_db_connection = connection_manager.get_raw_psycopg2_connection(self.current_db_connection_info)
            
            try:
                visualization_result = await self.visualization_service.generate_visualization_json(
                    query, 
                    dynamic_llm_service=dynamic_llm_service,
                    dynamic_db_connection=dynamic_db_connection,
                    provided_schema=provided_schema,
                    token_tracker=self.token_tracker,
                    model_name=self.current_model_name
                )
                if not visualization_result: raise ValueError("Failed to generate visualization data.")
                visualization_data = visualization_result.get("visualization_data", {})
                answer_text = visualization_result.get("answer_text", "Here's a visualization of the database schema you requested.")
                response_payload = {"answer_text": answer_text, "graph": visualization_data, "strategy_used": "VISUALIZE"}
                await queue.put(format_sse("structured_response", response_payload))
                return "Successfully provided a structured response for the visualization query."
            finally:
                # Close dynamic connection if it was opened
                if dynamic_db_connection:
                    dynamic_db_connection.close()
                    logger.info("Dynamic database connection closed for visualization")
        except Exception as e:
            logger.error(f"Error in visualization tool: {e}", exc_info=True)
            await queue.put(format_sse("error", {"message": f"Error in visualization tool: {str(e)}"}))
            return f"Error: An error occurred during schema visualization: {e}"

    async def stream_query(self, query: str, model_name: Optional[str] = None, 
                          temperature: Optional[float] = 0.0, api_key: Optional[str] = None, 
                          chat_history: Optional[List[Dict[str, str]]] = None, 
                          short_term_memory: Optional[List[str]] = None, 
                          db_connection_info: Optional[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        """
        Main orchestration method for streaming AI agent query processing.
        
        This is the core method that handles the complete lifecycle of a user query,
        from initial processing through tool selection and execution to final response
        streaming. It implements a sophisticated agent architecture with real-time
        feedback and comprehensive error handling.
        
        Processing Pipeline:
        1. LLM Service Selection: Choose appropriate provider and model
        2. Agent Initialization: Setup tools, prompts, and execution context
        3. Query Contextualization: Process chat history and memory
        4. Tool Selection: Agent chooses best tool via ReAct reasoning
        5. Tool Execution: Run selected tool with real-time progress
        6. Response Streaming: Stream results and token usage to client
        
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
            
        Event Types Emitted:
            - status_update: Progress notifications during processing
            - sql_generated: Generated SQL queries (for transparency)
            - structured_response: Final results with data and metadata
            - token_usage: Token consumption summary (final event)
            - error: Error messages with context
            
        Error Handling Strategy:
            - Graceful degradation for LLM service failures
            - Comprehensive logging with request context
            - User-friendly error messages
            - Resource cleanup in all failure scenarios
            
        Performance Considerations:
            - Async/await throughout for non-blocking operations
            - Request-scoped token tracking for accuracy
            - Connection pooling for database efficiency
            - Streaming for real-time user feedback
        """
        # Initialize async communication queue for real-time events
        event_queue = asyncio.Queue()
        callback_handler = AsyncStreamingCallbackHandler(event_queue)
        
        # Note: token_tracker is request-scoped via FastAPI, no manual reset needed
        
        try:
            # =================================================================
            # DYNAMIC LLM SERVICE SELECTION AND INITIALIZATION
            # =================================================================
            service_to_load = None
            if model_name:
                # Extract service name from model specification
                # Example: 'gemini-1.5-flash' -> 'gemini'
                service_to_load = model_name.split('-')[0].lower()

            # Use factory pattern to get appropriate LLM service
            # Falls back to default service if no specific provider requested
            self.current_request_llm_service = llm_service_factory(
                service_to_load,
                api_key=api_key  # Pass custom API key for per-request override
            ) if service_to_load else self.default_llm_service
            
            logger.info(f"Using LLM Service: {type(self.current_request_llm_service).__name__} for model '{model_name or 'default'}'")

            # Initialize LangChain-compatible model wrapper
            # Store current request model configuration for use across all tools
            # This ensures that all LLM calls within this request use the same model
            # specified by the user, rather than falling back to hardcoded defaults
            self.current_model_name = model_name                    # Store user-provided model name
            self.current_temperature = temperature                  # Store user-provided temperature
            
            effective_model_name = model_name or self.settings.GEMINI_RAG_MODEL_NAME
            effective_temperature = temperature if temperature is not None else 0.0
            
            logger.info(f"Initializing LangChain model with: model='{effective_model_name}', temperature={effective_temperature}")
            
            self.langchain_llm = self.current_request_llm_service.get_langchain_chat_model(
                model_name=effective_model_name,
                temperature=effective_temperature
            )

            # Store dynamic database connection info for this request
            self.current_db_connection_info = db_connection_info
            logger.info(f"Successfully initialized LangChain model for this request.")
            
            if db_connection_info:
                logger.info(f"Using dynamic database connection to {db_connection_info.get('db_host')}:{db_connection_info.get('db_port')}/{db_connection_info.get('db_name')}")
            else:
                logger.info("Using default database connection from settings")

        except Exception as e:
            # Handle LLM service initialization failures gracefully
            logger.error(f"Failed to get model '{model_name}': {e}", exc_info=True)
            await event_queue.put(format_sse("error", {"message": f"Model '{model_name}' or its service is not supported or configured."}))
            yield f"event: error\ndata: {json.dumps({'message': f'Model {model_name} not supported.'})}\n\n"
            return

        # =================================================================
        # CONVERSATION CONTEXT PROCESSING
        # =================================================================
        # Format chat history for agent context understanding
        self.last_formatted_history = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in (chat_history or [])
        ])
        
        # Format short-term memory for immediate context
        formatted_short_term_memory = "\n".join(short_term_memory or [])

        # =================================================================
        # TOOL INITIALIZATION WITH QUEUE BINDING
        # =================================================================
        # Bind the event queue to each tool using partial functions
        # This allows tools to send real-time progress updates
        history_tool_with_queue = partial(self._answer_from_history_tool, event_queue)
        sql_tool_with_queue = partial(self._sql_workflow_tool, event_queue)
        dq_tool_with_queue = partial(self._dq_workflow_tool, event_queue)
        viz_tool_with_queue = partial(self._visualize_schema_tool, event_queue)
        
        # Define agent tools with clear descriptions for ReAct reasoning
        tools = [
            Tool(
                name="answer_from_history", 
                description="Use for general conversation, greetings, or questions about the conversation history itself. This is the default choice if no other tool is appropriate.", 
                func=history_tool_with_queue, 
                coroutine=history_tool_with_queue
            ),
            Tool(
                name="get_database_answer", 
                description="Use for questions about data, numbers, lists, and creating data charts that require querying the database.", 
                func=sql_tool_with_queue, 
                coroutine=sql_tool_with_queue
            ),
            Tool(
                name="get_data_quality_info", 
                description="Use for questions about data quality (DQ) rules or data validation processes.", 
                func=dq_tool_with_queue, 
                coroutine=dq_tool_with_queue
            ),
            Tool(
                name="visualize_database_schema", 
                description="Use ONLY for creating visual graphs of database tables and their relationships.", 
                func=viz_tool_with_queue, 
                coroutine=viz_tool_with_queue
            ),
        ]
        
        # Prepare tool information for agent prompt
        formatted_tools = "\n".join([f"- {tool.name}: {tool.description}" for tool in tools])
        tool_names = ", ".join([tool.name for tool in tools])

        # =================================================================
        # AGENT PROMPT TEMPLATE CONSTRUCTION
        # =================================================================
        # Sophisticated prompt engineering for optimal tool selection
        template = f"""You are an advanced routing agent. Your primary goal is to answer a user's question by selecting the best tool.

You have access to a database with this schema:
<schema>
{self.db_schema}
</schema>

You have access to the following tools:
<tools>
{{tools}}
</tools>

You MUST follow this two-step process:

**Step 1: Analyze Context and Reformulate the Question.**
First, analyze the `chat_history` and `short_term_memory` to understand the full context of the user's `input`.
- If the `input` is a follow-up question (e.g., "what about for Q2?", "and for Canada?"), you MUST reformulate it into a complete, standalone question that can be understood without the history.
- If the `input` is already a standalone question, use it as is.
- If the `input` is a general conversational question (e.g., "hello", "thank you", "what did you just say?"), the reformulated question is the original input.

**Step 2: Select a Tool.**
Based on your reformulated question from Step 1, select the single best tool from the list: [{{tool_names}}]
- Use `get_database_answer` for specific questions that require querying the database for data.
- Use `answer_from_history` for conversational questions that can be answered using the chat history alone. This is your default choice if no other tool fits.

You MUST format your response EXACTLY as follows, with no preamble:
Thought: I will first reformulate the user's question based on the conversation history. Then I will select the best tool for the reformulated question.
Action: [the name of the single tool I have chosen]
Action Input: [the reformulated, standalone question from Step 1]

Here is the conversation history for context:
<chat_history>
{{chat_history}}
</chat_history>

Here is the short term memory:
<short_term_memory>
{{short_term_memory}}
</short_term_memory>

Begin!

User Input: {{input}}
{{agent_scratchpad}}
"""
        
        # Create prompt template with dynamic variable binding
        prompt = ChatPromptTemplate.from_template(template).partial(
            tools=formatted_tools,
            tool_names=tool_names
        )
        
        # =================================================================
        # AGENT CREATION AND CONFIGURATION
        # =================================================================
        # Create ReAct agent with custom output parser
        agent = create_react_agent(self.langchain_llm, tools, prompt)
        
        # Configure agent executor with single-iteration strategy
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,                           # Enable detailed logging
            handle_parsing_errors=True,             # Graceful error handling
            max_iterations=1,                       # Single-shot execution
            output_parser=StopAfterToolOutputParser()  # Custom parser
        )
        
        # =================================================================
        # AGENT EXECUTION WITH STREAMING COORDINATION
        # =================================================================
        async def run_agent_task():
            """
            Execute the agent in a separate async task for non-blocking operation.
            
            This function handles the actual agent execution and ensures proper
            cleanup and token reporting regardless of success or failure.
            """
            try:
                # Invoke agent with full context
                await agent_executor.ainvoke(
                    {
                        "input": query, 
                        "chat_history": self.last_formatted_history, 
                        "short_term_memory": formatted_short_term_memory
                    },
                    config={"callbacks": [callback_handler]}
                )
            except Exception as e:
                logger.error(f"Agent execution error: {e}", exc_info=True)
                await event_queue.put(format_sse("error", {"message": f"Agent process failed: {e}"}))
            finally:
                # Send token usage as final event before ending stream
                total_usage = self.token_tracker.get_total_usage()
                if total_usage.total_token_count > 0:  # Only send if we have actual usage
                    token_usage_data = {
                        "token_usage": total_usage.to_dict(),
                        "llm_calls_count": self.token_tracker.get_call_count()
                    }
                    await event_queue.put(format_sse("token_usage", token_usage_data))
                
                # Signal end of stream
                await event_queue.put(None)

        # Start agent execution as background task
        agent_task = asyncio.create_task(run_agent_task())
        
        # =================================================================
        # EVENT STREAMING WITH EARLY TERMINATION
        # =================================================================
        has_sent_structured_response = False
        
        # Stream events until completion or early termination
        while True:
            event = await event_queue.get()
            if event is None:  # End of stream signal
                break
            
            # Early termination optimization: stop after structured response
            if has_sent_structured_response:
                # Still send token_usage event even after structured response
                if "event: token_usage" in event:
                    yield event
                # Cancel agent task if still running (optimization)
                if not agent_task.done():
                    agent_task.cancel()
                continue
            
            # Yield event to client
            yield event
            
            # Check for structured response completion
            if "event: structured_response" in event:
                has_sent_structured_response = True
        
        # Ensure agent task completes cleanly
        try:
            await agent_task
        except asyncio.CancelledError:
            logger.info("Agent task cancelled after sending structured response.")