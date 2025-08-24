from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import asyncio
import json
from datetime import datetime

from app.services.db import get_database_service

router = APIRouter(prefix="/database", tags=["database"])

class DatabaseConnection(BaseModel):
    name: str = Field(..., description="Human-readable connection name")
    type: str = Field(..., description="Database type (postgresql, mysql, sqlite, snowflake)")
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database: str = Field(..., description="Database name or file path")
    schema: Optional[str] = None
    account: Optional[str] = None  # For Snowflake
    warehouse: Optional[str] = None  # For Snowflake

class SavedConnection(DatabaseConnection):
    id: str
    created_at: datetime
    last_used: Optional[datetime] = None
    is_active: bool = False

class ConnectionTestResult(BaseModel):
    success: bool
    message: str
    connection_info: Optional[Dict[str, Any]] = None

# In-memory storage for demo (replace with database in production)
saved_connections: List[SavedConnection] = []

@router.post("/test-connection", response_model=ConnectionTestResult)
async def test_database_connection(connection: DatabaseConnection):
    """Test database connection without saving it"""
    try:
        # Get appropriate database service
        db_service = get_database_service(connection.type)
        
        # Build connection parameters based on database type
        if connection.type == "sqlite":
            # SQLite only needs database path
            test_result = await asyncio.to_thread(
                db_service.test_connection,
                database=connection.database
            )
        elif connection.type == "snowflake":
            # Snowflake has different parameters
            test_result = await asyncio.to_thread(
                db_service.test_connection,
                account=connection.account,
                username=connection.username,
                password=connection.password,
                database=connection.database,
                schema=connection.schema,
                warehouse=connection.warehouse
            )
        else:
            # PostgreSQL, MySQL, etc.
            test_result = await asyncio.to_thread(
                db_service.test_connection,
                host=connection.host,
                port=connection.port,
                username=connection.username,
                password=connection.password,
                database=connection.database,
                schema=connection.schema
            )
        
        if test_result.get("success", False):
            return ConnectionTestResult(
                success=True,
                message=f"Successfully connected to {connection.type.upper()} database",
                connection_info={
                    "database_type": connection.type,
                    "database_name": connection.database,
                    "tables_count": test_result.get("tables_count", 0),
                    "version": test_result.get("version", "Unknown")
                }
            )
        else:
            return ConnectionTestResult(
                success=False,
                message=test_result.get("error", "Connection failed")
            )
            
    except Exception as e:
        return ConnectionTestResult(
            success=False,
            message=f"Connection error: {str(e)}"
        )

@router.post("/connections", response_model=SavedConnection)
async def save_connection(connection: DatabaseConnection):
    """Save a new database connection"""
    try:
        # Generate unique ID
        connection_id = f"{connection.type}_{len(saved_connections) + 1}_{int(datetime.now().timestamp())}"
        
        # Create saved connection
        saved_connection = SavedConnection(
            id=connection_id,
            name=connection.name,
            type=connection.type,
            host=connection.host,
            port=connection.port,
            username=connection.username,
            password=connection.password,  # In production, encrypt this
            database=connection.database,
            schema=connection.schema,
            account=connection.account,
            warehouse=connection.warehouse,
            created_at=datetime.now(),
            is_active=False
        )
        
        # Add to storage
        saved_connections.append(saved_connection)
        
        return saved_connection
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save connection: {str(e)}")

@router.get("/connections", response_model=List[SavedConnection])
async def get_saved_connections():
    """Get all saved database connections"""
    return saved_connections

@router.get("/connections/{connection_id}", response_model=SavedConnection)
async def get_connection(connection_id: str):
    """Get a specific database connection"""
    connection = next((conn for conn in saved_connections if conn.id == connection_id), None)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    return connection

@router.delete("/connections/{connection_id}")
async def delete_connection(connection_id: str):
    """Delete a database connection"""
    global saved_connections
    initial_count = len(saved_connections)
    saved_connections = [conn for conn in saved_connections if conn.id != connection_id]
    
    if len(saved_connections) == initial_count:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    return {"message": "Connection deleted successfully"}

@router.post("/connections/{connection_id}/activate")
async def activate_connection(connection_id: str):
    """Activate a database connection (set as current)"""
    # Deactivate all connections
    for conn in saved_connections:
        conn.is_active = False
    
    # Activate the specified connection
    connection = next((conn for conn in saved_connections if conn.id == connection_id), None)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    connection.is_active = True
    connection.last_used = datetime.now()
    
    return {"message": f"Connection '{connection.name}' activated successfully"}

@router.get("/connections/active/current", response_model=Optional[SavedConnection])
async def get_active_connection():
    """Get the currently active database connection"""
    active_connection = next((conn for conn in saved_connections if conn.is_active), None)
    return active_connection

@router.post("/connections/{connection_id}/test", response_model=ConnectionTestResult)
async def test_saved_connection(connection_id: str):
    """Test a saved database connection"""
    connection = next((conn for conn in saved_connections if conn.id == connection_id), None)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    # Convert SavedConnection back to DatabaseConnection for testing
    db_connection = DatabaseConnection(
        name=connection.name,
        type=connection.type,
        host=connection.host,
        port=connection.port,
        username=connection.username,
        password=connection.password,
        database=connection.database,
        schema=connection.schema,
        account=connection.account,
        warehouse=connection.warehouse
    )
    
    return await test_database_connection(db_connection)

@router.get("/types", response_model=List[Dict[str, Any]])
async def get_supported_database_types():
    """Get list of supported database types with their configurations"""
    return [
        {
            "type": "postgresql",
            "label": "PostgreSQL",
            "default_port": 5432,
            "fields": ["host", "port", "username", "password", "database", "schema"],
            "required_fields": ["host", "port", "username", "password", "database"]
        },
        {
            "type": "mysql",
            "label": "MySQL",
            "default_port": 3306,
            "fields": ["host", "port", "username", "password", "database"],
            "required_fields": ["host", "port", "username", "password", "database"]
        },
        {
            "type": "sqlite",
            "label": "SQLite",
            "default_port": None,
            "fields": ["database"],
            "required_fields": ["database"],
            "description": "File path to SQLite database"
        },
        {
            "type": "snowflake",
            "label": "Snowflake",
            "default_port": 443,
            "fields": ["account", "username", "password", "database", "schema", "warehouse"],
            "required_fields": ["account", "username", "password", "database"]
        }
    ]
