#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script to verify filename column is accessible via SQLAlchemy ORM"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import SessionLocal, engine, Base
from src.models import Analysis
from sqlalchemy import inspect

def main():
    print("🔍 Testing filename column access...")
    
    # 1. Check database schema directly
    print("\n📊 Database schema check:")
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns('analyses')]
    print(f"   Columns: {columns}")
    print(f"   ✅ filename in DB: {'filename' in columns}")
    
    # 2. Check SQLAlchemy model definition
    print("\n📋 Model definition check:")
    if hasattr(Analysis, '__table__'):
        model_cols = [c.name for c in Analysis.__table__.columns]
        print(f"   Model columns: {model_cols}")
        print(f"   ✅ filename in Model: {'filename' in model_cols}")
    else:
        print("   ⚠️ Analysis.__table__ not available")
    
    # 3. Try to query with ORM
    print("\n🔎 ORM query test:")
    db = SessionLocal()
    try:
        recent = db.query(Analysis).order_by(Analysis.upload_timestamp.desc()).first()
        if recent:
            # Use getattr with default to avoid AttributeError
            filename_val = getattr(recent, 'filename', None)
            if filename_val is not None:
                print(f"   ✅ filename via ORM: OK")
                print(f"   Value: {filename_val}")
            else:
                print(f"   ❌ filename attribute returned None")
                # List available attributes for debugging
                attrs = [a for a in dir(recent) if not a.startswith('_')][:20]
                print(f"   Available attrs: {attrs}")
        else:
            print("   ⚠️ No analysis records found in database")
    except Exception as e:
        print(f"   ❌ ORM query error: {e}")
    finally:
        db.close()
    
    print("\n✅ Test complete.")

if __name__ == "__main__":
    main()