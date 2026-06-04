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
    access_token: Optional[str] = Cookie(None)
):
    """Admin dashboard"""
    # Token kontrolü
    if not access_token:
        logger.warning("⚠️ No access_token cookie")
        return RedirectResponse(url="/login", status_code=303)
    
    # "Bearer " prefix'ini kaldır
    if access_token.startswith("Bearer "):
        access_token = access_token[7:]
    
    # Token decode
    try:
        from jose import jwt
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            return RedirectResponse(url="/login", status_code=303)
    except Exception as e:
        logger.error(f"❌ Token decode error: {e}")
        return RedirectResponse(url="/login", status_code=303)
    
    # Dashboard verilerini çek
    try:
        # İstatistikler
        total = db.query(func.count(Analysis.id)).scalar() or 0
        accepted = db.query(func.count(Analysis.id)).filter(Analysis.status == "accepted").scalar() or 0
        rejected = db.query(func.count(Analysis.id)).filter(Analysis.status == "rejected").scalar() or 0
        low_conf = db.query(func.count(Analysis.id)).filter(Analysis.status == "low_confidence").scalar() or 0
        
        avg_conf_result = db.query(func.avg(Analysis.confidence_score)).filter(Analysis.confidence_score > 0).first()
        avg_conf = round(avg_conf_result[0], 3) if avg_conf_result and avg_conf_result[0] else 0.0
        
        # Son analizler (ID'ye göre sırala, en yeni önce)
        recent = db.query(Analysis).order_by(desc(Analysis.id)).limit(20).all()
        
        logger.info(f"📊 Dashboard stats: total={total}, accepted={accepted}, recent={len(recent)}")
        
        recent_analyses = []
        for a in recent:
            recent_analyses.append({
                "id": a.id,
                "filename": a.filename or "unknown",
                "status": a.status or "unknown",
                "confidence": round(a.confidence_score, 3) if a.confidence_score else 0.0,
                "upload_date": a.upload_timestamp.strftime("%Y-%m-%d %H:%M") if a.upload_timestamp else "N/A",
                "analysis_duration_ms": a.analysis_duration_ms or 0,
                "ocr_preview": (a.ocr_text_preview[:100] + "...") if a.ocr_text_preview else "",
                "entities_count": len(a.entities_json) if a.entities_json else 0,
                "entities_json": a.entities_json or {},
                "qa_summary": a.qa_summary or ""
            })
        
        return templates.TemplateResponse("admin_dashboard.html", {
            "request": request,
            "stats": {
                "total": total,
                "accepted": accepted,
                "rejected": rejected,
                "low_confidence": low_conf,
                "avg_confidence": avg_conf
            },
            "recent_analyses": recent_analyses,
            "model_version": "tesseract-ocr-tur+eng"
        })
        
    except Exception as e:
        logger.error(f"❌ Dashboard error: {e}", exc_info=True)
        return templates.TemplateResponse("admin_dashboard.html", {
            "request": request,
            "stats": {"total": 0, "accepted": 0, "rejected": 0, "low_confidence": 0, "avg_confidence": 0},
            "recent_analyses": [],
            "model_version": "error"
        })


@router.get("/api/analytics")
async def get_analytics(
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(None)
):
    """JSON endpoint for analytics"""
    if not access_token:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    
    try:
        total = db.query(func.count(Analysis.id)).scalar() or 0
        accepted = db.query(func.count(Analysis.id)).filter(Analysis.status == "accepted").scalar() or 0
        rejected = db.query(func.count(Analysis.id)).filter(Analysis.status == "rejected").scalar() or 0
        
        return JSONResponse(content={
            "total": total,
            "accepted": accepted,
            "rejected": rejected
        })
    except Exception as e:
        logger.error(f"❌ Analytics error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/logout")
async def logout():
    """Logout"""
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response