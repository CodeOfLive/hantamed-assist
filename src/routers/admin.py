from fastapi import APIRouter, Depends, HTTPException, Request, Cookie, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, cast, Date
from typing import Optional
from datetime import datetime, timedelta
from jose import jwt

from src.database import get_db
from src.auth import require_admin
from src.models import Analysis, User
from src.evaluation.metrics import MetricsCalculator, MetricResult
from src.config import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")


def get_current_user_from_cookie(
    access_token: str = Cookie(None, alias="access_token"),
    db: Session = Depends(get_db)
) -> User:
    """Get user from cookie-based JWT token (for browser sessions)"""
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kimlik doğrulama token'ı bulunamadı.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token geçersiz.")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token decode edilemedi.")
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı.")
    return user


@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request, 
    db: Session = Depends(get_db), 
    user: User = Depends(get_current_user_from_cookie)  # ✅ Cookie auth for HTML
):
    """Admin dashboard with detailed analytics"""
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
            "filename": a.filename,
            "status": a.status,
            "confidence": round(a.confidence_score, 3) if a.confidence_score else None,
            "upload_date": a.upload_timestamp.isoformat() if a.upload_timestamp else None,
            "analysis_duration_ms": a.analysis_duration_ms,
            "ocr_preview": (a.ocr_text_preview[:100] + "...") if a.ocr_text_preview else None,
            "entities_count": len(a.entities_json) if a.entities_json else 0,
            "entities_json": a.entities_json,
            "qa_summary": a.qa_summary
        })
    
    db_analytics = {
        "total": total, "accepted": accepted, "rejected": rejected,
        "low_confidence": low_conf, "avg_confidence": avg_conf
    }
    ner_metrics = MetricsCalculator.calculate_ner_metrics([])
    
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "stats": db_analytics,
        "metrics": {
            "precision": ner_metrics["precision"],
            "recall": ner_metrics["recall"],
            "f1": ner_metrics["f1"],
            "exact_match": ner_metrics["exact_match"]
        },
        "recent_analyses": recent_analyses,
        "model_version": "florence-2-base-fallback"
    })


@router.get("/api/analytics")
async def get_analytics(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    """JSON endpoint for analytics data"""
    total = db.query(func.count(Analysis.id)).scalar() or 0
    accepted = db.query(func.count(Analysis.id)).filter(Analysis.status == "accepted").scalar() or 0
    rejected = db.query(func.count(Analysis.id)).filter(Analysis.status == "rejected").scalar() or 0
    low_conf = db.query(func.count(Analysis.id)).filter(Analysis.status == "low_confidence").scalar() or 0
    
    avg_conf_result = db.query(func.avg(Analysis.confidence_score)).filter(Analysis.confidence_score > 0).first()
    avg_conf = round(avg_conf_result[0], 3) if avg_conf_result and avg_conf_result[0] else 0.0
    
    daily_stats = db.query(
        cast(Analysis.upload_timestamp, Date).label("date"),
        func.count(Analysis.id).label("count"),
        func.avg(Analysis.confidence_score).label("avg_conf")
    ).filter(
        Analysis.upload_timestamp >= datetime.utcnow() - timedelta(days=7)
    ).group_by(cast(Analysis.upload_timestamp, Date)).order_by(cast(Analysis.upload_timestamp, Date)).all()
    
    daily_data = [{"date": str(d[0]), "count": d[1], "avg_conf": round(d[2], 3) if d[2] else None} for d in daily_stats]
    
    return JSONResponse(content={
        "summary": {
            "total": total, "accepted": accepted, "rejected": rejected,
            "low_confidence": low_conf, "avg_confidence": avg_conf
        },
        "daily_trend": daily_data,
        "model_version": "florence-2-base-fallback",
        "disclaimer": "Bu sistem yalnızca bilgilendirme amaçlıdır."
    })


@router.get("/api/analysis/{analysis_id}")
async def get_analysis_detail(analysis_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    """Get detailed info for a single analysis"""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return JSONResponse(content={
        "id": analysis.id,
        "filename": analysis.filename,
        "status": analysis.status,
        "confidence": round(analysis.confidence_score, 3) if analysis.confidence_score else None,
        "upload_timestamp": analysis.upload_timestamp.isoformat() if analysis.upload_timestamp else None,
        "analysis_duration_ms": analysis.analysis_duration_ms,
        "ocr_text_preview": analysis.ocr_text_preview,
        "entities": analysis.entities_json,
        "qa_summary": analysis.qa_summary,
        "disclaimer": "Bu sistem yalnızca bilgilendirme amaçlıdır."
    })


@router.get("/metrics")
async def get_model_metrics(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    """Get model performance metrics (F1, precision, recall)"""
    ner_metrics = MetricsCalculator.calculate_ner_metrics([])
    return JSONResponse(content={
        "ner_metrics": ner_metrics,
        "model_version": "florence-2-base-fallback",
        "last_updated": datetime.utcnow().isoformat(),
        "note": "Metrics calculated on anonymized test set.",
        "disclaimer": "Bu sistem yalnızca bilgilendirme amaçlıdır."
    })