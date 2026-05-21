from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import Analysis
from src.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/api/history", tags=["history"])

def format_timestamp(dt) -> str:
    """Safely format datetime for frontend"""
    if dt is None:
        return ""
    try:
        # Handle both datetime objects and Unix timestamps
        if isinstance(dt, datetime):
            return dt.isoformat()
        return datetime.fromtimestamp(dt).isoformat()
    except (ValueError, OSError, OverflowError):
        return ""

@router.get("/")
@router.get("")
async def get_history(db: Session = Depends(get_db), user = Depends(get_current_user)):
    """Get analysis history for admin dashboard"""
    try:
        logs = db.query(Analysis).order_by(Analysis.upload_timestamp.desc()).limit(50).all()
        
        history = []
        for l in logs:
            # ✅ Safe timestamp handling
            ts = format_timestamp(l.upload_timestamp)
            
            history.append({
                "id": l.id,
                "image_hash": l.image_hash or "",
                "upload_timestamp": ts,
                "relevance_score": l.relevance_score if l.relevance_score is not None else 0.0,
                "avg_confidence": l.avg_confidence if l.avg_confidence is not None else 0.0,
                "status": l.status or "unknown",
                "latency_ms": l.latency_ms if l.latency_ms is not None else 0.0
            })
        
        return {
            "history": history,
            "count": len(history),
            "disclaimer": "Bu sistem yalnızca bilgilendirme amaçlıdır. Teşhis, tedavi veya ilaç önerisi yapmaz. Tüm kararlar için yetkili hekime danışın."
        }
    except Exception as e:
        return {
            "history": [],
            "count": 0,
            "error": str(e),
            "disclaimer": "Bu sistem yalnızca bilgilendirme amaçlıdır. Teşhis, tedavi veya ilaç önerisi yapmaz. Tüm kararlar için yetkili hekime danışın."
        }