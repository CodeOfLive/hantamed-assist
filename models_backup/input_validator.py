import os
from PIL import Image, ImageEnhance, ImageFilter
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

    def _preprocess_image(self, img: Image.Image) -> Image.Image:
        """Enhance image for better OCR accuracy"""
        # Convert to grayscale
        img = img.convert('L')
        
        # Increase contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)
        
        # Sharpen
        img = img.filter(ImageFilter.SHARPEN)
        
        # Resize for better OCR (Tesseract works best at 300 DPI equivalent)
        width, height = img.size
        if width < 1200:
            scale = 1200 / width
            img = img.resize((int(width * scale), int(height * scale)), Image.Resampling.LANCZOS)
        
        return img

    def check(self, image_path: str) -> dict:
        try:
            # Tesseract binary kontrolü
            if not os.path.exists(pytesseract.pytesseract.tesseract_cmd):
                try:
                    pytesseract.get_tesseract_version()
                except Exception as e:
                    logging.error(f"Tesseract not found: {e}")
                    return {
                        "score": 0.0, 
                        "accepted": False, 
                        "reason": "OCR engine not available."
                    }
            
            # OCR işlemi - enhanced preprocessing ile
            with Image.open(image_path) as img:
                processed_img = self._preprocess_image(img)
                # Türkçe + İngilizce + config for better accuracy
                custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,:;!?-()/%°"'
                text = pytesseract.image_to_string(processed_img, lang="tur+eng", config=custom_config).lower().strip()
            
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
            
            # Medikal içerik skorlama
            if len(med_matches) == 0:
                score = 0.3
            elif len(med_matches) == 1:
                score = 0.5
            elif len(med_matches) == 2:
                score = 0.7
            else:
                score = min(0.5 + (len(med_matches) * 0.2), 1.0)
            
            logging.info(f"Validation score: {score} (accepted: {score >= 0.4})")
            
            return {
                "score": score,
                "accepted": score >= 0.4,
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