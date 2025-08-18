#!/usr/bin/env python3
"""
Phase 5.3 Dependency Injection Validation Tests

This test suite validates the enhanced dependency injection system in deps.py,
ensuring all multi-database dependencies work correctly and maintain backward
compatibility.

Test Coverage:
1. Utility functions for database connection extraction
2. Multi-database service dependencies
3. Enhanced composite service dependencies
4. Backward compatibility with existing PostgreSQL workflows

Author: Multi-Database Migration System
Date: 2024
"""

import pytest
import sys
import os
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

# Add the project root to Python path
project_root = r"c:\Codes\BUILDS\Deloitte\brain_llm"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Test imports
from app.api.v1.deps import (
    extract_db_connection_info_from_request,
    validate_database_connection_info,
    get_connection_manager,
    get_database_service,
    get_dynamic_database_connection,
    get_database_service_from_request,
    get_token_usage_service,
    get_visualization_service
)

class TestUtilityFunctions:
    """Test utility functions for database connection handling."""
    
    def test_extract_db_connection_info_basic(self):
        """Test basic database connection info extraction."""
        request_data = {
            'db_connection_info': {
                'db_type': 'mysql',
                'db_host': 'localhost',
                'db_port': 3306,
                'db_name': 'testdb',
                'db_user': 'user',
                'db_password': 'password'
            }
        }
        
        result = extract_db_connection_info_from_request(request_data)
        
        assert result['db_type'] == 'mysql'
        assert result['db_host'] == 'localhost'
        assert result['db_port'] == 3306
        assert result['db_name'] == 'testdb'
        assert result['db_user'] == 'user'
        assert result['db_password'] == 'password'
    
    def test_extract_db_connection_info_defaults(self):
        """Test extraction with default values for missing fields."""
        request_data = {}
        
        result = extract_db_connection_info_from_request(request_data)
        
        # Should default to PostgreSQL with environment defaults
        assert result['db_type'] == 'postgresql'
        assert 'db_host' in result
        assert 'db_port' in result
        assert 'db_name' in result
    
    def test_validate_database_connection_info_sqlite(self):
        """Test validation for SQLite connections."""
        sqlite_info = {
            'db_type': 'sqlite',
            'db_name': '/path/to/database.db'
        }
        
        assert validate_database_connection_info(sqlite_info) == True
        
        # Test missing db_name for SQLite
        invalid_sqlite = {'db_type': 'sqlite'}
        assert validate_database_connection_info(invalid_sqlite) == False
    
    def test_validate_database_connection_info_other_dbs(self):
        """Test validation for PostgreSQL, MySQL, Snowflake."""
        valid_info = {
            'db_type': 'postgresql',
            'db_host': 'localhost',
            'db_port': 5432,
            'db_name': 'testdb',
            'db_user': 'user',
            'db_password': 'password'
        }
        
        assert validate_database_connection_info(valid_info) == True
        
        # Test missing required field
        invalid_info = {
            'db_type': 'mysql',
            'db_host': 'localhost',
            'db_port': 3306,
            # Missing db_name, db_user, db_password
        }
        
        assert validate_database_connection_info(invalid_info) == False

