import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/hantamed.db")
SECRET_KEY = os.getenv("SECRET_KEY", "HantaMed-Secure-Secret-Key-2024-Production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
DEFAULT_ADMIN_PASS = "HantaMed2024!"
MODEL_NAME = "microsoft/Florence-2-base"
CONFIDENCE_THRESHOLD = 0.7
MAX_FILE_SIZE = 5 * 1024 * 1024 # 5MB
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}
MEDICAL_KEYWORDS = {
    "reçete", "rx", "ilaç", "eczane", "doz", "laboratuvar", "tahlil", 
    "plt", "kreatinin", "wbc", "hastane", "dr.", "test", "teşhis",
    "hct", "hb", "glukoz", "ürea", "sgot", "sgpt", "tsh", "hba1c"
}
COMMERCIAL_KEYWORDS = {
    "market", "kasa", "toplam tutar", "indirim", "barkod", "fatura", 
    "adet", "kdv", "fiş", "alışveriş", "kasada", "alışveriş"
}