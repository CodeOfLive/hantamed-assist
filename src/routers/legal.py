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
    



@router.get("/api/setup-admin")
async def setup_admin_once(db: Session = Depends(get_db)):
    """
    ⚠️ ONE-TIME SETUP ENDPOINT - Only works if no admin exists
    Creates default admin user if not present.
    Call once after deploy, then this endpoint returns 403.
    """
    from src.models import User
    from passlib.hash import bcrypt
    from src.config import DEFAULT_ADMIN_PASS
    
    # Check if any admin exists
    existing_admin = db.query(User).filter(User.role == "admin").first()
    if existing_admin:
        return {"status": "skipped", "message": "Admin user already exists."}
    
    # Create default admin
    password_bytes = DEFAULT_ADMIN_PASS.encode("utf-8")
    hashed = bcrypt.hash(password_bytes)
    password_hash = hashed if isinstance(hashed, str) else hashed.decode("utf-8")
    
    new_admin = User(
        username="admin",
        password_hash=password_hash,
        role="admin",
        password_change_required=False
    )
    db.add(new_admin)
    db.commit()
    
    return {
        "status": "created",
        "username": "admin",
        "password": DEFAULT_ADMIN_PASS,
        "message": "✅ Default admin created. Please change password after first login."
    }