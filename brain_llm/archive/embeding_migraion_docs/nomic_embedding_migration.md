# Nomic Embedding Migration for DQ Rule Manager

## Overview

This documentation outlines the migration from `all-MiniLM-L6-v2` (sentence-transformers) to `nomic-embed-text` (Ollama) for both rule population and query embedding in the DQ Rule Manager system.

## Current vs Future Implementation

### 🔄 Current State
- **Embedding Model**: `all-MiniLM-L6-v2` via `sentence-transformers`
- **Rule Population**: Local model generates embeddings during CSV processing
- **Query Embedding**: Same local model encodes user queries for similarity search
- **Dependencies**: `sentence-transformers`, `torch`

### 🚀 Future State  
- **Embedding Model**: `nomic-embed-text` via Ollama
- **Rule Population**: Ollama API generates embeddings during CSV/PDF processing
- **Query Embedding**: Same Ollama API encodes user queries for similarity search
- **Dependencies**: `langchain-community`, `langchain-ollama`

## Migration Benefits

### ✅ Advantages of Nomic-Embed-Text
- **Better Quality**: Superior semantic understanding for data quality contexts
- **Consistency**: Same model used across the entire application
- **Centralized**: Single Ollama server for all embedding needs
- **Scalability**: Ollama can handle concurrent requests efficiently
- **Future-Proof**: Easier to upgrade to newer embedding models

### ⚠️ Considerations
- **Network Dependency**: Requires Ollama server to be running
- **Latency**: Network calls vs local computation
- **Error Handling**: Need to handle Ollama server unavailability

## Prerequisites

### 1. Ollama Installation
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull the nomic-embed-text model
ollama pull nomic-embed-text

# Verify the model is available
ollama list
```

### 2. Python Dependencies
```bash
# Install required packages
pip install "langchain-community>=0.2.7" "langchain-ollama>=0.3.2"
```

### 3. Configuration Updates
Update `app/core/config.py`:
```python
class Settings(BaseSettings):
    # Current embedding settings
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    
    # Future embedding settings (add these)
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    EMBEDDING_PROVIDER: str = "ollama"  # "sentence-transformers" or "ollama"
    
    # Timeout and retry settings for Ollama
    OLLAMA_REQUEST_TIMEOUT: int = 30
    OLLAMA_MAX_RETRIES: int = 3
```

## Implementation Changes

### 1. Enhanced DQ Rule Manager

Create a new version that supports both embedding providers:

```python
# app/services/dq_rule_manager.py (Enhanced Version)

from typing import List, Dict, Any, Optional, Union
import pandas as pd
import chromadb
import logging
import os
import asyncio
from app.core.config import Settings

# Conditional imports based on provider
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from langchain_community.embeddings import OllamaEmbeddings
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

logger = logging.getLogger(__name__)

