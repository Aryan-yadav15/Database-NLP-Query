"""
Test Suite for MySQL and SQLite Database Services
================================================

This test suite validates the implementation of MySQL and SQLite database services
following the same patterns established by the PostgreSQL service tests.

Test Coverage:
- Connection management and validation
- Schema introspection and extraction
- Query execution (SELECT, INSERT, UPDATE, DELETE)
- Parameterized queries for SQL injection prevention
- Error handling and recovery
- Feature support validation
- Service factory integration

Author: Brain LLM Team
"""

import pytest
import os
import tempfile
import sqlite3
import mysql.connector
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from app.services.db.base import ConnectionInfo, QueryResult
from app.services.db.mysql import MySQLService
from app.services.db.sqlite import SQLiteService
from app.services.db import get_database_service, get_supported_database_types


class TestMySQLService:
    """Test suite for MySQL database service implementation."""
    
    @pytest.fixture
    def mysql_connection_info(self):
        """Fixture providing MySQL connection information for testing."""
        return ConnectionInfo(
            db_type="mysql",
            db_host="localhost",
            db_port=3306,
            db_name="test_database",
            db_user="test_user",
            db_password="test_password"
        )
    
    @pytest.fixture
    def mysql_service(self):
        """Fixture providing MySQL service instance."""
        return MySQLService()
    
    def test_mysql_service_initialization(self, mysql_service):
        """Test MySQL service can be initialized successfully."""
        assert mysql_service is not None
        assert isinstance(mysql_service, MySQLService)
        assert mysql_service.get_database_type() == "mysqlservice"
    
    def test_get_connection_string(self, mysql_service, mysql_connection_info):
        """Test MySQL connection string generation."""
        connection_string = mysql_service.get_connection_string(mysql_connection_info)
        
        assert "mysql+mysqlconnector://" in connection_string
        assert "test_user" in connection_string
        assert "localhost:3306" in connection_string
        assert "test_database" in connection_string
        # Password should be URL encoded
        assert "test_password" in connection_string
    
    def test_get_supported_features(self, mysql_service):
        """Test MySQL supported features matrix."""
        features = mysql_service.get_supported_features()
        
        assert isinstance(features, dict)
        assert features["connection_pooling"] == True
        assert features["transactions"] == True
        assert features["foreign_keys"] == True
        assert features["stored_procedures"] == True
        assert features["json_support"] == True
        assert features["auto_increment"] == True
        assert features["upsert"] == True
        assert features["array_support"] == False  # Not native in MySQL
        assert features["materialized_views"] == False  # Not supported
    
    @patch('mysql.connector.connect')
    def test_mysql_connection_success(self, mock_connect, mysql_service, mysql_connection_info):
        """Test successful MySQL connection."""
        # Mock connection and cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'test': 1}
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        # Test connection context manager
        connections = list(mysql_service.get_connection(mysql_connection_info))
        
        assert len(connections) == 1
        assert mock_connect.called
        mock_connection.close.assert_called_once()
    
    @patch('mysql.connector.connect')
    def test_mysql_connection_failure(self, mock_connect, mysql_service, mysql_connection_info):
        """Test MySQL connection failure handling."""
        # Mock connection failure
        mock_connect.side_effect = mysql.connector.Error("Connection failed")
        
        with pytest.raises(Exception):
            list(mysql_service.get_connection(mysql_connection_info))
    
    @patch('mysql.connector.connect')
    def test_validate_mysql_connection_success(self, mock_connect, mysql_service, mysql_connection_info):
        """Test MySQL connection validation success."""
        # Mock successful connection
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("8.0.33",)
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        is_valid, error = mysql_service.validate_connection(mysql_connection_info)
        
        assert is_valid == True
        assert error is None
        mock_connect.assert_called_once()
        mock_connection.close.assert_called_once()
    
    @patch('mysql.connector.connect')
    def test_validate_mysql_connection_failure(self, mock_connect, mysql_service, mysql_connection_info):
        """Test MySQL connection validation failure."""
        # Mock connection failure
        mock_connect.side_effect = mysql.connector.Error("Access denied")
        
        is_valid, error = mysql_service.validate_connection(mysql_connection_info)
        
        assert is_valid == False
        assert "Access denied" in error
    
    def test_mysql_query_execution_mock(self, mysql_service):
        """Test MySQL query execution with mocked connection."""
        # Mock connection and cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        
        # Mock SELECT query response
        mock_cursor.description = [('id',), ('name',)]
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'name': 'John'},
            {'id': 2, 'name': 'Jane'}
        ]
        mock_connection.cursor.return_value = mock_cursor
        
        result = mysql_service.execute_query(mock_connection, "SELECT id, name FROM users")
        
        assert result.success == True
        assert result.row_count == 2
        assert len(result.data) == 2
        assert result.columns == ['id', 'name']
        assert result.data[0]['name'] == 'John'
    
    def test_mysql_insert_query_mock(self, mysql_service):
        """Test MySQL INSERT query execution."""
        # Mock connection and cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        
        # Mock INSERT query response
        mock_cursor.description = None
        mock_cursor.rowcount = 1
        mock_cursor.lastrowid = 123
        mock_connection.cursor.return_value = mock_cursor
        
        result = mysql_service.execute_query(mock_connection, "INSERT INTO users (name) VALUES ('Test')")
        
        assert result.success == True
        assert result.row_count == 1
        assert len(result.data) == 1
        assert result.data[0]['last_insert_id'] == 123
    
    def test_mysql_parameterized_query(self, mysql_service):
        """Test MySQL parameterized query execution."""
        # Mock connection and cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        
        mock_cursor.description = [('id',), ('name',)]
        mock_cursor.fetchall.return_value = [{'id': 1, 'name': 'John'}]
        mock_connection.cursor.return_value = mock_cursor
        
        params = {'user_id': 1}
        result = mysql_service.execute_query_with_params(
            mock_connection, 
            "SELECT id, name FROM users WHERE id = %(user_id)s", 
            params
        )
        
        assert result.success == True
        assert result.row_count == 1
        mock_cursor.execute.assert_called_once()


