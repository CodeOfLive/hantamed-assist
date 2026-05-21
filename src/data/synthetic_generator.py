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

def generate_synthetic_data(count=1300):
    if os.path.exists("data/raw/synth_imgs") and os.path.exists("data/raw/ground_truth.json"):
        return
    
    os.makedirs("data/raw/synth_imgs", exist_ok=True)
    gt = []
    
    for i in range(count):
        w, h = 250, 400
        img = Image.new('RGB', (w,h), color='white')
        draw = ImageDraw.Draw(img)
        
        content = []
        is_rec = i < 1000
        if is_rec:
            drug = random.choice(DRUGS)
            draw.text((20, 20), "REÇETE", fill='black')
            draw.text((20, 60), f"İlaç: {drug['name']}", fill='black')
            draw.text((20, 90), f"Doz: {drug['dose']}", fill='black')
            content.append({"type": "drug", "value": drug})
        else:
            test = random.choice(LAB_TESTS)
            val = round(random.uniform(10, 200), 1)
            draw.text((20, 20), "LABORATUVAR RAPORU", fill='black')
            draw.text((20, 60), f"{test}: {val} {UNITS[test]}", fill='black')
            content.append({"type": "lab", "test": test, "value": val, "unit": UNITS[test]})
            
        draw.text((20, h-40), f"Hasta No: [REDACTED] | Tarih: 2024-01-01", fill='gray')
        path = f"data/raw/synth_imgs/img_{i}.png"
        img.save(path)
        gt.append({"id": i, "path": path, "ground_truth": content})
        
    with open("data/raw/ground_truth.json", "w") as f:
        json.dump(gt, f, indent=2)