class DQRuleManager:
    """Enhanced DQ Rule Manager supporting multiple embedding providers."""
    
    def __init__(self, settings: Settings):
        """Initialize with configurable embedding provider."""
        self.settings = settings
        self._initialize_embedding_model()
        self._initialize_chromadb()
        
        # Auto-populate if collection is empty
        if self.collection.count() == 0:
            logger.warning(f"Collection '{self.collection.name}' is empty. Populating rules...")
            self._populate_rules()
            
        logger.info(f"DQ Rule Manager initialized. Collection contains {self.collection.count()} rules.")
    
    def _initialize_embedding_model(self):
        """Initialize the embedding model based on configuration."""
        provider = self.settings.EMBEDDING_PROVIDER.lower()
        
        if provider == "ollama":
            if not OLLAMA_AVAILABLE:
                raise ImportError("Ollama dependencies not available. Install: pip install langchain-community langchain-ollama")
            
            logger.info(f"Initializing Ollama embedding model: {self.settings.OLLAMA_EMBEDDING_MODEL}")
            self.embedding_model = OllamaEmbeddings(
                model=self.settings.OLLAMA_EMBEDDING_MODEL,
                base_url=self.settings.OLLAMA_BASE_URL,
                request_timeout=self.settings.OLLAMA_REQUEST_TIMEOUT
            )
            self.embedding_provider = "ollama"
            
        elif provider == "sentence-transformers":
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                raise ImportError("Sentence-transformers not available. Install: pip install sentence-transformers")
            
            logger.info(f"Initializing sentence-transformers model: {self.settings.EMBEDDING_MODEL_NAME}")
            self.embedding_model = SentenceTransformer(self.settings.EMBEDDING_MODEL_NAME)
            self.embedding_provider = "sentence-transformers"
            
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")
    
    def _initialize_chromadb(self):
        """Initialize ChromaDB client and collection."""
        logger.info(f"Initializing ChromaDB client at path: {self.settings.DQ_CHROMA_PATH}")
        self.client = chromadb.PersistentClient(path=self.settings.DQ_CHROMA_PATH)
        self.collection = self.client.get_or_create_collection(name=self.settings.DQ_COLLECTION_NAME)
    
    def _encode_texts(self, texts: List[str], show_progress: bool = True) -> List[List[float]]:
        """Encode texts using the configured embedding provider."""
        try:
            if self.embedding_provider == "ollama":
                # Ollama batch embedding
                logger.info(f"Generating embeddings for {len(texts)} texts using Ollama...")
                embeddings = self.embedding_model.embed_documents(texts)
                return embeddings
                
            elif self.embedding_provider == "sentence-transformers":
                # Sentence-transformers batch embedding
                logger.info(f"Generating embeddings for {len(texts)} texts using sentence-transformers...")
                embeddings = self.embedding_model.encode(texts, show_progress_bar=show_progress)
                return embeddings.tolist()
                
        except Exception as e:
            logger.error(f"Error generating embeddings with {self.embedding_provider}: {str(e)}")
            raise
    
    def _encode_single_text(self, text: str) -> List[float]:
        """Encode a single text using the configured embedding provider."""
        try:
            if self.embedding_provider == "ollama":
                # Ollama single query embedding
                embedding = self.embedding_model.embed_query(text)
                return embedding
                
            elif self.embedding_provider == "sentence-transformers":
                # Sentence-transformers single embedding
                embedding = self.embedding_model.encode(text)
                return embedding.tolist()
                
        except Exception as e:
            logger.error(f"Error generating single embedding with {self.embedding_provider}: {str(e)}")
            raise
    
    def _populate_rules(self):
        """Populate ChromaDB with rules from CSV file using batch processing."""
        try:
            csv_path = self.settings.DQ_RULES_FILE
            if not os.path.exists(csv_path):
                logger.error(f"DQ rules CSV file not found at {csv_path}")
                return

            logger.info(f"Loading rules from: {csv_path}")
            df_rules = pd.read_csv(csv_path)
            
            # Clean and prepare data
            df_rules.columns = [
                'Domain', 'SAP_Module', 'Data_Type', 'Rule_ID', 
                'Description', 'Quality_Dimension', 'Attribute_Group'
            ]
            df_rules['Rule_ID'] = df_rules['Rule_ID'].astype(str)
            df_rules.dropna(subset=['Domain', 'Rule_ID', 'Description'], inplace=True)
            
            # Prepare documents for embedding
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

            # Generate embeddings using the configured provider
            embeddings = self._encode_texts(documents, show_progress=True)
            
            # Add to ChromaDB
            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Successfully populated {len(documents)} rules into ChromaDB")
            
        except Exception as e:
            logger.error(f"Error populating rules: {str(e)}", exc_info=True)
            raise
    
    async def find_relevant_rules(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Find relevant rules using semantic search with configured embedding provider."""
        try:
            if self.collection.count() == 0:
                logger.warning("Collection is empty. Repopulating...")
                self._populate_rules()
                if self.collection.count() == 0:
                    logger.error("Collection is still empty after repopulation")
                    return []

            # Generate query embedding
            query_embedding = self._encode_single_text(query)
            
            # Search for similar rules
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["metadatas", "distances"]
            )
            
            # Process results
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
                        'relevance_score': 1 - results['distances'][0][i] if results['distances'][0][i] < 1 else 0,
                        'embedding_provider': self.embedding_provider
                    }
                    rules.append(rule)
            
            logger.info(f"Found {len(rules)} relevant rules for query using {self.embedding_provider}")
            return rules
            
        except Exception as e:
            logger.error(f"Error finding relevant rules: {str(e)}", exc_info=True)
            return []
    
    def find_relevant_rules_sync(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Synchronous version of find_relevant_rules."""
        # Implementation identical to async version but without async/await
        # (Copy the logic from find_relevant_rules method)
        pass
    
    def get_embedding_info(self) -> Dict[str, Any]:
        """Get information about the current embedding configuration."""
        return {
            "provider": self.embedding_provider,
            "model_name": (
                self.settings.OLLAMA_EMBEDDING_MODEL if self.embedding_provider == "ollama" 
                else self.settings.EMBEDDING_MODEL_NAME
            ),
            "base_url": getattr(self.settings, 'OLLAMA_BASE_URL', None),
            "collection_count": self.collection.count()
        }
```

### 2. Batch Processing for Large Datasets

For handling large CSV/PDF files with Ollama:

```python
def _populate_rules_with_batching(self, batch_size: int = 32):
    """Populate rules with batch processing for better Ollama performance."""
    try:
        # ... data loading logic ...
        
        total_docs = len(documents)
        logger.info(f"Processing {total_docs} documents in batches of {batch_size}")
        
        # Process in batches to avoid overwhelming Ollama
        for i in range(0, total_docs, batch_size):
            batch_end = min(i + batch_size, total_docs)
            batch_documents = documents[i:batch_end]
            batch_metadatas = metadatas[i:batch_end]
            batch_ids = ids[i:batch_end]
            
            logger.info(f"Processing batch {i//batch_size + 1}/{(total_docs + batch_size - 1)//batch_size}")
            
            # Generate embeddings for this batch
            batch_embeddings = self._encode_texts(batch_documents, show_progress=False)
            
            # Add batch to ChromaDB
            self.collection.add(
                embeddings=batch_embeddings,
                documents=batch_documents,
                metadatas=batch_metadatas,
                ids=batch_ids
            )
            
            # Optional: Small delay between batches
            if self.embedding_provider == "ollama":
                await asyncio.sleep(0.1)  # 100ms delay to be gentle on Ollama
        
        logger.info(f"Successfully populated {total_docs} rules in {(total_docs + batch_size - 1)//batch_size} batches")
        
    except Exception as e:
        logger.error(f"Error in batch population: {str(e)}", exc_info=True)
        raise
```

### 3. Error Handling and Fallback

```python
def _encode_with_retry(self, texts: Union[str, List[str]], max_retries: int = 3) -> Union[List[float], List[List[float]]]:
    """Encode text(s) with retry logic for Ollama connectivity issues."""
    is_single_text = isinstance(texts, str)
    
    for attempt in range(max_retries):
        try:
            if is_single_text:
                return self._encode_single_text(texts)
            else:
                return self._encode_texts(texts)
                
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Embedding attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"All {max_retries} embedding attempts failed: {str(e)}")
                raise
