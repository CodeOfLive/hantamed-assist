"""
Admin panel router for HantaMed Assist
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Cookie, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional
from datetime import datetime, timedelta
import logging

from src.database import get_db
from src.models import Analysis, User
from src.config import SECRET_KEY, ALGORITHM

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request, 
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(None)  # Cookie'den oku
):
    """Admin dashboard"""
    import logging
    logger = logging.getLogger(__name__)
    if not access_token:
        logger.warning("⚠️ No access_token cookie found")
        return RedirectResponse(url="/login", status_code=303)
    
    if access_token.startswith("Bearer "):
        access_token = access_token[7:]
    
    try:
        from jose import jwt
        from src.config import SECRET_KEY, ALGORITHM
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            logger.warning("⚠️ Token has no 'sub' claim")
            return RedirectResponse(url="/login", status_code=303)
    except Exception as e:
        logger.error(f"❌ Token decode error: {e}")
        return RedirectResponse(url="/login", status_code=303)
    
    try:
        total = db.query(func.count(Analysis.id)).scalar() or 0
        accepted = db.query(func.count(Analysis.id)).filter(Analysis.status == "accepted").scalar() or 0
        rejected = db.query(func.count(Analysis.id)).filter(Analysis.status == "rejected").scalar() or 0
        low_conf = db.query(func.count(Analysis.id)).filter(Analysis.status == "low_confidence").scalar() or 0
        
        avg_conf_result = db.query(func.avg(Analysis.confidence_score)).filter(Analysis.confidence_score > 0).first()
        avg_conf = round(avg_conf_result[0], 3) if avg_conf_result and avg_conf_result[0] else 0.0
        
        recent = db.query(Analysis).order_by(desc(Analysis.upload_timestamp)).limit(20).all()
        recent_analyses = []
        for a in recent:
            recent_analyses.append({
                "id": a.id,
                "filename": a.filename or "unknown",
                "status": a.status,
                "confidence": round(a.confidence_score, 3) if a.confidence_score else None,
                "upload_date": a.upload_timestamp.isoformat() if a.upload_timestamp else None,
                "analysis_duration_ms": a.analysis_duration_ms,
                "ocr_preview": (a.ocr_text_preview[:100] + "...") if a.ocr_text_preview else None,
                "entities_count": len(a.entities_json) if a.entities_json else 0,
                "entities_json": a.entities_json,
                "qa_summary": a.qa_summary
            })
        
        try:
            from src.evaluation.metrics import MetricsCalculator
            ner_metrics = MetricsCalculator.calculate_ner_metrics([])
        except Exception:
            ner_metrics = {"precision": 0, "recall": 0, "f1": 0, "exact_match": 0}
        
        return templates.TemplateResponse("admin_dashboard.html", {
            "request": request,
            "stats": {
                "total": total, "accepted": accepted, "rejected": rejected,
                "low_confidence": low_conf, "avg_confidence": avg_conf
            },
            "metrics": {
                "precision": ner_metrics["precision"], "recall": ner_metrics["recall"],
                "f1": ner_metrics["f1"], "exact_match": ner_metrics["exact_match"]
            },
            "recent_analyses": recent_analyses,
            "model_version": "florence-2-base-fallback"
        })
    except Exception as e:
        logger.error(f"Dashboard error: {e}", exc_info=True)
        return templates.TemplateResponse("admin_dashboard.html", {
            "request": request,
            "stats": {"total": 0, "accepted": 0, "rejected": 0, "low_confidence": 0, "avg_confidence": 0},
            "metrics": {"precision": 0, "recall": 0, "f1": 0, "exact_match": 0},
            "recent_analyses": [],
            "model_version": "error"
        })


@router.get("/api/analytics")
async def get_analytics(db: Session = Depends(get_db)):
    """JSON endpoint for analytics"""
    try:
        total = db.query(func.count(Analysis.id)).scalar() or 0
        accepted = db.query(func.count(Analysis.id)).filter(Analysis.status == "accepted").scalar() or 0
        rejected = db.query(func.count(Analysis.id)).filter(Analysis.status == "rejected").scalar() or 0
        low_conf = db.query(func.count(Analysis.id)).filter(Analysis.status == "low_confidence").scalar() or 0
        
        return JSONResponse(content={
            "summary": {
                "total": total, "accepted": accepted, "rejected": rejected,
                "low_confidence": low_conf, "avg_confidence": 0
            },
            "model_version": "florence-2-base-fallback"
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})