#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Force-add filename column to SQLAlchemy Analysis model at runtime"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import Column, String
from src.models import Analysis, Base
from src.database import engine

def main():
    print("🔧 Adding filename column to Analysis model dynamically...")
    
    # Check if column already exists in model
    if hasattr(Analysis, 'filename'):
        print("✅ filename already exists in Analysis model")
        return
    
    # Add column to model definition
    if not hasattr(Analysis, '__table__'):
        Base.metadata.reflect(bind=engine)
    
    # Append column if not already present
    if 'filename' not in [c.name for c in Analysis.__table__.columns]:
        Analysis.__table__.append_column(Column('filename', String(255), nullable=True))
        print("✅ filename column appended to Analysis.__table__")
    else:
        print("✅ filename already in Analysis.__table__")
    
    # Test query
    from src.database import SessionLocal
    db = SessionLocal()
    recent = db.query(Analysis).order_by(Analysis.upload_timestamp.desc()).first()
    if recent:
        val = getattr(recent, 'filename', 'NOT_FOUND')
        print(f"🔎 Query result: filename = {val}")
    db.close()
    
    print("✅ Fix complete.")

if __name__ == "__main__":
    main()