class TestDatabaseServiceDependencies:
    """Test multi-database service dependency injection."""
    
    @patch('app.api.v1.deps.ConnectionManager')
    def test_get_connection_manager_singleton(self, mock_connection_manager):
        """Test that connection manager is a singleton."""
        # Call dependency multiple times
        cm1 = get_connection_manager()
        cm2 = get_connection_manager()
        
        # Should be the same instance due to @lru_cache
        assert cm1 is cm2
        mock_connection_manager.assert_called_once()
    
    @patch('app.api.v1.deps.ConnectionManager')
    def test_get_database_service(self, mock_connection_manager):
        """Test database service factory dependency."""
        mock_cm_instance = Mock()
        mock_connection_manager.return_value = mock_cm_instance
        mock_service = Mock()
        mock_cm_instance.get_database_service.return_value = mock_service
        
        # Test factory function
        from app.api.v1.deps import get_database_service
        
        result = get_database_service('postgresql', {})
        
        mock_cm_instance.get_database_service.assert_called_once_with('postgresql', {})
        assert result == mock_service
    
    @pytest.mark.asyncio
    async def test_get_dynamic_database_connection(self):
        """Test dynamic database connection dependency."""
        mock_connection_manager = Mock()
        mock_connection_manager.get_connection_via_service.return_value = iter([Mock()])
        
        db_connection_info = {
            'db_type': 'postgresql',
            'db_host': 'localhost',
            'db_port': 5432,
            'db_name': 'testdb',
            'db_user': 'user',
            'db_password': 'password'
        }
        
        # Test the generator function
        from app.api.v1.deps import get_dynamic_database_connection
        
        generator = get_dynamic_database_connection(
            db_connection_info, mock_connection_manager
        )
        
        # Should yield connections
        connections = list(generator)
        assert len(connections) > 0
        mock_connection_manager.get_connection_via_service.assert_called_once()

class TestCompositeServiceDependencies:
    """Test enhanced composite service dependencies."""
    
    @pytest.mark.asyncio
    @patch('app.api.v1.deps.TokenUsageService')
    async def test_get_token_usage_service(self, mock_token_service_class):
        """Test token usage service with database service dependency."""
        # Mock database service
        mock_db_service = Mock()
        mock_token_service_instance = Mock()
        mock_token_service_class.return_value = mock_token_service_instance
        
        from app.api.v1.deps import get_token_usage_service
        
        result = await get_token_usage_service(mock_db_service)
        
        # Should create TokenUsageService with db_service
        mock_token_service_class.assert_called_once_with(db_service=mock_db_service)
        assert result == mock_token_service_instance
    
    @patch('app.api.v1.deps.VisualizationService')
    def test_get_visualization_service_enhanced(self, mock_viz_service_class):
        """Test enhanced visualization service with database service."""
        mock_llm_service = Mock()
        mock_db_service = Mock()
        mock_viz_service_instance = Mock()
        mock_viz_service_class.return_value = mock_viz_service_instance
        
        from app.api.v1.deps import get_visualization_service
        
        result = get_visualization_service(mock_llm_service, mock_db_service)
        
        # Should create VisualizationService with both LLM and DB services
        mock_viz_service_class.assert_called_once_with(
            llm_service=mock_llm_service, 
            db_service=mock_db_service
        )
        assert result == mock_viz_service_instance

class TestRequestBasedDependencies:
    """Test request-based dependency extraction."""
    
    @pytest.mark.asyncio
    @patch('app.api.v1.deps.ConnectionManager')
    async def test_get_database_service_from_request(self, mock_connection_manager):
        """Test extracting database service from request."""
        # Mock request with db_connection_info in state
        mock_request = Mock()
        mock_request.state.db_connection_info = {
            'db_type': 'mysql',
            'db_host': 'localhost'
        }
        
        mock_cm_instance = Mock()
        mock_connection_manager.return_value = mock_cm_instance
        mock_service = Mock()
        mock_cm_instance.get_database_service.return_value = mock_service
        
        from app.api.v1.deps import get_database_service_from_request
        
        result = get_database_service_from_request(mock_request, mock_cm_instance)
        
        # Should extract mysql from request state
        mock_cm_instance.get_database_service.assert_called_once_with('mysql')
        assert result == mock_service
    
    @patch('app.api.v1.deps.ConnectionManager')
    def test_get_database_service_from_request_fallback(self, mock_connection_manager):
        """Test fallback to PostgreSQL when extraction fails."""
        # Mock request without db_connection_info
        mock_request = Mock()
        mock_request.state = Mock()
        # No db_connection_info attribute
        
        mock_cm_instance = Mock()
        mock_connection_manager.return_value = mock_cm_instance
        mock_service = Mock()
        mock_cm_instance.get_database_service.return_value = mock_service
        
        from app.api.v1.deps import get_database_service_from_request
        
        result = get_database_service_from_request(mock_request, mock_cm_instance)
        
        # Should default to postgresql
        mock_cm_instance.get_database_service.assert_called_once_with('postgresql')
        assert result == mock_service

