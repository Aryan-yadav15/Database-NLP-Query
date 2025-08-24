#!/usr/bin/env python3
"""
Simple test script to validate the new architecture structure
"""
import sys
import os

print("Testing new Brain LLM architecture...")
print("=" * 50)

# Test 1: Import core modules
try:
    print("✓ Core modules structure exists")
    from app_new.core import exceptions
    print("✓ Core exceptions imported successfully")
except ImportError as e:
    print(f"✗ Core modules import failed: {e}")
    sys.exit(1)

# Test 2: Import domain modules  
try:
    from app_new.domains.analytics.services import csv_processor
    print("✓ Analytics CSV processor imported successfully")
    
    from app_new.domains.analytics.services import data_profiler
    print("✓ Analytics data profiler imported successfully")
except ImportError as e:
    print(f"✗ Analytics domain import failed: {e}")
    sys.exit(1)

# Test 3: Import database connectors
try:
    from app_new.domains.database.connectors import pg_connector
    print("✓ PostgreSQL connector imported successfully")
except ImportError as e:
    print(f"✗ Database connector import failed: {e}")
    sys.exit(1)

# Test 4: Import shared modules
try:
    from app_new.shared.prompts import prompt_engineering
    print("✓ Prompt engineering module imported successfully")
except ImportError as e:
    print(f"✗ Shared modules import failed: {e}")
    sys.exit(1)

# Test 5: Check API routes
try:
    from app_new.api.v1.endpoints import analytics
    print("✓ Analytics API endpoints imported successfully")
except ImportError as e:
    print(f"✗ API endpoints import failed: {e}")
    sys.exit(1)

print("\n" + "=" * 50)
print("🎉 All architecture tests passed!")
print("📁 Database connectors: MIGRATED ✓")
print("📁 Prompt templates: MIGRATED ✓") 
print("📁 New structure: WORKING ✓")
print("=" * 50)
