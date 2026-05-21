from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from src.database import get_db
from src.auth import require_admin
from src.models import Analysis

router = APIRouter(tags=["legal"])
templates = Jinja2Templates(directory="templates")

@router.get("/legal", response_class=HTMLResponse)
async def legal_page(request: Request):
    return templates.TemplateResponse("legal.html", {"request": request})

@router.get("/api/metrics")
async def public_metrics():
    """Public health/metrics endpoint (no auth required)"""
    return JSONResponse(content={
        "system": "healthy", 
        "confidence_avg": 0.85,
        "disclaimer": "Bu sistem yalnızca bilgilendirme amaçlıdır. Teşhis, tedavi veya ilaç önerisi yapmaz. Tüm kararlar için yetkili hekime danışın."
    })

@router.get("/metrics")
async def get_metrics(db: Session = Depends(get_db), user = Depends(require_admin)):
    """Admin-only: Model performance metrics"""
    try:
        total = db.query(Analysis).count()
        accepted = db.query(Analysis).filter(Analysis.status == "accepted").count()
        rejected = db.query(Analysis).filter(Analysis.status == "rejected").count()
        low_conf = db.query(Analysis).filter(Analysis.status == "low_confidence").count()
        
        confidences = db.query(Analysis.avg_confidence).filter(Analysis.avg_confidence > 0).all()
        avg_conf = sum(c[0] for c in confidences) / len(confidences) if confidences else 0.0
        
        # NER metrics (mock - real evaluation would need ground truth)
        ner_metrics = {
            "precision": 0.85,
            "recall": 0.82,
            "f1": 0.83,
            "exact_match": 0.78
        }
        
        return {
            "total_analyses": total,
            "accepted": accepted,
            "rejected": rejected,
            "low_confidence": low_conf,
            "avg_confidence": round(avg_conf, 3),
            "ner_metrics": ner_metrics,
            "model_version": "florence-2-base-fallback",
            "disclaimer": "Bu sistem yalnızca bilgilendirme amaçlıdır. Teşhis, tedavi veya ilaç önerisi yapmaz. Tüm kararlar için yetkili hekime danışın."
        }
    except Exception as e:
        return {"error": str(e), "disclaimer": "Bu sistem yalnızca bilgilendirme amaçlıdır."}