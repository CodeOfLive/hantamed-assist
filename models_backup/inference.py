import torch
from transformers import AutoProcessor, AutoModelForCausalLM
from src.config import MODEL_NAME, CONFIDENCE_THRESHOLD
from src.models.ml_utils import parse_entities, calculate_confidence
import os
import time
import warnings
import re

warnings.filterwarnings("ignore", message=".*flash_attn.*")
os.environ["FLASH_ATTENTION_DISABLE"] = "1"

class FlorencePipeline:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.processor = None
        self._fallback_mode = self.device == "cpu"
        self._initialized = False
        self._init_error = None
        
    def _lazy_load(self):
        if self._initialized:
            return
        try:
            self.processor = AutoProcessor.from_pretrained(MODEL_NAME, trust_remote_code=True)
            dtype = torch.float16 if self.device == "cuda" else torch.float32
            
            self.model = AutoModelForCausalLM.from_pretrained(
                MODEL_NAME, 
                torch_dtype=dtype,
                device_map="auto" if self.device == "cuda" else None,
                trust_remote_code=True,
                attn_implementation="eager" if self.device == "cpu" else None,
                low_cpu_mem_usage=True
            ).eval()
            self._initialized = True
        except Exception as e:
            self._init_error = str(e)
            self._fallback_mode = True
            warnings.warn(f"Model load failed: {e}. Using safe fallback mode.")
    
    def _fallback_analyze(self, image, task="<OCR>") -> dict:
        return {
            "text": "",
            "entities": {},
            "avg_confidence": 0.0,
            "latency_ms": 0,
            "fallback": True,
            "warning": "CPU fallback mode: Limited analysis. Consult a physician for medical decisions."
        }
    
    def _sanitize_output(self, text: str, entities: dict) -> tuple:
        text = re.sub(r'[A-Za-z]:\\[^\s]+|data/raw/[^\s]+|\.png|\.jpg|\.jpeg', '', text)
        text = re.sub(r'\b\d{11}\b|\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', '[REDACTED]', text, flags=re.I)
        text = ' '.join(text.split()).strip()
        safe_entities = {}
        medical_keys = ['drug', 'dosage', 'lab', 'test', 'value', 'unit', 'name']
        for k, v in entities.items():
            if any(mk in k.lower() for mk in medical_keys) and isinstance(v, dict):
                safe_entities[k] = {kk: vv for kk, vv in v.items() if any(mk in kk.lower() for mk in medical_keys)}
        return text, safe_entities
    
    def analyze(self, image, task="<OCR>") -> dict:
        try:
            if self._fallback_mode or not self._initialized:
                self._lazy_load()
                if self._fallback_mode:
                    return self._fallback_analyze(image, task)
            
            start = time.time()
            prompt = f"{task}"
            inputs = self.processor(images=image, text=prompt, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                generated_ids = self.model.generate(
                    inputs["input_ids"], 
                    pixel_values=inputs["pixel_values"], 
                    max_new_tokens=128,
                    do_sample=False,
                    pad_token_id=self.processor.tokenizer.pad_token_id if hasattr(self.processor.tokenizer, 'pad_token_id') else 0
                )
            
            generated_text = self.processor.decode(generated_ids[0], skip_special_tokens=True)
            latency = (time.time() - start) * 1000
            
            entities = parse_entities(generated_text, task)
            conf = calculate_confidence(generated_text, entities)
            
            clean_text, clean_entities = self._sanitize_output(generated_text, entities)
            
            return {
                "text": clean_text,
                "entities": clean_entities,
                "avg_confidence": conf,
                "latency_ms": latency,
                "fallback": False
            }
        except Exception as e:
            warnings.warn(f"Analysis error: {e}. Using fallback.")
            return self._fallback_analyze(image, task)