import re
import json

def parse_entities(ocr_text: str, task: str) -> dict:
    entities = {}
    lines = ocr_text.strip().split('\n')
    drug_pat = re.compile(r'([A-ZİĞÖŞÜÇ]{3,}[\w]*)\s+([\d\.]+)\s*(mg|ml|gr|IU)')
    lab_pat = re.compile(r'(\w+)\s*[:=]\s*([\d\.]+)\s*(\w+)')
    
    for line in lines:
        m = drug_pat.search(line)
        if m:
            entities[f"drug_{len(entities)}"] = {"name": m.group(1), "dosage": f"{m.group(2)} {m.group(3)}"}
        l = lab_pat.search(line)
        if l:
            entities[f"lab_{len(entities)}"] = {"test": l.group(1), "value": f"{l.group(2)} {l.group(3)}"}
    return entities

def calculate_confidence(text: str, entities: dict) -> float:
    if not entities: return 0.5
    conf = 0.6
    if len(text) > 100: conf += 0.15
    if len(entities) > 0: conf += 0.15
    return min(conf, 1.0)
