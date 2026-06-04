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
from src.config import CONFIDENCE_THRESHOLD, MAX_FILE_SIZE, ALLOWED_EXTENSIONS, MEDICAL_KEYWORDS
from loguru import logger
import shutil
from PIL import Image
import pytesseract

router = APIRouter(prefix="/api", tags=["analyze"])


def _cleanup_temp_file(path: str):
    """Geçici dosyayı sil"""
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        logger.warning(f"Cleanup failed for {path}: {e}")


def _perform_ocr(image_path: str) -> str:
    """Gerçek Tesseract OCR ile metin çıkar"""
    try:
        img = Image.open(image_path)
        # Türkçe + İngilizce OCR
        text = pytesseract.image_to_string(img, lang='tur+eng')
        return text.strip()
    except Exception as e:
        logger.error(f"❌ OCR failed: {e}")
        return ""


def _check_medical_content(ocr_text: str) -> dict:
    """OCR metninde medikal anahtar kelimeleri kontrol et"""
    if not ocr_text:
        return {
            "is_valid": False, 
            "score": 0.0, 
            "reason": "OCR metni boş", 
            "keywords_found": []
        }
    
    text_lower = ocr_text.lower()
    keywords_found = [kw for kw in MEDICAL_KEYWORDS if kw.lower() in text_lower]
    
    # Skor: bulunan kelime sayısına göre (5+ kelime = 1.0)
    score = min(1.0, len(keywords_found) / 5.0)
    
    return {
        "is_valid": score >= 0.2,  # En az 1 kelime bulunmalı
        "score": score,
        "reason": f"{len(keywords_found)} medikal kelime bulundu",
        "keywords_found": keywords_found[:10]
    }


def _extract_entities(ocr_text: str) -> dict:
    """OCR metninden basit entity çıkarımı"""
    entities = {}
    text_lower = ocr_text.lower()
    
    # Yaygın ilaç isimleri (gerçek sistemde AI kullanılır)
    drug_names = [
        "paracetamol", "ibuprofen", "amoxicillin", "omeprazole", 
        "metformin", "atorvastatin", "lisinopril", "salbutamol",
        "cetirizine", "pantoprazol", "aspirin", "metoprolol",
        "amlodipin", "losartan", "ramipril", "bisoprolol",
        "prednol", "dekort", "avil", "nurofen", "majezik",
        "dolven", "apranax", "muscoril", "parol", "talvos",
        "rifampisin", "izoniazid", "etambutol", "pirazinamid"
    ]
    
    drug_idx = 0
    for drug in drug_names:
        if drug in text_lower:
            entities[f"drug_{drug_idx}"] = {
                "name": drug.title(),
                "confidence": 0.85,
                "type": "medication"
            }
            drug_idx += 1
    
    return entities


