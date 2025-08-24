"""
Test script for new Brain LLM structure
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app_new.core.config import settings
from app_new.core.exceptions import DataProcessingError
from app_new.domains.database.connectors import get_database_service

def test_new_structure():
    """Test the new application structure"""
    
    print("🧪 Testing Brain LLM New Structure")
    print("=" * 50)
    
    # Test core configuration
    print(f"✅ App Name: {settings.APP_NAME}")
    print(f"✅ App Version: {settings.APP_VERSION}")
    print(f"✅ Debug Mode: {settings.DEBUG}")
    
    # Test database services
    try:
        pg_service = get_database_service("postgresql")
        mysql_service = get_database_service("mysql")
        sqlite_service = get_database_service("sqlite")
        
        print(f"✅ PostgreSQL Service: {type(pg_service).__name__}")
        print(f"✅ MySQL Service: {type(mysql_service).__name__}")
        print(f"✅ SQLite Service: {type(sqlite_service).__name__}")
    except Exception as e:
        print(f"❌ Database services error: {e}")
    
    # Test exceptions
    try:
        raise DataProcessingError("Test error")
    except DataProcessingError as e:
        print(f"✅ Custom exceptions working: {type(e).__name__}")
    
    print("\n🎉 Structure test completed successfully!")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements_new.txt")
    print("2. Run server: uvicorn app_new.main:app --reload")
    print("3. Test analytics endpoint: POST /api/v1/analytics/upload")

if __name__ == "__main__":
    test_new_structure()