class TestSQLiteService:
    """Test suite for SQLite database service implementation."""
    
    @pytest.fixture
    def sqlite_connection_info(self):
        """Fixture providing SQLite connection information for testing."""
        return ConnectionInfo(
            db_type="sqlite",
            db_host="",  # Not used for SQLite
            db_port=0,   # Not used for SQLite
            db_name=":memory:",  # In-memory database for testing
            db_user="",  # Not used for SQLite
            db_password=""  # Not used for SQLite
        )
    
    @pytest.fixture
    def sqlite_file_connection_info(self, tmp_path):
        """Fixture providing file-based SQLite connection information."""
        db_file = tmp_path / "test.db"
        return ConnectionInfo(
            db_type="sqlite",
            db_host="",
            db_port=0,
            db_name=str(db_file),
            db_user="",
            db_password=""
        )
    
    @pytest.fixture
    def sqlite_service(self):
        """Fixture providing SQLite service instance."""
        return SQLiteService()
    
    def test_sqlite_service_initialization(self, sqlite_service):
        """Test SQLite service can be initialized successfully."""
        assert sqlite_service is not None
        assert isinstance(sqlite_service, SQLiteService)
        assert sqlite_service.get_database_type() == "sqliteservice"
    
    def test_get_connection_string_memory(self, sqlite_service, sqlite_connection_info):
        """Test SQLite in-memory connection string generation."""
        connection_string = sqlite_service.get_connection_string(sqlite_connection_info)
        assert connection_string == "sqlite:///:memory:"
    
    def test_get_connection_string_file(self, sqlite_service, sqlite_file_connection_info):
        """Test SQLite file-based connection string generation."""
        connection_string = sqlite_service.get_connection_string(sqlite_file_connection_info)
        assert "sqlite:///" in connection_string
        assert "test.db" in connection_string
    
    def test_get_supported_features(self, sqlite_service):
        """Test SQLite supported features matrix."""
        features = sqlite_service.get_supported_features()
        
        assert isinstance(features, dict)
        assert features["connection_pooling"] == False  # SQLite is file-based
        assert features["transactions"] == True
        assert features["foreign_keys"] == True  # But disabled by default
        assert features["window_functions"] == True
        assert features["json_support"] == True
        assert features["auto_increment"] == True
        assert features["upsert"] == True
        assert features["in_memory_database"] == True
        assert features["file_based"] == True
        assert features["stored_procedures"] == False  # Not supported
        assert features["materialized_views"] == False  # Not supported
    
    def test_sqlite_memory_connection_success(self, sqlite_service, sqlite_connection_info):
        """Test successful SQLite in-memory connection."""
        connections = list(sqlite_service.get_connection(sqlite_connection_info))
        
        assert len(connections) == 1
        # Connection should be automatically closed by context manager
    
    def test_sqlite_file_connection_success(self, sqlite_service, sqlite_file_connection_info):
        """Test successful SQLite file-based connection."""
        connections = list(sqlite_service.get_connection(sqlite_file_connection_info))
        
        assert len(connections) == 1
        # Database file should be created
        assert os.path.exists(sqlite_file_connection_info.db_name)
    
    def test_validate_sqlite_connection_memory(self, sqlite_service, sqlite_connection_info):
        """Test SQLite in-memory connection validation."""
        is_valid, error = sqlite_service.validate_connection(sqlite_connection_info)
        
        assert is_valid == True
        assert error is None
    
    def test_validate_sqlite_connection_file(self, sqlite_service, sqlite_file_connection_info):
        """Test SQLite file-based connection validation."""
        is_valid, error = sqlite_service.validate_connection(sqlite_file_connection_info)
        
        assert is_valid == True
        assert error is None
        # Database file should be created during validation
        assert os.path.exists(sqlite_file_connection_info.db_name)
    
    def test_sqlite_query_execution_real(self, sqlite_service, sqlite_connection_info):
        """Test SQLite query execution with real in-memory database."""
        for connection in sqlite_service.get_connection(sqlite_connection_info):
            # Create test table
            create_result = sqlite_service.execute_query(
                connection, 
                "CREATE TABLE test_users (id INTEGER PRIMARY KEY, name TEXT)"
            )
            assert create_result.success == True
            
            # Insert test data
            insert_result = sqlite_service.execute_query(
                connection,
                "INSERT INTO test_users (name) VALUES ('John'), ('Jane')"
            )
            assert insert_result.success == True
            assert insert_result.row_count == 2
            
            # Query test data
            select_result = sqlite_service.execute_query(
                connection,
                "SELECT id, name FROM test_users ORDER BY id"
            )
            assert select_result.success == True
            assert select_result.row_count == 2
            assert len(select_result.data) == 2
            assert select_result.data[0]['name'] == 'John'
            assert select_result.data[1]['name'] == 'Jane'
    
    def test_sqlite_parameterized_query(self, sqlite_service, sqlite_connection_info):
        """Test SQLite parameterized query execution."""
        for connection in sqlite_service.get_connection(sqlite_connection_info):
            # Create test table
            sqlite_service.execute_query(
                connection, 
                "CREATE TABLE test_users (id INTEGER PRIMARY KEY, name TEXT)"
            )
            
            # Insert with parameters
            params = {'name': 'TestUser'}
            insert_result = sqlite_service.execute_query_with_params(
                connection,
                "INSERT INTO test_users (name) VALUES (:name)",
                params
            )
            assert insert_result.success == True
            
            # Query with parameters
            select_params = {'user_name': 'TestUser'}
            select_result = sqlite_service.execute_query_with_params(
                connection,
                "SELECT id, name FROM test_users WHERE name = :user_name",
                select_params
            )
            assert select_result.success == True
            assert select_result.row_count == 1
            assert select_result.data[0]['name'] == 'TestUser'
    
    def test_sqlite_schema_extraction(self, sqlite_service, sqlite_connection_info):
        """Test SQLite schema extraction functionality."""
        for connection in sqlite_service.get_connection(sqlite_connection_info):
            # Create test schema
            sqlite_service.execute_query(
                connection,
                """
                CREATE TABLE customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE
                )
                """
            )
            
            sqlite_service.execute_query(
                connection,
                """
                CREATE TABLE orders (
                    id INTEGER PRIMARY KEY,
                    customer_id INTEGER,
                    total REAL,
                    FOREIGN KEY (customer_id) REFERENCES customers(id)
                )
                """
            )
            
            # Extract schema
            schema_string = sqlite_service.get_schema_string(connection)
            
            assert "Database: main" in schema_string
            assert "SQLite Version:" in schema_string
            assert "Table: customers" in schema_string
            assert "Table: orders" in schema_string
            assert "PRIMARY KEY" in schema_string
            assert "Foreign Key:" in schema_string
    
    def test_sqlite_table_names(self, sqlite_service, sqlite_connection_info):
        """Test SQLite table name extraction."""
        for connection in sqlite_service.get_connection(sqlite_connection_info):
            # Create test tables
            sqlite_service.execute_query(connection, "CREATE TABLE table1 (id INTEGER)")
            sqlite_service.execute_query(connection, "CREATE TABLE table2 (id INTEGER)")
            
            table_names = sqlite_service.get_table_names(connection)
            
            assert "table1" in table_names
            assert "table2" in table_names
            assert len(table_names) == 2
    
    def test_sqlite_create_database_file(self, sqlite_service, tmp_path):
        """Test SQLite database file creation."""
        db_file = tmp_path / "created_test.db"
        
        success = sqlite_service.create_database_file(str(db_file))
        
        assert success == True
        assert os.path.exists(db_file)
        
        # Verify database was created properly
        connection = sqlite3.connect(str(db_file))
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys")
        fk_setting = cursor.fetchone()[0]
        cursor.close()
        connection.close()
        
        assert fk_setting == 1  # Foreign keys should be enabled


