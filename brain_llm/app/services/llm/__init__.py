"""
LLM Service Factory
===================

This module acts as the central factory for all Large Language Model (LLM) services
within the application. It implements the **Factory Design Pattern** to decouple the
rest of the application from the specific implementation details of any given
LLM provider (e.g., Google Gemini, Anthropic Claude, OpenAI GPT).

Core Concepts:
--------------
1.  **Abstraction**: The application interacts with a generic `BaseLLMService` interface,
    not with a concrete `GeminiLLMService` or `ClaudeLLMService`.
2.  **Decoupling**: The main application logic (e.g., `LangChainStreamingService`) does
    not need to be changed when adding, removing, or modifying an LLM provider.
3.  **Centralized Registration**: The `_llm_services` dictionary acts as a single,
    authoritative registry of all available LLM services.

How to Add a New LLM Service (e.g., for 'Llama'):
-------------------------------------------------
To add support for a new LLM provider, follow these three simple steps:

1.  **Create the Service Class**:
    -   In the `app/services/llm/` directory, create a new file (e.g., `llama_service.py`).
    -   Inside this file, define a new class (e.g., `LlamaLLMService`) that inherits
        from `BaseLLMService`.
    -   Implement all the abstract methods defined in `BaseLLMService`.

2.  **Import the New Service Class**:
    -   In *this* file (`__init__.py`), add an import statement for your new class.
        ```python
        from .llama_service import LlamaLLMService
        ```

3.  **Register the Service**:
    -   Add a new entry to the `_llm_services` dictionary below. The key should be a
        simple, lowercase string that will be used to request the service (e.g., via
        an API query parameter).
        ```python
        "llama": LlamaLLMService
        ```

After these steps, the new LLM can be invoked throughout the application by
referencing its key (e.g., calling the API with `?model_name=llama`).
"""

from typing import Type, Optional
from app.services.llm.base import BaseLLMService

# --- Step 1: Import all available LLM service implementations ---
# Each new LLM service class must be imported here to be discoverable by the factory.
from .gemini import GeminiLLMService
from app.core.config import settings

# Example for a future Llama service:
# from .llama_service import LlamaLLMService


# --- Step 2: Register the imported services in the dictionary ---
# This dictionary maps a simple, lowercase string identifier (the "key") to the
# corresponding service class. This is the central registry for the factory.
_llm_services: dict[str, Type[BaseLLMService]] = {
    "gemini": GeminiLLMService,
    # Example for a future Llama service:
    # "llama": LlamaLLMService,
}


def get_llm_service(service_name: str, api_key: Optional[str] = None) -> BaseLLMService:
    """
    Factory function to instantiate and return a specific LLM service.

    This function is the single entry point for the rest of the application to
    obtain a concrete LLM service instance without needing to know about the
    specific implementation classes. It looks up the requested service by its
    string key and returns an initialized object.

    Args:
        service_name: The string identifier for the desired LLM service. This key
                    must exist in the `_llm_services` dictionary. The lookup is
                    case-insensitive. Defaults to "gemini".
        api_key: Optional API key to pass to the service constructor.

    Returns:
        An initialized instance of the requested LLM service class, which
        conforms to the `BaseLLMService` interface.

    Raises:
        ValueError: If the provided `service_name` does not correspond to any
                    registered service in the `_llm_services` dictionary.
    """
    # Use .lower() to ensure the lookup is case-insensitive.
    service_class = _llm_services.get(service_name.lower())
    if not service_class:
        raise ValueError(f"Unsupported LLM service: '{service_name}'. Supported services are: {list(_llm_services.keys())}")
    
    # Import settings here to avoid circular imports
    from app.core.config import settings
    
    # Instantiate the service with correct parameter order (settings first, then api_key)
    return service_class(settings, api_key=api_key)