```

## Migration Steps

### Phase 1: Preparation
1. **Install Ollama** and pull `nomic-embed-text` model
2. **Update dependencies** in `requirements.txt`
3. **Add configuration** options to support both providers
4. **Test Ollama connectivity** with simple embedding calls

### Phase 2: Code Updates
1. **Update DQRuleManager** to support multiple providers
2. **Add error handling** and retry logic for Ollama
3. **Implement batch processing** for large datasets
4. **Update existing service integrations**

### Phase 3: Migration
1. **Backup existing ChromaDB** collection
2. **Change configuration** to use Ollama
3. **Regenerate embeddings** for existing rules
4. **Test query functionality** with new embeddings
5. **Verify results** match expected quality

### Phase 4: Cleanup
1. **Remove sentence-transformers** dependencies if no longer needed
2. **Update documentation** and examples
3. **Monitor performance** and optimize batch sizes

## Testing Migration

### 1. Validation Script
```python
# test_embedding_migration.py

async def test_embedding_migration():
    """Test both embedding providers with the same queries."""
    
    # Test queries
    test_queries = [
        "customer data validation rules",
        "sales amount completeness check",
        "duplicate record detection"
    ]
    
    # Test with sentence-transformers
    settings_st = Settings(EMBEDDING_PROVIDER="sentence-transformers")
    dq_manager_st = DQRuleManager(settings_st)
    
    # Test with Ollama
    settings_ollama = Settings(EMBEDDING_PROVIDER="ollama")
    dq_manager_ollama = DQRuleManager(settings_ollama)
    
    for query in test_queries:
        print(f"\nTesting query: '{query}'")
        
        # Get results from both providers
        rules_st = await dq_manager_st.find_relevant_rules(query, n_results=3)
        rules_ollama = await dq_manager_ollama.find_relevant_rules(query, n_results=3)
        
        print(f"Sentence-transformers found {len(rules_st)} rules")
        print(f"Ollama found {len(rules_ollama)} rules")
        
        # Compare results
        print("Top rule from each provider:")
        if rules_st:
            print(f"  ST: {rules_st[0]['Description'][:100]}...")
        if rules_ollama:
            print(f"  Ollama: {rules_ollama[0]['Description'][:100]}...")
