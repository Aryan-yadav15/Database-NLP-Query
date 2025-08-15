"""
SQL Query Processing and Database Schema Management Module
=========================================================

This module provides the core functionality for intelligent SQL query processing,
database schema introspection, and LLM-powered query routing for the Brain LLM system.

Key Responsibilities:
1. Database schema extraction and caching for LLM context
2. Natural language to SQL query conversion using LLMs
3. SQL query execution with error handling and result processing
4. Query routing logic (SQL vs conversational responses)
5. Entity extraction and data quality rule generation
6. Result formatting and visualization data preparation

Architecture Components:
- Schema Introspection: Analyzes PostgreSQL database structure
- Query Router: Determines appropriate processing strategy for user queries
- SQL Generator: Converts natural language to executable SQL using LLM
- Result Processor: Formats query results for frontend consumption
- Visualization Engine: Generates graph data for entity relationship diagrams

Database Support:
- Primary: AdventureWorks sample database (PostgreSQL)
- Schema: Supports multi-schema databases with automatic discovery
- Relationships: Extracts foreign key relationships for intelligent querying

Author: Brain LLM Team
"""

import asyncio
import pandas as pd
import psycopg2
import logging
import json
import re
from typing import Dict, List, Optional, Any, Tuple, TYPE_CHECKING
from app.core.config import settings
from app.services.llm.base import BaseLLMService

# Type checking import to avoid circular dependencies
if TYPE_CHECKING:
    from app.services.token_tracker import RequestTokenTracker

# Import centralized prompt templates for consistency
from app.prompts.prompt_engineering import (
    ADVENTUREWORKS_SCHEMA_FOR_LLM, 
    DECIDE_QUERY_PATH_PROMPT_TEMPLATE,
    GENERATE_SQL_PROMPT_TEMPLATE,
    FORMAT_SQL_RESULTS_PROMPT_TEMPLATE,
    GENERATE_DQ_SQL_PROMPT_TEMPLATE,
    EXTRACT_ENTITIES_PROMPT_TEMPLATE,
    GENERATE_VISUALIZATION_JSON_PROMPT_TEMPLATE
)

# Import optimized result formatter (eliminates LLM calls for formatting)
from app.services.result_formatter import format_sql_results_optimized

# Module-level logger for SQL processing operations
logger = logging.getLogger(__name__)

