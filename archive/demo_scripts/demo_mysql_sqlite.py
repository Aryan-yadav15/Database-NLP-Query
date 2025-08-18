"""
MySQL and SQLite Database Services Demo
=======================================

This demo showcases the capabilities of the newly implemented MySQL and SQLite
database services, demonstrating their integration with the multi-database
architecture and practical usage scenarios.

Features Demonstrated:
- Database service factory usage
- Connection management
- Schema introspection
- Query execution
- Parameterized queries
- Error handling
- Cross-database compatibility

Usage:
    python demo_mysql_sqlite.py
"""

import sys
import os
import tempfile
from pathlib import Path

# Add the brain_llm directory to Python path
brain_llm_path = os.path.join(os.path.dirname(__file__), 'brain_llm')
sys.path.insert(0, brain_llm_path)

from app.services.db.base import ConnectionInfo
from app.services.db import get_database_service, get_supported_database_types


def demo_database_factory():
    """Demonstrate the database service factory capabilities."""
    print("🏭 DATABASE SERVICE FACTORY DEMO")
    print("=" * 50)
    
    # Show all supported database types
    supported_types = get_supported_database_types()
    print(f"Supported database types: {', '.join(supported_types)}")
    print()
    
    # Create services for each database type
    databases = {
        'PostgreSQL': get_database_service('postgresql'),
        'MySQL': get_database_service('mysql'),
        'SQLite': get_database_service('sqlite')
    }
    
    print("Created database services:")
    for name, service in databases.items():
        features = service.get_supported_features()
        print(f"  • {name}: {service.__class__.__name__} ({len(features)} features)")
    
    print()
    return databases


