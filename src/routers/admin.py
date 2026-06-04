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
import json

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
    """Admin dashboard - robust version with error handling"""
    # Token kontrolü
    if not access_token:
        logger.warning("⚠️ No access_token cookie")
        return RedirectResponse(url="/login", status_code=303)
    
    if access_token.startswith("Bearer "):
        access_token = access_token[7:]
    
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
    stats = {"total": 0, "accepted": 0, "rejected": 0, "low_confidence": 0, "avg_confidence": 0}
    recent_analyses = []
    model_version = "tesseract-ocr-tur+eng"
    
    try:
        # Toplam analiz sayısı
        stats["total"] = db.query(func.count(Analysis.id)).scalar() or 0
        logger.info(f"📊 Total analyses: {stats['total']}")
        
        # Kabul edilen
        stats["accepted"] = db.query(func.count(Analysis.id)).filter(Analysis.status == "accepted").scalar() or 0
        
        # Reddedilen
        stats["rejected"] = db.query(func.count(Analysis.id)).filter(Analysis.status == "rejected").scalar() or 0
        
        # Düşük güven
        stats["low_confidence"] = db.query(func.count(Analysis.id)).filter(Analysis.status == "low_confidence").scalar() or 0
        
        # Ortalama güven skoru
        avg_result = db.query(func.avg(Analysis.confidence_score)).filter(Analysis.confidence_score > 0).first()
        stats["avg_confidence"] = round(avg_result[0], 3) if avg_result and avg_result[0] else 0.0
        
        # Son analizler
        recent = db.query(Analysis).order_by(desc(Analysis.id)).limit(20).all()
        logger.info(f"📊 Recent analyses count: {len(recent)}")
        
        for a in recent:
            try:
                # Entities sayısını hesapla (dict veya string olabilir)
                entities_count = 0
                if a.entities_json:
                    if isinstance(a.entities_json, dict):
                        entities_count = len(a.entities_json)
                    elif isinstance(a.entities_json, str):
                        try:
                            entities_count = len(json.loads(a.entities_json))
                        except:
                            entities_count = 0
                
                recent_analyses.append({
                    "id": a.id,
                    "filename": a.filename or "unknown",
                    "status": a.status or "unknown",
                    "confidence": round(float(a.confidence_score), 3) if a.confidence_score else 0.0,
                    "upload_date": a.upload_timestamp.strftime("%Y-%m-%d %H:%M") if a.upload_timestamp else "N/A",
                    "analysis_duration_ms": int(a.analysis_duration_ms) if a.analysis_duration_ms else 0,
                    "ocr_preview": (a.ocr_text_preview[:100] + "...") if a.ocr_text_preview else "",
                    "entities_count": entities_count,
                    "qa_summary": a.qa_summary or ""
                })
            except Exception as e:
                logger.error(f"❌ Error processing analysis {a.id}: {e}", exc_info=True)
                continue
        
        logger.info(f"✅ Dashboard rendered: {len(recent_analyses)} analyses")
        
    except Exception as e:
        logger.error(f"❌ Dashboard data fetch error: {e}", exc_info=True)
        model_version = f"error: {str(e)}"
    
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "stats": stats,
        "recent_analyses": recent_analyses,
        "model_version": model_version
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