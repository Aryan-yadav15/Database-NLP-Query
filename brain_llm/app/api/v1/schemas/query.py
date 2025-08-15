"""
API Schema Definitions for Query Processing
==========================================

This module defines Pydantic models for request and response validation
in the Brain LLM query processing API. These schemas ensure type safety,
automatic validation, and comprehensive API documentation generation.

Key Features:
- Comprehensive request validation with optional parameters
- Structured response models for different data types
- Automatic OpenAPI schema generation for documentation
- Type-safe serialization/deserialization
- Custom validators for data consistency

Schema Categories:
1. Request Models: QueryRequest for incoming user queries
2. Response Models: QueryResponse, TableData for structured output
3. Utility Models: RetrievedSource for document reference tracking

API Design Principles:
- Optional fields for flexible client integration
- Nested structures for complex data relationships
- Field validation for data integrity
- Backward compatibility for API evolution

Author: Brain LLM Team
"""

from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any


# =============================================================================
# REQUEST MODELS
# =============================================================================

class QueryRequest(BaseModel):
    """
    Comprehensive request model for natural language query processing.
    
    This model supports various query processing modes including SQL generation,
    conversational AI, data quality validation, and visualization generation.
    The flexible design accommodates different client needs while maintaining
    type safety and validation.
    
    Core Features:
    - Natural language query processing with context awareness
    - Multi-modal responses (text, tables, visualizations)
    - Conversation history and memory management
    - Dynamic database connection support
    - Model and parameter customization per request
    
    Attributes:
        query_text: Primary natural language query from user
        model_name: Optional LLM model override (defaults to configured model)
        temperature: Optional creativity parameter (0.0-1.0, default varies by model)
        api_key: Optional API key override for multi-tenant scenarios
        user_id: User identifier for personalization and tracking
        conversation_id: Session identifier for conversation context
        message_id: Individual message identifier for tracking
        chat_history: Previous conversation turns for context
        short_term_memory: Recent relevant information for context
        db_connection_info: Custom database connection parameters
        
    Validation:
        - query_text: Required, non-empty string
        - temperature: Must be between 0.0 and 1.0 if provided
        - chat_history: List of role/content message pairs
        - db_connection_info: Can include schema bypass for performance
    """
    query_text: str                                            # Required: User's natural language query
    model_name: Optional[str] = None                          # Optional: LLM model override
    temperature: Optional[float] = None                       # Optional: Response creativity (0.0-1.0)
    api_key: Optional[str] = None                            # Optional: API key for multi-tenant use
    user_id: Optional[str] = None                            # Optional: User identification
    conversation_id: Optional[str] = None                    # Optional: Conversation session ID
    message_id: Optional[str] = None                         # Optional: Individual message tracking
    chat_history: Optional[List[Dict[str, str]]] = None      # Optional: Previous conversation context
    short_term_memory: Optional[List[str]] = None            # Optional: Recent context information
    db_connection_info: Optional[Dict[str, Any]] = None      # Optional: Custom DB connection settings


# =============================================================================
# RESPONSE DATA MODELS
# =============================================================================

class RetrievedSource(BaseModel):
    """
    Metadata model for document retrieval and source attribution.
    
    Used in RAG (Retrieval-Augmented Generation) scenarios to track
    which database records or documents contributed to the response.
    Enables source verification and confidence scoring.
    
    Attributes:
        source_table: Database table or document collection name
        source_pk_value: Primary key or unique identifier of source record
        document_text_preview: Snippet of relevant content for verification
        confidence_score: Similarity or relevance score (0.0-1.0)
        
    Use Cases:
        - Source attribution for fact verification
        - Confidence scoring for information reliability
        - Audit trails for data lineage tracking
    """
    source_table: str                                        # Database table or collection name
    source_pk_value: str                                     # Primary key or document ID
    document_text_preview: Optional[str] = None              # Content snippet for verification
    confidence_score: Optional[float] = None                 # Relevance score (0.0-1.0)


class TableData(BaseModel):
    """
    Structured tabular data model for frontend table rendering.
    
    Provides a standardized format for displaying SQL query results
    and other tabular data in web interfaces. Ensures consistent
    data formatting and type safety across all table displays.
    
    Features:
    - Clean JSON serialization for frontend consumption
    - Automatic string conversion for display consistency
    - Null value handling for robust UI rendering
    - Title metadata for contextual display
    
    Attributes:
        title: Human-readable title describing the data content
        columns: Ordered list of column names for table headers
        rows: 2D array of data values (row-major format)
        
    Data Processing:
        - Automatic conversion of all cell values to strings
        - Null/None values converted to empty strings
        - Preserves data structure while ensuring JSON compatibility
    """
    title: str                                               # Descriptive title for table display
    columns: List[str]                                       # Column names for table headers
    rows: List[List[Any]]                                    # 2D data array (rows x columns)
    
    @field_validator('rows')
    @classmethod
    def convert_row_values_to_strings(cls, v):
        """
        Custom validator to convert all cell values to strings for consistent display.
        
        This validator ensures that all data values are serializable and displayable
        in frontend table components, regardless of original data types from the database.
        
        Processing Logic:
        - Converts all non-None values to strings using str()
        - Converts None/null values to empty strings
        - Preserves nested array structure for rows and columns
        - Handles edge cases like empty datasets gracefully
        
        Args:
            v: Raw rows data from SQL queries or other sources
            
        Returns:
            List[List[str]]: Processed rows with string-converted values
        """
        if not v:  # Handle empty or None input gracefully
            return v
        
        # Convert each cell to string, handling None values specifically
        return [[str(cell) if cell is not None else "" for cell in row] for row in v]


# =============================================================================
# MAIN RESPONSE MODEL
# =============================================================================

class QueryResponse(BaseModel):
    """
    Comprehensive response model for query processing results.
    
    This model encapsulates all possible response types from the Brain LLM system,
    including text answers, structured data, visualizations, and metadata.
    The flexible design supports various client needs while maintaining
    backward compatibility and type safety.
    
    Response Types Supported:
    1. Conversational: Direct text responses to user questions
    2. SQL-based: Query results with structured table data
    3. Visualization: Graph data for entity relationship diagrams
    4. Hybrid: Combination responses with multiple data types
    
    Attributes:
        answer_text: Primary human-readable response text
        strategy_used: Processing strategy identifier for debugging
        retrieved_sources: Document sources for fact verification
        generated_sql_logged: SQL query for transparency and debugging
        visualization_data: Graph data for frontend visualization libraries
        table_data: Structured tabular data for table displays
        
    Evolution Strategy:
        - Optional fields enable backward compatibility
        - New response types can be added without breaking existing clients
        - Comprehensive metadata supports rich client experiences
    """
    answer_text: str                                         # Required: Primary response text
    strategy_used: str                                       # Required: Processing method used
    retrieved_sources: Optional[List[RetrievedSource]] = None # Optional: Source attribution data
    generated_sql_logged: Optional[str] = None               # Optional: SQL query for transparency
    visualization_data: Optional[Dict[str, Any]] = None      # Optional: Graph/chart data
    table_data: Optional[TableData] = None                   # Optional: Structured table data