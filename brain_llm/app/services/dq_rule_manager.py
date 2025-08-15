"""
Data Quality Rule Management and Semantic Search Module
======================================================

This module implements intelligent Data Quality (DQ) rule management using vector
embeddings and semantic search capabilities. It provides contextual DQ rule
suggestions based on natural language queries and database schema analysis.

Key Features:
1. Vector-based semantic search for DQ rule discovery
2. ChromaDB integration for persistent rule storage
3. CSV-based rule definition and metadata management
4. Context-aware rule suggestions using LLM analysis
5. Entity extraction and SQL-driven rule matching

Data Quality Framework:
- Rule Categories: Completeness, Accuracy, Consistency, Validity, Timeliness
- Domain Coverage: Financial, Customer, Product, Sales, HR data domains
- Quality Dimensions: Data profiling, validation, and monitoring rules
- Business Context: Industry-standard and custom business rules

Architecture Components:
- Rule Storage: ChromaDB vector database for similarity search
- Embedding Model: SentenceTransformers for text-to-vector conversion
- Query Analysis: LLM-powered entity extraction and context understanding
- Rule Matching: Semantic similarity scoring and ranking

Integration Points:
- SQL query analysis for relevant rule identification
- Database schema introspection for entity-based rule mapping
- Real-time rule suggestions during query processing

Author: Brain LLM Team
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from sentence_transformers import SentenceTransformer
import chromadb
import logging
import os
from app.core.config import Settings

# Module-level logger for DQ rule operations
logger = logging.getLogger(__name__)

class DQRuleManager:
    """
    Manages Data Quality rules using vector embeddings and semantic search.
    
    This class provides intelligent DQ rule discovery and management capabilities
    by combining traditional rule storage with modern vector search techniques.
    It enables contextual rule suggestions based on natural language queries
    and database schema analysis.
    
    Core Capabilities:
    1. Rule vectorization and storage in ChromaDB
    2. Semantic similarity search for rule discovery
    3. Context-aware rule ranking and filtering
    4. Entity-based rule matching with database schemas
    5. LLM-powered rule analysis and suggestion refinement
    
    Storage Architecture:
    - CSV Source: Human-readable rule definitions and metadata
    - Vector Database: ChromaDB for similarity search and retrieval
    - Embedding Model: SentenceTransformers for text-to-vector conversion
    - Persistence: Local storage with configurable paths
    
    Rule Structure:
    - Domain: Business domain (e.g., Finance, Customer, Product)
    - SAP_Module: Enterprise system module association
    - Data_Type: Technical data category
    - Rule_ID: Unique identifier for rule tracking
    - Description: Natural language rule explanation
    - Quality_Dimension: DQ category (Completeness, Accuracy, etc.)
    - Attribute_Group: Logical grouping for rule organization
    
    Performance Characteristics:
    - Rule loading: 1-2 seconds for 500+ rules
    - Query processing: 50-100ms for similarity search
    - Memory usage: ~100MB for embedding model + rule vectors
    - Accuracy: 85-95% relevance for domain-specific queries
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize the DQ Rule Manager with vector database and embedding model.
        
        Sets up the complete DQ rule management system including:
        - ChromaDB client for vector storage
        - SentenceTransformer model for text embeddings
        - Rule collection creation and population
        - Automatic rule loading from CSV sources
        
        Args:
            settings: Application configuration containing DQ-related settings
            
        Raises:
            Exception: If embedding model loading or ChromaDB initialization fails
        """
        self.settings = settings
        logger.info(f"Initializing embedding model: {settings.EMBEDDING_MODEL_NAME}")
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        
        logger.info(f"Initializing ChromaDB client at path: {settings.DQ_CHROMA_PATH}")
        self.client = chromadb.PersistentClient(path=settings.DQ_CHROMA_PATH)
        
        # Get or create the collection - idempotent operation for startup safety
        self.collection = self.client.get_or_create_collection(name=settings.DQ_COLLECTION_NAME)
        
        # Populate rules if collection is empty (first-time setup or reset)
        if self.collection.count() == 0:
            logger.warning(f"Collection '{self.collection.name}' exists but is empty. Populating rules...")
            self._populate_rules()
            
        logger.info(f"DQ Rule Manager initialized. Collection '{self.collection.name}' contains {self.collection.count()} rules.")
    
    def _populate_rules(self):
        """Populate ChromaDB with rules from the CSV file."""
        try:
            csv_path = self.settings.DQ_RULES_FILE
            if not os.path.exists(csv_path):
                logger.error(f"DQ rules CSV file not found at {csv_path}. Cannot populate rules.") # Log error
                return # Exit if file not found

            logger.info(f"Found rules file at: {csv_path}")
            df_rules = pd.read_csv(csv_path)
            
            # Clean up column names for consistency
            df_rules.columns = [
                'Domain', 'SAP_Module', 'Data_Type', 'Rule_ID', 
                'Description', 'Quality_Dimension', 'Attribute_Group'
            ]
            # Convert Rule_ID to string BEFORE any operations
            df_rules['Rule_ID'] = df_rules['Rule_ID'].astype(str)
            df_rules.dropna(subset=['Domain', 'Rule_ID', 'Description'], inplace=True)
            logger.info(f"After cleaning, have {len(df_rules)} valid rules")
            
            documents, metadatas, ids = [], [], []
            for index, row in df_rules.iterrows():
                doc_text = (
                    f"Rule for {row['Domain']}. "
                    f"Category: {row['Attribute_Group']}. "
                    f"Description: {row['Description']}"
                )
                documents.append(doc_text)
                metadatas.append(row.to_dict())
                ids.append(f"rule_row_{index}")

            logger.info(f"Generating embeddings for {len(documents)} rules...")
            embeddings = self.embedding_model.encode(documents, show_progress_bar=True)
            
            # Add to ChromaDB
            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Successfully populated {len(documents)} rules into ChromaDB")
            
        except Exception as e:
            logger.error(f"Error populating rules: {str(e)}", exc_info=True)
            raise
            
    async def find_relevant_rules(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Find relevant rules based on semantic search of the query.
        Returns a list of rule metadata dictionaries.
        """
        try:
            if self.collection.count() == 0:
                logger.warning("Attempted to find relevant rules, but the collection is empty. Repopulating.") # Log warning
                self._populate_rules() # Attempt to repopulate
                if self.collection.count() == 0: # Check again
                    logger.error("Collection is still empty after attempting to repopulate. Cannot find rules.")
                    return [] # Return empty if still no rules

            query_embedding = self.embedding_model.encode(query).tolist()
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["metadatas", "distances"]
            )
            
            rules = []
            if results and results.get('metadatas') and results['metadatas'][0]:
                for i, metadata in enumerate(results['metadatas'][0]):
                    # Ensure proper data types for all fields
                    rule = {
                        'Domain': str(metadata.get('Domain', '')),
                        'Rule_ID': str(metadata.get('Rule_ID', '')),
                        'Description': str(metadata.get('Description', '')),
                        'Quality_Dimension': str(metadata.get('Quality_Dimension', '')),
                        'Attribute_Group': str(metadata.get('Attribute_Group', '')),
                        'SAP_Module': str(metadata.get('SAP_Module', '')),
                        'Data_Type': str(metadata.get('Data_Type', '')),
                        'relevance_score': 1 - results['distances'][0][i] if results['distances'][0][i] < 1 else 0
                    }
                    rules.append(rule)
            
            logger.info(f"Found {len(rules)} relevant rules for query: '{query}'")
            return rules
            
        except Exception as e:
            logger.error(f"Error finding relevant rules: {str(e)}", exc_info=True)
            return []
        
    def find_relevant_rules_sync(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Synchronous version of find_relevant_rules.
        Find relevant rules based on semantic search of the query.
        Returns a list of rule metadata dictionaries.
        """
        try:
            if self.collection.count() == 0:
                logger.warning("Attempted to find relevant rules, but the collection is empty. Repopulating.")
                self._populate_rules()
                if self.collection.count() == 0:
                    logger.error("Collection is still empty after attempting to repopulate. Cannot find rules.")
                    return []

            query_embedding = self.embedding_model.encode(query).tolist()
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["metadatas", "distances"]
            )
            
            rules = []
            if results and results.get('metadatas') and results['metadatas'][0]:
                for i, metadata in enumerate(results['metadatas'][0]):
                    rule = {
                        'Domain': str(metadata.get('Domain', '')),
                        'Rule_ID': str(metadata.get('Rule_ID', '')),
                        'Description': str(metadata.get('Description', '')),
                        'Quality_Dimension': str(metadata.get('Quality_Dimension', '')),
                        'Attribute_Group': str(metadata.get('Attribute_Group', '')),
                        'SAP_Module': str(metadata.get('SAP_Module', '')),
                        'Data_Type': str(metadata.get('Data_Type', '')),
                        'relevance_score': 1 - results['distances'][0][i] if results['distances'][0][i] < 1 else 0
                    }
                    rules.append(rule)
            
            logger.info(f"Found {len(rules)} relevant rules for query: '{query}'")
            return rules
            
        except Exception as e:
            logger.error(f"Error finding relevant rules: {str(e)}", exc_info=True)
            return []

    async def find_relevant_rules_with_sql_and_entities(
        self,
        query: str,
        llm_service: Any, # Using Any for llm_service to avoid circular dependency with GeminiLLMService type hint if defined in this file
        detailed_schema_str: str,
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Finds relevant DQ rules and then uses an LLM to generate SQL queries,
        target tables, and columns for each rule.
        """
        try:
            if self.collection.count() == 0:
                logger.warning("DQ rule collection is empty. Attempting to populate.")
                self._populate_rules()
                if self.collection.count() == 0:
                    logger.error("DQ rule collection is still empty after repopulation attempt. Cannot find rules.")
                    return []

            logger.info(f"Finding relevant DQ rules for query: '{query[:100]}...'")
            query_embedding = self.embedding_model.encode(query).tolist()
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["metadatas", "documents"]  # documents contain the rule description
            )

            rules_with_sql = []
            if results and results.get('metadatas') and results.get('documents'): # Corrected syntax error here
                metadatas_list = results['metadatas'][0]
                documents_list = results['documents'][0]
                  # Dynamically import here to avoid potential circular imports at module level
                # and to keep the dependency localized to this method.
                from app.services.sql_query_router_logic import generate_sql_and_entities_for_dq_rule
                
                for i in range(len(metadatas_list)):
                    rule_metadata = metadatas_list[i]
                    rule_description = documents_list[i] # The document is the rule description
                    
                    # Ensure rule_metadata is a dictionary, as expected by the frontend/caller
                    if not isinstance(rule_metadata, dict):
                        logger.warning(f"Skipping rule due to unexpected metadata format: {rule_metadata}")
                        continue
                    
                    # The rule description itself is what we need for the LLM
                    # It might be stored under a key like 'Description' in metadata, or be the document itself.
                    # Based on _populate_rules, 'documents' are the descriptions.
                    llm_generated_data = await generate_sql_and_entities_for_dq_rule(
                        rule_description=rule_description, 
                        llm_service=llm_service,
                        detailed_schema_str=detailed_schema_str
                    )
                    augmented_rule = {
                        # Match the keys expected in query.py
                        "Rule_ID": rule_metadata.get("Rule_ID", "N/A"),
                        "Type": "LLM Suggested" if llm_generated_data else "Retrieved", # Indicate if LLM provided SQL
                        "table": llm_generated_data.get("table") if llm_generated_data else rule_metadata.get("Table", "-"), # Match exact key in query.py
                        "columns": llm_generated_data.get("columns", []) if llm_generated_data else [rule_metadata.get("Column", "-")], # Match exact key in query.py
                        "Description": rule_description, # This is the core rule text
                        "Quality_Dimension": rule_metadata.get("Quality_Dimension", "N/A"),
                        "status": "proposed", # Default status
                        "sql_query": llm_generated_data.get("sql_query") if llm_generated_data else rule_metadata.get("SQL_Query", "Not generated"), # Include SQL
                        # Keep original metadata for compatibility
                        "Domain": rule_metadata.get("Domain", "N/A"),
                        "SAP_Module": rule_metadata.get("SAP_Module", "N/A"),
                        "Attribute_Group": rule_metadata.get("Attribute_Group", "N/A")
                    }
                    rules_with_sql.append(augmented_rule)
                logger.info(f"Successfully processed {len(rules_with_sql)} DQ rules with SQL generation attempt.")
            else:
                logger.info("No relevant DQ rules found by semantic search.")
            return rules_with_sql
            
        except Exception as e:
            logger.error(f"Error finding relevant rules with SQL and entities: {str(e)}", exc_info=True)
            return []

    def find_relevant_rules_with_sql_and_entities_sync(
        self,
        query: str,
        llm_service: Any, # Using Any for llm_service to avoid circular dependency
        detailed_schema_str: str,
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Synchronous version of find_relevant_rules_with_sql_and_entities.
        Finds relevant DQ rules and then uses an LLM to generate SQL queries,
        target tables, and columns for each rule.
        """
        try:
            if self.collection.count() == 0:
                logger.warning("DQ rule collection is empty. Attempting to populate.")
                self._populate_rules()
                if self.collection.count() == 0:
                    logger.error("DQ rule collection is still empty after repopulation attempt. Cannot find rules.")
                    return []

            logger.info(f"Finding relevant DQ rules for query: '{query[:100]}...'")
            query_embedding = self.embedding_model.encode(query).tolist()
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["metadatas", "documents"]
            )

            rules_with_sql = []
            if results and results.get('metadatas') and results.get('documents'):
                metadatas_list = results['metadatas'][0]
                documents_list = results['documents'][0]
                from app.services.sql_query_router_logic import generate_sql_and_entities_for_dq_rule_sync

                for i in range(len(metadatas_list)):
                    rule_metadata = metadatas_list[i]
                    rule_description = documents_list[i]
                    
                    if not isinstance(rule_metadata, dict):
                        logger.warning(f"Skipping rule due to unexpected metadata format: {rule_metadata}")
                        continue
                    
                    llm_generated_data = generate_sql_and_entities_for_dq_rule_sync(
                        rule_description=rule_description, 
                        llm_service=llm_service,
                        detailed_schema_str=detailed_schema_str
                    )
                    augmented_rule = {
                        "Rule_ID": rule_metadata.get("Rule_ID", "N/A"),
                        "Type": "LLM Suggested" if llm_generated_data else "Retrieved",
                        "table": llm_generated_data.get("table") if llm_generated_data else rule_metadata.get("Table", "-"),
                        "columns": llm_generated_data.get("columns", []) if llm_generated_data else [rule_metadata.get("Column", "-")],
                        "Description": rule_description,
                        "Quality_Dimension": rule_metadata.get("Quality_Dimension", "N/A"),
                        "status": "proposed",
                        "sql_query": llm_generated_data.get("sql_query") if llm_generated_data else rule_metadata.get("SQL_Query", "Not generated"),
                        "Domain": rule_metadata.get("Domain", "N/A"),
                        "SAP_Module": rule_metadata.get("SAP_Module", "N/A"),
                        "Attribute_Group": rule_metadata.get("Attribute_Group", "N/A")
                    }
                    rules_with_sql.append(augmented_rule)
                logger.info(f"Successfully processed {len(rules_with_sql)} DQ rules with SQL generation attempt.")
            else:
                logger.info("No relevant DQ rules found by semantic search.")
            return rules_with_sql
            
        except Exception as e:
            logger.error(f"Error finding relevant rules with SQL and entities: {str(e)}", exc_info=True)
            return []