def get_detailed_database_schema_string(conn) -> str:
    """
    Fetches a comprehensive database schema description optimized for LLM consumption.
    
    This function performs deep schema introspection to extract table structures,
    relationships, and metadata that enables LLMs to generate accurate SQL queries.
    The output is formatted as a human-readable text description rather than raw SQL.
    
    Schema Components Extracted:
    1. Table names and schemas (excludes system tables)
    2. Column definitions with data types and constraints
    3. Primary key identification for each table
    4. Foreign key relationships between tables
    5. Index information for query optimization hints
    
    Args:
        conn: Active PostgreSQL connection with read access to information_schema
        
    Returns:
        str: Formatted schema description suitable for LLM prompts, or error message
        
    Performance Notes:
        - Results should be cached to avoid repeated schema queries
        - Typical execution time: 100-500ms depending on database size
        - Memory usage scales with number of tables/columns
        
    Error Handling:
        - Returns descriptive error message if connection fails
        - Logs warnings for empty databases or permission issues
        - Gracefully handles malformed schema information
        
    Example Output:
        "Table: sales.customer
         Columns: customer_id (integer, PK), name (varchar), email (varchar)
         Foreign Keys: None"
    """
    if not conn:
        logger.error("Database connection is not available for schema fetching.")
        return "SCHEMA_UNAVAILABLE: No database connection."
        
    schema_string_parts = ["Database Schema Description:"]
    cursor = None
    try:
        cursor = conn.cursor()
        # Get all tables from user-defined schemas - excludes PostgreSQL system tables
        cursor.execute("""
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema', 'pg_toast', 'tiger', 'tiger_data', 'topology')
              AND table_type = 'BASE TABLE'
            ORDER BY table_schema, table_name;
        """)
        tables_with_schema = cursor.fetchall()
        
        if not tables_with_schema:
            logger.warning("No user tables found in the database.")
            return "SCHEMA_UNAVAILABLE: No user tables found."
            
        for table_row in tables_with_schema:
            table_schema = table_row['table_schema']
            table_name = table_row['table_name']
            fully_qualified_table_name = f"{table_schema}.{table_name}"
            schema_string_parts.append(f"\nTable: {fully_qualified_table_name}")

            # Get columns and their data types
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position;
            """, (table_schema, table_name))
            columns_info = []
            for col_row in cursor.fetchall():
                col_info = f"{col_row['column_name']} ({col_row['data_type']})"
                if col_row['is_nullable'] == 'NO':
                    col_info += " NOT NULL"
                columns_info.append(col_info)
            schema_string_parts.append(f"  Columns: {', '.join(columns_info)}")

            # Get Primary Keys
            cursor.execute("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
                WHERE tc.table_schema = %s AND tc.table_name = %s AND tc.constraint_type = 'PRIMARY KEY';
            """, (table_schema, table_name))
            pk_columns = [row['column_name'] for row in cursor.fetchall()]
            if pk_columns:
                schema_string_parts.append(f"  Primary Key(s): {', '.join(pk_columns)}")
                logger.info(f"Table: {fully_qualified_table_name}, Primary Keys: {pk_columns}")

            # Get Foreign Keys
            cursor.execute("""
                SELECT
                    kcu.column_name,
                    ccu.table_schema AS foreign_table_schema,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name -- Removed ccu.table_schema = tc.table_schema as it's redundant with constraint_name join
                WHERE tc.table_schema = %s AND tc.table_name=%s AND tc.constraint_type = 'FOREIGN KEY';
            """, (table_schema, table_name))
            fk_info = []
            for fk_row in cursor.fetchall():
                fk_info.append(f"{fk_row['column_name']} -> {fk_row['foreign_table_schema']}.{fk_row['foreign_table_name']}({fk_row['foreign_column_name']})")
            if fk_info:
                schema_string_parts.append(f"  Foreign Key(s): {', '.join(fk_info)}")
                logger.info(f"Table: {fully_qualified_table_name}, Foreign Keys: {fk_info}")

        final_schema_string = "\n".join(schema_string_parts)
        logger.info(f"Final generated schema string for LLM:\n{final_schema_string}")
        return final_schema_string

    except psycopg2.Error as e:
        logger.error(f"Database error while fetching schema: {e}", exc_info=True) # Added exc_info for more details
        return f"SCHEMA_UNAVAILABLE: Error fetching schema - {str(e)}"
    except Exception as e: # Catch any other unexpected errors
        logger.error(f"Unexpected error while fetching schema: {e}", exc_info=True)
        return f"SCHEMA_UNAVAILABLE: Unexpected error - {str(e)}"
    finally:
        if cursor:
            cursor.close()


def decide_query_path_via_llm(
    user_query: str,
    llm_service: BaseLLMService, # type: ignore
    detailed_schema_str: str,
    max_retries: int = 1,
    model_name: Optional[str] = None
) -> str:
    """
    Uses an LLM to decide if a query is better suited for SQL, RAG, DQ, or visualization processing.
    """
    schema_to_use_in_prompt = detailed_schema_str
    if not detailed_schema_str or "SCHEMA_UNAVAILABLE" in detailed_schema_str or "Error" in detailed_schema_str:
        logger.warning("Detailed schema unavailable or contains error. Using basic fallback schema for decision.")
        schema_to_use_in_prompt = ADVENTUREWORKS_SCHEMA_FOR_LLM

    prompt = DECIDE_QUERY_PATH_PROMPT_TEMPLATE.format(
        schema_to_use_in_prompt=schema_to_use_in_prompt,
        user_query=user_query
    )

    logger.info(f"Sending query to LLM for path decision: '{user_query}'")

    for attempt in range(max_retries):
        try:
            response_text = llm_service.generate_text(
                prompt=prompt,
                model_name=model_name or settings.GEMINI_RAG_MODEL_NAME,  # Use provided model or fallback
                temperature=0.1
            )
            if response_text:
                # Extract the decision from the response
                match = re.search(r"ROUTE: (\w+)", response_text)
                if match:
                    decision = f"ROUTE: {match.group(1).upper()}"
                    logger.info(f"LLM decided path: {decision}")
                    return decision
            logger.warning(f"Could not determine query path from LLM response on attempt {attempt + 1}: {response_text}")
        except Exception as e:
            logger.error(f"Error during LLM path decision on attempt {attempt + 1}: {e}")

    # Fallback if all retries fail
    logger.warning("LLM path decision failed after all retries. Defaulting to SQL.")
    return "ROUTE: SQL"

