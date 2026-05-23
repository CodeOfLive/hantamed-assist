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
    
    # ✅ Storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 10
    
    # ✅ Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()


# ✅ Global settings instance (this is what main.py imports)
settings = get_settings()