class TestDatabaseServiceFactory:
    """Test suite for database service factory integration."""
    
    def test_factory_supports_mysql(self):
        """Test factory supports MySQL service creation."""
        supported_types = get_supported_database_types()
        
        assert "mysql" in supported_types
        assert "mariadb" in supported_types
        
        # Test service creation
        mysql_service = get_database_service("mysql")
        assert isinstance(mysql_service, MySQLService)
        
        # Test with alias
        mariadb_service = get_database_service("mariadb")
        assert isinstance(mariadb_service, MySQLService)
    
    def test_factory_supports_sqlite(self):
        """Test factory supports SQLite service creation."""
        supported_types = get_supported_database_types()
        
        assert "sqlite" in supported_types
        assert "sqlite3" in supported_types
        
        # Test service creation
        sqlite_service = get_database_service("sqlite")
        assert isinstance(sqlite_service, SQLiteService)
        
        # Test with alias
        sqlite3_service = get_database_service("sqlite3")
        assert isinstance(sqlite3_service, SQLiteService)
    
    def test_factory_with_connection_info(self):
        """Test factory service creation with connection info."""
        mysql_conn_info = ConnectionInfo(
            db_type="mysql",
            db_host="localhost",
            db_port=3306,
            db_name="test",
            db_user="user",
            db_password="pass"
        )
        
        mysql_service = get_database_service("mysql", mysql_conn_info)
        assert isinstance(mysql_service, MySQLService)
        assert mysql_service.connection_info == mysql_conn_info
        
        sqlite_conn_info = ConnectionInfo(
            db_type="sqlite",
            db_host="",
            db_port=0,
            db_name=":memory:",
            db_user="",
            db_password=""
        )
        
        sqlite_service = get_database_service("sqlite", sqlite_conn_info)
        assert isinstance(sqlite_service, SQLiteService)
        assert sqlite_service.connection_info == sqlite_conn_info
    
    def test_factory_unsupported_database(self):
        """Test factory handling of unsupported database types."""
        with pytest.raises(ValueError) as exc_info:
            get_database_service("oracle")
        
        assert "Unsupported database type" in str(exc_info.value)
        assert "oracle" in str(exc_info.value)


