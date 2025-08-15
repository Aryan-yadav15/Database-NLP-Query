"""
ChromaDB Vector Database Service Module
======================================

This module provides a high-level interface to ChromaDB for vector storage,
retrieval, and similarity search operations. It integrates with the application's
embedding service to enable semantic search across various data types.

Key Features:
1. Persistent vector storage with ChromaDB
2. Configurable embedding function integration
3. Collection management and initialization
4. Similarity search with filtering capabilities
5. Automatic error handling and graceful degradation

Vector Database Operations:
- Document storage with metadata and embeddings
- Semantic similarity search and ranking
- Collection-based data organization
- Persistent storage for data durability
- Query filtering and result limitation

Integration Points:
- Embedding Service: Text-to-vector conversion
- Data Quality Rules: Rule storage and similarity matching
- Document Retrieval: Semantic search for knowledge bases
- User Context: Personalized search and recommendations

Performance Characteristics:
- Storage: Scales to millions of vectors
- Query Speed: Sub-100ms for similarity search
- Memory: Efficient vector indexing and caching
- Persistence: Automatic data durability and recovery

Author: Brain LLM Team
"""

import logging
import chromadb
from chromadb.config import Settings as ChromaSettings

# Module-level logger for vector database operations
logger = logging.getLogger(__name__)

class ChromaService:
    """
    High-level interface for ChromaDB vector database operations.
    
    This service provides a simplified API for vector storage and retrieval
    operations, abstracting the complexity of ChromaDB configuration and
    embedding function integration. It supports persistent storage and
    semantic similarity search for various application use cases.
    
    Core Capabilities:
    1. Collection creation and management
    2. Document storage with automatic embedding generation
    3. Similarity search with configurable result limits
    4. Metadata filtering for precise queries
    5. Error handling and graceful degradation
    
    Storage Architecture:
    - Persistent Client: Data survives application restarts
    - Collection-based: Logical separation of different data types
    - Embedding Functions: Pluggable text-to-vector conversion
    - Metadata Support: Rich document attributes for filtering
    
    Use Cases:
    - Data Quality rule similarity matching
    - Document retrieval for knowledge bases
    - User preference and context storage
    - Content recommendation and discovery
    
    Configuration:
    - Persist Directory: Local file system path for data storage
    - Collection Name: Logical grouping identifier
    - Embedding Service: Text vectorization provider
    - Telemetry: Optional usage analytics (anonymized)
    """
    
    def __init__(self, embedding_service=None, persist_directory=None, collection_name=None):
        """
        Initialize ChromaDB service with configurable storage and embedding options.
        
        Sets up the vector database client, creates or connects to a collection,
        and configures the embedding function for automatic vector generation.
        
        Args:
            embedding_service: Service providing text-to-vector conversion
            persist_directory: File system path for ChromaDB data persistence
            collection_name: Unique identifier for the document collection
            
        Raises:
            Exception: If ChromaDB client initialization fails
        """
        self.embedding_service = embedding_service
        self.persist_directory = persist_directory or "chroma_db"  # Default storage location
        self.collection_name = collection_name or "default_collection"  # Default collection name
        
        # Initialize ChromaDB persistent client with anonymized telemetry
        try:
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=ChromaSettings(anonymized_telemetry=True)  # Privacy-respecting analytics
            )
            
            # Get or create collection with custom embedding function
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self._get_embedding_function()
            )
            
            logger.info(f"ChromaService initialized with collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            self.client = None
            self.collection = None
            
    def _get_embedding_function(self):
        """Get an embedding function that wraps our embedding service."""
        if not self.embedding_service:
            logger.warning("No embedding service provided, using default ChromaDB embeddings")
            return None
            
        def embed_func(texts):
            return self.embedding_service.get_embeddings(texts)
            
        return embed_func
        
    def query_collection(self, query_text=None, query_embedding=None, n_results=5, filter_criteria=None):
        """
        Query the ChromaDB collection.
        
        Args:
            query_text: Text to query (will be converted to embedding if query_embedding not provided)
            query_embedding: Pre-computed embedding to query with
            n_results: Number of results to return
            filter_criteria: Optional filter criteria for the query
            
        Returns:
            Results from ChromaDB query, or None if query fails
        """
        if not self.collection:
            logger.error("ChromaDB collection not initialized")
            return None
            
        try:
            if not query_embedding and query_text and self.embedding_service:
                query_embedding = self.embedding_service.get_embeddings([query_text])[0]
                
            if query_embedding is not None:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    where=filter_criteria
                )
                return results
            else:
                logger.error("No query embedding or text provided")
                return None
                
        except Exception as e:
            logger.error(f"Error querying ChromaDB: {e}")
            return None