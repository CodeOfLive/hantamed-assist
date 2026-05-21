import os
from PIL import Image
import pytesseract
import json
import logging
from src.config import MEDICAL_KEYWORDS, COMMERCIAL_KEYWORDS
import re

# ✅ Cross-platform Tesseract path handling
TESSERACT_PATH = os.getenv("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

class InputValidator:
    def __init__(self):
        self.medical_re = re.compile('|'.join(MEDICAL_KEYWORDS), re.IGNORECASE)
        self.comm_re = re.compile('|'.join(COMMERCIAL_KEYWORDS), re.IGNORECASE)

    def check(self, image_path: str) -> dict:
        try:
            # Tesseract binary kontrolü
            if not os.path.exists(pytesseract.pytesseract.tesseract_cmd):
                try:
                    # System PATH'te tesseract var mı kontrol et
                    pytesseract.get_tesseract_version()
                except Exception as e:
                    logging.error(f"Tesseract not found: {e}")
                    return {
                        "score": 0.0, 
                        "accepted": False, 
                        "reason": "OCR engine not available."
                    }
            
            # OCR işlemi
            with Image.open(image_path) as img:
                # Türkçe + İngilizce OCR
                text = pytesseract.image_to_string(img, lang="tur+eng").lower().strip()
            
            # Debug log (Render logs'unda görünecek)
            logging.info(f"OCR text preview: {text[:200] if text else '(empty)'}...")
            
            # Boş metin kontrolü
            if not text or len(text) < 10:
                logging.warning(f"OCR text too short: {len(text)} chars")
                return {"score": 0.0, "accepted": False, "reason": "OCR metni boş veya çok kısa."}
            
            # Keyword matching
            med_matches = self.medical_re.findall(text)
            comm_matches = self.comm_re.findall(text)
            
            logging.info(f"Medical matches: {len(med_matches)} -> {med_matches[:5]}")
            logging.info(f"Commercial matches: {len(comm_matches)} -> {comm_matches[:5]}")
            
            # Ticari belge ise reddet
            if len(comm_matches) >= 3 and len(med_matches) == 0:
                return {"score": 0.0, "accepted": False, "reason": "Ticari belge algılandı."}
            
            # Medikal içerik skorlama - test için düşük threshold
            if len(med_matches) == 0:
                score = 0.3  # Sentetik veri için
            elif len(med_matches) == 1:
                score = 0.5
            elif len(med_matches) == 2:
                score = 0.7
            else:
                score = min(0.5 + (len(med_matches) * 0.2), 1.0)
            
            logging.info(f"Validation score: {score} (accepted: {score >= 0.4})")
            
            return {
                "score": score,
                "accepted": score >= 0.4,  # Test için düşük threshold
                "reason": "Medikal içerik tespit edildi." if score >= 0.4 else "Yetersiz medikal anahtar kelime.",
                "debug": {
                    "medical_matches": len(med_matches),
                    "commercial_matches": len(comm_matches),
                    "ocr_len": len(text),
                    "sample_keywords": med_matches[:3] if med_matches else []
                }
            }
            
        except Exception as e:
            logging.error(f"Validation error: {e}", exc_info=True)
            return {
                "score": 0.0, 
                "accepted": False, 
                "reason": f"Doğrulama hatası: {str(e)}"
            }