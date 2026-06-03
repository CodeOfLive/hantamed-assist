"""
Database models for HantaMed Assist
KVKK-compliant: No personal data stored without consent
"""
# ✅ KRİTİK: Base'i database.py'den import et (aynı Base nesnesini kullan!)
from src.database import Base
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean
from datetime import datetime


class User(Base):
    """Admin user model for authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="admin", nullable=False)
    password_change_required = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


class Analysis(Base):
    """Medical image analysis result model"""
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # ✅ File info
    filename = Column(String(255), nullable=True)
    image_hash = Column(String(64), unique=True, index=True, nullable=False)
    file_size_kb = Column(Float, nullable=True)
    image_format = Column(String(10), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    
    # ✅ Timestamps
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    
    # ✅ Analysis results
    relevance_score = Column(Float, nullable=True)
    avg_confidence = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    status = Column(String(50), default="pending", nullable=False)
    extracted_entities = Column(JSON, nullable=True)
    model_version = Column(String(50), nullable=True)
    latency_ms = Column(Float, nullable=True)
    qa_summary = Column(Text, nullable=True)
    
    # ✅ Additional fields for admin panel
    analysis_duration_ms = Column(Float, nullable=True)
    ocr_text_preview = Column(Text, nullable=True)
    entities_json = Column(JSON, nullable=True)
    
    # ✅ User tracking
    user_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Analysis(id={self.id}, filename='{self.filename}', status='{self.status}')>"


class SystemLog(Base):
    """System audit log"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    level = Column(String(10), nullable=False)
    module = Column(String(50), nullable=True)
    message = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=True)