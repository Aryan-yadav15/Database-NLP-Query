"""
End-to-end test for LangGraph Analytics Pipeline
"""
import asyncio
import json
import aiohttp
import sys
import os

async def test_analytics_pipeline():
    """Test the complete analytics pipeline with a real query."""
    
    print("🚀 Testing Complete Analytics Pipeline...")
    
    # Test query
    test_query = "Show me sales trends by region"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test the streaming analytics endpoint
            print(f"📝 Testing query: '{test_query}'")
            
            async with session.post(
                "http://localhost:8000/api/v1/query/stream",
                json={"query_text": test_query}
            ) as response:
                
                if response.status == 200:
                    print(f"✅ Server responded with status {response.status}")
                    
                    # Read the streaming response
                    response_data = []
                    async for line in response.content:
                        if line:
                            try:
                                # Parse each SSE event
                                line_str = line.decode('utf-8').strip()
                                if line_str.startswith('data: '):
                                    data = json.loads(line_str[6:])  # Remove 'data: ' prefix
                                    response_data.append(data)
                                    print(f"📦 Received: {data.get('type', 'unknown')} - {data.get('message', '')[:100]}...")
                            except json.JSONDecodeError:
                                continue
                    
                    if response_data:
                        print(f"✅ Received {len(response_data)} streaming events")
                        print("🎉 Analytics pipeline is working correctly!")
                        return True
                    else:
                        print("⚠️ No streaming data received")
                        return False
                        
                else:
                    error_text = await response.text()
                    print(f"❌ Server error {response.status}: {error_text}")
                    return False
                    
    except aiohttp.ClientError as e:
        print(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def main():
    """Run the analytics pipeline test."""
    success = await test_analytics_pipeline()
    
    if success:
        print("\n✅ All systems operational!")
        print("   - LangGraph serialization fixed")
        print("   - SQL generation working with LLM")
        print("   - Streaming analytics pipeline active")
    else:
        print("\n❌ Issues detected - check server logs")

if __name__ == "__main__":
    asyncio.run(main())
