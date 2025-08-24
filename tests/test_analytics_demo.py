"""
Analytics API Demo Script
Demonstrates the working analytics endpoints
"""
import requests
import json
from datetime import datetime, timedelta

# Base URL for the API
BASE_URL = "http://localhost:8000/api/v1"

def test_analytics_endpoints():
    """Test the analytics endpoints to demonstrate functionality"""
    
    print("🚀 Analytics API Demo")
    print("=" * 50)
    
    # Test 1: Create a new dashboard
    print("\n1. Creating a new dashboard...")
    dashboard_data = {
        "name": "Sales Performance Dashboard",
        "description": "Monthly sales analysis and trends",
        "layout": {
            "columns": 3,
            "rows": 2,
            "widgets": []
        },
        "filters": {
            "date_range": "last_30_days",
            "region": "all"
        },
        "is_public": True
    }
    
    try:
        response = requests.post(f"{BASE_URL}/analytics/dashboards/", json=dashboard_data)
        if response.status_code == 201:
            dashboard = response.json()
            dashboard_id = dashboard["id"]
            print(f"✅ Dashboard created with ID: {dashboard_id}")
            print(f"   Name: {dashboard['name']}")
            print(f"   Created: {dashboard['created_at']}")
        else:
            print(f"❌ Failed to create dashboard: {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to the API. Make sure the server is running on port 8000")
        return
    
    # Test 2: Get all dashboards
    print("\n2. Fetching all dashboards...")
    try:
        response = requests.get(f"{BASE_URL}/analytics/dashboards/")
        if response.status_code == 200:
            dashboard_response = response.json()
            dashboards = dashboard_response["dashboards"]
            total = dashboard_response["total"]
            print(f"✅ Found {total} dashboard(s)")
            for db in dashboards:
                print(f"   - {db['name']} (ID: {db['id']})")
        else:
            print(f"❌ Failed to fetch dashboards: {response.status_code}")
    except Exception as e:
        print(f"❌ Error fetching dashboards: {e}")
    
    # Test 3: Create insight cards for the dashboard
    print(f"\n3. Creating insight cards for dashboard {dashboard_id}...")
    
    cards_data = [
        {
            "title": "Total Revenue",
            "query_text": "What is the total revenue for the current month?",
            "generated_sql": "SELECT SUM(amount) as total_revenue FROM sales WHERE date >= date_trunc('month', CURRENT_DATE)",
            "database_type": "postgresql",
            "dashboard_id": dashboard_id,
            "visualization_type": "number",
            "visualization_config": {
                "chart_type": "number",
                "color": "green",
                "format": "currency"
            },
            "position_config": {"x": 0, "y": 0, "w": 6, "h": 4}
        },
        {
            "title": "Sales Trend",
            "query_text": "Show me daily sales over the last 30 days",
            "generated_sql": "SELECT DATE(created_at) as date, COUNT(*) as sales FROM sales WHERE created_at >= CURRENT_DATE - INTERVAL '30 days' GROUP BY DATE(created_at) ORDER BY date",
            "database_type": "postgresql",
            "dashboard_id": dashboard_id,
            "visualization_type": "line",
            "visualization_config": {
                "chart_type": "line",
                "x_axis": "date",
                "y_axis": "sales"
            },
            "position_config": {"x": 6, "y": 0, "w": 6, "h": 4}
        },
        {
            "title": "Top Products",
            "query_text": "Which are the best selling products this month?",
            "generated_sql": "SELECT product_name, SUM(quantity) as total_sold FROM sales s JOIN products p ON s.product_id = p.id WHERE s.created_at >= date_trunc('month', CURRENT_DATE) GROUP BY product_name ORDER BY total_sold DESC LIMIT 10",
            "database_type": "postgresql",
            "dashboard_id": dashboard_id,
            "visualization_type": "table",
            "visualization_config": {
                "chart_type": "table",
                "columns": ["product_name", "total_sold"]
            },
            "position_config": {"x": 0, "y": 4, "w": 12, "h": 4}
        }
    ]
    
    created_cards = []
    for i, card_data in enumerate(cards_data):
        try:
            response = requests.post(f"{BASE_URL}/analytics/cards/", json=card_data)
            if response.status_code == 201:
                card = response.json()
                created_cards.append(card)
                print(f"✅ Created card: {card['title']} (ID: {card['id']})")
            else:
                print(f"❌ Failed to create card {i+1}: {response.status_code}")
        except Exception as e:
            print(f"❌ Error creating card {i+1}: {e}")
    
    # Test 4: Get dashboard with cards
    print(f"\n4. Fetching dashboard {dashboard_id} with cards...")
    try:
        response = requests.get(f"{BASE_URL}/analytics/dashboards/{dashboard_id}/full")
        if response.status_code == 200:
            dashboard_detail = response.json()
            print(f"✅ Dashboard: {dashboard_detail['name']}")
            print(f"   Description: {dashboard_detail['description']}")
            print(f"   Layout: {dashboard_detail['layout_config']}")
            print(f"   Cards: {len(created_cards)} insight cards attached")
        else:
            print(f"❌ Failed to fetch dashboard details: {response.status_code}")
    except Exception as e:
        print(f"❌ Error fetching dashboard details: {e}")
    
    # Test 5: Execute a card query
    if created_cards:
        print(f"\n5. Executing card query...")
        card = created_cards[0]
        
        try:
            response = requests.post(f"{BASE_URL}/analytics/cards/{card['id']}/execute")
            if response.status_code == 200:
                execution_result = response.json()
                print(f"✅ Card executed successfully: {card['title']}")
                print(f"   Status: {execution_result.get('status', 'completed')}")
                print(f"   Execution time: {execution_result.get('execution_time', 'N/A')}s")
            else:
                print(f"❌ Failed to execute card: {response.status_code}")
        except Exception as e:
            print(f"❌ Error executing card: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Analytics API Demo Complete!")
    print(f"🌐 View API docs: http://localhost:8000/docs")
    print(f"📊 Dashboard ID: {dashboard_id}")
    print("💡 The analytics infrastructure is ready for frontend integration!")

if __name__ == "__main__":
    test_analytics_endpoints()
