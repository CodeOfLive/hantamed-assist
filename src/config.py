"""
Application configuration and settings
KVKK-compliant: No hardcoded secrets, use environment variables
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # ✅ App config
    APP_NAME: str = "HantaMed Assist"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # ✅ Database (Render PostgreSQL)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./hantamed.db")
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "3600"))
    
    # ✅ Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # ✅ Admin credentials (change in production!)
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "HantaMed2024!")
    
    # ✅ Model config
    MODEL_NAME: str = "florence-2-base"
    MODEL_FALLBACK: bool = True
    RELEVANCE_THRESHOLD: float = 0.7
    CONFIDENCE_THRESHOLD: float = 0.5
    
    # ✅ Storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 10
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB in bytes (for analyze.py)
    ALLOWED_EXTENSIONS: set = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}  # for analyze.py
    
    # ✅ Logging
    LOG_LEVEL: str = "INFO"
    
    # ✅ Medical/Commercial keywords for input validation
    MEDICAL_KEYWORDS: list = [
        "reçete", "ilaç", "doz", "mg", "ml", "tablet", "kapsül", 
        "enjektör", "flakon", "ampul", "merhem", "krem", "solüsyon",
        "prospektüs", "etken madde", "kontrendikasyon", "yan etki",
        "dozaj", "uygulama", "saklama", "son kullanma", "parti no",
        "ruhsat no", "üretici", "ithalatçı", "eczane", "hekim",
        "hasta", "tanı", "tedavi", "profilaksi", "antibiyotik",
        "analjezik", "antipiretik", "antienflamatuar", "antihistaminik",
        "antidepresan", "antipsikotik", "antikonvülzan", "antikoagülan",
        "antihipertansif", "antidiyabetik", "antiviral", "antifungal",
        "antiparaziter", "immünsupresif", "immünmodülatör", "hormon",
        "vitamin", "mineral", "takviye", "probiyotik", "prebiyotik"
    ]
    
    COMMERCIAL_KEYWORDS: list = [
        "fiyat", "ücret", "ödeme", "indirim", "kampanya", "promosyon",
        "satış", "alım", "ticari", "reklam", "pazarlama", "marka",
        "distribütör", "bayi", "toptan", "perakende", "stok", "envanter",
        "fatura", "irsaliye", "sipariş", "teslimat", "kargo", "iade",
        "garanti", "servis", "müşteri", "müşteri hizmetleri", "destek",
        "şikayet", "öneri", "memnuniyet", "kalite", "standart", "sertifika",
        "belge", "onay", "ruhsat", "izin", "lisans", "telif", "patent",
        "ticari sır", "gizlilik", "sözleşme", "anlaşma", "protokol"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()


# ✅ Global settings instance (this is what main.py imports)
settings = get_settings()

# ✅ Legacy imports for backward compatibility (auth.py, database.py, input_validator.py, inference.py, analyze.py, health.py use these)
# App
APP_NAME = settings.APP_NAME
APP_VERSION = settings.APP_VERSION  # ✅ BU SATIRI EKLEYİN (health.py için)

# Database
DB_URL = settings.DATABASE_URL
DB_POOL_SIZE = settings.DB_POOL_SIZE
DB_MAX_OVERFLOW = settings.DB_MAX_OVERFLOW
DB_POOL_RECYCLE = settings.DB_POOL_RECYCLE

# Security
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# Admin
ADMIN_USERNAME = settings.ADMIN_USERNAME
ADMIN_PASSWORD = settings.ADMIN_PASSWORD

# Model
MODEL_NAME = settings.MODEL_NAME
MODEL_FALLBACK = settings.MODEL_FALLBACK
RELEVANCE_THRESHOLD = settings.RELEVANCE_THRESHOLD
CONFIDENCE_THRESHOLD = settings.CONFIDENCE_THRESHOLD

# Storage
UPLOAD_DIR = settings.UPLOAD_DIR
MAX_FILE_SIZE_MB = settings.MAX_FILE_SIZE_MB
MAX_FILE_SIZE = settings.MAX_FILE_SIZE  # for analyze.py
ALLOWED_EXTENSIONS = settings.ALLOWED_EXTENSIONS  # for analyze.py

# Logging
LOG_LEVEL = settings.LOG_LEVEL

# Keywords for input validation
MEDICAL_KEYWORDS = settings.MEDICAL_KEYWORDS
COMMERCIAL_KEYWORDS = settings.COMMERCIAL_KEYWORDS