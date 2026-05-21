#!/bin/bash
export DATABASE_URL=sqlite:///./hantamed.db
export SECRET_KEY=HantaMed-Secure-Secret-Key-2024-Production
python -m src.data.pipeline
alembic upgrade head
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 1