import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ✅ PostgreSQL + SQLite destekli DATABASE_URL
DB_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/hantamed.db")

# ✅ PostgreSQL connection pooling ayarları
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))

# Security & Auth
SECRET_KEY = os.getenv("SECRET_KEY", "HantaMed-Secure-Secret-Key-2024-Production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
DEFAULT_ADMIN_PASS = os.getenv("DEFAULT_ADMIN_PASS", "HantaMed2024!")

# ML Model Config
MODEL_NAME = "microsoft/Florence-2-base"
CONFIDENCE_THRESHOLD = 0.7

# File Upload Limits
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}

# Input Validation Keywords
MEDICAL_KEYWORDS = {
    "reçete", "rx", "ilaç", "eczane", "doz", "laboratuvar", "tahlil", 
    "plt", "kreatinin", "wbc", "hastane", "dr.", "test", "teşhis",
    "hct", "hb", "glukoz", "ürea", "sgot", "sgpt", "tsh", "hba1c"
}
COMMERCIAL_KEYWORDS = {
    "market", "kasa", "toplam tutar", "indirim", "barkod", "fatura", 
    "adet", "kdv", "fiş", "alışveriş", "kasada", "alışveriş"
}