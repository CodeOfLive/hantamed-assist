import os
import json
import time
import uuid
import hashlib
from datetime import datetime
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

def _log_analysis(db: Session, filename: str, image_hash: str, relevance_score: float, 
                avg_confidence: float, status: str, extracted_entities: dict, 
                latency_ms: float, qa_summary: str, ocr_preview: str = None):
    """Log analysis with enhanced details for admin panel"""
    try:
        # Truncate long text fields for storage efficiency
        ocr_preview = (ocr_preview[:500] + "...") if ocr_preview and len(ocr_preview) > 500 else ocr_preview
        qa_summary = (qa_summary[:500] + "...") if qa_summary and len(qa_summary) > 500 else qa_summary
        
        log_entry = Analysis(
            filename=filename[:255],  # Limit filename length
            image_hash=image_hash,
            relevance_score=relevance_score,
            avg_confidence=avg_confidence,
            status=status,
            # New fields for admin panel
            upload_timestamp=datetime.utcnow(),
            analysis_duration_ms=int(latency_ms),
            ocr_text_preview=ocr_preview,
            entities_json=extracted_entities if extracted_entities else {},
            confidence_score=avg_confidence,
            # Existing fields
            extracted_entities=json.dumps(extracted_entities) if extracted_entities else "{}",
            latency_ms=int(latency_ms),
            qa_summary=qa_summary
        )
        db.add(log_entry)
        db.commit()
        logger.info(f"Analysis logged: {filename} -> {status}")
    except Exception as e:
        logger.error(f"Logging failed: {e}")
        db.rollback()
        # Don't raise - logging failure shouldn't break the API

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
    tmp_path = None
    
    try:
        if not accepted_policy:
            raise HTTPException(400, detail="Veri işleme politikası kabul edilmelidir.")
        
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(400, detail="Desteklenmeyen dosya formatı.")
        
        # Save uploaded file
        tmp_path = f"uploads/{uuid.uuid4().hex}{ext}"
        os.makedirs("uploads", exist_ok=True)
        with open(tmp_path, "wb") as f:
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                os.remove(tmp_path)
                raise HTTPException(400, detail="Dosya boyutu 5MB limitini aşıyor.")
            f.write(content)
        
        # Validation with OCR
        val = validator.check(tmp_path)
        image_hash = hashlib.sha256(content).hexdigest()
        ocr_preview = val.get("debug", {}).get("sample_keywords", [])
        ocr_preview_str = ", ".join(ocr_preview[:10]) if ocr_preview else None
        
        # Reject if not medical content
        if val["score"] < 0.4:
            latency_ms = (time.time() - start_time) * 1000
            background_tasks.add_task(_cleanup_temp_file, tmp_path)
            _log_analysis(
                db, file.filename, image_hash, val["score"], 0.0, 
                "rejected", {}, latency_ms, val["reason"], ocr_preview_str
            )
            return {
                "status": "rejected",
                "reason": "Yalnızca hantavirüs teşhis/tedavi süreçlerine ait reçete, laboratuvar raporu veya tıbbi görseller kabul edilmektedir.",
                "disclaimer": "Bu sistem yalnızca bilgilendirme amaçlıdır. Teşhis, tedavi veya ilaç önerisi yapmaz. Tüm kararlar için yetkili hekime danışın."
            }

        # Florence-2 inference
        img = Image.open(tmp_path).convert("RGB")
        res = model.analyze(img)
        
        # Cleanup temp file
        background_tasks.add_task(_cleanup_temp_file, tmp_path)
        
        # PII redaction
        redacted = redactor.clean_json(res.get("entities", {}))
        
        # Determine status and summary
        qa_summary = ""
        status_val = "accepted"
        if res["avg_confidence"] < CONFIDENCE_THRESHOLD or res.get("fallback"):
            qa_summary = "Yetersiz veri veya düşük güven skoru. Lütfen doktorunuza danışın."
            status_val = "low_confidence"
        else:
            qa_summary = "Veriler analiz edildi. Sonuçlar bilgilendirme amaçlıdır."
        
        # Log with enhanced details
        latency_ms = (time.time() - start_time) * 1000
        _log_analysis(
            db, file.filename, image_hash, val["score"], res["avg_confidence"], 
            status_val, redacted, latency_ms, qa_summary, ocr_preview_str
        )
        
        return {
            "status": "success" if status_val == "accepted" else "warning",
            "entities": redacted,
            "avg_confidence": res["avg_confidence"],
            "qa_summary": qa_summary,
            "disclaimer": "Bu sistem yalnızca bilgilendirme amaçlıdır. Teşhis, tedavi veya ilaç önerisi yapmaz. Tüm kararlar için yetkili hekime danışın.",
            "metadata": {
                "latency_ms": int(latency_ms),
                "model_version": "florence-2-base-fallback" if res.get("fallback") else "florence-2-base",
                "filename": file.filename
            }
        }
        
    except HTTPException:
        if tmp_path and os.path.exists(tmp_path):
            background_tasks.add_task(_cleanup_temp_file, tmp_path)
        raise
    except Exception as e:
        logger.error(f"Analyze failed: {e}", exc_info=True)
        if tmp_path and os.path.exists(tmp_path):
            background_tasks.add_task(_cleanup_temp_file, tmp_path)
        raise HTTPException(500, detail="Analiz sırasında beklenmeyen hata.")