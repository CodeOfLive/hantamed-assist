import os
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random

DRUGS = [
    {"name": "Rifampisin", "dose": "600 mg"}, {"name": "Doksiciklin", "dose": "100 mg"},
    {"name": "Azitromisin", "dose": "500 mg"}, {"name": "Favipiravir", "dose": "600 mg"},
    {"name": "Remdesivir", "dose": "100 mg"}
]
LAB_TESTS = ["WBC", "PLT", "Kreatinin", "ALT", "AST", "HCT"]
UNITS = {"WBC": "10^3/uL", "PLT": "10^3/uL", "Kreatinin": "mg/dL", "ALT": "U/L", "AST": "U/L", "HCT": "%"}

def generate_synthetic_image(output_dir: str, count: int = 100, start_id: int = 0):
    """Generate synthetic prescription/lab report images with OCR-readable text"""
    os.makedirs(output_dir, exist_ok=True)
    
    # ✅ Add explicit text overlay for OCR testing
    def add_ocr_text(img, text, position=(50, 100), font_size=20):
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        # Try to load a font, fallback to default
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", font_size)
        except:
            font = ImageFont.load_default()
        draw.text(position, text, fill=(0, 0, 0), font=font)
        return img
    
    for i in range(count):
        img_id = start_id + i
        
        # Create blank white image
        img = Image.new('RGB', (800, 600), color='white')
        
        # ✅ Add OCR-readable medical text with keywords from config
        medical_texts = [
            "Reçete No: RX-2024-001",
            "Hasta: Test Hasta",
            "İlaç: Rifampisin 600mg",
            "Doz: 1x1 tablet",
            "Laboratuvar: HantaVirüs PCR",
            "Sonuç: Negatif",
            "Tarih: 2024-01-15",
            "Dr. Ahmet Yılmaz",
            "Eczane: Sağlık Eczanesi"
        ]
        
        y_pos = 50
        for text in medical_texts:
            img = add_ocr_text(img, text, position=(50, y_pos), font_size=18)
            y_pos += 30
        
        # Save image
        output_path = os.path.join(output_dir, f"img_{img_id:03d}.png")
        img.save(output_path)
        
        # Log for debugging
        print(f"✅ Generated: {output_path} with OCR text")