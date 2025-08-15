# brain_LLM/app/api/v1/endpoints/generate.py
"""
Text Generation API Endpoint Module
===================================

This module provides RESTful API endpoints for direct text generation using
Large Language Models. It offers simple, non-streaming text generation
capabilities for use cases like summarization, content creation, and general NLP tasks.

Key Features:
- Synchronous text generation for quick responses
- Configurable model selection per request
- Pydantic request/response validation
- Comprehensive error handling and logging
- FastAPI dependency injection for service management

Use Cases:
- Document summarization and content extraction
- Text transformation and rewriting
- Template-based content generation
- Quick Q&A without complex workflow requirements

API Design:
- RESTful POST endpoint with JSON request/response
- Request validation via Pydantic models
- HTTP status codes for proper client error handling
- Dependency injection for service abstraction

Performance Characteristics:
- Synchronous processing: 2-5 seconds for typical requests
- Memory efficient: No streaming overhead
- Stateless: Each request is independent
- Token usage: Varies by model and prompt complexity

Author: Brain LLM Team
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

# Application services and configuration
from app.api.v1.deps import get_llm_service
from app.services.llm.base import BaseLLMService
from app.core.config import settings

# Module-level logger for API endpoint operations
logger = logging.getLogger(__name__)

# FastAPI router instance for text generation endpoints
router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class GenerationRequest(BaseModel):
    """
    Request model for text generation API.
    
    Defines the structure and validation rules for incoming text generation requests.
    Uses Pydantic for automatic validation, serialization, and API documentation.
    
    Attributes:
        prompt (str): Input text prompt for the LLM to process
        
    Validation:
        - prompt: Required string field (min length handled by LLM service)
        - Additional validation can be added via Pydantic validators
        
    Example:
        {
            "prompt": "Summarize the key benefits of cloud computing in 3 bullet points"
        }
    """
    prompt: str  # Required input text for LLM processing


class GenerationResponse(BaseModel):
    """
    Response model for text generation API.
    
    Defines the structure of successful text generation responses.
    Ensures consistent API contract and enables automatic documentation.
    
    Attributes:
        text (str): Generated text output from the LLM
        
    Example:
        {
            "text": "• Cost efficiency through pay-as-you-use pricing..."
        }
    """
    text: str  # Generated text output from LLM


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.post("/text", response_model=GenerationResponse)
async def generate_text_endpoint(
    request: GenerationRequest,
    model_name: Optional[str] = None,
    llm_service: BaseLLMService = Depends(get_llm_service)
):
    """
    Generate text using Large Language Models for general-purpose tasks.
    
    This endpoint provides direct text generation capabilities without the complexity
    of streaming or multi-step workflows. It's designed for simple use cases where
    users need quick text generation, summarization, or content transformation.
    
    Features:
    - Synchronous processing for immediate results
    - Configurable model selection via query parameter
    - Automatic error handling with appropriate HTTP status codes
    - Request logging for monitoring and debugging
    
    Args:
        request: GenerationRequest containing the input prompt
        model_name: Optional model override (defaults to configured RAG model)
        llm_service: Injected LLM service instance for text generation
        
    Returns:
        GenerationResponse: Contains the generated text
        
    Raises:
        HTTPException: 500 status for any generation failures
        
    Example Usage:
        POST /api/v1/generate/text
        {
            "prompt": "Explain quantum computing in simple terms"
        }
        
        Response:
        {
            "text": "Quantum computing uses quantum mechanics principles..."
        }
        
    Query Parameters:
        - model_name: Override default model (e.g., ?model_name=gemini-1.5-pro)
        
    Performance:
        - Response time: 2-5 seconds depending on prompt complexity
        - Token usage: Varies by model and prompt length
        - Memory: Minimal (no streaming state management)
    """
    try:
        # Model selection: Use query parameter or fall back to configured default
        # This allows per-request model customization while maintaining sensible defaults
        model_to_use = model_name or settings.GEMINI_RAG_MODEL_NAME

        # Log request details for monitoring and debugging
        # Helps track usage patterns and performance metrics
        logger.info(f"Generating text with model: {model_to_use}")
        
        # Call LLM service for text generation
        # The service handles API communication, error handling, and response parsing
        generated_text = llm_service.generate_text(
            prompt=request.prompt,
            model_name=model_to_use
        )
        
        # Return structured response with generated content
        return GenerationResponse(text=generated_text)
    
    except Exception as e:
        # Comprehensive error handling with logging and user-friendly responses
        # Log full exception details for debugging while returning safe error messages
        logger.error(f"Error during text generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="Failed to generate text from the model."
        )