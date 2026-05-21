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
            if not os.path.exists(pytesseract.pytesseract.tesseract_cmd):
                try:
                    pytesseract.get_tesseract_version()
                except Exception:
                    return {
                        "score": 0.0, 
                        "accepted": False, 
                        "reason": "Tesseract binary not found."
                    }
            
            with Image.open(image_path) as img:
                text = pytesseract.image_to_string(img, lang="tur+eng").lower()
            
            logging.info(f"OCR text preview: {text[:200]}...")
            
            if not text or len(text.strip()) < 10:
                return {"score": 0.0, "accepted": False, "reason": "OCR metni boş veya çok kısa."}
            
            med_matches = len(self.medical_re.findall(text))
            comm_matches = len(self.comm_re.findall(text))
            
            logging.info(f"Medical matches: {med_matches}, Commercial matches: {comm_matches}")
            
            if comm_matches >= 3 and med_matches == 0:
                return {"score": 0.0, "accepted": False, "reason": "Ticari belge algılandı."}
            
            # Medikal içerik skorlama - test için düşük threshold
            if med_matches == 0:
                score = 0.3
            elif med_matches == 1:
                score = 0.5
            elif med_matches == 2:
                score = 0.7
            else:
                score = min(0.5 + (med_matches * 0.2), 1.0)
            
            return {
                "score": score,
                "accepted": score >= 0.4,
                "reason": "Medikal içerik tespit edildi." if score >= 0.4 else "Yetersiz medikal anahtar kelime.",
                "debug": {"medical_matches": med_matches, "commercial_matches": comm_matches, "ocr_len": len(text)}
            }
            
        except Exception as e:
            logging.error(f"Validation error: {e}", exc_info=True)
            return {
                "score": 0.0, 
                "accepted": False, 
                "reason": f"Doğrulama hatası: {str(e)}"
            }