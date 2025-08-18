#!/usr/bin/env python3
"""
API Integration Test Script
==========================

This script tests the Chat UI to Backend integration by sending a test payload
and verifying the streaming response format.
"""

import json
import requests
import time

def test_backend_direct():
    """Test the backend API directly"""
    print("🔧 Testing Backend API directly...")
    
    url = "http://localhost:8000/api/v1/query/stream"
    payload = {
        "query_text": "what are the total number of artists",
        "user_id": "b521b8a1-0b9d-45e6-991d-1476c5f6fee8",
        "conversation_id": "test-conversation-id",
        "message_id": "test-message-id",
        "chat_history": [],
        "short_term_memory": [
            "SUMMARY: The table names are case sensitive, use double quotes while generating commands"
        ],
        "model_name": "gemini-2.0-flash",
        "temperature": 0.2,
        "api_key": "xyz",
        "db_connection_info": {
            "db_host": "localhost",
            "db_port": 5432,
            "db_user": "postgres",
            "db_name": "chinook",
            "db_password": "iamaryan15",
            "db_schema": None
        }
    }
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            },
            stream=True
        )
        
        if response.status_code == 200:
            print("✅ Backend API is responding")
            print("📡 Streaming response:")
            
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])
                        print(f"   📋 {data.get('type', 'unknown')}: {data}")
                    except json.JSONDecodeError:
                        print(f"   ⚠️  Could not parse: {line}")
                        
        else:
            print(f"❌ Backend API failed with status: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend API. Is it running on port 8000?")
    except Exception as e:
        print(f"❌ Error testing backend API: {e}")

def test_frontend_api():
    """Test the frontend API route"""
    print("\n🌐 Testing Frontend API route...")
    
    url = "http://localhost:3000/api/v1/query"
    payload = {
        "query": "what are the total number of artists",
        "conversation_id": "test-conversation-id",
        "message_id": "test-message-id",
        "chat_history": [],
        "short_term_memory": [
            "SUMMARY: The table names are case sensitive, use double quotes while generating commands"
        ],
        "db_connection": {
            "db_host": "localhost",
            "db_port": 5432,
            "db_user": "postgres",
            "db_name": "chinook",
            "db_password": "iamaryan15",
            "db_schema": None
        }
    }
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            },
            stream=True
        )
        
        if response.status_code == 200:
            print("✅ Frontend API route is working")
            print("📡 Streaming response:")
            
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])
                        print(f"   📋 {data.get('type', 'unknown')}: {data}")
                    except json.JSONDecodeError:
                        print(f"   ⚠️  Could not parse: {line}")
                        
        else:
            print(f"❌ Frontend API route failed with status: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to frontend API. Is Next.js running on port 3000?")
    except Exception as e:
        print(f"❌ Error testing frontend API: {e}")

def check_services():
    """Check if both services are running"""
    print("🔍 Checking service availability...")
    
    # Check backend
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend service is running")
        else:
            print(f"⚠️  Backend service returned status: {response.status_code}")
    except:
        print("❌ Backend service is not accessible")
    
    # Check frontend
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend service is running")
        else:
            print(f"⚠️  Frontend service returned status: {response.status_code}")
    except:
        print("❌ Frontend service is not accessible")

if __name__ == "__main__":
    print("🚀 API Integration Test")
    print("=" * 50)
    
    check_services()
    test_backend_direct()
    test_frontend_api()
    
    print("\n✨ Test complete!")
    print("\n📋 Next steps:")
    print("1. Open http://localhost:3000 in your browser")
    print("2. Try sending a message: 'what are the total number of artists'")
    print("3. Verify streaming response appears in real-time")