class TestBackwardCompatibility:
    """Test backward compatibility with existing PostgreSQL workflows."""
    
    def test_default_values_preserve_postgresql(self):
        """Test that default values preserve existing PostgreSQL behavior."""
        # Empty request should default to PostgreSQL
        empty_request = {}
        result = extract_db_connection_info_from_request(empty_request)
        
        assert result['db_type'] == 'postgresql'
        # Should include PostgreSQL environment defaults
        assert 'db_host' in result
        assert 'db_port' in result
    
    def test_postgresql_validation_works(self):
        """Test that PostgreSQL validation still works correctly."""
        pg_info = {
            'db_type': 'postgresql',
            'db_host': 'localhost',
            'db_port': 5432,
            'db_name': 'adventureworks',
            'db_user': 'postgres',
            'db_password': 'password'
        }
        
        assert validate_database_connection_info(pg_info) == True

def run_all_tests():
    """Run all Phase 5.3 dependency injection tests."""
    print("🧪 Running Phase 5.3 Dependency Injection Tests...")
    print("=" * 60)
    
    # Test utility functions
    print("\n📋 Testing Utility Functions...")
    test_utils = TestUtilityFunctions()
    test_utils.test_extract_db_connection_info_basic()
    test_utils.test_extract_db_connection_info_defaults()
    test_utils.test_validate_database_connection_info_sqlite()
    test_utils.test_validate_database_connection_info_other_dbs()
    print("✅ Utility functions tests passed!")
    
    # Test database service dependencies
    print("\n🔌 Testing Database Service Dependencies...")
    test_db_deps = TestDatabaseServiceDependencies()
    test_db_deps.test_get_connection_manager_singleton()
    test_db_deps.test_get_database_service()
    asyncio.run(test_db_deps.test_get_dynamic_database_connection())
    print("✅ Database service dependency tests passed!")
    
    # Test composite service dependencies
    print("\n🔧 Testing Composite Service Dependencies...")
    test_composite = TestCompositeServiceDependencies()
    asyncio.run(test_composite.test_get_token_usage_service())
    test_composite.test_get_visualization_service_enhanced()
    print("✅ Composite service dependency tests passed!")
    
    # Test request-based dependencies
    print("\n📨 Testing Request-Based Dependencies...")
    test_request = TestRequestBasedDependencies()
    asyncio.run(test_request.test_get_database_service_from_request())
    test_request.test_get_database_service_from_request_fallback()
    print("✅ Request-based dependency tests passed!")
    
    # Test backward compatibility
    print("\n🔄 Testing Backward Compatibility...")
    test_compat = TestBackwardCompatibility()
    test_compat.test_default_values_preserve_postgresql()
    test_compat.test_postgresql_validation_works()
    print("✅ Backward compatibility tests passed!")
    
    print("\n🎉 All Phase 5.3 Dependency Injection Tests Passed!")
    print("=" * 60)
    print("✅ Enhanced dependency injection system is working correctly")
    print("✅ Multi-database dependencies are properly configured")
    print("✅ Backward compatibility is maintained")
    print("✅ Ready for Phase 5.4 (Frontend Enhancement)")

if __name__ == "__main__":
    try:
        run_all_tests()
        print("\n📊 Phase 5.3 Validation Summary:")
        print("- ✅ Utility functions for connection extraction")
        print("- ✅ Multi-database service factory dependencies")
        print("- ✅ Enhanced composite service dependencies")
        print("- ✅ Request-based database service extraction")
        print("- ✅ Backward compatibility with PostgreSQL")
        print("\n🚀 Ready to proceed with Phase 5.4!")
        
    except Exception as e:
        print(f"\n❌ Phase 5.3 test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
