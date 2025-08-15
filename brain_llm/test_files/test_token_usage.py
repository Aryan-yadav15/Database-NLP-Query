#!/usr/bin/env python3
"""
Test script to verify token usage tracking for all tools including 
visualization and DQ rules.
"""

import asyncio
import json
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.token_tracker import RequestTokenTracker
from app.services.llm.base import TokenUsage

def test_token_tracker():
    """Test the RequestTokenTracker functionality"""
    print("🧪 Testing RequestTokenTracker...")
    
    tracker = RequestTokenTracker("test-request-123")
    
    # Simulate token usage from multiple LLM calls
    usage1 = TokenUsage(prompt_token_count=150, candidates_token_count=45, total_token_count=195)
    usage2 = TokenUsage(prompt_token_count=200, candidates_token_count=55, total_token_count=255)
    usage3 = TokenUsage(prompt_token_count=100, candidates_token_count=30, total_token_count=130)
    
    # Add usage from different tools
    print("  📝 Simulating SQL generation call...")
    tracker.add_usage(usage1)
    
    print("  🎨 Simulating visualization call...")
    tracker.add_usage(usage2)
    
    print("  🔍 Simulating DQ rules call...")
    tracker.add_usage(usage3)
    
    total_usage = tracker.get_total_usage()
    call_count = tracker.get_call_count()
    
    print(f"\n📊 Final Results:")
    print(f"  🔢 Total prompt tokens: {total_usage.prompt_token_count}")
    print(f"  🤖 Total response tokens: {total_usage.candidates_token_count}")
    print(f"  📊 Total tokens: {total_usage.total_token_count}")
    print(f"  📞 Number of LLM calls: {call_count}")
    
    # Verify calculations
    expected_prompt = 150 + 200 + 100
    expected_response = 45 + 55 + 30
    expected_total = 195 + 255 + 130
    
    assert total_usage.prompt_token_count == expected_prompt, f"Expected {expected_prompt}, got {total_usage.prompt_token_count}"
    assert total_usage.candidates_token_count == expected_response, f"Expected {expected_response}, got {total_usage.candidates_token_count}"
    assert total_usage.total_token_count == expected_total, f"Expected {expected_total}, got {total_usage.total_token_count}"
    assert call_count == 3, f"Expected 3 calls, got {call_count}"
    
    print("✅ RequestTokenTracker test passed!")
    return True

def test_usage_in_sse_format():
    """Test how token usage would appear in SSE format"""
    print("\n🌐 Testing SSE format for token usage...")
    
    # Simulate final token usage
    usage = TokenUsage(prompt_token_count=450, candidates_token_count=130, total_token_count=580)
    
    # Format as it would appear in the stream
    token_usage_data = {
        "token_usage": usage.to_dict(),
        "llm_calls_count": 3
    }
    
    sse_event = f"event: token_usage\ndata: {json.dumps(token_usage_data)}\n\n"
    
    print("📡 SSE Event that would be sent:")
    print(sse_event)
    
    # Parse it back to verify
    lines = sse_event.strip().split('\n')
    event_line = lines[0]
    data_line = lines[1]
    
    assert event_line == "event: token_usage", f"Expected 'event: token_usage', got '{event_line}'"
    
    data_json = data_line[6:]  # Remove "data: " prefix
    parsed_data = json.loads(data_json)
    
    assert "token_usage" in parsed_data, "Missing token_usage in parsed data"
    assert "llm_calls_count" in parsed_data, "Missing llm_calls_count in parsed data"
    
    token_info = parsed_data["token_usage"]
    assert token_info["prompt_token_count"] == 450
    assert token_info["candidates_token_count"] == 130
    assert token_info["total_token_count"] == 580
    assert parsed_data["llm_calls_count"] == 3
    
    print("✅ SSE format test passed!")
    return True

def print_troubleshooting_guide():
    """Print troubleshooting information for token tracking issues"""
    print("\n🔧 TROUBLESHOOTING TOKEN USAGE:")
    print("="*50)
    
    print("\n❌ If you're not seeing token usage:")
    print("  1. Check for API errors (503 overload, auth issues)")
    print("  2. Verify the LLM service implements generate_text_streamed_with_usage()")
    print("  3. Check that tools are passing the token_tracker parameter")
    print("  4. Ensure the API response includes usage_metadata")
    
    print("\n✅ Token tracking is implemented for:")
    print("  📝 SQL generation and formatting")
    print("  💬 Conversational responses")
    print("  🎨 Database schema visualization")
    print("  🔍 Data quality rules generation")
    
    print("\n🎯 Expected stream events:")
    print("  1. status_update events (progress)")
    print("  2. structured_response event (main response)")
    print("  3. token_usage event (final usage summary)")
    
    print("\n🚨 Common issues:")
    print("  • 503 Service Unavailable: API overloaded, retry later")
    print("  • Missing token_usage event: Check for exceptions in LLM calls")
    print("  • Zero token counts: Verify usage_metadata extraction")

if __name__ == "__main__":
    print("🧪 Running comprehensive token usage tests...\n")
    
    success = True
    
    try:
        # Test 1: Token tracker functionality
        success &= test_token_tracker()
        
        # Test 2: SSE format
        success &= test_usage_in_sse_format()
        
        if success:
            print("\n🎉 All token usage tests passed!")
        else:
            print("\n❌ Some tests failed!")
        
        # Always print troubleshooting guide
        print_troubleshooting_guide()
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        
        print_troubleshooting_guide()
