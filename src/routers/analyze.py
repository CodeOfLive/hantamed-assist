import os
import json
import time
import uuid
import hashlib
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request, BackgroundTasks
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import Analysis, SystemLog
from src.privacy_handler import process_privacy
from src.models.input_validator import InputValidator
from src.models.inference import FlorencePipeline
from src.privacy.pii_redactor import PiiRedactor
from src.config import CONFIDENCE_THRESHOLD, MAX_FILE_SIZE, ALLOWED_EXTENSIONS
from src.auth import get_current_user
from loguru import logger
import shutil
from PIL import Image

router = APIRouter(prefix="/api", tags=["analyze"])
validator = InputValidator()
redactor = PiiRedactor()
model = FlorencePipeline()

def _cleanup_temp_file(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        logger.warning(f"Cleanup failed for {path}: {e}")

def _log_analysis(db: Session, image_hash: str, relevance_score: float, avg_confidence: float, 
                status: str, extracted_entities: str, latency_ms: float, qa_summary: str):
    try:
        log_entry = Analysis(
            image_hash=image_hash,
            relevance_score=relevance_score,
            avg_confidence=avg_confidence,
            status=status,
            extracted_entities=extracted_entities,
            latency_ms=latency_ms,
            qa_summary=qa_summary[:500] if qa_summary else None
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        logger.error(f"Logging failed: {e}")
        db.rollback()

@router.post("/analyze")
async def analyze_image(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...), 
    accepted_policy: bool = True,
    db: Session = Depends(get_db)
):
    start_time = time.time()
    image_hash = None
    
    try:
        if not accepted_policy:
            raise HTTPException(400, detail="Veri işleme politikası kabul edilmelidir.")
        
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(400, detail="Desteklenmeyen dosya formatı.")
        
        tmp_path = f"uploads/{uuid.uuid4().hex}{ext}"
        os.makedirs("uploads", exist_ok=True)
        with open(tmp_path, "wb") as f:
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                os.remove(tmp_path)
                raise HTTPException(400, detail="Dosya boyutu 5MB limitini aşıyor.")
            f.write(content)
        
        val = validator.check(tmp_path)
        image_hash = hashlib.sha256(content).hexdigest()
        
        if val["score"] < 0.4:
            background_tasks.add_task(_cleanup_temp_file, tmp_path)
            _log_analysis(db, image_hash, val["score"], 0.0, "rejected", "{}", 0, val["reason"])
            return {
                "status": "rejected",
                "reason": "Yalnızca hantavirüs teşhis/tedavi süreçlerine ait reçete, laboratuvar raporu veya tıbbi görseller kabul edilmektedir.",
                "disclaimer": "Bu sistem yalnızca bilgilendirme amaçlıdır. Teşhis, tedavi veya ilaç önerisi yapmaz. Tüm kararlar için yetkili hekime danışın."
            }

        img = Image.open(tmp_path).convert("RGB")
        res = model.analyze(img)
        
        background_tasks.add_task(_cleanup_temp_file, tmp_path)
        redacted = redactor.clean_json(res.get("entities", {}))
        
        qa_summary = ""
        status_val = "accepted"
        if res["avg_confidence"] < CONFIDENCE_THRESHOLD or res.get("fallback"):
            qa_summary = "Yetersiz veri veya düşük güven skoru. Lütfen doktorunuza danışın."
            status_val = "low_confidence"
        else:
            qa_summary = "Veriler analiz edildi. Sonuçlar bilgilendirme amaçlıdır."
        
        _log_analysis(
            db, image_hash, val["score"], res["avg_confidence"], status_val,
            json.dumps(redacted), res.get("latency_ms", 0), qa_summary
        )
        
        return {
            "status": "success" if status_val == "accepted" else "warning",
            "entities": redacted,
            "avg_confidence": res["avg_confidence"],
            "qa_summary": qa_summary,
            "disclaimer": "Bu sistem yalnızca bilgilendirme amaçlıdır. Teşhis, tedavi veya ilaç önerisi yapmaz. Tüm kararlar için yetkili hekime danışın.",
            "metadata": {
                "latency_ms": res.get("latency_ms", 0),
                "model_version": "florence-2-base-fallback" if res.get("fallback") else "florence-2-base"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analyze failed: {e}")
        if image_hash and tmp_path and os.path.exists(tmp_path):
            background_tasks.add_task(_cleanup_temp_file, tmp_path)
        raise HTTPException(500, detail="Analiz sırasında beklenmeyen hata.")