def _log_analysis(db: Session, filename: str, image_hash: str, relevance_score: float, 
                avg_confidence: float, status: str, extracted_entities: dict, 
                latency_ms: float, qa_summary: str, ocr_preview: str = None):
    """Analizi veritabanına güvenli bir şekilde kaydet"""
    try:
        # ✅ GÜVENLİ KESME: None kontrolü ekle
        safe_filename = (filename[:255] if filename else "unknown_file")
        safe_ocr = (ocr_preview[:500] + "...") if ocr_preview and len(ocr_preview) > 500 else (ocr_preview or "")
        safe_summary = (qa_summary[:500] + "...") if qa_summary and len(qa_summary) > 500 else (qa_summary or "")
        
        log_entry = Analysis(
            filename=safe_filename,
            image_hash=image_hash,
            relevance_score=float(relevance_score or 0.0),
            avg_confidence=float(avg_confidence or 0.0),
            status=status,
            upload_timestamp=datetime.utcnow(),
            analysis_duration_ms=int(latency_ms or 0),
            ocr_text_preview=safe_ocr,
            entities_json=extracted_entities if extracted_entities else {},
            confidence_score=float(avg_confidence or 0.0),
            extracted_entities=json.dumps(extracted_entities) if extracted_entities else "{}",
            latency_ms=int(latency_ms or 0),
            qa_summary=safe_summary
        )
        db.add(log_entry)
        db.commit()
        logger.info(f"✅ Analysis logged successfully: {safe_filename} -> {status}")
    except Exception as e:
        logger.error(f"❌ Logging failed: {e}", exc_info=True)
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
    tmp_path = None

     # ✅ GÜVENLİ FILENAME ERİŞİMİ
    filename = getattr(file, 'filename', None) or "unknown_file.png"
    logger.info(f"📁 Received file: {filename}")

    try:
        if not accepted_policy:
            raise HTTPException(400, detail="Veri işleme politikası kabul edilmelidir.")
        
        ext = os.path.splitext(filename)[1].lower() if '.' in filename else ".png"
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(400, detail="Desteklenmeyen dosya formatı.")
        
        # Dosyayı kaydet
        tmp_path = f"uploads/{uuid.uuid4().hex}{ext}"
        os.makedirs("uploads", exist_ok=True)
        with open(tmp_path, "wb") as f:
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                os.remove(tmp_path)
                raise HTTPException(400, detail="Dosya boyutu 5MB limitini aşıyor.")
            f.write(content)
        
        image_hash = hashlib.sha256(content).hexdigest()
        
        # ✅ GERÇEK OCR (Tesseract)
        logger.info(f"🔍 Starting OCR for: {filename}")
        ocr_text = _perform_ocr(tmp_path)
        logger.info(f"📝 OCR text length: {len(ocr_text)} chars")
        logger.info(f"📝 OCR preview: {ocr_text[:200]}")
        
        # ✅ Medikal içerik kontrolü
        val = _check_medical_content(ocr_text)
        logger.info(f"🔬 Medical check: score={val['score']:.2f}, valid={val['is_valid']}, keywords={val['keywords_found']}")
        
        ocr_preview_str = ", ".join(val.get("keywords_found", []))
        
        
        # Tıbbi içerik yoksa reddet
        if not val["is_valid"]:
            latency_ms = (time.time() - start_time) * 1000
            background_tasks.add_task(_cleanup_temp_file, tmp_path)
            _log_analysis(
                db, filename, image_hash, val["score"], 0.0, 
                "rejected", {}, latency_ms, val["reason"], ocr_preview_str
            )
            return {
                "status": "rejected",
                "reason": "Yalnızca reçete, laboratuvar raporu veya tıbbi görseller kabul edilmektedir. Yeterli medikal içerik bulunamadı.",
                "disclaimer": "Bu sistem yalnızca bilgilendirme amaçlıdır. Teşhis, tedavi veya ilaç önerisi yapmaz. Tüm kararlar için yetkili hekime danışın."
            }

        # ✅ Entity çıkarımı
        entities = _extract_entities(ocr_text)
        logger.info(f"📦 Entities extracted: {len(entities)}")
        
        # Geçici dosyayı sil
        background_tasks.add_task(_cleanup_temp_file, tmp_path)
        
        # Durum belirle
        avg_confidence = val["score"]
        qa_summary = ""
        status_val = "accepted"
        
        if avg_confidence < CONFIDENCE_THRESHOLD:
            qa_summary = "Yetersiz veri veya düşük güven skoru. Lütfen daha net bir görsel yükleyin veya doktorunuza danışın."
            status_val = "low_confidence"
        else:
            qa_summary = f"Veriler başarıyla analiz edildi. {len(entities)} ilaç/etken madde tespit edildi. Sonuçlar bilgilendirme amaçlıdır."
        
        # Veritabanına kaydet
        latency_ms = (time.time() - start_time) * 1000
        _log_analysis(
            db, filename, image_hash, val["score"], avg_confidence, 
            status_val, entities, latency_ms, qa_summary, ocr_preview_str
        )
        
        return {
            "status": "success" if status_val == "accepted" else "warning",
            "entities": entities,
            "avg_confidence": avg_confidence,
            "qa_summary": qa_summary,
            "disclaimer": "Bu sistem yalnızca bilgilendirme amaçlıdır. Teşhis, tedavi veya ilaç önerisi yapmaz. Tüm kararlar için yetkili hekime danışın.",
            "metadata": {
                "latency_ms": int(latency_ms),
                "model_version": "tesseract-ocr-tur+eng",
                "filename": filename,
                "keywords_found": val.get("keywords_found", [])
            }
        }
        
    except HTTPException:
        if tmp_path and os.path.exists(tmp_path):
            background_tasks.add_task(_cleanup_temp_file, tmp_path)
        raise
    except Exception as e:
        logger.error(f"❌ Analyze failed: {e}", exc_info=True)
        if tmp_path and os.path.exists(tmp_path):
            background_tasks.add_task(_cleanup_temp_file, tmp_path)
        raise HTTPException(500, detail=f"Analiz sırasında beklenmeyen hata: {str(e)}")