```

### 2. Performance Comparison
```python
import time

def benchmark_embedding_providers():
    """Compare performance between embedding providers."""
    
    test_documents = ["sample rule description"] * 100
    
    # Benchmark sentence-transformers
    start_time = time.time()
    embeddings_st = sentence_transformer_model.encode(test_documents)
    st_time = time.time() - start_time
    
    # Benchmark Ollama
    start_time = time.time()
    embeddings_ollama = ollama_model.embed_documents(test_documents)
    ollama_time = time.time() - start_time
    
    print(f"Sentence-transformers: {st_time:.2f}s for {len(test_documents)} documents")
    print(f"Ollama: {ollama_time:.2f}s for {len(test_documents)} documents")
```

## Configuration Examples

### Development Environment
```python
# .env.development
EMBEDDING_PROVIDER=sentence-transformers
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
```

### Production Environment
```python
# .env.production
EMBEDDING_PROVIDER=ollama
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_BASE_URL=http://ollama-server:11434
OLLAMA_REQUEST_TIMEOUT=30
OLLAMA_MAX_RETRIES=3
```

## Monitoring and Troubleshooting

### Health Check Endpoint
```python
@router.get("/health/embeddings")
async def check_embedding_health():
    """Health check for embedding service."""
    try:
        dq_manager = get_dq_rule_manager()
        embedding_info = dq_manager.get_embedding_info()
        
        # Test a simple embedding
        test_embedding = dq_manager._encode_single_text("test query")
        
        return {
            "status": "healthy",
            "provider": embedding_info["provider"],
            "model": embedding_info["model_name"],
            "embedding_dimensions": len(test_embedding),
            "collection_count": embedding_info["collection_count"]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| `Connection refused` | Ollama server not running | Start Ollama: `ollama serve` |
| `Model not found` | nomic-embed-text not pulled | Run: `ollama pull nomic-embed-text` |
| `Timeout errors` | Large batch sizes | Reduce batch size to 16-32 |
| `Memory issues` | Processing too many documents | Implement batch processing |
| `Inconsistent results` | Different embedding spaces | Regenerate all embeddings with same model |

## Future Considerations

### 1. Hybrid Approach
Consider maintaining both providers for fallback:
```python
async def find_relevant_rules_with_fallback(self, query: str) -> List[Dict[str, Any]]:
    """Try Ollama first, fallback to sentence-transformers if needed."""
    try:
        return await self.find_relevant_rules_ollama(query)
    except Exception as e:
        logger.warning(f"Ollama failed, falling back to sentence-transformers: {e}")
        return await self.find_relevant_rules_sentence_transformers(query)
```

### 2. Model Versioning
Track embedding model versions in ChromaDB metadata:
```python
collection_metadata = {
    "embedding_model": "nomic-embed-text",
    "embedding_provider": "ollama", 
    "created_date": "2025-01-11",
    "model_version": "v1.0"
}
```

### 3. Performance Optimization
- **Caching**: Cache embeddings for frequently queried texts
- **Batch Optimization**: Tune batch sizes based on Ollama server capacity
- **Connection Pooling**: Reuse connections to Ollama server
- **Async Processing**: Use async/await for concurrent embedding generation

This migration will provide better semantic understanding for data quality rule matching while maintaining backward compatibility during the transition period.