class TestIntegrationScenarios:
    """Integration test scenarios for MySQL and SQLite services."""
    
    def test_cross_database_consistency(self):
        """Test that both services provide consistent interfaces."""
        mysql_service = get_database_service("mysql")
        sqlite_service = get_database_service("sqlite")
        
        # Both should have the same interface methods
        interface_methods = [
            'get_connection', 'get_engine', 'validate_connection',
            'get_schema_string', 'get_table_names', 'get_table_schema',
            'execute_query', 'execute_query_with_params',
            'get_connection_string', 'get_supported_features'
        ]
        
        for method in interface_methods:
            assert hasattr(mysql_service, method)
            assert hasattr(sqlite_service, method)
            assert callable(getattr(mysql_service, method))
            assert callable(getattr(sqlite_service, method))
    
    def test_feature_matrix_completeness(self):
        """Test that both services provide complete feature matrices."""
        mysql_service = get_database_service("mysql")
        sqlite_service = get_database_service("sqlite")
        
        mysql_features = mysql_service.get_supported_features()
        sqlite_features = sqlite_service.get_supported_features()
        
        # Both should have the same feature keys for consistency
        common_features = [
            'connection_pooling', 'transactions', 'foreign_keys',
            'stored_procedures', 'window_functions', 'json_support',
            'upsert', 'auto_increment'
        ]
        
        for feature in common_features:
            assert feature in mysql_features
            assert feature in sqlite_features
            assert isinstance(mysql_features[feature], bool)
            assert isinstance(sqlite_features[feature], bool)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
