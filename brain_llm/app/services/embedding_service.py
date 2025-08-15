"""
Text Embedding Service Module
=============================

This module provides text embedding capabilities using SentenceTransformers
for converting text into high-dimensional vectors used in semantic search,
similarity matching, and vector database operations.

Key Features:
- Sentence transformer model for text-to-vector conversion
- Optimized for semantic similarity tasks
- Integration with ChromaDB vector database
- Used for Data Quality rule matching and document retrieval

Model Details:
- Model: all-MiniLM-L6-v2 (384-dimensional embeddings)
- Size: ~80MB download, loads in 2-3 seconds
- Performance: ~1000 texts/second on CPU
- Quality: Good balance of speed vs. accuracy for business use

Author: Brain LLM Team
"""

from sentence_transformers import SentenceTransformer
from typing import List
from app.core.config import settings
import logging

# Module-level logger for embedding operations
logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Text embedding service using SentenceTransformers for vector operations.
    
    This service provides a high-level interface for converting text into
    numerical vectors that can be used for semantic similarity, clustering,
    and vector database operations throughout the application.
    
    Architecture:
    - Wraps SentenceTransformers library for ease of use
    - Singleton pattern via dependency injection for performance
    - Centralized model configuration through settings
    - Error handling and logging for production reliability
    
    Performance Characteristics:
    - Model loading: 2-3 seconds on first initialization
    - Embedding generation: ~1ms per short text on CPU
    - Memory usage: ~200MB for model + embeddings cache
    - Thread safety: SentenceTransformers is thread-safe
    """
    
    def __init__(self):
        """
        Initialize the embedding service with configured model.
        
        Loads the SentenceTransformers model specified in settings.
        This is an expensive operation (2-3 seconds) but only happens
        once per application lifecycle due to singleton pattern.
        
        Raises:
            Exception: If model loading fails (network, disk space, etc.)
            
        Side Effects:
            - Downloads model if not cached locally (~80MB)
            - Loads model into memory (~200MB)
            - Logs successful initialization
        """
        try:
            # Load the configured sentence transformer model
            # Model name comes from centralized settings for consistency
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
            
            logger.info(
                f"Successfully loaded embedding model: {settings.EMBEDDING_MODEL_NAME}. "
                f"Model produces {self.model.get_sentence_embedding_dimension()}-dimensional vectors."
            )
            
        except Exception as e:
            # Log detailed error for debugging and re-raise for caller handling
            logger.error(
                f"Failed to load embedding model '{settings.EMBEDDING_MODEL_NAME}': {e}. "
                f"Check network connection, disk space, and model name."
            )
            raise

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embeddings for the input text.
        
        Converts input text into a high-dimensional vector representation
        that captures semantic meaning. These vectors can be used for:
        - Similarity search in vector databases
        - Clustering and classification tasks
        - Semantic matching of business rules
        - Document retrieval and ranking
        
        Args:
            text (str): Input text to convert to vector embedding
            
        Returns:
            List[float]: 384-dimensional embedding vector
            
        Raises:
            Exception: If embedding generation fails (model error, invalid input)
            
        Performance:
            - Short text (< 100 words): ~1ms
            - Long text (> 500 words): ~5-10ms  
            - Batch processing recommended for multiple texts
            
        Example:
            embeddings = service.embed_text("What are the sales by region?")
            # Returns: [0.1234, -0.5678, 0.9012, ..., 0.3456] (384 values)
            
        Thread Safety:
            This method is thread-safe and can be called concurrently
            from multiple requests without synchronization.
        """
        try:
            # Generate embeddings using the loaded SentenceTransformer model
            # Model automatically handles tokenization, encoding, and pooling
            embeddings = self.model.encode(text)
            
            # Convert numpy array to Python list for JSON serialization
            embedding_list = embeddings.tolist()
            
            # Log embedding generation for debugging (without full vector data)
            logger.debug(
                f"Generated {len(embedding_list)}-dimensional embedding for text: "
                f"'{text[:50]}{'...' if len(text) > 50 else ''}'"
            )
            
            return embedding_list
            
        except Exception as e:
            # Log error with context for debugging
            logger.error(
                f"Error generating embeddings for text '{text[:100]}...': {e}. "
                f"Check input format and model state."
            )
            raise