def generate_sql_via_llm(
    user_query: str,
    llm_service: BaseLLMService,
    detailed_schema_str: str,
    max_retries: int = 1,
    model_name: Optional[str] = None
) -> Optional[str]:
    """
    Generates a SQL query from a user query using an LLM.
    """
    schema_to_use_in_prompt = detailed_schema_str
    if not detailed_schema_str or "SCHEMA_UNAVAILABLE" in detailed_schema_str or "Error" in detailed_schema_str:
        logger.warning("Detailed schema unavailable or contains error. Using basic fallback schema for SQL generation.")
        schema_to_use_in_prompt = ADVENTUREWORKS_SCHEMA_FOR_LLM
        
    prompt = GENERATE_SQL_PROMPT_TEMPLATE.format(
        detailed_schema_str=schema_to_use_in_prompt,
        user_query=user_query
    )

    logger.info(f"Sending query to LLM for SQL generation: '{user_query}'")
    
    for attempt in range(max_retries):
        try:
            raw_response = llm_service.generate_text(
                prompt=prompt,
                model_name=model_name or settings.GEMINI_SQL_MODEL_NAME,  # Use provided model or fallback
                temperature=0.1
            )
            
            # Use the LLM service's dedicated parser
            sql_query = llm_service.parse_sql_from_text(raw_response)

            if not sql_query:
                logger.warning(f"LLM did not return a valid SQL query on attempt {attempt + 1}: {raw_response}")
                if attempt >= max_retries - 1:
                    return None
                continue

            logger.info(f"LLM generated SQL: {sql_query}")
            return sql_query
        except Exception as e:
            logger.error(f"Error calling LLM for SQL generation (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt >= max_retries - 1:
                return None
    
    logger.error("Failed to generate SQL query after all retries.")
    return None


def execute_sql_query_pg(pg_conn: psycopg2.extensions.connection, sql_query: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    # ... (initial checks) ...
    logger.info(f"Executing SQL with psycopg2 cursor: {sql_query}")
    cursor = None
    try:
        cursor = pg_conn.cursor()
        cursor.execute(sql_query)
        
        if cursor.description is None: # No results, or not a SELECT query that returns rows
            logger.info("Query executed (psycopg2), but cursor has no description (no rows returned or not a SELECT).")
            # Create an empty DataFrame with expected columns if possible, or handle as no data
            # For this specific query, we expect 'standardcost'
            # If SQL was SELECT "standardcost" ..., col_name_from_sql = "standardcost"
            col_name_from_sql = sql_query.split(' ')[1].strip('"') # very naive way to get selected col
            df = pd.DataFrame(columns=[col_name_from_sql])
            return df, "The query executed successfully but returned no results."

        colnames = [desc[0] for desc in cursor.description]
        logger.info(f"PSYCOPG2 DEBUG: Column names from cursor: {colnames}")
        
        rows = cursor.fetchall()
        logger.info(f"PSYCOPG2 DEBUG: Fetched {len(rows)} rows.")

        if not rows:
            df = pd.DataFrame(columns=colnames) # Empty df with correct columns
            logger.info("Query executed successfully (psycopg2), but returned no rows.")
            return df, "The query executed successfully but returned no results."

        for i, row_tuple in enumerate(rows[:5]): # Log first few rows
            logger.info(f"PSYCOPG2 DEBUG: Row {i} data: {row_tuple}")
            if colnames and len(row_tuple) == len(colnames) and colnames[0] == 'standardcost':
                logger.info(f"PSYCOPG2 DEBUG: Value for 'standardcost' in row {i}: {repr(row_tuple[0])}")
                logger.info(f"PSYCOPG2 DEBUG: Type of value for 'standardcost' in row {i}: {type(row_tuple[0])}")


        df = pd.DataFrame(rows, columns=colnames)
        
        # --- DETAILED DATAFRAME DEBUGGING (After manual creation) ---
        logger.info(f"--- API SQL EXEC DataFrame Debug (from psycopg2 cursor) ---")
        logger.info(f"DataFrame shape: {df.shape}")
        logger.info(f"DataFrame columns: {df.columns.tolist()}")
        logger.info(f"DataFrame dtypes:\n{df.dtypes.to_string()}")
        if not df.empty:
            logger.info(f"DataFrame head (raw data):\n{df.head().to_string()}")
            target_col_name_in_df = "standardcost"
            if target_col_name_in_df in df.columns:
                first_row_value = df.iloc[0][target_col_name_in_df]
                logger.info(f"Value in '{target_col_name_in_df}' column for first row: {repr(first_row_value)}")
                logger.info(f"Type of value in '{target_col_name_in_df}' column for first row: {type(first_row_value)}")
                logger.info(f"Is '{target_col_name_in_df}' pd.isna() for first row? {pd.isna(first_row_value)}")
            else:
                logger.warning(f"Critical: '{target_col_name_in_df}' column NOT FOUND. Available: {df.columns.tolist()}")
        else:
            logger.info("DataFrame is empty.")
        logger.info(f"--- End API SQL EXEC DataFrame Debug (from psycopg2 cursor) ---")
        # --- END DETAILED DATAFRAME DEBUGGING ---

        return df, None
    except psycopg2.Error as e:
        # ... (your error handling) ...
        error_msg = f"PostgreSQL error during query execution (psycopg2): {e}"
        logger.error(error_msg, exc_info=True)
        return None, error_msg
    except Exception as e:
        # ... (your error handling) ...
        error_msg = f"An unexpected error occurred during SQL execution (psycopg2): {e}"
        logger.error(error_msg, exc_info=True)
        return None, error_msg
    finally:
        if cursor:
            cursor.close()


def format_sql_results_via_llm(
    sql_query: str,
    results_df: pd.DataFrame,
    user_query: str,
    llm_service: BaseLLMService = None,
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    OPTIMIZED: Uses programmatic formatting instead of LLM calls.
    This eliminates unnecessary token usage while providing the same output format.
    """
    logger.info("Using optimized result formatting (no LLM call)")
    return format_sql_results_optimized(sql_query, results_df, user_query)

import psycopg2
from collections import Counter
import json # Added for parsing LLM JSON response

logger = logging.getLogger(__name__)


def extract_entities_from_query(user_query: str, llm_service: BaseLLMService, schema_summary: str, model_name: Optional[str] = None) -> Optional[List[str]]:
    """
    Extracts table or entity names from the user query using an LLM.
    """
    prompt = EXTRACT_ENTITIES_PROMPT_TEMPLATE.format(
        schema_summary=schema_summary,
        user_query=user_query
    )
    logger.info(f"Extracting entities from query: '{user_query}'")
    try:
        response_text = llm_service.generate_text(
            prompt=prompt,
            model_name=model_name or settings.GEMINI_RAG_MODEL_NAME,  # Use provided model or fallback
            temperature=0.1
        )
        if response_text:
            # The LLM is prompted to return a JSON list
            parsed_json = llm_service.parse_json_from_text(response_text)
            if isinstance(parsed_json, list):
                logger.info(f"Extracted entities: {parsed_json}")
                return parsed_json
            else:
                 logger.warning(f"Could not parse entities list from LLM response: {response_text}")
    except Exception as e:
        logger.error(f"Error extracting entities: {e}")
    return None


async def generate_sql_and_entities_for_dq_rule(
    rule_description: str,
    llm_service: BaseLLMService,
    detailed_schema_str: str,
    max_retries: int = 1,
    model_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Asynchronously generates SQL and target entities for a DQ rule using an LLM.
    """
    # This function can be implemented similarly to the sync version but with async calls
    # For now, we'll just call the sync version in a thread to avoid blocking.
    return await asyncio.to_thread(
        generate_sql_and_entities_for_dq_rule_sync,
        rule_description, llm_service, detailed_schema_str, max_retries, None, model_name
    )

def generate_sql_and_entities_for_dq_rule_sync(
    rule_description: str,
    llm_service: BaseLLMService,
    detailed_schema_str: str,
    max_retries: int = 1,
    token_tracker: Optional['RequestTokenTracker'] = None,
    model_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Synchronously generates SQL and target entities for a DQ rule using an LLM.
    """
    prompt = GENERATE_DQ_SQL_PROMPT_TEMPLATE.format(
        detailed_schema_str=detailed_schema_str,
        rule_description=rule_description
    )
    logger.info(f"Attempting to generate SQL and entities for DQ rule (sync): '{rule_description[:100]}...' ")

    for attempt in range(max_retries):
        try:
            # Use streaming with token tracking if available
            if hasattr(llm_service, 'generate_text_streamed_with_usage'):
                response_generator = llm_service.generate_text_streamed_with_usage(
                    prompt=prompt,
                    model_name=model_name or settings.GEMINI_SQL_MODEL_NAME,  # Use provided model or fallback
                    temperature=0.1
                )
                
                response_parts = []
                for chunk, usage in response_generator:
                    if chunk:
                        response_parts.append(chunk)
                    if usage and token_tracker:
                        token_tracker.add_usage(usage)
                
                response_text = "".join(response_parts)
            else:
                # Fallback to non-streaming method
                response_text = llm_service.generate_text(
                    prompt=prompt,
                    model_name=model_name or settings.GEMINI_SQL_MODEL_NAME,  # Use provided model or fallback
                    temperature=0.1
                )
            if response_text:
                # The LLM is prompted to return a JSON object. We need to robustly parse it.
                match = re.search(r"```(?:json)?\s*({.*?})\s*```", response_text, re.DOTALL)
                if match:
                    json_str = match.group(1)
                else:
                    json_str = response_text.strip()

                try:
                    parsed_json = json.loads(json_str)
                    # Corrected validation to check for 'table' instead of 'target_table'
                    if parsed_json and 'sql_query' in parsed_json and 'table' in parsed_json:
                        logger.info(f"Successfully generated SQL and entities for DQ rule: {parsed_json}")
                        return parsed_json
                    else:
                        logger.warning(f"LLM response for DQ rule did not contain required keys on attempt {attempt + 1}: {parsed_json}")
                except json.JSONDecodeError:
                    logger.warning(f"Failed to decode JSON from LLM response for DQ rule on attempt {attempt + 1}: {response_text}")

        except Exception as e:
            logger.error(f"An unexpected error occurred during DQ rule SQL generation on attempt {attempt + 1}: {e}", exc_info=True)

    logger.error(f"Failed to generate SQL for DQ rule after {max_retries} retries.")
    return None


# ==============================================================================
# MAIN VISUALIZATION FUNCTION
# ==============================================================================

async def generate_visualization_json(
    user_query: str,
    llm_service: BaseLLMService,
    db_connection: psycopg2.extensions.connection,
    detailed_schema_str: str,
    max_retries: int = 1,
    model_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Generates a JSON object for graph visualization based on a user query.
    """
    prompt = GENERATE_VISUALIZATION_JSON_PROMPT_TEMPLATE.format(
        schema=detailed_schema_str,
        question=user_query
    )
    logger.info(f"Generating visualization JSON for query: '{user_query}'")

    for attempt in range(max_retries):
        try:
            response_text = llm_service.generate_text(
                prompt=prompt,
                model_name=model_name or settings.GEMINI_RAG_MODEL_NAME,  # Use provided model or fallback
                temperature=0.1
            )
            if response_text:
                # The LLM is prompted to return a JSON object
                parsed_json = llm_service.parse_json_from_text(response_text)
                if parsed_json and 'graph' in parsed_json:
                    logger.info("Successfully generated visualization JSON.")
                    return parsed_json
                else:
                    logger.warning(f"Could not parse visualization JSON from LLM response on attempt {attempt + 1}: {response_text}")
        except Exception as e:
            logger.error(f"Error generating visualization JSON on attempt {attempt + 1}: {e}")

    logger.error("Failed to generate visualization JSON after all retries.")
    return None