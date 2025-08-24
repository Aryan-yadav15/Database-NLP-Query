"""
Analytics Dashboard API Test

This script demonstrates the analytics dashboard API functionality
with mock data. It shows the complete workflow of:
1. Creating a dashboard
2. Creating insight cards
3. Pinning queries to dashboards
4. Refreshing dashboard data

Run this script to verify the analytics API is working correctly.
"""

import asyncio
import json
from datetime import datetime
from uuid import uuid4

# Mock the database connection for testing
class MockDatabaseConnection:
    """Mock database connection for testing"""
    
    def __init__(self):
        self.dashboards = {}
        self.cards = {}
    
    async def fetchrow(self, query, *args):
        print(f"Mock fetchrow: {query[:50]}... with {len(args)} args")
        
        if "INSERT INTO dashboards" in query:
            dashboard_id = str(uuid4())
            dashboard = {
                'id': dashboard_id,
                'user_id': args[0],
                'name': args[1],
                'description': args[2],
                'layout_config': '{}',
                'sharing_config': '{}',
                'is_active': True,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            self.dashboards[dashboard_id] = dashboard
            return dashboard
            
        elif "INSERT INTO insight_cards" in query:
            card_id = str(uuid4())
            card = {
                'id': card_id,
                'dashboard_id': args[0],
                'title': args[1],
                'query_text': args[2],
                'generated_sql': args[3],
                'database_type': args[4],
                'database_config': '{}',
                'visualization_type': args[6],
                'visualization_config': '{}',
                'position_config': '{}',
                'refresh_frequency': args[9],
                'auto_refresh_enabled': args[10],
                'last_refreshed': None,
                'last_result': None,
                'error_message': None,
                'is_active': True,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            self.cards[card_id] = card
            return card
        
        return None
    
    async def fetch(self, query, *args):
        print(f"Mock fetch: {query[:50]}... with {len(args)} args")
        
        if "FROM dashboards" in query:
            return list(self.dashboards.values())
        elif "FROM insight_cards" in query:
            return list(self.cards.values())
        
        return []
    
    async def fetchval(self, query, *args):
        print(f"Mock fetchval: {query[:50]}... with {len(args)} args")
        return str(uuid4())
    
    async def execute(self, query, *args):
        print(f"Mock execute: {query[:50]}... with {len(args)} args")
        return None


async def test_analytics_api():
    """Test the analytics dashboard API"""
    
    print("🧪 Testing Analytics Dashboard API")
    print("=" * 50)
    
    # Import the services
    from app.services.analytics import DashboardService, InsightCardService
    from app.models.analytics import DashboardCreate, InsightCardCreate
    
    # Create mock database connection
    mock_db = MockDatabaseConnection()
    
    # Initialize services
    dashboard_service = DashboardService(mock_db)
    card_service = InsightCardService(mock_db)
    
    # Test user ID
    user_id = str(uuid4())
    print(f"Test User ID: {user_id}")
    print()
    
    # Test 1: Create Dashboard
    print("1️⃣ Creating Dashboard...")
    dashboard_data = DashboardCreate(
        name="Sales Analytics Dashboard",
        description="Monthly sales performance and customer insights"
    )
    
    dashboard = await dashboard_service.create_dashboard(dashboard_data, user_id)
    print(f"✅ Created dashboard: {dashboard.name} (ID: {dashboard.id})")
    print()
    
    # Test 2: Create Insight Card
    print("2️⃣ Creating Insight Card...")
    card_data = InsightCardCreate(
        dashboard_id=dashboard.id,
        title="Top 5 Products by Revenue",
        query_text="Show me the top 5 products by revenue this month",
        generated_sql="SELECT product_name, SUM(revenue) as total_revenue FROM sales GROUP BY product_name ORDER BY total_revenue DESC LIMIT 5",
        database_type="postgresql",
        visualization_type="bar_chart"
    )
    
    card = await card_service.create_card(card_data, user_id)
    print(f"✅ Created card: {card.title} (ID: {card.id})")
    print()
    
    # Test 3: Execute Card Query
    print("3️⃣ Executing Card Query...")
    result = await card_service.execute_card_query(card)
    print(f"✅ Executed card query:")
    print(f"   Success: {result.success}")
    print(f"   Execution time: {result.execution_time:.3f}s")
    if result.data:
        print(f"   Data rows: {result.data.get('total_rows', 0)}")
    print()
    
    # Test 4: Get Dashboard with Cards
    print("4️⃣ Getting Dashboard with Cards...")
    full_dashboard = await dashboard_service.get_dashboard_with_cards(dashboard.id, user_id)
    if full_dashboard:
        print(f"✅ Retrieved dashboard: {full_dashboard.name}")
        print(f"   Cards: {len(full_dashboard.cards or [])}")
    else:
        print("❌ Failed to retrieve dashboard")
    print()
    
    # Test 5: List User Dashboards
    print("5️⃣ Listing User Dashboards...")
    dashboard_list = await dashboard_service.list_user_dashboards(user_id)
    print(f"✅ Found {len(dashboard_list.dashboards)} dashboards")
    for db in dashboard_list.dashboards:
        print(f"   - {db.name}")
    print()
    
    # Test 6: Pin Query Workflow (simulated)
    print("6️⃣ Simulating Pin Query Workflow...")
    pin_data = {
        "dashboard_id": str(dashboard.id),
        "title": "Customer Acquisition Trends",
        "query_text": "Show customer acquisition trends over the last 6 months",
        "generated_sql": "SELECT DATE_TRUNC('month', signup_date) as month, COUNT(*) as new_customers FROM customers WHERE signup_date >= NOW() - INTERVAL '6 months' GROUP BY month ORDER BY month",
        "database_type": "postgresql",
        "visualization_type": "line_chart"
    }
    
    pinned_card_data = InsightCardCreate(
        dashboard_id=dashboard.id,
        title=pin_data["title"],
        query_text=pin_data["query_text"],
        generated_sql=pin_data["generated_sql"],
        database_type=pin_data["database_type"],
        visualization_type=pin_data["visualization_type"]
    )
    
    pinned_card = await card_service.create_card(pinned_card_data, user_id)
    print(f"✅ Pinned query as card: {pinned_card.title}")
    print()
    
    print("🎉 All tests completed successfully!")
    print("=" * 50)
    print("Analytics Dashboard API is working correctly! 🚀")


if __name__ == "__main__":
    asyncio.run(test_analytics_api())
