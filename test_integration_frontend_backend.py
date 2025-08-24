"""
Integration Test - Frontend + Backend Analytics
Tests the complete analytics workflow from frontend to backend
"""
import requests
import time
import json

def test_frontend_backend_integration():
    """Test the complete integration between frontend and backend"""
    
    print("🔄 Testing Frontend + Backend Analytics Integration")
    print("=" * 60)
    
    # Test 1: Backend API Health Check
    print("\n1. Testing Backend API Health...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend API is running and healthy")
        else:
            print(f"❌ Backend API health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to backend API: {e}")
        return False
    
    # Test 2: Frontend Accessibility
    print("\n2. Testing Frontend Accessibility...")
    try:
        response = requests.get("http://localhost:3000", timeout=10)
        if response.status_code == 200:
            print("✅ Frontend is accessible")
        else:
            print(f"❌ Frontend accessibility failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to frontend: {e}")
        return False
    
    # Test 3: Analytics API Endpoints
    print("\n3. Testing Analytics API Endpoints...")
    
    # Test dashboard creation
    dashboard_data = {
        "name": "Integration Test Dashboard",
        "description": "Testing frontend-backend integration",
        "layout": {"columns": 12, "rows": 6, "widgets": []},
        "filters": {},
        "is_public": False
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/analytics/dashboards/", 
            json=dashboard_data,
            timeout=10
        )
        if response.status_code == 201:
            dashboard = response.json()
            print(f"✅ Dashboard created successfully: {dashboard['name']}")
            dashboard_id = dashboard['id']
        else:
            print(f"❌ Dashboard creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Dashboard creation request failed: {e}")
        return False
    
    # Test dashboard listing
    try:
        response = requests.get("http://localhost:8000/api/v1/analytics/dashboards/", timeout=10)
        if response.status_code == 200:
            dashboards_response = response.json()
            dashboards = dashboards_response.get("dashboards", [])
            print(f"✅ Dashboard listing successful: {len(dashboards)} dashboards found")
        else:
            print(f"❌ Dashboard listing failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Dashboard listing request failed: {e}")
        return False
    
    # Test card creation
    card_data = {
        "title": "Integration Test Card",
        "query_text": "What is the total revenue?",
        "generated_sql": "SELECT SUM(amount) as total_revenue FROM sales",
        "database_type": "postgresql",
        "dashboard_id": dashboard_id,
        "visualization_type": "number",
        "visualization_config": {"chart_type": "number", "format": "currency"},
        "position_config": {"x": 0, "y": 0, "w": 6, "h": 4}
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/analytics/cards/", 
            json=card_data,
            timeout=10
        )
        if response.status_code == 201:
            card = response.json()
            print(f"✅ Card created successfully: {card['title']}")
            card_id = card['id']
        else:
            print(f"❌ Card creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Card creation request failed: {e}")
        return False
    
    # Test card execution
    try:
        response = requests.post(
            f"http://localhost:8000/api/v1/analytics/cards/{card_id}/execute",
            timeout=10
        )
        if response.status_code == 200:
            execution_result = response.json()
            print(f"✅ Card execution successful")
        else:
            print(f"❌ Card execution failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Card execution request failed: {e}")
        return False
    
    # Test 4: Full Dashboard Retrieval
    print("\n4. Testing Full Dashboard Retrieval...")
    try:
        response = requests.get(
            f"http://localhost:8000/api/v1/analytics/dashboards/{dashboard_id}/full",
            timeout=10
        )
        if response.status_code == 200:
            full_dashboard = response.json()
            print(f"✅ Full dashboard retrieval successful: {full_dashboard['name']}")
        else:
            print(f"❌ Full dashboard retrieval failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Full dashboard retrieval request failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 INTEGRATION TEST PASSED!")
    print("\n📋 Summary:")
    print("✅ Backend API: Running and healthy")
    print("✅ Frontend: Accessible and responsive")
    print("✅ Dashboard CRUD: Working")
    print("✅ Card Management: Working") 
    print("✅ Card Execution: Working")
    print("✅ Full Integration: Success")
    
    print(f"\n🚀 Your analytics system is ready!")
    print(f"🌐 Frontend: http://localhost:3000 (Click Analytics Dashboard tab)")
    print(f"📊 Backend API: http://localhost:8000/docs")
    print(f"📈 Dashboard ID: {dashboard_id}")
    
    return True

if __name__ == "__main__":
    success = test_frontend_backend_integration()
    exit(0 if success else 1)
