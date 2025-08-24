#!/usr/bin/env python3
"""
Test script for complete LangGraph Analytics Service functionality
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_all_functionality():
    """Test all enhanced functionality: SQL, DQ rules, and visualization."""
    
    # Import required services
    from app.services.langgraph_analytics_service import LangGraphAnalyticsService
    from app.services.llm import get_llm_service
    from app.services.dq_rule_manager import DQRuleManager
    from app.services.visualization_service import VisualizationService
    from app.services.token_tracker import RequestTokenTracker
    from app.core.config import Settings
    
    try:
        # Initialize services
        print("🔧 Initializing services...")
        settings = Settings()
        llm_service = get_llm_service('gemini')
        dq_rule_manager = DQRuleManager(settings)
        visualization_service = VisualizationService(llm_service)
        token_tracker = RequestTokenTracker()
        
        # Create analytics service
        db_schema = "AdventureWorks sample database schema"
        service = LangGraphAnalyticsService(
            llm_service=llm_service,
            settings=settings,
            db_schema=db_schema,
            dq_rule_manager=dq_rule_manager,
            visualization_service=visualization_service,
            token_tracker=token_tracker
        )
        
        print("✅ Services initialized successfully")
        
        # Test queries
        test_cases = [
            {
                "name": "SQL Query",
                "query": "Show me the top 10 customers by total sales",
                "expected_strategy": "SQL"
            },
            {
                "name": "DQ Rules Query", 
                "query": "Find data quality rules for customer validation",
                "expected_strategy": "DQ_RULE"
            },
            {
                "name": "Visualization Query",
                "query": "Create a schema diagram showing table relationships",
                "expected_strategy": "VISUALIZE"
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            print(f"\n🧪 Testing: {test_case['name']}")
            print(f"   Query: {test_case['query']}")
            
            event_count = 0
            strategy_used = None
            
            async for event in service.stream_analytics_query(test_case['query']):
                event_count += 1
                
                # Extract strategy from structured response
                if "structured_response" in event and "strategy_used" in event:
                    try:
                        import json
                        # Extract JSON data
                        data_start = event.find('{"')
                        if data_start != -1:
                            json_data = event[data_start:]
                            data = json.loads(json_data)
                            strategy_used = data.get("strategy_used")
                    except:
                        pass
                    
                    print(f"   ✅ Completed in {event_count} events")
                    break
            
            results.append({
                "name": test_case['name'],
                "events": event_count,
                "strategy": strategy_used,
                "expected": test_case['expected_strategy'],
                "success": strategy_used == test_case['expected_strategy']
            })
        
        # Summary
        print(f"\n📊 Complete Test Results:")
        print("=" * 60)
        for result in results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} {result['name']}: {result['events']} events, strategy: {result['strategy']}")
        
        total_passed = sum(1 for r in results if r['success'])
        print(f"\n🎯 Overall: {total_passed}/{len(results)} tests passed")
        
        if total_passed == len(results):
            print("🎉 ALL TESTS PASSED! Enhanced LangGraph service is fully functional.")
        else:
            print("⚠️  Some tests failed. Check the implementation.")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Testing Complete Enhanced LangGraph Analytics Service")
    print("=" * 60)
    asyncio.run(test_all_functionality())
