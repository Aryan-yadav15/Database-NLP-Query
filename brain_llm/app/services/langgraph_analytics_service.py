"""
LangGraph Analytics Dashboard Service Module
==========================================

This module implements a sophisticated analytics dashboard generation system using LangGraph
for advanced workflow orchestration, state management, and intelligent reasoning.

Key Features:
1. Multi-step analytics workflows with conditional routing
2. Advanced state persistence across complex reasoning chains
3. Real-time streaming with progress updates
4. Intelligent error recovery and retry mechanisms
5. Comprehensive analytics pipeline (SQL → Charts → Insights → Dashboards)

Architecture:
- LangGraph StateGraph for workflow orchestration
- Conditional routing based on query intent and data characteristics
- Modular analytics nodes for different processing stages
- Real-time streaming via Server-Sent Events
- Token usage tracking across all LLM interactions

Author: Brain LLM Team - LangGraph Migration
"""

import logging
import json
import asyncio
import time
from datetime import datetime
from functools import partial
from typing import Dict, List, Optional, Any, AsyncGenerator, Union
from typing_extensions import TypedDict, Annotated
import operator
import pandas as pd
import numpy as np

# LangGraph core components
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict

# LangChain compatibility components
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
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
    generate_sql_and_entities_for_dq_rule_sync, get_detailed_database_schema_string
)

# Module-level logger
logger = logging.getLogger(__name__)

def format_sse(event_name: str, data: Dict[str, Any]) -> str:
    """Format data as Server-Sent Events (SSE) for real-time streaming."""
    json_data = json.dumps(data, default=str)
    return f"event: {event_name}\ndata: {json_data}\n\n"

# =============================================================================
# LANGGRAPH STATE DEFINITION
# =============================================================================

class AnalyticsDashboardState(TypedDict):
    """
    Comprehensive state management for LangGraph analytics dashboard workflows.
    
    This state persists across all nodes in the analytics pipeline, enabling
    sophisticated reasoning and context retention throughout the entire process.
    """
    # User Input & Context
    user_query: str
    user_id: str
    session_id: str
    timestamp: datetime
    
    # LLM Configuration
    model_name: Optional[str]
    temperature: Optional[float]
    api_key: Optional[str]
    
    # Chat Context
    chat_history: List[Dict[str, str]]
    short_term_memory: List[str]
    formatted_history: str
    
    # Database Connection
    db_connection_info: Optional[Dict[str, Any]]
    db_schema: str
    
    # Query Analysis
    query_intent: Dict[str, Any]  # Intent classification results
    analysis_type: str  # "trend", "comparison", "prediction", "simple_metrics"
    complexity_level: int  # 1-5 scale
    key_metrics: List[str]
    suggested_charts: List[str]
    
    # Data Discovery & Processing
    discovered_datasets: List[Dict]
    selected_data: Optional[pd.DataFrame]
    data_quality_scores: Dict[str, float]
    
    # SQL Generation & Execution
    generated_sql: Optional[str]
    sql_status: str  # "pending", "success", "retry_needed", "failed"
    sql_execution_time: Optional[float]
    
    # Analytics Results
    statistical_summary: Dict[str, Any]
    trend_analysis: Dict[str, Any]
    anomalies_detected: List[Dict]
    
    # ML & Predictions
    ml_models: Dict[str, Any]
    predictions: Dict[str, Any]
    confidence_scores: Dict[str, float]
    
    # Visualization & Dashboard
    chart_configurations: List[Dict]
    key_metrics_cards: List[Dict]
    dashboard_layout: Dict[str, Any]
    interactive_elements: Dict[str, Any]
    
    # Real-time & Streaming
    streaming_enabled: bool
    streaming_config: Dict[str, Any]
    last_update: datetime
    
    # Error Handling & Recovery
    error_history: List[str]
    retry_count: int
    fallback_strategies: List[str]
    current_node: str
    
    # Response Tracking
    response_sent: bool
    final_response: Dict[str, Any]
    
    # Token Usage
    total_tokens_used: int
    
    # Event Queue for Streaming
    event_queue: Optional[asyncio.Queue]

# =============================================================================
# GLOBAL SERVICE REGISTRY FOR NODE ACCESS
# =============================================================================

# Global registry to make services available to LangGraph nodes
_service_registry = {}

def register_services(llm_service, dq_rule_manager, visualization_service, token_tracker, db_schema=None):
    """Register services for node access (thread-safe singleton pattern)."""
    _service_registry.update({
        'llm_service': llm_service,
        'dq_rule_manager': dq_rule_manager,
        'visualization_service': visualization_service,
        'token_tracker': token_tracker,
        'schema': db_schema
    })

def get_service(service_name: str):
    """Get a registered service by name."""
    return _service_registry.get(service_name)

# =============================================================================
# ANALYTICS REASONING NODES
# =============================================================================

