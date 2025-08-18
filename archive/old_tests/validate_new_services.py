"""
Simple validation script for MySQL and SQLite services
=====================================================

This script provides basic validation of the MySQL and SQLite database services
without requiring external test frameworks. It tests core functionality and
reports any issues found.

Usage:
    python validate_new_services.py
"""

import sys
import os
import tempfile
import sqlite3
from pathlib import Path

# Add the brain_llm directory to Python path
brain_llm_path = os.path.join(os.path.dirname(__file__), 'brain_llm')
sys.path.insert(0, brain_llm_path)

try:
    from app.services.db.base import ConnectionInfo, QueryResult
    from app.services.db.mysql import MySQLService
    from app.services.db.sqlite import SQLiteService
    from app.services.db import get_database_service, get_supported_database_types
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the correct directory")
    sys.exit(1)


def test_mysql_service_basic():
    """Test basic MySQL service functionality."""
    print("\\n=== Testing MySQL Service ===")
    
    try:
        # Test service creation
        mysql_service = MySQLService()
        print("✓ MySQL service created successfully")
        
        # Test connection info
        conn_info = ConnectionInfo(
            db_type="mysql",
            db_host="localhost",
            db_port=3306,
            db_name="test",
            db_user="user",
            db_password="password"
        )
        print("✓ MySQL connection info created")
        
        # Test connection string generation
        conn_string = mysql_service.get_connection_string(conn_info)
        assert "mysql+mysqlconnector://" in conn_string
        print(f"✓ MySQL connection string: {conn_string}")
        
        # Test supported features
        features = mysql_service.get_supported_features()
        assert isinstance(features, dict)
        assert features["connection_pooling"] == True
        assert features["auto_increment"] == True
        print(f"✓ MySQL features loaded: {len(features)} features")
        
        print("✓ All MySQL basic tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ MySQL test failed: {e}")
        return False


def test_sqlite_service_basic():
    """Test basic SQLite service functionality."""
    print("\\n=== Testing SQLite Service ===")
    
    try:
        # Test service creation
        sqlite_service = SQLiteService()
        print("✓ SQLite service created successfully")
        
        # Test in-memory connection info
        memory_conn_info = ConnectionInfo(
            db_type="sqlite",
            db_host="",
            db_port=0,
            db_name=":memory:",
            db_user="",
            db_password=""
        )
        print("✓ SQLite in-memory connection info created")
        
        # Test file connection info
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            file_conn_info = ConnectionInfo(
                db_type="sqlite",
                db_host="",
                db_port=0,
                db_name=tmp_file.name,
                db_user="",
                db_password=""
            )
        print("✓ SQLite file connection info created")
        
        # Test connection string generation
        memory_conn_string = sqlite_service.get_connection_string(memory_conn_info)
        assert memory_conn_string == "sqlite:///:memory:"
        print(f"✓ SQLite memory connection string: {memory_conn_string}")
        
        file_conn_string = sqlite_service.get_connection_string(file_conn_info)
        assert "sqlite:///" in file_conn_string
        print(f"✓ SQLite file connection string: {file_conn_string}")
        
        # Test supported features
        features = sqlite_service.get_supported_features()
        assert isinstance(features, dict)
        assert features["connection_pooling"] == False
        assert features["file_based"] == True
        assert features["in_memory_database"] == True
        print(f"✓ SQLite features loaded: {len(features)} features")
        
        # Clean up temp file
        try:
            os.unlink(file_conn_info.db_name)
        except:
            pass
        
        print("✓ All SQLite basic tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ SQLite test failed: {e}")
        return False


