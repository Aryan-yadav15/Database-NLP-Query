#!/usr/bin/env python3
"""
Test script to verify token usage tracking is working correctly.
Run this to test the implementation without breaking existing functionality.
"""

import asyncio
import json
from app.services.llm import get_llm_service
from app.services.token_tracker import RequestTokenTracker
from app.services.langchain_service import LangChainStreamingService
from app.core.config import Settings

async def test_token_tracking():
    """Test that token tracking works with the streaming service"""
    
    # Initialize services
    settings = Settings()
    llm_service = get_llm_service("gemini")
    token_tracker = RequestTokenTracker("test-request-123")
    
    # Initialize LangChain service with token tracker
    # Note: We'll need to create mock objects for the dependencies we don't need for this test
    
    print("✅ Services initialized successfully")
    
    # Test direct LLM service token tracking
    print("\n🧪 Testing direct LLM service with token tracking...")
    
    try:
        generator = llm_service.generate_text_streamed_with_usage(
            prompt="What is 2+2?",
            model_name="gemini-1.5-flash",
            temperature=0.1
        )
        
        text_parts = []
        for chunk, usage in generator:
            if chunk:
                text_parts.append(chunk)
                print(f"📝 Chunk: {chunk[:50]}...")
            if usage:
                token_tracker.add_usage(usage)
                print(f"🔢 Token usage: {usage.to_dict()}")
        
        full_text = "".join(text_parts)
        total_usage = token_tracker.get_total_usage()
        
        print(f"\n📊 Results:")
        print(f"Generated text: {full_text}")
        print(f"Total token usage: {total_usage.to_dict()}")
        print(f"Number of LLM calls: {token_tracker.get_call_count()}")
        
        if total_usage.total_token_count > 0:
            print("✅ Token tracking is working!")
        else:
            print("❌ Token tracking returned zero tokens")
            
    except Exception as e:
        print(f"❌ Error during token tracking test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_token_tracking())