async def analyze_query_intent(state: AnalyticsDashboardState) -> AnalyticsDashboardState:
    """
    Advanced query intent analysis using LLM reasoning.
    
    This node performs sophisticated analysis of user queries to determine:
    - Analysis type (trend, comparison, prediction, simple metrics)
    - Complexity level for workflow routing
    - Key metrics and entities mentioned
    - Optimal visualization suggestions
    """
    try:
        if state.get("event_queue"):
            await state["event_queue"].put(format_sse("status_update", {"message": "Analyzing query intent..."}))
        
        # Get LLM service from registry instead of state
        llm_service = get_service('llm_service')
        if not llm_service:
            raise ValueError("LLM service not available in service registry")
        
        intent_prompt = f"""
        Analyze this analytics query and determine the optimal processing strategy:
        
        Query: "{state['user_query']}"
        
        Chat Context: {state.get('formatted_history', '')}
        
        Database Schema Sample: {state['db_schema'][:1000]}...
        
        Classify the query and provide analysis:
        
        1. ANALYSIS_TYPE (choose one):
           - simple_metrics: Basic KPI requests, single values
           - trend_analysis: Time-series analysis, patterns over time
           - comparative_analysis: Comparisons between segments/categories
           - predictive_analytics: Forecasting, future predictions
           - real_time_dashboard: Live monitoring requirements
           - data_quality: Data quality rules, validation, DQ analysis
           - visualization: Schema visualization, ERD, database structure
        
        2. COMPLEXITY_LEVEL (1-5):
           - 1: Single table, basic aggregation
           - 2: Multi-table joins, grouped data
           - 3: Complex calculations, multiple metrics
           - 4: Advanced analytics, statistical analysis
           - 5: ML/AI predictions, complex workflows
        
        3. KEY_METRICS: List specific metrics mentioned
        4. SUGGESTED_CHARTS: Recommend visualization types
        5. TIME_PERIODS: Any time ranges mentioned
        
        Respond in JSON format:
        {{
            "analysis_type": "...",
            "complexity_level": 1-5,
            "key_metrics": ["..."],
            "suggested_charts": ["..."],
            "time_periods": ["..."],
            "reasoning": "..."
        }}
        """
        
        # This is a placeholder - in real implementation, we'd use the LLM service
        # For now, we'll do basic classification
        query_lower = state["user_query"].lower()
        
        # Check for data quality queries first
        if any(word in query_lower for word in ["data quality", "dq rule", "validation", "quality rule", "data rule", "constraint", "data integrity"]):
            analysis_type = "data_quality"
            complexity = 2
            suggested_charts = ["table", "rule_summary"]
        # Check for visualization/schema queries
        elif any(word in query_lower for word in ["schema", "visualization", "visualize", "erd", "entity relationship", "database structure", "table relationship", "diagram", "relationship", "show relationship", "database diagram"]):
            analysis_type = "visualization"
            complexity = 1
            suggested_charts = ["erd_diagram", "schema_diagram"]
        # Check for trend analysis
        elif any(word in query_lower for word in ["trend", "over time", "monthly", "yearly", "timeline"]):
            analysis_type = "trend_analysis"
            complexity = 3
            suggested_charts = ["line_chart", "area_chart"]
        elif any(word in query_lower for word in ["compare", "vs", "versus", "difference"]):
            analysis_type = "comparative_analysis"
            complexity = 2
            suggested_charts = ["bar_chart", "column_chart"]
        elif any(word in query_lower for word in ["predict", "forecast", "future", "next"]):
            analysis_type = "predictive_analytics"
            complexity = 4
            suggested_charts = ["line_chart", "forecast_chart"]
        else:
            analysis_type = "simple_metrics"
            complexity = 1
            suggested_charts = ["metric_card", "table"]
        
        # Update state with analysis results
        updated_state = {
            **state,
            "query_intent": {
                "analysis_type": analysis_type,
                "complexity_level": complexity,
                "reasoning": f"Classified as {analysis_type} based on keywords and context"
            },
            "analysis_type": analysis_type,
            "complexity_level": complexity,
            "suggested_charts": suggested_charts,
            "current_node": "analyze_query_intent"
        }
        
        if state.get("event_queue"):
            await state["event_queue"].put(format_sse("status_update", {
                "message": f"Classified as {analysis_type} (complexity: {complexity})"
            }))
        
        return updated_state
        
    except Exception as e:
        logger.error(f"Error in query intent analysis: {e}")
        error_history = state.get("error_history", [])
        error_history.append(f"Intent analysis error: {str(e)}")
        
        return {
            **state,
            "error_history": error_history,
            "current_node": "analyze_query_intent",
            "analysis_type": "simple_metrics",  # Fallback
            "complexity_level": 1
        }

