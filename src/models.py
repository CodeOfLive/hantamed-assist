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
    role = Column(String(20), default="admin", nullable=False)  # admin, operator, viewer
    password_change_required = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    analyses = relationship("Analysis", back_populates="user", lazy="select")

class Analysis(Base):
    """Analysis log entry - anonymized, no PII"""
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # File info (anonymized)
    filename = Column(String(255), nullable=True)  # Original filename (sanitized)
    image_hash = Column(String(64), index=True, nullable=False)  # SHA256 hash of content
    
    # Validation & inference results
    relevance_score = Column(Float, nullable=False)  # InputValidator score (0.0-1.0)
    avg_confidence = Column(Float, nullable=True)  # Model confidence average
    status = Column(String(20), nullable=False)  # accepted/rejected/low_confidence
    
    # Extracted data (anonymized)
    extracted_entities = Column(Text, nullable=True)  # JSON string of entities
    qa_summary = Column(Text, nullable=True)  # QA-generated summary
    
    # Performance metrics
    latency_ms = Column(Integer, nullable=True)  # Inference latency
    
    # ✅ Admin panel detailed fields (migration 003)
    upload_timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    analysis_duration_ms = Column(Integer, nullable=True)  # Total processing time
    ocr_text_preview = Column(Text, nullable=True)  # First 500 chars of OCR output
    entities_json = Column(JSON, nullable=True)  # Structured entities dict
    confidence_score = Column(Float, nullable=True)  # Duplicate for explicit queries
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="analyses")
    
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemLog(Base):
    """System audit log - for debugging and compliance"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(String(10), nullable=False)  # INFO/WARNING/ERROR
    module = Column(String(50), nullable=True)  # e.g., "validator", "inference"
    message = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=True)  # Structured context (anonymized)