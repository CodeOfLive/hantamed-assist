import re
import json

class PiiRedactor:
    PII_PATTERNS = {
        'tc_kimlik': r'\b\d{11}\b',
        'phone': r'\b(\+90|0)?\s?5\d{2}\s?\d{3}\s?\d{2}\s?\d{2}\b',
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'hospital_ids': r'\b(PROTOKOL|HASTA NO|DOSYA NO)[:\s]*[\w\d-]+\b',
        'address': r'(\bMahalle|Cadde|Sokak|Apt|Kat)\b[\s\w\.,]*\d+',
        'doctor_signature': r'(Dr\.|Uzm\.|Prof\.)\s[A-Za-z\s]{3,}',
        'barcode': r'\b\d{12,15}\b'
    }
    
    SAFE_FIELDS = {'drug_name', 'dosage', 'lab_value', 'symptom_code', 'test_name', 'unit', 'reference_range'}

    def clean_text(self, ocr_text: str) -> str:
        if not ocr_text: return ""
        for pattern in self.PII_PATTERNS.values():
            ocr_text = re.sub(pattern, '[REDACTED]', ocr_text)
        return ocr_text

    def clean_json(self, entities: dict) -> dict:
        safe = {}
        for k, v in entities.items():
            if k not in self.SAFE_FIELDS:
                if isinstance(v, str):
                    safe[k] = self.clean_text(v)
                else:
                    continue
            else:
                safe[k] = v
        return safe