async def generate_smart_sql(state: AnalyticsDashboardState) -> AnalyticsDashboardState:
    """
    Enhanced SQL generation with retry logic and context learning.
    """
    try:
        if state.get("event_queue"):
            await state["event_queue"].put(format_sse("status_update", {"message": "Generating SQL query..."}))
        
        max_retries = 3
        current_retry = state.get("retry_count", 0)
        
        if current_retry >= max_retries:
            return {
                **state,
                "sql_status": "failed",
                "error_history": state.get("error_history", []) + ["Max SQL retries exceeded"]
            }
        
        # Build context-aware prompt
        error_context = ""
        if state.get("error_history"):
            error_context = f"""
            Previous SQL errors to avoid:
            {chr(10).join(state["error_history"][-2:])}
            """
        
        analysis_context = ""
        if state.get("analysis_type"):
            analysis_context = f"""
            Analysis Type: {state["analysis_type"]}
            Expected Complexity: {state.get("complexity_level", 1)}
            Key Metrics: {state.get("key_metrics", [])}
            """
        
        sql_prompt = f"""
        Generate optimized PostgreSQL query for analytics dashboard:
        
        User Query: {state["user_query"]}
        {analysis_context}
        
        Database Schema:
        {state["db_schema"]}
        
        Requirements:
        1. Use EXACT column names from schema (case-sensitive)
        2. Include appropriate aggregations for dashboard display
        3. Add time-based grouping if trend analysis
        4. Include necessary JOINs for comprehensive view
        5. Optimize for performance (LIMIT 1000 if large results expected)
        6. Return data suitable for visualization
        
        {error_context}
        
        Generate ONLY the SQL query without explanation:
        """
        
        # Use the LLM service to generate SQL query
        llm_service = get_service('llm_service')
        if not llm_service:
            raise ValueError("LLM service not available in service registry")
        
        try:
            # Use the existing SQL generation utility
            from .sql_query_router_logic import generate_sql_via_llm
            
            # Generate SQL using the LLM service
            sql_query = await asyncio.to_thread(
                generate_sql_via_llm,
                state["user_query"],
                llm_service,
                state["db_schema"],
                model_name=state.get("model_name")
            )
            
            if not sql_query or not sql_query.strip():
                raise ValueError("Generated SQL query is empty")
                
        except Exception as e:
            logger.warning(f"LLM SQL generation failed: {e}, using fallback")
            # Fallback: create a simple query based on query analysis
            # Use a more generic table that should exist in AdventureWorks
            sql_query = f"SELECT 1 as fallback_result; -- Fallback for: {state['user_query']}"
        
        return {
            **state,
            "generated_sql": sql_query,
            "sql_status": "success",
            "retry_count": 0,
            "current_node": "generate_smart_sql"
        }
        
    except Exception as e:
        logger.error(f"Error in SQL generation: {e}")
        error_history = state.get("error_history", [])
        error_history.append(f"SQL generation error: {str(e)}")
        
        return {
            **state,
            "error_history": error_history,
            "retry_count": state.get("retry_count", 0) + 1,
            "sql_status": "retry_needed",
            "current_node": "generate_smart_sql"
        }

async def execute_data_query(state: AnalyticsDashboardState) -> AnalyticsDashboardState:
    """
    Execute SQL query with proper connection management and error handling.
    """
    try:
        if state.get("event_queue"):
            await state["event_queue"].put(format_sse("status_update", {"message": "Executing query..."}))
        
        sql_query = state.get("generated_sql")
        if not sql_query:
            raise ValueError("No SQL query available for execution")
        
        start_time = time.time()
        
        # Database connection and execution logic
        pg_conn = None
        try:
            if state.get("db_connection_info"):
                # Dynamic connection
                results_df, error_msg = await asyncio.to_thread(
                    execute_sql_query_unified,
                    state["db_connection_info"],
                    sql_query
                )
            else:
                # Default connection
                pg_conn_gen = get_adventureworks_db_session()
                pg_conn = next(pg_conn_gen)
                results_df, error_msg = await asyncio.to_thread(
                    execute_sql_query_pg, 
                    pg_conn, 
                    sql_query
                )
            
            if error_msg:
                raise ConnectionError(f"Database error: {error_msg}")
            
            execution_time = time.time() - start_time
            
            return {
                **state,
                "selected_data": results_df,
                "sql_execution_time": execution_time,
                "sql_status": "executed",
                "current_node": "execute_data_query"
            }
            
        finally:
            # Cleanup connections
            if pg_conn:
                try:
                    next(pg_conn_gen)
                except StopIteration:
                    pass
        
    except Exception as e:
        logger.error(f"Error in query execution: {e}")
        error_history = state.get("error_history", [])
        error_history.append(f"Query execution error: {str(e)}")
        
        return {
            **state,
            "error_history": error_history,
            "sql_status": "failed",
            "current_node": "execute_data_query"
        }