def test_sqlite_real_operations():
    """Test SQLite with real database operations."""
    print("\\n=== Testing SQLite Real Operations ===")
    
    try:
        sqlite_service = SQLiteService()
        
        # Test in-memory database
        memory_conn_info = ConnectionInfo(
            db_type="sqlite",
            db_host="",
            db_port=0,
            db_name=":memory:",
            db_user="",
            db_password=""
        )
        
        # Test connection validation
        is_valid, error = sqlite_service.validate_connection(memory_conn_info)
        assert is_valid == True
        assert error is None
        print("✓ SQLite connection validation passed")
        
        # Test real database operations
        for connection in sqlite_service.get_connection(memory_conn_info):
            # Create table
            create_result = sqlite_service.execute_query(
                connection,
                "CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT, value REAL)"
            )
            assert create_result.success == True
            print("✓ Table created successfully")
            
            # Insert data
            insert_result = sqlite_service.execute_query(
                connection,
                "INSERT INTO test_table (name, value) VALUES ('test1', 10.5), ('test2', 20.3)"
            )
            assert insert_result.success == True
            assert insert_result.row_count == 2
            print("✓ Data inserted successfully")
            
            # Query data
            select_result = sqlite_service.execute_query(
                connection,
                "SELECT id, name, value FROM test_table ORDER BY id"
            )
            assert select_result.success == True
            assert select_result.row_count == 2
            assert len(select_result.data) == 2
            assert select_result.data[0]['name'] == 'test1'
            print("✓ Data queried successfully")
            
            # Test parameterized query
            param_result = sqlite_service.execute_query_with_params(
                connection,
                "SELECT * FROM test_table WHERE name = :name",
                {'name': 'test1'}
            )
            assert param_result.success == True
            assert param_result.row_count == 1
            print("✓ Parameterized query executed successfully")
            
            # Test schema extraction
            schema_string = sqlite_service.get_schema_string(connection)
            assert "test_table" in schema_string
            assert "PRIMARY KEY" in schema_string
            print("✓ Schema extraction successful")
            
            # Test table names
            table_names = sqlite_service.get_table_names(connection)
            assert "test_table" in table_names
            print("✓ Table names extracted successfully")
        
        print("✓ All SQLite real operations passed!")
        return True
        
    except Exception as e:
        print(f"✗ SQLite real operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_factory_integration():
    """Test database service factory integration."""
    print("\\n=== Testing Factory Integration ===")
    
    try:
        # Test supported types
        supported_types = get_supported_database_types()
        assert "mysql" in supported_types
        assert "sqlite" in supported_types
        assert "postgresql" in supported_types
        print(f"✓ Supported types: {supported_types}")
        
        # Test MySQL service creation via factory
        mysql_service = get_database_service("mysql")
        assert isinstance(mysql_service, MySQLService)
        print("✓ MySQL service created via factory")
        
        # Test MySQL alias
        mariadb_service = get_database_service("mariadb")
        assert isinstance(mariadb_service, MySQLService)
        print("✓ MariaDB alias works")
        
        # Test SQLite service creation via factory
        sqlite_service = get_database_service("sqlite")
        assert isinstance(sqlite_service, SQLiteService)
        print("✓ SQLite service created via factory")
        
        # Test SQLite alias
        sqlite3_service = get_database_service("sqlite3")
        assert isinstance(sqlite3_service, SQLiteService)
        print("✓ SQLite3 alias works")
        
        # Test with connection info
        conn_info = ConnectionInfo(
            db_type="sqlite",
            db_host="",
            db_port=0,
            db_name=":memory:",
            db_user="",
            db_password=""
        )
        
        service_with_conn = get_database_service("sqlite", conn_info)
        assert isinstance(service_with_conn, SQLiteService)
        assert service_with_conn.connection_info == conn_info
        print("✓ Service created with connection info")
        
        # Test unsupported database
        try:
            get_database_service("oracle")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Unsupported database type" in str(e)
            print("✓ Unsupported database properly rejected")
        
        print("✓ All factory integration tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Factory integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_based_sqlite():
    """Test SQLite file-based database creation and operations."""
    print("\\n=== Testing File-based SQLite ===")
    
    try:
        sqlite_service = SQLiteService()
        
        # Create temporary database file
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        # Test database file creation
        success = sqlite_service.create_database_file(db_path)
        assert success == True
        assert os.path.exists(db_path)
        print(f"✓ Database file created: {db_path}")
        
        # Test connection to file database
        file_conn_info = ConnectionInfo(
            db_type="sqlite",
            db_host="",
            db_port=0,
            db_name=db_path,
            db_user="",
            db_password=""
        )
        
        is_valid, error = sqlite_service.validate_connection(file_conn_info)
        assert is_valid == True
        assert error is None
        print("✓ File database connection validated")
        
        # Test operations on file database
        for connection in sqlite_service.get_connection(file_conn_info):
            # Create table
            sqlite_service.execute_query(
                connection,
                "CREATE TABLE file_test (id INTEGER PRIMARY KEY, data TEXT)"
            )
            
            # Insert data
            sqlite_service.execute_query(
                connection,
                "INSERT INTO file_test (data) VALUES ('persistent data')"
            )
            print("✓ Data written to file database")
        
        # Verify data persists by reconnecting
        for connection in sqlite_service.get_connection(file_conn_info):
            result = sqlite_service.execute_query(
                connection,
                "SELECT data FROM file_test"
            )
            assert result.success == True
            assert result.row_count == 1
            assert result.data[0]['data'] == 'persistent data'
            print("✓ Data persisted across connections")
        
        # Clean up
        os.unlink(db_path)
        print("✓ All file-based SQLite tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ File-based SQLite test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation tests."""
    print("Database Services Validation Script")
    print("=" * 50)
    
    tests = [
        test_mysql_service_basic,
        test_sqlite_service_basic,
        test_sqlite_real_operations,
        test_factory_integration,
        test_file_based_sqlite
    ]
    
    results = []
    
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{i+1}. {test.__name__}: {status}")
    
    print(f"\\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! MySQL and SQLite services are working correctly.")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
