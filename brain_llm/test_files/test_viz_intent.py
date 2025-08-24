#!/usr/bin/env python3
"""
Test script for visualization intent classification
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_visualization_intent():
    """Test that visualization queries are properly classified."""
    
    from app.services.langgraph_analytics_service import analyze_query_intent, register_services
    from app.services.llm import get_llm_service
    
    try:
        # Initialize required services
        llm_service = get_llm_service('gemini')
        register_services(llm_service, None, None, None, "test schema")
        
        # Test different visualization queries
        test_queries = [
            "visualize the relationship for all database",
            "show me the database diagram", 
            "create a schema visualization",
            "display table relationships",
            "show entity relationship diagram"
        ]
        
        for query in test_queries:
            print(f"\n🧪 Testing: '{query}'")
            
            # Create test state
            state = {
                "user_query": query,
                "db_schema": "test schema",
                "formatted_history": "",
                "event_queue": None
            }
            
            # Analyze intent
            result = await analyze_query_intent(state)
            
            analysis_type = result.get("analysis_type", "unknown")
            complexity = result.get("complexity_level", 0)
            
            print(f"   Analysis Type: {analysis_type}")
            print(f"   Complexity: {complexity}")
            
            if analysis_type == "visualization":
                print("   ✅ Correctly identified as visualization")
            else:
                print(f"   ❌ Incorrectly identified as {analysis_type}")
        
        print(f"\n📊 Intent classification test completed")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Testing Visualization Intent Classification")
    print("=" * 50)
    asyncio.run(test_visualization_intent())