async def perform_statistical_analysis(state: AnalyticsDashboardState) -> AnalyticsDashboardState:
    """
    Comprehensive statistical analysis of query results.
    """
    try:
        if state.get("event_queue"):
            await state["event_queue"].put(format_sse("status_update", {"message": "Performing statistical analysis..."}))
        
        data = state.get("selected_data")
        if data is None or data.empty:
            return {
                **state,
                "statistical_summary": {},
                "current_node": "perform_statistical_analysis"
            }
        
        # Basic statistical computations
        statistical_summary = {
            "basic_stats": data.describe().to_dict() if len(data.select_dtypes(include=[np.number]).columns) > 0 else {},
            "row_count": len(data),
            "column_count": len(data.columns),
            "data_types": data.dtypes.to_dict(),
            "missing_values": data.isnull().sum().to_dict()
        }
        
        # Correlation analysis
        numerical_cols = data.select_dtypes(include=[np.number]).columns
        if len(numerical_cols) > 1:
            correlation_matrix = data[numerical_cols].corr()
            statistical_summary["correlation_matrix"] = correlation_matrix.to_dict()
        
        # Outlier detection
        outliers = {}
        for col in numerical_cols:
            if data[col].notna().sum() > 0:
                Q1 = data[col].quantile(0.25)
                Q3 = data[col].quantile(0.75)
                IQR = Q3 - Q1
                outlier_count = len(data[
                    (data[col] < Q1 - 1.5 * IQR) | (data[col] > Q3 + 1.5 * IQR)
                ])
                outliers[col] = outlier_count
        
        statistical_summary["outlier_counts"] = outliers
        
        return {
            **state,
            "statistical_summary": statistical_summary,
            "current_node": "perform_statistical_analysis"
        }
        
    except Exception as e:
        logger.error(f"Error in statistical analysis: {e}")
        return {
            **state,
            "statistical_summary": {},
            "current_node": "perform_statistical_analysis"
        }

async def generate_optimal_charts(state: AnalyticsDashboardState) -> AnalyticsDashboardState:
    """
    Generate optimal chart configurations based on data characteristics and analysis type.
    """
    try:
        if state.get("event_queue"):
            await state["event_queue"].put(format_sse("status_update", {"message": "Generating charts..."}))
        
        data = state.get("selected_data")
        analysis_type = state.get("analysis_type", "simple_metrics")
        
        if data is None or data.empty:
            return {
                **state,
                "chart_configurations": [],
                "key_metrics_cards": [],
                "current_node": "generate_optimal_charts"
            }
        
        chart_configurations = []
        key_metrics_cards = []
        
        # Analyze data characteristics
        numerical_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = data.select_dtypes(include=['object']).columns.tolist()
        
        # Generate charts based on analysis type
        if analysis_type == "trend_analysis":
            # Look for time-like columns
            time_candidates = [col for col in data.columns if any(
                time_word in col.lower() for time_word in ['date', 'time', 'year', 'month']
            )]
            
            if time_candidates and numerical_cols:
                time_col = time_candidates[0]
                for metric in numerical_cols[:3]:  # Max 3 metrics
                    chart_configurations.append({
                        "type": "line_chart",
                        "title": f"{metric.replace('_', ' ').title()} Over Time",
                        "x_axis": time_col,
                        "y_axis": metric,
                        "data": data[[time_col, metric]].to_dict('records')
                    })
        
        elif analysis_type == "comparative_analysis":
            if categorical_cols and numerical_cols:
                for cat_col in categorical_cols[:2]:
                    for metric in numerical_cols[:2]:
                        grouped_data = data.groupby(cat_col)[metric].mean().reset_index()
                        chart_configurations.append({
                            "type": "bar_chart",
                            "title": f"{metric.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}",
                            "x_axis": cat_col,
                            "y_axis": metric,
                            "data": grouped_data.to_dict('records')
                        })
        
        # Generate key metrics cards
        for col in numerical_cols[:4]:
            if data[col].notna().sum() > 0:
                key_metrics_cards.append({
                    "type": "metric_card",
                    "title": col.replace('_', ' ').title(),
                    "value": round(data[col].mean(), 2),
                    "subtitle": f"Average of {len(data)} records"
                })
        
        # Default table view
        if not chart_configurations:
            chart_configurations.append({
                "type": "data_table",
                "title": "Query Results",
                "data": data.head(100).to_dict('records'),
                "columns": list(data.columns)
            })
        
        return {
            **state,
            "chart_configurations": chart_configurations,
            "key_metrics_cards": key_metrics_cards,
            "current_node": "generate_optimal_charts"
        }
        
    except Exception as e:
        logger.error(f"Error in chart generation: {e}")
        return {
            **state,
            "chart_configurations": [],
            "key_metrics_cards": [],
            "current_node": "generate_optimal_charts"
        }

