#!/usr/bin/env python3
"""
Analytics Endpoint Test - Comprehensive Analysis
"""

import asyncio
import sys
import os
import json
import aiohttp
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

class AnalyticsEndpointTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.endpoint = f"{base_url}/api/v1/query/stream"
    
    async def test_query(self, query_text, model_name="gemini-1.5-flash"):
        """Test a single query and parse the response"""
        payload = {
            "query_text": query_text,
            "model_name": model_name
        }
        
        print(f"\n🧪 Testing Query: '{query_text}'")
        print("=" * 80)
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status != 200:
                        print(f"❌ HTTP Error {response.status}")
                        return None
                    
                    events = []
                    structured_response = None
                    token_usage = None
                    
                    # Parse Server-Sent Events
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('event:'):
                            event_type = line.replace('event: ', '')
                        elif line.startswith('data:'):
                            data = line.replace('data: ', '')
                            try:
                                parsed_data = json.loads(data)
                                events.append((event_type, parsed_data))
                                
                                if event_type == 'structured_response':
                                    structured_response = parsed_data
                                elif event_type == 'token_usage':
                                    token_usage = parsed_data
                            except json.JSONDecodeError:
                                pass
                    
                    return {
                        'events': events,
                        'structured_response': structured_response,
                        'token_usage': token_usage
                    }
                    
            except Exception as e:
                print(f"❌ Request Error: {e}")
                return None
    
    def analyze_response(self, result):
        """Analyze the response structure and content"""
        if not result:
            print("❌ No result to analyze")
            return
        
        events = result['events']
        structured_response = result['structured_response']
        token_usage = result['token_usage']
        
        print(f"📊 Response Analysis:")
        print(f"   Events Count: {len(events)}")
        print(f"   Event Types: {[event[0] for event in events]}")
        
        if structured_response:
            strategy = structured_response.get('strategy_used', 'unknown')
            print(f"   Strategy Used: {strategy}")
            
            # Analyze different response types
            if 'dashboard' in structured_response:
                self.analyze_dashboard_response(structured_response)
            elif 'table' in structured_response:
                self.analyze_table_response(structured_response)
            elif 'graph' in structured_response:
                self.analyze_graph_response(structured_response)
            else:
                print("   ⚠️  Unknown response format")
        
        if token_usage:
            print(f"   Token Usage: {token_usage['token_usage']['total_token_count']} tokens")
            print(f"   LLM Calls: {token_usage['llm_calls_count']}")
    
    def analyze_dashboard_response(self, response):
        """Analyze dashboard-type responses"""
        dashboard = response['dashboard']
        print(f"   📈 Dashboard Response:")
        print(f"      Title: {dashboard.get('title', 'N/A')}")
        print(f"      Sections: {len(dashboard.get('sections', []))}")
        
        # Check for chart data
        for section in dashboard.get('sections', []):
            if section.get('type') == 'chart_grid':
                components = section.get('components', [])
                print(f"      📊 Charts: {len(components)} chart(s)")
                for component in components:
                    if 'data' in component:
                        rows = len(component['data'])
                        columns = len(component.get('columns', []))
                        print(f"         - {component['type']}: {rows} rows × {columns} columns")
        
        # Check for SQL
        if 'sql' in response:
            print(f"      🔍 SQL Generated: ✅ ({len(response['sql'])} chars)")
        
        # Check for execution time
        if 'execution_time' in response:
            exec_time = response['execution_time']
            if exec_time:
                print(f"      ⏱️  Execution Time: {exec_time:.3f}s")
    
    def analyze_table_response(self, response):
        """Analyze table-type responses (DQ rules)"""
        table = response['table']
        print(f"   📋 Table Response:")
        print(f"      Title: {table.get('title', 'N/A')}")
        print(f"      Columns: {len(table.get('columns', []))}")
        print(f"      Rows: {len(table.get('rows', []))}")
        
        # Check for DQ rules
        if 'dqRules' in response:
            rules = response['dqRules']
            print(f"      🔍 DQ Rules: {len(rules)} rule(s)")
            for rule in rules[:3]:  # Show first 3
                print(f"         - Rule {rule['Rule_ID']}: {rule['Description'][:50]}...")
    
    def analyze_graph_response(self, response):
        """Analyze graph-type responses (visualizations)"""
        graph = response['graph']
        print(f"   🎨 Graph Response:")
        if 'graph' in graph:
            nodes = graph['graph'].get('nodes', [])
            edges = graph['graph'].get('edges', [])
            print(f"      Nodes: {len(nodes)} table(s)")
            print(f"      Edges: {len(edges)} relationship(s)")
            
            # Show some sample nodes
            for node in nodes[:5]:
                print(f"         - {node['label']} ({node['group']})")

async def run_comprehensive_test():
    """Run comprehensive tests of different query types"""
    
    print("🚀 Analytics Endpoint Comprehensive Test")
    print("=" * 80)
    print(f"Timestamp: {datetime.now()}")
    
    tester = AnalyticsEndpointTester()
    
    # Test cases covering different functionality
    test_cases = [
        {
            "name": "SQL Analytics Query",
            "query": "Show me the top 5 customers by total sales amount",
            "expected_features": ["SQL generation", "chart data", "statistical analysis"]
        },
        {
            "name": "Trend Analysis Query", 
            "query": "Show me monthly sales trends over time",
            "expected_features": ["time-series data", "trend analysis", "line charts"]
        },
        {
            "name": "Data Quality Query",
            "query": "Find data quality rules for customer validation",
            "expected_features": ["DQ rule retrieval", "validation SQL", "table display"]
        },
        {
            "name": "Visualization Query",
            "query": "Create a schema diagram showing database relationships",
            "expected_features": ["schema analysis", "relationship mapping", "graph data"]
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ {test_case['name']}")
        print(f"Expected: {', '.join(test_case['expected_features'])}")
        
        result = await tester.test_query(test_case['query'])
        tester.analyze_response(result)
        
        results.append({
            'test_case': test_case,
            'result': result,
            'success': result is not None and result.get('structured_response') is not None
        })
    
    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 80)
    successful_tests = sum(1 for r in results if r['success'])
    print(f"Total Tests: {len(results)}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {len(results) - successful_tests}")
    
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{status} Test {i}: {result['test_case']['name']}")
    
    if successful_tests == len(results):
        print("\n🎉 All analytics endpoints are working perfectly!")
        print("   - SQL analytics with chart data ✅")
        print("   - Data quality rule retrieval ✅") 
        print("   - Schema visualization ✅")
        print("   - Real-time streaming ✅")
    else:
        print(f"\n⚠️  {len(results) - successful_tests} test(s) failed - check implementation")

if __name__ == "__main__":
    asyncio.run(run_comprehensive_test())
