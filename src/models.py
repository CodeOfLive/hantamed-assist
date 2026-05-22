"""
Database models for HantaMed Assist
KVKK-compliant: No PII stored, anonymized logging only
"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()


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
    
    analyses = relationship("Analysis", back_populates="user", lazy="select")


class Analysis(Base):
    """Analysis log entry - anonymized, no PII"""
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # ✅ File info
    filename = Column(String(255), nullable=True)
    image_hash = Column(String(64), index=True, nullable=False)
    file_size_kb = Column(Integer, nullable=True)
    image_format = Column(String(10), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    
    # ✅ Timestamps
    upload_timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # ✅ Validation & inference results
    relevance_score = Column(Float, nullable=False)
    avg_confidence = Column(Float, nullable=True)
    status = Column(String(20), nullable=False)
    
    # ✅ Extracted data (anonymized)
    extracted_entities = Column(Text, nullable=True)
    model_version = Column(String(50), nullable=True)
    qa_summary = Column(Text, nullable=True)
    
    # ✅ Performance metrics
    latency_ms = Column(Integer, nullable=True)
    
    # ✅ Admin panel detailed fields (migration 003)
    analysis_duration_ms = Column(Integer, nullable=True)
    ocr_text_preview = Column(Text, nullable=True)
    entities_json = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)  # ✅✅✅ BU SATIR KRİTİK ✅✅✅
    
    # ✅ Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="analyses")
    
    created_at = Column(DateTime, default=datetime.utcnow)


class SystemLog(Base):
    """System audit log - for debugging and compliance"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(String(10), nullable=False)
    module = Column(String(50), nullable=True)
    message = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=True)