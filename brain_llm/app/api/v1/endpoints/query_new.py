# In brain_LLM/app/api/v1/endpoints/query_new.py
# Replace the entire file content with this:

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import logging
import json

from app.api.v1.schemas.query import QueryRequest
from app.api.v1.deps import get_langchain_streaming_service
from app.services.langchain_service import LangChainStreamingService
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/stream", response_class=StreamingResponse)
async def stream_process_query(
    request_payload: QueryRequest,
    langchain_svc: LangChainStreamingService = Depends(get_langchain_streaming_service)
) -> StreamingResponse:
    """
    Processes a query using the LangChain agent and streams the entire
    thought and execution process back to the client using Server-Sent Events.
    """
    log_payload = request_payload.model_dump()
    if log_payload.get("api_key"):
        log_payload["api_key"] = "********"
    if log_payload.get("db_connection_info") and log_payload.get("db_connection_info", {}).get("db_password"):
        log_payload["db_connection_info"]["db_password"] = "********"
    
    logger.info(f"Received streaming request with payload: {json.dumps(log_payload)}")
    logger.info(
        f"RAG_CLIENT: Preparing to send payload to brain_LLM:\n"
        f"{json.dumps(log_payload, indent=2)}"
    )
    
    chat_history = request_payload.chat_history or []
    short_term_memory = request_payload.short_term_memory or []
    
    # The service method is an async generator.
    # StreamingResponse will iterate over it and send the yielded chunks.
    return StreamingResponse(
        langchain_svc.stream_query(
            query=request_payload.query_text,
            chat_history=chat_history,
            short_term_memory=short_term_memory,
            model_name=request_payload.model_name,
            temperature=request_payload.temperature,
            api_key=request_payload.api_key,
            db_connection_info=request_payload.db_connection_info
        ),
        media_type="text/event-stream"
    )

# Note: The old, non-streaming process_query endpoint has been removed.
# This file now exclusively handles the new streaming logic.