"""
Database Visualization and Entity Relationship Service Module
============================================================

This module provides intelligent database visualization capabilities, generating
interactive graph representations of database schemas and entity relationships
based on natural language queries and table analysis.

Key Features:
1. Automatic entity extraction from natural language queries
2. Dynamic database schema visualization generation
3. Table relationship mapping and graph structure creation
4. Smart table selection based on query context and centrality
5. JSON graph data generation for frontend visualization libraries

Visualization Components:
- Node Generation: Creates nodes for tables, columns, and relationships
- Edge Generation: Maps foreign key relationships and logical connections
- Layout Optimization: Provides positioning hints for graph rendering
- Query Context: Highlights relevant entities based on user queries

Integration Points:
- D3.js/Cytoscape.js compatible JSON output format
- React/Vue.js frontend component integration
- Interactive exploration of database relationships
- Query result correlation with schema visualization

Database Analysis:
- Centrality scoring for table importance ranking
- Relationship depth analysis for connected components
- Query-driven subgraph extraction for focused views

Author: Brain LLM Team
"""

import asyncio
from typing import Dict, Any, Optional, List
from collections import Counter
import psycopg2
import json
import logging
import re

from app.services.llm.base import BaseLLMService
from app.services.token_tracker import RequestTokenTracker
from app.services.db.base import BaseDatabaseService
from app.prompts.prompt_engineering import GENERATE_VISUALIZATION_JSON_PROMPT_TEMPLATE, EXTRACT_ENTITIES_PROMPT_TEMPLATE
from app.core.config import settings

# Module-level logger for visualization operations
logger = logging.getLogger(__name__)

