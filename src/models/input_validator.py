import os
import sys
from PIL import Image
import pytesseract
import json
import re
from src.config import MEDICAL_KEYWORDS, COMMERCIAL_KEYWORDS

# === WINDOWS TESSERACT PATH FIX (HARDCODED) ===
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(TESSERACT_PATH):
    # PATH'e ekle
    tesseract_dir = os.path.dirname(TESSERACT_PATH)
    if tesseract_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = tesseract_dir + os.pathsep + os.environ.get("PATH", "")
    # pytesseract'e doÄŸrudan yol ver
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    # Environment variable fallback
    os.environ["TESSERACT_CMD"] = TESSERACT_PATH
else:
    # Fallback: sistem PATH'inde ara
    pass
# === END FIX ===


class InputValidator:
    def __init__(self):
        self.medical_re = re.compile("|".join(MEDICAL_KEYWORDS), re.IGNORECASE)
        self.comm_re = re.compile("|".join(COMMERCIAL_KEYWORDS), re.IGNORECASE)

    def check(self, image_path: str) -> dict:
        try:
            # Tesseract binary kontrolÃ¼
            if not os.path.exists(pytesseract.pytesseract.tesseract_cmd):
                return {
                    "score": 0.0, 
                    "accepted": False, 
                    "reason": f"Tesseract binary not found at: {pytesseract.pytesseract.tesseract_cmd}"
                }
            
            with Image.open(image_path) as img:
                # TÃ¼rkÃ§e + Ä°ngilizce OCR
                text = pytesseract.image_to_string(img, lang="tur+eng").lower()
            
            if not text or len(text.strip()) < 10:
                return {"score": 0.0, "accepted": False, "reason": "OCR metni boÅŸ veya Ã§ok kÄ±sa."}
            
            med_matches = len(self.medical_re.findall(text))
            comm_matches = len(self.comm_re.findall(text))
            
            # Ticari belge ise reddet
            if comm_matches >= 3 and med_matches == 0:
                return {"score": 0.0, "accepted": False, "reason": "Ticari belge algÄ±landÄ± (market fiÅŸi, fatura vb.)."}
            
            # Medikal iÃ§erik skorlama
            if med_matches == 0:
                score = 0.1
            elif med_matches == 1:
                score = 0.4
            elif med_matches == 2:
                score = 0.65
            else:
                score = min(0.4 + (med_matches * 0.25), 1.0)
            
            return {
                "score": score,
                "accepted": score >= 0.4,
                "reason": "Medikal iÃ§erik tespit edildi." if score >= 0.4 else "Yetersiz medikal anahtar kelime.",
                "debug": {"medical_matches": med_matches, "commercial_matches": comm_matches, "ocr_len": len(text)}
            }
            
        except Exception as e:
            return {
                "score": 0.0, 
                "accepted": False, 
                "reason": f"DoÄŸrulama hatasÄ±: {str(e)}"
            }