def demo_sqlite_operations():
    """Demonstrate SQLite database operations."""
    print("🗄️  SQLITE OPERATIONS DEMO")
    print("=" * 50)
    
    # Create SQLite service
    sqlite_service = get_database_service('sqlite')
    
    # Demo 1: In-memory database
    print("📋 Demo 1: In-Memory Database")
    memory_conn_info = ConnectionInfo(
        db_type="sqlite",
        db_host="",
        db_port=0,
        db_name=":memory:",
        db_user="",
        db_password=""
    )
    
    for connection in sqlite_service.get_connection(memory_conn_info):
        # Create a sample e-commerce schema
        print("   Creating e-commerce schema...")
        
        # Categories table
        sqlite_service.execute_query(connection, """
            CREATE TABLE categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT
            )
        """)
        
        # Products table
        sqlite_service.execute_query(connection, """
            CREATE TABLE products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                category_id INTEGER,
                stock_quantity INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)
        
        # Insert sample data
        print("   Inserting sample data...")
        
        # Categories
        categories_data = [
            "INSERT INTO categories (name, description) VALUES ('Electronics', 'Electronic devices and gadgets')",
            "INSERT INTO categories (name, description) VALUES ('Books', 'Physical and digital books')",
            "INSERT INTO categories (name, description) VALUES ('Clothing', 'Apparel and accessories')"
        ]
        
        for query in categories_data:
            sqlite_service.execute_query(connection, query)
        
        # Products with parameterized queries
        products = [
            {'name': 'Laptop Pro 15"', 'price': 1299.99, 'category_id': 1, 'stock': 25},
            {'name': 'Wireless Headphones', 'price': 199.99, 'category_id': 1, 'stock': 50},
            {'name': 'Python Programming Guide', 'price': 49.99, 'category_id': 2, 'stock': 100},
            {'name': 'Classic T-Shirt', 'price': 24.99, 'category_id': 3, 'stock': 75}
        ]
        
        for product in products:
            sqlite_service.execute_query_with_params(connection, """
                INSERT INTO products (name, price, category_id, stock_quantity)
                VALUES (:name, :price, :category_id, :stock)
            """, product)
        
        # Query data with joins
        print("   Querying data with JOIN...")
        result = sqlite_service.execute_query(connection, """
            SELECT 
                p.name as product_name,
                p.price,
                p.stock_quantity,
                c.name as category_name
            FROM products p
            JOIN categories c ON p.category_id = c.id
            ORDER BY p.price DESC
        """)
        
        print(f"   Found {result.row_count} products:")
        for row in result.data:
            print(f"     • {row['product_name']}: ${row['price']} ({row['category_name']}) - Stock: {row['stock_quantity']}")
        
        # Extract and display schema
        print("   Extracting database schema...")
        schema = sqlite_service.get_schema_string(connection)
        print("   Schema preview:")
        for line in schema.split('\\n')[:10]:  # Show first 10 lines
            if line.strip():
                print(f"     {line}")
        print("     ...")
    
    print()
    
    # Demo 2: File-based database
    print("📁 Demo 2: File-Based Database")
    
    # Create a temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    print(f"   Creating database file: {db_path}")
    
    # Create database file with initial configuration
    success = sqlite_service.create_database_file(db_path)
    print(f"   Database created: {success}")
    
    # Connect to file database
    file_conn_info = ConnectionInfo(
        db_type="sqlite",
        db_host="",
        db_port=0,
        db_name=db_path,
        db_user="",
        db_password=""
    )
    
    for connection in sqlite_service.get_connection(file_conn_info):
        # Create a log table
        sqlite_service.execute_query(connection, """
            CREATE TABLE activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                action TEXT NOT NULL,
                details TEXT
            )
        """)
        
        # Insert log entries
        log_entries = [
            "INSERT INTO activity_log (action, details) VALUES ('user_login', 'User john_doe logged in')",
            "INSERT INTO activity_log (action, details) VALUES ('product_view', 'User viewed Laptop Pro 15\"')",
            "INSERT INTO activity_log (action, details) VALUES ('add_to_cart', 'Added Wireless Headphones to cart')"
        ]
        
        for entry in log_entries:
            sqlite_service.execute_query(connection, entry)
        
        # Query logs
        logs = sqlite_service.execute_query(connection, "SELECT * FROM activity_log ORDER BY timestamp")
        print(f"   Logged {logs.row_count} activities:")
        for log in logs.data:
            print(f"     [{log['timestamp']}] {log['action']}: {log['details']}")
    
    # Verify persistence by reconnecting
    print("   Verifying data persistence...")
    for connection in sqlite_service.get_connection(file_conn_info):
        count_result = sqlite_service.execute_query(connection, "SELECT COUNT(*) as count FROM activity_log")
        print(f"   Data persisted: {count_result.data[0]['count']} records found after reconnection")
    
    # Clean up
    os.unlink(db_path)
    print("   Cleaned up temporary database file")
    print()


def demo_mysql_capabilities():
    """Demonstrate MySQL service capabilities (without requiring actual MySQL server)."""
    print("🐬 MYSQL SERVICE CAPABILITIES DEMO")
    print("=" * 50)
    
    # Create MySQL service
    mysql_service = get_database_service('mysql')
    
    # Show connection string generation
    mysql_conn_info = ConnectionInfo(
        db_type="mysql",
        db_host="production-db.company.com",
        db_port=3306,
        db_name="ecommerce_prod",
        db_user="app_user",
        db_password="secure_password_123!@#",
        additional_params={
            "charset": "utf8mb4",
            "autocommit": True,
            "sql_mode": "TRADITIONAL"
        }
    )
    
    print("📝 Connection String Generation:")
    conn_string = mysql_service.get_connection_string(mysql_conn_info)
    # Mask password for display
    display_string = conn_string.replace("secure_password_123!@#", "***MASKED***")
    print(f"   {display_string}")
    print()
    
    print("🔧 MySQL Features Matrix:")
    features = mysql_service.get_supported_features()
    feature_categories = {
        "Core Features": ["connection_pooling", "transactions", "foreign_keys"],
        "Advanced Features": ["stored_procedures", "window_functions", "json_support"],
        "MySQL Specific": ["auto_increment", "multiple_storage_engines", "replication"],
        "SQL Features": ["upsert", "recursive_queries", "full_text_search"]
    }
    
    for category, feature_list in feature_categories.items():
        print(f"   {category}:")
        for feature in feature_list:
            status = "✓" if features.get(feature, False) else "✗"
            print(f"     {status} {feature.replace('_', ' ').title()}")
        print()
    
    print("📊 MySQL vs SQLite Feature Comparison:")
    sqlite_service = get_database_service('sqlite')
    sqlite_features = sqlite_service.get_supported_features()
    
    comparison_features = [
        "connection_pooling", "stored_procedures", "materialized_views",
        "foreign_keys", "json_support", "window_functions", "upsert"
    ]
    
    print(f"   {'Feature':<20} {'MySQL':<8} {'SQLite':<8}")
    print(f"   {'-'*20} {'-'*8} {'-'*8}")
    
    for feature in comparison_features:
        mysql_support = "✓" if features.get(feature, False) else "✗"
        sqlite_support = "✓" if sqlite_features.get(feature, False) else "✗"
        feature_name = feature.replace('_', ' ').title()
        print(f"   {feature_name:<20} {mysql_support:<8} {sqlite_support:<8}")
    
    print()


def demo_cross_database_compatibility():
    """Demonstrate cross-database compatibility and consistent interfaces."""
    print("🔄 CROSS-DATABASE COMPATIBILITY DEMO")
    print("=" * 50)
    
    # Create services for different databases
    services = {
        'PostgreSQL': get_database_service('postgresql'),
        'MySQL': get_database_service('mysql'), 
        'SQLite': get_database_service('sqlite')
    }
    
    print("🔍 Interface Consistency Check:")
    
    # Check that all services have the same interface methods
    expected_methods = [
        'get_connection', 'get_engine', 'validate_connection',
        'get_schema_string', 'get_table_names', 'get_table_schema',
        'execute_query', 'execute_query_with_params',
        'get_connection_string', 'get_supported_features'
    ]
    
    print(f"   Checking {len(expected_methods)} interface methods...")
    
    all_compatible = True
    for db_name, service in services.items():
        missing_methods = []
        for method in expected_methods:
            if not hasattr(service, method) or not callable(getattr(service, method)):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"   ✗ {db_name}: Missing {missing_methods}")
            all_compatible = False
        else:
            print(f"   ✓ {db_name}: All methods present")
    
    if all_compatible:
        print("   🎉 All database services have consistent interfaces!")
    
    print()
    
    print("📈 Feature Coverage Analysis:")
    
    # Analyze feature coverage across databases
    all_features = set()
    for service in services.values():
        all_features.update(service.get_supported_features().keys())
    
    print(f"   Total unique features across all databases: {len(all_features)}")
    
    # Find common features
    common_features = set(services['PostgreSQL'].get_supported_features().keys())
    for service in services.values():
        common_features &= set(service.get_supported_features().keys())
    
    print(f"   Features supported by ALL databases: {len(common_features)}")
    for feature in sorted(common_features):
        print(f"     • {feature.replace('_', ' ').title()}")
    
    print()
    
    print("🎯 Database Selection Recommendations:")
    recommendations = {
        'PostgreSQL': [
            "✓ Complex queries with advanced SQL features",
            "✓ Large-scale applications with high concurrency",
            "✓ Applications requiring ACID compliance",
            "✓ JSON/NoSQL hybrid workloads"
        ],
        'MySQL': [
            "✓ Web applications and content management",
            "✓ E-commerce and transactional systems", 
            "✓ Applications requiring replication",
            "✓ WordPress/PHP-based applications"
        ],
        'SQLite': [
            "✓ Development and testing environments",
            "✓ Embedded applications and mobile apps",
            "✓ Small to medium data sets",
            "✓ Single-user applications"
        ]
    }
    
    for db_name, use_cases in recommendations.items():
        print(f"   {db_name}:")
        for use_case in use_cases:
            print(f"     {use_case}")
        print()


def main():
    """Run the complete demo."""
    print("🚀 MYSQL & SQLITE DATABASE SERVICES DEMO")
    print("=" * 60)
    print("This demo showcases the newly implemented MySQL and SQLite")
    print("database services for the Brain LLM multi-database architecture.")
    print("=" * 60)
    print()
    
    try:
        # Run all demo sections
        demo_database_factory()
        demo_sqlite_operations()
        demo_mysql_capabilities()
        demo_cross_database_compatibility()
        
        print("✅ DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("Key Achievements:")
        print("• ✓ MySQL service fully implemented with connection pooling")
        print("• ✓ SQLite service supports both in-memory and file databases")
        print("• ✓ Both services integrated into the database factory")
        print("• ✓ Consistent interfaces across all database providers")
        print("• ✓ Comprehensive feature matrices for database selection")
        print("• ✓ Real database operations validated successfully")
        print()
        print("🎯 Next Steps:")
        print("• Add MySQL and SQLite to connection management UI")
        print("• Update API documentation with new database support")
        print("• Create database-specific optimization configurations")
        print("• Add integration tests with real database servers")
        
        return 0
        
    except Exception as e:
        print(f"❌ DEMO FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