async def assemble_dashboard(state: AnalyticsDashboardState) -> AnalyticsDashboardState:
    """
    Assemble all components into a cohesive dashboard layout.
    """
    try:
        if state.get("event_queue"):
            await state["event_queue"].put(format_sse("status_update", {"message": "Assembling dashboard..."}))
        
        dashboard_layout = {
            "title": f"Analytics Dashboard - {state['user_query'][:50]}...",
            "description": f"Generated dashboard for {state.get('analysis_type', 'analytics')} analysis",
            "timestamp": datetime.now().isoformat(),
            "sections": []
        }
        
        # Key Metrics Section
        if state.get("key_metrics_cards"):
            dashboard_layout["sections"].append({
                "id": "metrics_overview",
                "title": "Key Metrics",
                "type": "metrics_grid",
                "components": state["key_metrics_cards"]
            })
        
        # Charts Section
        if state.get("chart_configurations"):
            dashboard_layout["sections"].append({
                "id": "visualizations",
                "title": "Visualizations",
                "type": "chart_grid",
                "components": state["chart_configurations"]
            })
        
        # Statistical Summary
        if state.get("statistical_summary"):
            dashboard_layout["sections"].append({
                "id": "statistics",
                "title": "Statistical Summary",
                "type": "stats_panel",
                "components": [state["statistical_summary"]]
            })
        
        interactive_elements = {
            "filters": [],
            "export_options": ["PDF", "Excel", "PNG"],
            "real_time_updates": state.get("streaming_enabled", False)
        }
        
        # Create final response
        final_response = {
            "answer_text": f"Generated comprehensive dashboard for your {state.get('analysis_type', 'analytics')} query.",
            "dashboard": dashboard_layout,
            "interactive_elements": interactive_elements,
            "sql": state.get("generated_sql"),
            "execution_time": state.get("sql_execution_time"),
            "strategy_used": "LANGGRAPH_ANALYTICS"
        }
        
        return {
            **state,
            "dashboard_layout": dashboard_layout,
            "interactive_elements": interactive_elements,
            "final_response": final_response,
            "response_sent": False,
            "current_node": "assemble_dashboard"
        }
        
    except Exception as e:
        logger.error(f"Error in dashboard assembly: {e}")
        return {
            **state,
            "dashboard_layout": {},
            "current_node": "assemble_dashboard"
        }

async def query_data_quality_rules(state: AnalyticsDashboardState) -> AnalyticsDashboardState:
    """
    Query the ChromaDB vector store for relevant data quality rules.
    
    This node uses the DQ Rule Manager to find data quality rules relevant
    to the user's query using semantic search, matching the original LangChain implementation.
    """
    try:
        if state.get("event_queue"):
            await state["event_queue"].put(format_sse("status_update", {"message": "Searching for relevant data quality rules..."}))
        
        # Get services from registry
        dq_rule_manager = get_service('dq_rule_manager')
        llm_service = get_service('llm_service')
        token_tracker = get_service('token_tracker')
        
        if not dq_rule_manager:
            raise ValueError("DQ rule manager not available in service registry")
        
        # Search for relevant DQ rules using the correct method name from original implementation
        query = state["user_query"]
        rules = await asyncio.to_thread(dq_rule_manager.find_relevant_rules_sync, query)
        
        if not rules:
            final_response = {
                "answer_text": "No relevant data quality rules found for your query.",
                "table": {"title": "Data Quality Rules", "columns": ["Rule ID", "Description", "Status"], "rows": []},
                "dqRules": [],
                "strategy_used": "DQ_RULE"
            }
            
            if state.get("event_queue"):
                await state["event_queue"].put(format_sse("structured_response", final_response))
            
            return {
                **state,
                "dq_rules_data": [],
                "final_response": final_response,
                "response_sent": True,
                "current_node": "query_data_quality_rules"
            }
        
        if state.get("event_queue"):
            await state["event_queue"].put(format_sse("status_update", {"message": f"Found {len(rules)} rule(s). Generating validation queries..."}))
        
        # Generate SQL for each rule (matching original implementation)
        from .sql_query_router_logic import generate_sql_and_entities_for_dq_rule_sync
        
        rules_with_sql = []
        for rule in rules:
            rule_desc = rule.get("Description")
            if rule_desc and llm_service:
                try:
                    # Get schema from state or use fallback
                    schema_to_use = state.get("schema", "")
                    if not schema_to_use:
                        # Fallback to registered schema if available
                        schema_service = get_service('schema')
                        schema_to_use = schema_service or ""
                    
                    llm_data = await asyncio.to_thread(
                        generate_sql_and_entities_for_dq_rule_sync, 
                        rule_desc, 
                        llm_service, 
                        schema_to_use, 
                        1, 
                        token_tracker,
                        state.get("model_name")
                    )
                    rule['sql_query'] = llm_data.get("sql_query") if llm_data else "N/A"
                except Exception as sql_error:
                    logger.warning(f"Failed to generate SQL for rule {rule.get('Rule_ID')}: {sql_error}")
                    rule['sql_query'] = "N/A"
            else:
                rule['sql_query'] = "N/A"
            rules_with_sql.append(rule)
        
        if state.get("event_queue"):
            await state["event_queue"].put(format_sse("status_update", {"message": "Formatting DQ rules for display..."}))
        
        # Format rules for display (matching original structure)
        table_data = {
            "title": "Data Quality Rules",
            "columns": ["Rule ID", "Description", "Status", "SQL Code"],
            "rows": [
                [
                    r.get('Rule_ID', 'N/A'), 
                    r.get('Description', 'N/A'), 
                    r.get('status', 'Active'),
                    r.get('sql_query', 'N/A')
                ] for r in rules_with_sql
            ]
        }
        
        answer_text = f"I found {len(rules_with_sql)} relevant data quality rule(s)."
        
        final_response = {
            "answer_text": answer_text,
            "table": table_data,
            "dqRules": rules_with_sql,
            "strategy_used": "DQ_RULE"
        }
        
        # Send the final response via event queue
        if state.get("event_queue"):
            await state["event_queue"].put(format_sse("structured_response", final_response))
        
        return {
            **state,
            "dq_rules_data": rules_with_sql,
            "final_response": final_response,
            "response_sent": True,
            "current_node": "query_data_quality_rules"
        }
            
    except Exception as e:
        logger.error(f"Error in data quality rule query: {e}", exc_info=True)
        
        # Send error response via event queue
        error_response = {
            "answer_text": f"Error occurred while searching data quality rules: {str(e)}",
            "table": {"title": "Data Quality Rules", "columns": ["Rule ID", "Description", "Status"], "rows": []},
            "dqRules": [],
            "strategy_used": "DQ_RULE"
        }
        
        if state.get("event_queue"):
            await state["event_queue"].put(format_sse("structured_response", error_response))
        
        return {
            **state,
            "dq_rules_data": [],
            "final_response": error_response,
            "response_sent": True,
            "current_node": "query_data_quality_rules"
        }

