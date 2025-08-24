"""
Test visualization query
"""
import asyncio
import json
import aiohttp

async def test_viz():
    """Test visualization query."""
    
    print("🎨 Testing Visualization Query...")
    
    query = "show me database schema visualization"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8000/api/v1/query/stream",
                json={"query_text": query}
            ) as response:
                
                print(f"📝 Status: {response.status}")
                
                if response.status == 200:
                    event_count = 0
                    
                    async for line in response.content:
                        if line:
                            try:
                                line_str = line.decode('utf-8').strip()
                                if line_str.startswith('data: '):
                                    event_count += 1
                                    data = json.loads(line_str[6:])
                                    
                                    event_type = data.get('type', 'unknown')
                                    message = data.get('message', '')
                                    
                                    print(f"Event {event_count}: Type='{event_type}', Message='{message}'")
                                    
                                    # Print full data for structured responses
                                    if event_type == 'structured_response':
                                        print(f"   Full Response Data Keys: {list(data.get('data', {}).keys())}")
                                        
                            except json.JSONDecodeError as e:
                                print(f"JSON Error: {e}")
                                continue
                    
                    print(f"\n📊 Total events received: {event_count}")
                else:
                    print(f"❌ HTTP Error: {response.status}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_viz())
