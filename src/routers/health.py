"""
Health check endpoint for monitoring and load balancers
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.database import get_db
from src.config import APP_VERSION

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for monitoring
    Returns database and storage status
    """
    try:
        # Database check
        db.execute("SELECT 1")
        db_status = "ok"
    except Exception:
        db_status = "error"
    
    # Storage check (simple file write test)
    try:
        import os
        test_file = os.path.join("uploads", ".health_check")
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)
        storage_status = True
    except Exception:
        storage_status = False
    
    # Model check (fallback mode indicator)
    model_status = "fallback"  # or "loaded" if model is ready
    
    return {
        "status": "healthy" if db_status == "ok" and storage_status else "degraded",
        "version": APP_VERSION,
        "checks": {
            "database": db_status,
            "storage": storage_status,
            "model": model_status
        },
        "legal": "This system is for informational purposes only. Consult a physician for medical decisions."
    }