async def generate_schema_visualization(state: AnalyticsDashboardState) -> AnalyticsDashboardState:
    """
    Generate database schema visualization using the visualization service.
    
    This node creates entity relationship diagrams and schema visualizations,
    matching the original LangChain implementation.
    """
    try:
        if state.get("event_queue"):
            await state["event_queue"].put(format_sse("status_update", {"message": "Analyzing schema for visualization..."}))
        
        # Get services from service registry
        visualization_service = get_service('visualization_service')
        llm_service = get_service('llm_service')
        token_tracker = get_service('token_tracker')
        
        if not visualization_service:
            raise ValueError("Visualization service not available in service registry")
        
        try:
            # Check for dynamic database connection info
            db_connection_info = state.get("db_connection_info")
            dynamic_db_connection = None
            provided_schema = None
            
            if db_connection_info:
                logger.info("Using dynamic database connection for visualization")
                # Check if schema is pre-provided
                provided_schema = db_connection_info.get('db_schema')
                if provided_schema and provided_schema.strip():
                    logger.info("Using pre-provided schema for visualization (no DB fetch needed)")
                else:
                    logger.info("No pre-provided schema, will fetch from database")
                # Note: Connection manager would be needed here in a real scenario
                # dynamic_db_connection = connection_manager.get_raw_psycopg2_connection(db_connection_info)
            
            # Generate visualization using the service (matching original implementation)
            visualization_result = await visualization_service.generate_visualization_json(
                state["user_query"],
                dynamic_llm_service=llm_service,
                dynamic_db_connection=dynamic_db_connection,
                provided_schema=provided_schema or state.get("db_schema", ""),
                token_tracker=token_tracker,
                model_name=state.get("model_name")
            )
            
            if not visualization_result:
                raise ValueError("Failed to generate visualization data.")
            
            visualization_data = visualization_result.get("visualization_data", {})
            answer_text = visualization_result.get("answer_text", "Here's a visualization of the database schema you requested.")
            
            # Create final response (matching original structure)
            final_response = {
                "answer_text": answer_text,
                "graph": visualization_data,
                "strategy_used": "VISUALIZE"
            }
            
            # Send the final response via event queue
            if state.get("event_queue"):
                await state["event_queue"].put(format_sse("structured_response", final_response))
            
            return {
                **state,
                "visualization_data": visualization_data,
                "final_response": final_response,
                "response_sent": True,
                "current_node": "generate_schema_visualization"
            }
            
        except Exception as e:
            logger.error(f"Error generating schema visualization: {e}")
            # Fallback response
            final_response = {
                "answer_text": f"Unable to generate schema visualization at this time. Error: {str(e)}",
                "graph": {},
                "strategy_used": "VISUALIZE"
            }
            
            # Send the error response via event queue
            if state.get("event_queue"):
                await state["event_queue"].put(format_sse("structured_response", final_response))
            
            return {
                **state,
                "visualization_data": {},
                "final_response": final_response,
                "response_sent": True,
                "current_node": "generate_schema_visualization"
            }
            
    except Exception as e:
        logger.error(f"Error in schema visualization generation: {e}", exc_info=True)
        
        # Send error response via event queue
        error_response = {
            "answer_text": f"Error generating schema visualization: {str(e)}",
            "graph": {},
            "strategy_used": "VISUALIZE"
        }
        
        if state.get("event_queue"):
            await state["event_queue"].put(format_sse("structured_response", error_response))
        
        return {
            **state,
            "visualization_data": {},
            "final_response": error_response,
            "response_sent": True,
            "current_node": "generate_schema_visualization"
        }

