"""
Database models for HantaMed Assist
KVKK-compliant: No PII stored, anonymized logging only
"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
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
    __tablename__ = "analyses"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=True)
    image_hash = Column(String(64), index=True, nullable=False)
    file_size_kb = Column(Integer, nullable=True)
    image_format = Column(String(10), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    upload_timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    relevance_score = Column(Float, nullable=False)
    avg_confidence = Column(Float, nullable=True)
    status = Column(String(20), nullable=False)
    extracted_entities = Column(Text, nullable=True)
    model_version = Column(String(50), nullable=True)
    qa_summary = Column(Text, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    analysis_duration_ms = Column(Integer, nullable=True)
    ocr_text_preview = Column(Text, nullable=True)
    entities_json = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="analyses")
    created_at = Column(DateTime, default=datetime.utcnow)


class SystemLog(Base):
    __tablename__ = "system_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(String(10), nullable=False)
    module = Column(String(50), nullable=True)
    message = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=True)

# CACHE_BUST: 2024-05-23-deploy-fix  ← Bu satır Docker'ın dosyayı "değişmiş" görmesini sağlar