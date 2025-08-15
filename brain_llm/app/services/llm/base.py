"""
Large Language Model (LLM) Service Abstraction Module
====================================================

This module defines the abstract base class and supporting data structures for
Large Language Model services in the Brain LLM application. It implements the
Strategy Pattern to provide a unified interface for different LLM providers.

Key Components:
- TokenUsage: Data class for tracking LLM API usage and costs
- BaseLLMService: Abstract base class defining the LLM service interface

Design Patterns:
- Strategy Pattern: Allows swapping LLM providers without code changes
- Factory Pattern: Used in conjunction with LLM service factory
- Template Method: Defines common interface while allowing provider-specific implementations

Supported LLM Providers:
- Google Gemini (via gemini.py)
- Anthropic Claude (extensible)
- OpenAI GPT (extensible)

Author: Brain LLM Team
"""

from abc import ABC, abstractmethod
from typing import Any, Generator, Optional, Tuple
from langchain_core.language_models.chat_models import BaseChatModel
from dataclasses import dataclass

@dataclass
class TokenUsage:
    """
    Data structure for tracking LLM token usage and API costs.
    
    This class provides a standardized way to track token consumption across
    different LLM providers, enabling cost monitoring and optimization.
    
    Attributes:
        prompt_token_count (int): Tokens used in the input prompt/context
        candidates_token_count (int): Tokens generated in the response
        total_token_count (int): Total tokens used (prompt + candidates)
        
    Usage:
        # Create usage tracking
        usage = TokenUsage(prompt_token_count=100, candidates_token_count=50)
        usage.total_token_count = usage.prompt_token_count + usage.candidates_token_count
        
        # Accumulate usage across multiple calls
        total_usage = TokenUsage()
        total_usage.add(usage1)
        total_usage.add(usage2)
    """
    prompt_token_count: int = 0          # Input tokens (prompt, context, system messages)
    candidates_token_count: int = 0      # Output tokens (generated responses)
    total_token_count: int = 0           # Total tokens for billing calculation
    
    def add(self, other: 'TokenUsage') -> None:
        """
        Accumulate token usage from another TokenUsage instance.
        
        This method enables tracking total usage across multiple LLM calls
        within a single request or session.
        
        Args:
            other (TokenUsage): Another TokenUsage instance to add to this one
            
        Example:
            session_usage = TokenUsage()
            session_usage.add(query1_usage)
            session_usage.add(query2_usage)
            print(f"Total session cost: {session_usage.total_token_count} tokens")
        """
        self.prompt_token_count += other.prompt_token_count
        self.candidates_token_count += other.candidates_token_count
        self.total_token_count += other.total_token_count
    
    def to_dict(self) -> dict:
        """
        Convert TokenUsage to dictionary for JSON serialization.
        
        This method enables easy integration with APIs, logging systems,
        and monitoring tools that expect JSON-serializable data.
        
        Returns:
            dict: Dictionary representation suitable for JSON serialization
            
        Example:
            usage_dict = token_usage.to_dict()
            response_data = {"result": result, "usage": usage_dict}
            return JSONResponse(response_data)
        """
        return {
            "prompt_token_count": self.prompt_token_count,
            "candidates_token_count": self.candidates_token_count,
            "total_token_count": self.total_token_count
        }