class VisualizationService:
    """
    Service for generating database schema visualizations and entity relationship graphs.
    
    This service combines natural language processing with database introspection
    to create meaningful visual representations of data relationships. It uses
    LLM intelligence to understand query context and highlight relevant schema components.
    
    Core Capabilities:
    1. Query-driven entity extraction and table identification
    2. Dynamic schema visualization based on query context
    3. Graph data generation in JSON format for frontend rendering
    4. Table centrality analysis for importance ranking
    5. Relationship mapping with foreign key analysis
    
    Visualization Types:
    - Full schema overview: Complete database structure
    - Query-focused subgraphs: Relevant tables for specific queries
    - Entity relationship diagrams: Logical data model representation
    - Table dependency graphs: Foreign key relationship networks
    
    Integration:
    - Frontend JavaScript libraries (D3.js, Cytoscape.js, vis.js)
    - Interactive exploration interfaces
    - Query result contextualization
    """
    
    def __init__(self, llm_service: BaseLLMService, db_service: Optional[BaseDatabaseService] = None):
        """
        Initialize the visualization service with LLM capabilities and optional database service.
        
        Args:
            llm_service: The language model service for entity extraction and analysis
            db_service: Optional database service for multi-database support (defaults to None for backward compatibility)
        """
        self.llm_service = llm_service
        self.db_service = db_service  # Support for multi-database architecture

    def _get_db_connection(self, db_connection_info: Optional[Dict[str, Any]] = None):
        """
        Get database connection using the new unified service architecture or legacy PostgreSQL.
        
        Args:
            db_connection_info: Optional database connection info for multi-database support
            
        Returns:
            Database connection object
        """
        if db_connection_info:
            # NEW: Use unified database service for multi-database support
            from app.services.connection_manager import ConnectionManager
            connection_manager = ConnectionManager()
            
            # For visualization service, we need raw connections
            db_type = db_connection_info.get('db_type', 'postgresql')
            if db_type.lower() == 'postgresql':
                # Use existing raw PostgreSQL connection method for backward compatibility
                return connection_manager.get_raw_psycopg2_connection(db_connection_info)
            else:
                # For other database types, use the service-based approach
                for connection in connection_manager.get_connection_via_service(db_connection_info):
                    return connection
        else:
            # LEGACY: Default PostgreSQL connection for backward compatibility
            return psycopg2.connect(
                host=settings.PG_HOST,
                port=settings.PG_PORT,
                dbname=settings.PG_DATABASE_AW,
                user=settings.PG_USER,
                password=settings.PG_PASSWORD
            )

    async def generate_visualization_json(
        self, 
        query: str, 
        table_names: Optional[List[str]] = None,
        dynamic_llm_service: Optional[BaseLLMService] = None,
        dynamic_db_connection: Optional[psycopg2.extensions.connection] = None,
        db_connection_info: Optional[Dict[str, Any]] = None,  # NEW: Multi-database support
        provided_schema: Optional[str] = None,
        token_tracker: Optional[RequestTokenTracker] = None,
        model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates a JSON object for graph visualization based on a query.
        This version includes robust parsing to handle imperfect LLM output.
        
        Enhanced Multi-Database Support:
        - db_connection_info: Database connection parameters with db_type field
        - Supports PostgreSQL, MySQL, SQLite, Snowflake through unified interface
        - Backward compatible with existing dynamic_db_connection parameter
        """
        try:
            # Use dynamic services if provided, otherwise fall back to defaults
            llm_service_to_use = dynamic_llm_service if dynamic_llm_service else self.llm_service
            db_conn_to_use = dynamic_db_connection if dynamic_db_connection else None
            
            # Enhanced connection management with multi-database support
            should_close_connection = False
            connection_source = "default"
            
            # Step 1: Get schema and determine target tables
            detailed_schema_str = None
            
            # Use provided schema if available (highest priority)
            if provided_schema and provided_schema.strip():
                logger.info("Using pre-provided schema for visualization")
                detailed_schema_str = provided_schema
            elif db_conn_to_use:
                # Use provided dynamic connection to fetch schema
                logger.info("Fetching schema from dynamic database connection")
                detailed_schema_str = self.get_detailed_schema(db_conn_to_use)
                connection_source = "dynamic"
            elif db_connection_info:
                # NEW: Use multi-database service connection
                logger.info(f"Creating {db_connection_info.get('db_type', 'postgresql')} connection for visualization")
                db_conn_to_use = self._get_db_connection(db_connection_info)
                detailed_schema_str = self.get_detailed_schema(db_conn_to_use)
                should_close_connection = True
                connection_source = "service"
            else:
                # Use default connection (fallback)
                logger.info("Using default database connection to fetch schema")
                db_conn_to_use = self._get_db_connection()
                detailed_schema_str = self.get_detailed_schema(db_conn_to_use)
                should_close_connection = True
                connection_source = "legacy"
            
            # Continue with target table determination
            target_tables = []
            if table_names:
                target_tables = table_names
            else:
                schema_summary = "\n".join([line.replace("Table:", "").strip() 
                                       for line in detailed_schema_str.split('\n') 
                                       if line.startswith('Table:')])
                extracted_tables = await asyncio.to_thread(self.extract_entities_from_query, query, schema_summary, llm_service_to_use, token_tracker, model_name)
                # Fallback if extraction fails or returns invalid
                if not extracted_tables or extracted_tables == ['""'] or extracted_tables == ['']:
                    logger.info("Entity extraction failed or returned invalid, using all tables fallback.")
                    # Need a connection for fallback table selection
                    fallback_conn = db_conn_to_use if db_conn_to_use else None
                    fallback_should_close = False
                    
                    if not fallback_conn:
                        if db_connection_info:
                            fallback_conn = self._get_db_connection(db_connection_info)
                        else:
                            fallback_conn = self._get_db_connection()
                        fallback_should_close = True
                    try:
                        target_tables = await asyncio.to_thread(self.get_top_n_central_tables, fallback_conn, 50)
                    finally:
                        if fallback_conn and not db_conn_to_use:
                            fallback_conn.close()
                else:
                    target_tables = extracted_tables
                    logger.info(f"Successfully extracted target tables: {target_tables}")
            
            # Check if we have target tables (common for both paths)
            if not target_tables:
                return {
                    "answer_text": "Failed to identify relevant tables for visualization.",
                    "visualization_data": {"graph": {"nodes": [], "edges": []}}
                }

            # Step 2: Build focused schema (common for both paths)
            focused_schema_parts = ["Database Schema Description (Focused View):\n"]
            table_lines_buffer = {}
            current_table = None
            for line in detailed_schema_str.split('\n'):
                if line.startswith('Table:'):
                    current_table = line.replace('Table:', '').strip()
                    table_lines_buffer[current_table] = [line]
                elif current_table:
                    table_lines_buffer[current_table] = table_lines_buffer.get(current_table, []) + [line]
            for table_name in target_tables:
                if table_name in table_lines_buffer:
                    focused_schema_parts.extend(table_lines_buffer[table_name])
            focused_schema_str = "\n".join(focused_schema_parts)

            # Step 3: Generate text from LLM with clear JSON instructions (common for both paths)
            prompt = GENERATE_VISUALIZATION_JSON_PROMPT_TEMPLATE.format(focused_schema_str=focused_schema_str, user_query=query)
            logger.info(f"Generating visualization for tables: {target_tables}")
            
            # Use streaming with token tracking if available
            if hasattr(llm_service_to_use, 'generate_text_streamed_with_usage'):
                response_generator = llm_service_to_use.generate_text_streamed_with_usage(
                    prompt=prompt,
                    model_name=model_name or settings.GEMINI_SQL_MODEL_NAME,  # Use provided model or fallback
                    temperature=0.0
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
                response_text = await asyncio.to_thread(
                    llm_service_to_use.generate_text,
                    prompt=prompt,
                    model_name=model_name or settings.GEMINI_SQL_MODEL_NAME,  # Use provided model or fallback
                    temperature=0.0
                )

            # --- ROBUST JSON EXTRACTION LOGIC ---
            logger.debug(f"Raw LLM response for visualization:\n---\n{response_text[:500]}...\n---")

            # Clean up the response text to handle common JSON issues
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '', 1).strip()
            if response_text.endswith('```'):
                response_text = response_text[:-3].strip()

            json_start_index = response_text.find('{')
            json_end_index = response_text.rfind('}')

            if json_start_index == -1 or json_end_index == -1:
                raise ValueError("Could not find a JSON object in the LLM's response.")

            json_string = response_text[json_start_index : json_end_index + 1]
            try:
                visualization_data = json.loads(json_string)
                if not isinstance(visualization_data, dict):
                    raise ValueError("Visualization data must be a JSON object")
                graph_data = visualization_data.get('graph', {})
                if not isinstance(graph_data, dict):
                    raise ValueError("Graph data must be a JSON object")
                nodes = graph_data.get('nodes', [])
                edges = graph_data.get('edges', [])
                if not isinstance(nodes, list) or not isinstance(edges, list):
                    raise ValueError("Nodes and edges must be arrays")
            except json.JSONDecodeError as je:
                logger.warning(f"Initial JSON parsing failed: {je}. Attempting to clean the JSON string.")
                json_string = json_string.replace('\\"', '"')
                json_string = re.sub(r',(\s*[}\]])', r'\1', json_string)
                visualization_data = json.loads(json_string)
            
            # Successful completion - return visualization data
            result = {
                "answer_text": "Here's a visualization of the database schema you requested.",
                "strategy_used": "VISUALIZE",
                "retrieved_sources": [],
                "generated_sql_logged": None,
                "visualization_data": visualization_data,
                "table_data": None
            }
            
            return result
        except (json.JSONDecodeError, ValueError) as e:
            error_msg = str(e)
            logger.error(f"Failed to generate or parse visualization JSON: {error_msg}\nLLM output (first 500 chars): {response_text[:500] if 'response_text' in locals() else ''}", exc_info=True)
            return {
                "answer_text": f"Error generating visualization: {error_msg}",
                "strategy_used": "VISUALIZE",
                "retrieved_sources": [],
                "generated_sql_logged": None,
                "visualization_data": {"graph": {"nodes": [], "edges": []}},
                "table_data": None
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"An unexpected error occurred during visualization generation: {error_msg}", exc_info=True)
            return {
                "answer_text": f"An unexpected error occurred: {error_msg}",
                "strategy_used": "VISUALIZE",
                "retrieved_sources": [],
                "generated_sql_logged": None,
                "visualization_data": {"graph": {"nodes": [], "edges": []}},
                "table_data": None
            }
        finally:
            # Clean up database connections
            if should_close_connection and db_conn_to_use and connection_source in ["service", "legacy"]:
                try:
                    if hasattr(db_conn_to_use, 'close'):
                        db_conn_to_use.close()
                        logger.info(f"Closed {connection_source} database connection")
                except Exception as cleanup_e:
                    logger.warning(f"Error closing database connection: {cleanup_e}")

    def get_schema_for_tables(self, db_conn, table_names: List[str]) -> str:
        """
        Fetches the schema details for a specific list of tables including relationships.
        """
        if not table_names:
            return "No tables specified."

        schema_details = []
        try:
            with db_conn.cursor() as cursor:
                # First get the table details
                for table_name in table_names:
                    table_parts = table_name.split('.')
                    if len(table_parts) == 2:
                        schema, tbl = table_parts
                        cursor.execute("""
                            SELECT column_name, data_type, is_nullable 
                            FROM information_schema.columns 
                            WHERE table_schema = %s AND table_name = %s
                            ORDER BY ordinal_position
                        """, (schema, tbl))
                    else:
                        cursor.execute("""
                            SELECT column_name, data_type, is_nullable 
                            FROM information_schema.columns 
                            WHERE table_name = %s
                            ORDER BY ordinal_position
                        """, (table_name,))
                    
                    columns = cursor.fetchall()
                    col_details = []
                    for col in columns:
                        col_name = col['column_name']
                        col_type = col['data_type']
                        is_null = col['is_nullable']
                        nullable_str = "NULL" if is_null == "YES" else "NOT NULL"
                        col_details.append(f"  {col_name} {col_type} {nullable_str}")
                    
                    schema_details.append(f"Table: {table_name}")
                    schema_details.append("Columns:")
                    schema_details.extend(col_details)
                
                # Now get foreign key relationships
                cursor.execute("""
                SELECT
                    format('%s.%s', kcu.table_schema, kcu.table_name) AS source_table,
                    kcu.column_name AS source_column,
                    format('%s.%s', ccu.table_schema, ccu.table_name) AS target_table,
                    ccu.column_name AS target_column
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND (
                    kcu.table_schema || '.' || kcu.table_name = ANY(%s) 
                    OR ccu.table_schema || '.' || ccu.table_name = ANY(%s)
                );
                """, (table_names, table_names))
                
                relationships = cursor.fetchall()
                if relationships:
                    schema_details.append("\nRelationships:")
                    for rel in relationships:
                        source_table = rel['source_table']
                        source_column = rel['source_column']
                        target_table = rel['target_table']
                        target_column = rel['target_column']
                        schema_details.append(f"  {source_table}.{source_column} -> {target_table}.{target_column}")
            
            return "\n".join(schema_details)
        except psycopg2.Error as e:
            logger.error(f"Database error in get_schema_for_tables: {e}")
            return f"Error fetching schema: {str(e)}"

    def extract_entities_from_query(self, query: str, schema_summary: str, llm_service: Optional[BaseLLMService] = None, token_tracker: Optional[RequestTokenTracker] = None, model_name: Optional[str] = None) -> List[str]:
        """
        Extract specific tables from the user query using LLM
        """
        try:
            # Use provided LLM service or fall back to default
            llm_service_to_use = llm_service if llm_service else self.llm_service
            
            prompt = EXTRACT_ENTITIES_PROMPT_TEMPLATE.format(
                user_query=query,
                schema_summary=schema_summary
            )
            
            # Use streaming with token tracking if available
            if hasattr(llm_service_to_use, 'generate_text_streamed_with_usage'):
                response_generator = llm_service_to_use.generate_text_streamed_with_usage(
                    prompt=prompt,
                    model_name=model_name or settings.GEMINI_RAG_MODEL_NAME,  # Use provided model or fallback
                    temperature=0.0
                )
                
                response_parts = []
                for chunk, usage in response_generator:
                    if chunk:
                        response_parts.append(chunk)
                    if usage and token_tracker:
                        token_tracker.add_usage(usage)
                
                response = "".join(response_parts)
            else:
                # Fallback to non-streaming method
                response = llm_service_to_use.generate_text(
                    prompt=prompt,
                    model_name=model_name or settings.GEMINI_RAG_MODEL_NAME,  # Use provided model or fallback
                    temperature=0.0
                )
            
            if not response or response.strip() == "":
                logger.info("No entities extracted from query")
                return []
                
            entities = [entity.strip() for entity in response.split(',') if entity.strip()]
            logger.info(f"Extracted entities from query: {entities}")
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting entities from query: {e}")
            return []
            
    def get_top_n_central_tables(self, db_conn, n: int = 12) -> List[str]:
        """
        Analyzes the entire database's foreign key graph to find the most "central" tables.
        """
        logger.info(f"Calculating centrality for all tables to find the top {n}...")
        try:
            # Use a dict cursor for easier data access
            with db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                fk_query = """
                SELECT
                    format('%s.%s', kcu.table_schema, kcu.table_name) AS source_table,
                    format('%s.%s', ccu.table_schema, ccu.table_name) AS target_table
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema NOT IN ('pg_catalog', 'information_schema');
                """
                
                cursor.execute(fk_query)
                relationships = cursor.fetchall()
                if not relationships:
                    logger.warning("No foreign key relationships found.")
                    return []
                
                logger.info(f"Found {len(relationships)} foreign key relationships in the database.")

                # Count table occurrences to determine centrality
                centrality_counter = Counter(
                    table_name
                    for row in relationships
                    for table_name in (row['source_table'], row['target_table'])
                )

                top_tables = [table for table, count in centrality_counter.most_common(n)]
                logger.info(f"Top {len(top_tables)} most central tables identified: {top_tables}")
                return top_tables
                
        except Exception as e:
            logger.error(f"Failed to calculate table centrality: {e}", exc_info=True)
            return []

    def get_detailed_schema(self, db_conn) -> str:
        """
        Get detailed database schema for the entire database
        """
        try:
            schema_parts = ["Database Schema Description:"]
            
            with db_conn.cursor() as cursor:
                # Get tables
                cursor.execute("""
                    SELECT table_schema, table_name
                    FROM information_schema.tables
                    WHERE table_type = 'BASE TABLE'
                    AND table_schema NOT IN ('pg_catalog', 'information_schema')
                    ORDER BY table_schema, table_name
                """)
                
                tables = cursor.fetchall()
                
                for table_row in tables:
                    schema = table_row['table_schema']
                    table = table_row['table_name']
                    schema_parts.append(f"\nTable: {schema}.{table}")
                    
                    # Get columns
                    cursor.execute("""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns
                        WHERE table_schema = %s AND table_name = %s
                        ORDER BY ordinal_position
                    """, (schema, table))
                    
                    schema_parts.append("Columns:")
                    for col_row in cursor.fetchall():
                        col_name = col_row['column_name']
                        data_type = col_row['data_type']
                        nullable = col_row['is_nullable']
                        nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
                        schema_parts.append(f"  {col_name} {data_type} {nullable_str}")
                
                # Get foreign key relationships
                cursor.execute("""
                SELECT
                    format('%s.%s', kcu.table_schema, kcu.table_name) AS source_table,
                    kcu.column_name AS source_column,
                    format('%s.%s', ccu.table_schema, ccu.table_name) AS target_table,
                    ccu.column_name AS target_column
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_schema NOT IN ('pg_catalog', 'information_schema');
                """)
                
                relationships = cursor.fetchall()
                if relationships:
                    schema_parts.append("\nRelationships:")
                    for rel in relationships:
                        source_table = rel['source_table']
                        source_column = rel['source_column']
                        target_table = rel['target_table']
                        target_column = rel['target_column']
                        schema_parts.append(f"  {source_table}.{source_column} -> {target_table}.{target_column}")
            
            return "\n".join(schema_parts)
        except Exception as e:
            logger.error(f"Error getting detailed database schema: {e}")
            return "Error fetching schema."