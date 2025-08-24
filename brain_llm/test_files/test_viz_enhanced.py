#!/usr/bin/env python3
"""
Test script for enhanced visualization integration in LangGraph Analytics Service
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_visualization_query():
    """Test visualization query functionality with enhanced implementation."""
    
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
        llm_service = get_llm_service('gemini')  # Use gemini as default service
        dq_rule_manager = DQRuleManager(settings)
        visualization_service = VisualizationService(llm_service)
        token_tracker = RequestTokenTracker()
        
        # Create analytics service with mock schema
        db_schema = """
        -- Sample AdventureWorks Schema
        CREATE TABLE Customer (
            CustomerID INT PRIMARY KEY,
            CustomerName VARCHAR(255),
            ContactName VARCHAR(255),
            Country VARCHAR(255)
        );
        
        CREATE TABLE Orders (
            OrderID INT PRIMARY KEY,
            CustomerID INT,
            OrderDate DATE,
            TotalAmount DECIMAL(10,2),
            FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID)
        );
        """
        
        service = LangGraphAnalyticsService(
            llm_service=llm_service,
            settings=settings,
            db_schema=db_schema,
            dq_rule_manager=dq_rule_manager,
            visualization_service=visualization_service,
            token_tracker=token_tracker
        )
        
        print("✅ Services initialized successfully")
        
        # Test visualization query
        print("\n🎨 Testing schema visualization query...")
        query = "Show me a visual diagram of the database schema"
        
        event_count = 0
        events_received = []
        
        async for event in service.stream_analytics_query(query):
            event_count += 1
            print(f"📡 Event {event_count}: {event.strip()}")
            events_received.append(event.strip())
            
            # Stop after structured response for this test
            if "structured_response" in event:
                print(f"🎯 Received structured response after {event_count} events")
                break
        
        print(f"\n📊 Test Results:")
        print(f"   Total events: {event_count}")
        print(f"   Events received: {len(events_received)}")
        
        # Check if we got the expected progression
        received_event_types = [event.split('\n')[0].replace('event: ', '') for event in events_received if event.startswith('event:')]
        
        print(f"   Event types: {received_event_types}")
        
        if "structured_response" in received_event_types:
            print("✅ SUCCESS: Received structured response for visualization query")
        else:
            print("❌ FAILED: No structured response received")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Testing Enhanced Visualization Integration")
    print("=" * 50)
    asyncio.run(test_visualization_query())