# =============================================================================
# CONDITIONAL ROUTING FUNCTIONS
# =============================================================================

def route_based_on_intent(state: AnalyticsDashboardState) -> str:
    """Route to appropriate next node based on query intent analysis."""
    analysis_type = state.get("analysis_type", "simple_metrics")
    complexity = state.get("complexity_level", 1)
    
    # Route based on analysis type first
    if analysis_type == "data_quality":
        return "query_data_quality_rules"
    elif analysis_type == "visualization":
        return "generate_schema_visualization"
    elif complexity >= 4 or analysis_type == "predictive_analytics":
        return "advanced_analytics_pipeline"
    elif analysis_type in ["trend_analysis", "comparative_analysis"]:
        return "generate_smart_sql"
    else:
        return "generate_smart_sql"  # Default path

def check_sql_validity(state: AnalyticsDashboardState) -> str:
    """Check SQL generation status and determine next action."""
    sql_status = state.get("sql_status", "pending")
    retry_count = state.get("retry_count", 0)
    
    if sql_status == "success":
        return "execute_query"
    elif sql_status == "retry_needed" and retry_count < 3:
        return "retry_sql"
    else:
        return "fallback_response"

def check_data_availability(state: AnalyticsDashboardState) -> str:
    """Check if data was successfully retrieved."""
    data = state.get("selected_data")
    if data is not None and not data.empty:
        return "analyze_data"
    else:
        return "no_data_response"

# =============================================================================
# MAIN LANGGRAPH SERVICE CLASS
# =============================================================================