class BaseLLMService(ABC):
    """
    Abstract base class defining the interface for Large Language Model services.
    
    This class implements the Strategy Pattern, allowing the application to work
    with different LLM providers (Google Gemini, Anthropic Claude, OpenAI GPT)
    through a unified interface.
    
    Key Responsibilities:
    1. Text generation (synchronous and streaming)
    2. Token usage tracking for cost monitoring
    3. Response parsing (JSON, SQL extraction)
    4. LangChain integration for complex workflows
    
    Design Benefits:
    - Provider independence: Switch LLM providers without code changes
    - Consistent error handling across all providers
    - Standardized token usage tracking
    - Type safety through abstract method definitions
    
    Implementation Notes:
    - All concrete implementations must override abstract methods
    - API keys are stored per-instance for multi-tenant support
    - Streaming methods use Python generators for memory efficiency
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LLM service with optional API key.
        
        Args:
            api_key (Optional[str]): Provider-specific API key for authentication.
                                   If None, implementation should use default configuration.
        """
        self.api_key = api_key  # Store API key per-instance for multi-tenant scenarios
    
    # =============================================================================
    # CORE TEXT GENERATION METHODS
    # =============================================================================
    
    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        model_name: str,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate a complete text response from a prompt (synchronous).
        
        This is the primary method for single-shot text generation where the
        complete response is needed before proceeding. Use this for:
        - SQL query generation
        - JSON data extraction
        - Short responses where streaming isn't beneficial
        
        Args:
            prompt (str): The input text/prompt for the LLM
            model_name (str): Provider-specific model identifier (e.g., "gemini-1.5-flash")
            temperature (float): Controls randomness (0.0 = deterministic, 1.0 = creative)
            
        Returns:
            str: Complete generated text response
            
        Raises:
            LLMServiceError: If generation fails or API errors occur
            
        Example:
            response = llm_service.generate_text(
                prompt="Generate SQL for: Show top 10 customers",
                model_name="gemini-1.5-flash",
                temperature=0.1  # Low temperature for precise SQL
            )
        """
        pass

    @abstractmethod
    def generate_text_streamed(
        self,
        prompt: str,
        model_name: str,
        temperature: float = 0.1,
    ) -> Generator[str, Any, None]:
        """
        Generate text with streaming response chunks (memory efficient).
        
        This method provides real-time streaming for long-form content generation.
        Use this for:
        - Interactive chat experiences
        - Long document generation
        - Real-time user feedback during processing
        
        Args:
            prompt (str): The input text/prompt for the LLM
            model_name (str): Provider-specific model identifier
            temperature (float): Controls randomness (default: 0.1 for consistency)
            
        Yields:
            str: Individual text chunks as they're generated
            
        Example:
            for chunk in llm_service.generate_text_streamed(prompt, model):
                print(chunk, end='', flush=True)  # Real-time display
        """
        pass

    @abstractmethod
    def generate_text_streamed_with_usage(
        self,
        prompt: str,
        model_name: str,
        temperature: float = 0.1,
    ) -> Generator[Tuple[str, Optional[TokenUsage]], Any, None]:
        """
        Generate text with streaming and token usage tracking.
        
        This method combines streaming generation with comprehensive token usage
        monitoring for cost tracking and optimization.
        
        Args:
            prompt (str): The input text/prompt for the LLM
            model_name (str): Provider-specific model identifier
            temperature (float): Controls randomness
            
        Yields:
            Tuple[str, Optional[TokenUsage]]: 
                - str: Text chunk
                - TokenUsage: Token usage info (may be None for intermediate chunks)
                
        Example:
            total_usage = TokenUsage()
            for chunk, usage in llm_service.generate_text_streamed_with_usage(prompt, model):
                print(chunk, end='')
                if usage:
                    total_usage.add(usage)
            print(f"Total cost: {total_usage.total_token_count} tokens")
        """
    pass

    def generate_text_streamed_with_usage_fallback(
        self,
        prompt: str,
        model_name: str,
        temperature: float = 0.1,
    ) -> Generator[Tuple[str, Optional[TokenUsage]], Any, None]:
        """
        Fallback implementation for LLM services that don't have usage tracking.
        This wraps the regular streaming method and yields None for token usage.
        """
        for chunk in self.generate_text_streamed(prompt, model_name, temperature):
            yield chunk, None

    @abstractmethod
    def parse_json_from_text(self, text: str) -> Any:
        """
        Parses a JSON object from a string, which might be embedded in markdown.

        Args:
            text: The text containing the JSON object.

        Returns:
            The parsed JSON object or None if parsing fails.
        """
        pass

    @abstractmethod
    def parse_sql_from_text(self, text: str) -> Optional[str]:
        """
        Extracts a SQL query from a string, potentially from a markdown block.

        Args:
            text: The text containing the SQL query.

        Returns:
            The extracted SQL query as a string, or None if no valid query is found.
        """
        pass

    @abstractmethod
    def get_langchain_chat_model(self, model_name: str, temperature: float) -> BaseChatModel:
        """
        Returns a LangChain-compatible chat model instance.

        Args:
            model_name: The specific model to use for the chat.
            temperature: The creativity of the chat responses.

        Returns:
            An instance of a LangChain-compatible chat model.
        """
        pass
