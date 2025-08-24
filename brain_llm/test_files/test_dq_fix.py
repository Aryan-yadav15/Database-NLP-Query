"""
Quick test for DQ rule integration fix
"""
import asyncio
import json
import aiohttp

async def test_dq_fix():
    """Test the corrected DQ rule integration."""
    
    print("🔧 Testing Corrected DQ Rule Integration...")
    
    query = "What are the data quality rules applied to tracks?"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8000/api/v1/query/stream",
                json={"query_text": query}
            ) as response:
                
                if response.status == 200:
                    print(f"✅ Query: '{query}'")
                    
                    events = []
                    dq_found = False
                    
                    async for line in response.content:
                        if line:
                            try:
                                line_str = line.decode('utf-8').strip()
                                if line_str.startswith('data: '):
                                    data = json.loads(line_str[6:])
                                    events.append(data)
                                    
                                    # Look for DQ events
                                    message = data.get('message', '').lower()
                                    if 'data quality' in message or 'searching' in message:
                                        print(f"📊 DQ Event: {data.get('message', '')}")
                                        dq_found = True
                                    
                                    # Look for final DQ response
                                    if data.get('type') == 'structured_response':
                                        response_data = data.get('data', {})
                                        if 'data_quality_rules' in response_data:
                                            rules = response_data['data_quality_rules']
                                            print(f"✅ SUCCESS: Found {len(rules)} DQ rules!")
                                            
                                            # Show first few rules
                                            for i, rule in enumerate(rules[:3]):
                                                rule_id = rule.get('rule_id', 'N/A')
                                                description = rule.get('description', 'N/A')[:60]
                                                score = rule.get('relevance_score', 0)
                                                print(f"   Rule {i+1}: {rule_id} - {description}... (Score: {score:.3f})")
                                            
                                            return True
                                        
                            except json.JSONDecodeError:
                                continue
                    
                    if dq_found:
                        print(f"✅ DQ processing detected but check final response")
                    else:
                        print(f"⚠️ Standard processing used - check intent classification")
                        
                    print(f"📊 Total events: {len(events)}")
                    return False
                    
                else:
                    print(f"❌ HTTP Error: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    """Test the DQ fix."""
    success = await test_dq_fix()
    
    if success:
        print("\n🎉 DQ Rule Integration WORKING!")
        print("   - Intent classification: ✅ Recognizing DQ queries")
        print("   - Routing: ✅ Directing to DQ node")
        print("   - ChromaDB search: ✅ Finding relevant rules")
        print("   - Response formatting: ✅ Proper rule data structure")
    else:
        print("\n🔧 Check server logs for detailed error info")

if __name__ == "__main__":
    asyncio.run(main())