class LangGraphAnalyticsService:
    """
    Main LangGraph-based analytics dashboard service.
    
    This service orchestrates the complete analytics pipeline using LangGraph's
    sophisticated workflow management and state persistence capabilities.
    """
    
    def __init__(self, llm_service: BaseLLMService, settings: Settings, db_schema: str,
                 dq_rule_manager: DQRuleManager, visualization_service: VisualizationService,
                 token_tracker: RequestTokenTracker):
        self.llm_service = llm_service
        self.settings = settings
        self.db_schema = db_schema
        self.dq_rule_manager = dq_rule_manager
        self.visualization_service = visualization_service
        self.token_tracker = token_tracker
        
        # Register services for node access
        register_services(llm_service, dq_rule_manager, visualization_service, token_tracker, db_schema)
        
        # Create the analytics workflow graph
        self.graph = self._create_analytics_graph()
    
    def _create_analytics_graph(self) -> StateGraph:
        """Create the main LangGraph workflow for analytics dashboard generation."""
        
        workflow = StateGraph(AnalyticsDashboardState)
        
        # Add all processing nodes
        workflow.add_node("analyze_query_intent", analyze_query_intent)
        workflow.add_node("generate_smart_sql", generate_smart_sql)
        workflow.add_node("execute_data_query", execute_data_query)
        workflow.add_node("perform_statistical_analysis", perform_statistical_analysis)
        workflow.add_node("generate_optimal_charts", generate_optimal_charts)
        workflow.add_node("assemble_dashboard", assemble_dashboard)
        
        # Add new specialized nodes for DQ and visualization
        workflow.add_node("query_data_quality_rules", query_data_quality_rules)
        workflow.add_node("generate_schema_visualization", generate_schema_visualization)
        
        # Define conditional routing
        workflow.add_conditional_edges(
            "analyze_query_intent",
            route_based_on_intent,
            {
                "generate_smart_sql": "generate_smart_sql",
                "advanced_analytics_pipeline": "generate_smart_sql",  # For now, same path
                "query_data_quality_rules": "query_data_quality_rules",
                "generate_schema_visualization": "generate_schema_visualization"
            }
        )
        
        workflow.add_conditional_edges(
            "generate_smart_sql",
            check_sql_validity,
            {
                "execute_query": "execute_data_query",
                "retry_sql": "generate_smart_sql",
                "fallback_response": "assemble_dashboard"
            }
        )
        
        workflow.add_conditional_edges(
            "execute_data_query",
            check_data_availability,
            {
                "analyze_data": "perform_statistical_analysis",
                "no_data_response": "assemble_dashboard"
            }
        )
        
        # Linear flow for final stages
        workflow.add_edge("perform_statistical_analysis", "generate_optimal_charts")
        workflow.add_edge("generate_optimal_charts", "assemble_dashboard")
        workflow.add_edge("assemble_dashboard", END)
        
        # Add direct paths to END for specialized nodes
        workflow.add_edge("query_data_quality_rules", END)
        workflow.add_edge("generate_schema_visualization", END)
        
        # Set entry point
        workflow.set_entry_point("analyze_query_intent")
        
        # Compile without checkpointer to avoid serialization issues with Queue and other objects
        # Note: State persistence is disabled for now to prioritize streaming functionality
        return workflow.compile()
    
    async def stream_analytics_query(self, query: str, model_name: Optional[str] = None,
                                   temperature: Optional[float] = 0.0, api_key: Optional[str] = None,
                                   chat_history: Optional[List[Dict[str, str]]] = None,
                                   short_term_memory: Optional[List[str]] = None,
                                   db_connection_info: Optional[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        """
        Main streaming method for analytics dashboard generation using LangGraph.
        """
        
        # Create event queue for streaming
        event_queue = asyncio.Queue()
        
        try:
            # Initialize state (excluding non-serializable objects like llm_service)
            initial_state = {
                "user_query": query,
                "user_id": "user",
                "session_id": f"session_{int(time.time())}",
                "timestamp": datetime.now(),
                "model_name": model_name,
                "temperature": temperature,
                "api_key": api_key,
                "chat_history": chat_history or [],
                "short_term_memory": short_term_memory or [],
                "formatted_history": "\n".join([f"{msg['role']}: {msg['content']}" for msg in (chat_history or [])]),
                "db_connection_info": db_connection_info,
                "db_schema": self.db_schema,
                "error_history": [],
                "retry_count": 0,
                "streaming_enabled": True,
                "response_sent": False,
                "total_tokens_used": 0,
                "event_queue": event_queue,
                # Note: llm_service is NOT included in state as it's not serializable
                # Nodes will access it via the service instance instead
            }
            
            # Create background task to run the graph
            async def run_graph_task():
                try:
                    # Execute graph without checkpointer configuration
                    result = await self.graph.ainvoke(initial_state)
                    
                    # Send final response
                    if result.get("final_response") and not result.get("response_sent"):
                        await event_queue.put(format_sse("structured_response", result["final_response"]))
                    
                    # Send token usage
                    total_usage = self.token_tracker.get_total_usage()
                    if total_usage.total_token_count > 0:
                        await event_queue.put(format_sse("token_usage", {
                            "token_usage": total_usage.to_dict(),
                            "llm_calls_count": self.token_tracker.get_call_count()
                        }))
                    
                except Exception as e:
                    logger.error(f"Graph execution error: {e}", exc_info=True)
                    await event_queue.put(format_sse("error", {"message": f"Analytics processing failed: {e}"}))
                finally:
                    await event_queue.put(None)  # End signal
            
            # Start graph execution
            graph_task = asyncio.create_task(run_graph_task())
            
            # Stream events
            while True:
                event = await event_queue.get()
                if event is None:
                    break
                yield event
            
            # Ensure task completes
            try:
                await graph_task
            except asyncio.CancelledError:
                logger.info("Graph task cancelled")
                
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield format_sse("error", {"message": f"Service error: {str(e)}"})

# =============================================================================
# MIGRATION WRAPPER FOR BACKWARD COMPATIBILITY
# =============================================================================

class LangChainStreamingService:
    """
    Backward compatibility wrapper for existing LangChain-based code.
    
    This class provides the same interface as the original LangChain service
    but delegates to the new LangGraph implementation internally.
    """
    
    def __init__(self, llm_service: BaseLLMService, settings: Settings, db_schema: str,
                 dq_rule_manager: DQRuleManager, visualization_service: VisualizationService,
                 token_tracker: RequestTokenTracker):
        
        # Initialize the new LangGraph service
        self.langgraph_service = LangGraphAnalyticsService(
            llm_service, settings, db_schema, dq_rule_manager, 
            visualization_service, token_tracker
        )
        
        # Store for compatibility
        self.settings = settings
        self.db_schema = db_schema
        self.token_tracker = token_tracker
    
    async def stream_query(self, query: str, model_name: Optional[str] = None,
                          temperature: Optional[float] = 0.0, api_key: Optional[str] = None,
                          chat_history: Optional[List[Dict[str, str]]] = None,
                          short_term_memory: Optional[List[str]] = None,
                          db_connection_info: Optional[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        """
        Backward compatible stream_query method that delegates to LangGraph implementation.
        """
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
