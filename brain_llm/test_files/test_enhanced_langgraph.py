"""
Test the enhanced LangGraph service with DQ rules and visualization
"""
import asyncio
import json
import aiohttp

async def test_data_quality_query():
    """Test a data quality related query."""
    
    print("🔍 Testing Data Quality RAG Integration...")
    
    dq_queries = [
        "What are the data quality rules applied to tracks?",
        "Show me data quality rules for customer data",
        "What validation rules exist for invoice table?"
    ]
    
    for query in dq_queries:
        print(f"\n📝 Query: '{query}'")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:8000/api/v1/query/stream",
                    json={"query_text": query}
                ) as response:
                    
                    if response.status == 200:
                        events = []
                        dq_events = []
                        
                        async for line in response.content:
                            if line:
                                try:
                                    line_str = line.decode('utf-8').strip()
                                    if line_str.startswith('data: '):
                                        data = json.loads(line_str[6:])
                                        events.append(data)
                                        
                                        # Look for DQ-specific events
                                        message = data.get('message', '').lower()
                                        if 'data quality' in message or 'dq rule' in message:
                                            dq_events.append(data)
                                            print(f"   📊 DQ Event: {data.get('message', '')}")
                                        
                                        # Look for final response with DQ data
                                        if data.get('type') == 'structured_response':
                                            response_data = data.get('data', {})
                                            if 'data_quality_rules' in response_data:
                                                rules_count = len(response_data.get('data_quality_rules', []))
                                                print(f"   ✅ Found {rules_count} DQ rules in response")
                                            
                                except json.JSONDecodeError:
                                    continue
                        
                        if dq_events:
                            print(f"   ✅ DQ-specific processing detected ({len(dq_events)} events)")
                        else:
                            print(f"   ⚠️ Standard processing used ({len(events)} events)")
                    else:
                        print(f"   ❌ HTTP Error: {response.status}")
                        
        except Exception as e:
            print(f"   ❌ Error: {e}")

async def test_visualization_query():
    """Test visualization related queries."""
    
    print("\n🎨 Testing Schema Visualization Integration...")
    
    viz_queries = [
        "Show me the database schema visualization",
        "Generate an entity relationship diagram",
        "What does the database structure look like?"
    ]
    
    for query in viz_queries:
        print(f"\n📝 Query: '{query}'")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:8000/api/v1/query/stream",
                    json={"query_text": query}
                ) as response:
                    
                    if response.status == 200:
                        events = []
                        viz_events = []
                        
                        async for line in response.content:
                            if line:
                                try:
                                    line_str = line.decode('utf-8').strip()
                                    if line_str.startswith('data: '):
                                        data = json.loads(line_str[6:])
                                        events.append(data)
                                        
                                        # Look for visualization-specific events
                                        message = data.get('message', '').lower()
                                        if 'visualization' in message or 'schema' in message or 'diagram' in message:
                                            viz_events.append(data)
                                            print(f"   🎨 Viz Event: {data.get('message', '')}")
                                        
                                        # Look for final response with visualization data
                                        if data.get('type') == 'structured_response':
                                            response_data = data.get('data', {})
                                            if 'schema_visualization' in response_data:
                                                print(f"   ✅ Schema visualization included in response")
                                            
                                except json.JSONDecodeError:
                                    continue
                        
                        if viz_events:
                            print(f"   ✅ Visualization processing detected ({len(viz_events)} events)")
                        else:
                            print(f"   ⚠️ Standard processing used ({len(events)} events)")
                    else:
                        print(f"   ❌ HTTP Error: {response.status}")
                        
        except Exception as e:
            print(f"   ❌ Error: {e}")

async def main():
    """Run enhanced LangGraph integration tests."""
    print("🚀 Enhanced LangGraph Service - DQ & Visualization Test Suite")
    print("=" * 65)
    
    # Test DQ rule integration
    await test_data_quality_query()
    
    # Test visualization integration
    await test_visualization_query()
    
    print("\n📊 Integration Test Summary:")
    print("   - Data Quality RAG: Enhanced query routing and DQ rule retrieval")
    print("   - Visualization Service: Schema diagram generation and ERD creation")
    print("   - LangGraph Routing: Intent-based routing to specialized nodes")
    
    print("\n✅ Enhanced LangGraph Service - Testing Complete!")

if __name__ == "__main__":
    asyncio.run(main())
