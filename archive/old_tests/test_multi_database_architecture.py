"""
Multi-Database Architecture Test Script
=======================================

This script tests the new multi-database architecture implementation
to ensure backward compatibility and validate the PostgreSQL service.

Test Coverage:
- Database service factory functionality
- PostgreSQL service implementation
- Enhanced connection manager
- Backward compatibility with existing code
- Connection validation and error handling

Author: Brain LLM Team
"""

import sys
import os

# Add the parent directory to the path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brain_llm'))

def test_database_service_factory():
    """Test the database service factory functionality."""
    print("🧪 Testing Database Service Factory...")
    
    try:
        from app.services.db import (
            get_database_service, 
            get_supported_database_types, 
            is_database_type_supported,
            validate_database_connection_info
        )
        
        # Test supported types
        supported_types = get_supported_database_types()
        print(f"   ✅ Supported database types: {supported_types}")
        
        # Test type checking
        assert is_database_type_supported("postgresql"), "PostgreSQL should be supported"
        assert is_database_type_supported("postgres"), "PostgreSQL alias should be supported"
        assert not is_database_type_supported("oracle"), "Oracle should not be supported yet"
        print("   ✅ Database type validation working")
        
        # Test service creation
        pg_service = get_database_service("postgresql")
        assert pg_service is not None, "PostgreSQL service should be created"
        print("   ✅ PostgreSQL service creation successful")
        
        # Test service features
        features = pg_service.get_supported_features()
        assert features.get("connection_pooling") == True, "PostgreSQL should support connection pooling"
        print(f"   ✅ PostgreSQL features: {len(features)} features supported")
        
        print("✅ Database Service Factory tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database Service Factory test failed: {e}")
        return False

def test_connection_info():
    """Test ConnectionInfo data class functionality."""
    print("🧪 Testing ConnectionInfo...")
    
    try:
        from app.services.db.base import ConnectionInfo
        
        # Test creation from dict
        conn_dict = {
            "db_type": "postgresql",
            "db_host": "localhost",
            "db_port": 5432,
            "db_name": "test",
            "db_user": "user",
            "db_password": "password"
        }
        
        conn_info = ConnectionInfo.from_dict(conn_dict)
        assert conn_info.db_type == "postgresql", "Database type should be set correctly"
        assert conn_info.db_port == 5432, "Port should be set correctly"
        print("   ✅ ConnectionInfo creation from dict working")
        
        # Test to_dict (password masking)
        conn_dict_out = conn_info.to_dict()
        assert conn_dict_out["db_password"] == "***", "Password should be masked in output"
        print("   ✅ Password masking in to_dict working")
        
        print("✅ ConnectionInfo tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ ConnectionInfo test failed: {e}")
        return False

def test_enhanced_connection_manager():
    """Test the enhanced connection manager."""
    print("🧪 Testing Enhanced Connection Manager...")
    
    try:
        from app.services.connection_manager import connection_manager
        
        # Test service caching
        pg_service1 = connection_manager.get_database_service("postgresql")
        pg_service2 = connection_manager.get_database_service("postgresql")
        assert pg_service1 is pg_service2, "Database services should be cached"
        print("   ✅ Database service caching working")
        
        # Test connection statistics
        stats = connection_manager.get_connection_statistics()
        assert "database_services_cached" in stats, "Statistics should include service count"
        assert stats["database_services_cached"] >= 1, "Should have at least one cached service"
        print(f"   ✅ Connection statistics: {stats}")
        
        # Test unsupported database type
        try:
            connection_manager.get_database_service("oracle")
            assert False, "Should raise error for unsupported database"
        except ValueError as e:
            assert "Unsupported database type" in str(e), "Should raise appropriate error"
            print("   ✅ Unsupported database type handling working")
        
        print("✅ Enhanced Connection Manager tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced Connection Manager test failed: {e}")
        return False

def test_postgresql_service():
    """Test PostgreSQL service functionality (without actual database connection)."""
    print("🧪 Testing PostgreSQL Service...")
    
    try:
        from app.services.db.postgresql import PostgreSQLService
        from app.services.db.base import ConnectionInfo
        
        # Create PostgreSQL service
        pg_service = PostgreSQLService()
        
        # Test supported features
        features = pg_service.get_supported_features()
        expected_features = ["connection_pooling", "transactions", "foreign_keys", "json_support"]
        for feature in expected_features:
            assert features.get(feature) == True, f"PostgreSQL should support {feature}"
        print(f"   ✅ PostgreSQL features validated: {len(features)} features")
        
        # Test connection string generation
        conn_info = ConnectionInfo(
            db_type="postgresql",
            db_host="localhost",
            db_port=5432,
            db_name="test",
            db_user="user",
            db_password="pass@word"
        )
        
        conn_string = pg_service.get_connection_string(conn_info)
        assert "postgresql+psycopg2://" in conn_string, "Connection string should use correct driver"
        assert "pass%40word" in conn_string, "Password should be URL encoded"
        print("   ✅ PostgreSQL connection string generation working")
        
        # Test database type
        db_type = pg_service.get_database_type()
        assert "postgresql" in db_type.lower(), "Database type should be PostgreSQL"
        print("   ✅ PostgreSQL database type identification working")
        
        print("✅ PostgreSQL Service tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL Service test failed: {e}")
        return False

def test_validation():
    """Test connection validation functionality."""
    print("🧪 Testing Connection Validation...")
    
    try:
        from app.services.db import validate_database_connection_info
        
        # Test valid connection info
        valid_conn = {
            "db_type": "postgresql",
            "db_host": "localhost",
            "db_port": 5432,
            "db_name": "test",
            "db_user": "user",
            "db_password": "password"
        }
        
        is_valid, error = validate_database_connection_info(valid_conn)
        assert is_valid == True, "Valid connection info should pass validation"
        assert error is None, "Should not have error for valid connection"
        print("   ✅ Valid connection info validation working")
        
        # Test invalid connection info (missing fields)
        invalid_conn = {
            "db_type": "postgresql",
            "db_host": "localhost"
            # Missing required fields
        }
        
        is_valid, error = validate_database_connection_info(invalid_conn)
        assert is_valid == False, "Invalid connection info should fail validation"
        assert error is not None, "Should have error message for invalid connection"
        assert "Missing required fields" in error, "Error should mention missing fields"
        print("   ✅ Invalid connection info validation working")
        
        # Test unsupported database type
        unsupported_conn = {
            "db_type": "oracle",
            "db_host": "localhost",
            "db_port": 1521,
            "db_name": "test",
            "db_user": "user",
            "db_password": "password"
        }
        
        is_valid, error = validate_database_connection_info(unsupported_conn)
        assert is_valid == False, "Unsupported database should fail validation"
        assert "Unsupported database type" in error, "Error should mention unsupported type"
        print("   ✅ Unsupported database type validation working")
        
        print("✅ Connection Validation tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Connection Validation test failed: {e}")
        return False

def run_all_tests():
    """Run all tests and report results."""
    print("🚀 Starting Multi-Database Architecture Tests\n")
    
    tests = [
        ("Database Service Factory", test_database_service_factory),
        ("ConnectionInfo", test_connection_info),
        ("Enhanced Connection Manager", test_enhanced_connection_manager),
        ("PostgreSQL Service", test_postgresql_service),
        ("Connection Validation", test_validation)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print('='*60)
        
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            failed += 1
    
    print(f"\n{'='*60}")
    print("🏁 TEST RESULTS")
    print('='*60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! Multi-database architecture is working correctly.")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
