# brain_LLM/app/services/token_tracker.py
"""
Request-Scoped Token Usage Tracking Module
==========================================

This module implements request-scoped token usage tracking for LLM API calls,
enabling accurate cost monitoring and billing across complex multi-step workflows.

Key Features:
- Request-scoped isolation prevents cross-request contamination
- Accumulates usage across multiple LLM service calls
- Supports streaming token usage updates to clients
- Enables cost analysis and usage optimization
- Thread-safe for concurrent request handling

Architecture:
- Each HTTP request gets its own RequestTokenTracker instance
- Tracker accumulates tokens from SQL generation, formatting, DQ rules, etc.
- Final usage totals are streamed back to client as Server-Sent Events
- Supports multiple LLM providers with unified tracking interface

Author: Brain LLM Team
"""

import logging
from typing import Optional
from app.services.llm.base import TokenUsage

# Module-level logger for tracking operations
logger = logging.getLogger(__name__)

class RequestTokenTracker:
    """
    Request-scoped token usage tracker that accumulates token usage
    across multiple LLM calls within a single request.
    
    This class implements the Accumulator pattern to collect token usage
    from various services (SQL generation, formatting, DQ validation, etc.)
    and provide consolidated usage reporting for cost monitoring.
    
    Design Benefits:
    - Request isolation: Each request gets independent tracking
    - Multi-call aggregation: Handles complex workflows with multiple LLM calls
    - Streaming support: Enables real-time usage reporting to clients
    - Provider agnostic: Works with any LLM service implementing TokenUsage
    
    Usage Pattern:
        1. FastAPI creates tracker per request via dependency injection
        2. Services add their token usage: tracker.add_usage(usage)
        3. Final totals sent to client: tracker.get_total_usage()
    """
    
    def __init__(self, request_id: Optional[str] = None):
        """
        Initialize a new token tracker for a specific request.
        
        Args:
            request_id: Unique identifier for this request (for logging/debugging)
            
        Attributes:
            request_id: Request identifier for correlation in logs
            accumulated_usage: Running total of all token usage
            _call_count: Number of LLM API calls made in this request
        """
        self.request_id = request_id                    # For request correlation in logs
        self.accumulated_usage = TokenUsage()          # Running total of token usage
        self._call_count = 0                          # Count of LLM API calls
        
        # Log tracker creation for debugging complex request flows
        logger.debug(f"Request {self.request_id}: Token tracker initialized")
        
    def add_usage(self, usage: TokenUsage) -> None:
        """
        Add token usage from an LLM call to the accumulated total.
        
        This method is called by LLM services after each API call to accumulate
        token usage throughout the request lifecycle. It handles None usage
        gracefully for robustness.
        
        Args:
            usage: Token usage from a single LLM API call
            
        Side Effects:
            - Updates accumulated_usage with new token counts
            - Increments call counter for usage analytics
            - Logs usage addition for debugging and monitoring
            
        Thread Safety:
            This method is thread-safe for the single-request use case,
            but not designed for cross-request sharing.
        """
        if usage:  # Guard against None usage from failed API calls
            self.accumulated_usage.add(usage)        # Add to running total
            self._call_count += 1                    # Increment call counter
            
            # Log detailed usage information for monitoring and debugging
            logger.debug(
                f"Request {self.request_id}: Added token usage {usage.to_dict()}. "
                f"Total calls: {self._call_count}, "
                f"Total tokens: {self.accumulated_usage.total_token_count}"
            )
    
    def get_total_usage(self) -> TokenUsage:
        """
        Get the total accumulated token usage for this request.
        
        This method returns the consolidated token usage across all LLM calls
        made during the request lifecycle. Used for final reporting to clients
        and internal cost tracking.
        
        Returns:
            TokenUsage: Consolidated usage with prompt, response, and total tokens
            
        Usage:
            # At end of request processing
            final_usage = tracker.get_total_usage()
            cost = calculate_cost(final_usage.total_token_count)
            
        Thread Safety:
            Read-only operation, safe for concurrent access within single request.
        """
        return self.accumulated_usage
    
    def get_call_count(self) -> int:
        """
        Get the number of LLM API calls made in this request.
        
        This metric is useful for:
        - Performance analysis (too many calls = optimization opportunity)
        - Cost analysis (call overhead vs. token costs)
        - Debugging complex workflows
        - Usage pattern analysis
        
        Returns:
            int: Number of individual LLM API calls made
            
        Example:
            High call count might indicate:
            - Multiple retry attempts
            - Complex multi-step reasoning
            - Inefficient prompt engineering
        """
        return self._call_count
    
    def reset(self) -> None:
        """
        Reset the tracker for reuse (though typically one tracker per request).
        
        This method clears all accumulated usage and resets counters to zero.
        Generally not needed since trackers are request-scoped, but provided
        for completeness and potential testing scenarios.
        
        Side Effects:
            - Clears accumulated_usage to zero
            - Resets call count to zero
            - Logs reset operation for debugging
            
        Warning:
            Use with caution in production - may lose important usage data.
        """
        self.accumulated_usage = TokenUsage()          # Reset to zero usage
        self._call_count = 0                          # Reset call counter
        
        # Log reset operation for debugging and audit trail
        logger.debug(f"Request {self.request_id}: Token tracker reset")
