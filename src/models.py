"""
Database models for HantaMed Assist
KVKK-compliant: No personal data stored without consent
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Analysis(Base):
    """Medical image analysis result model"""
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # ✅ File info (REQUIRED for admin panel)
    filename = Column(String(255), nullable=True)  # ✅ BU SATIRI EKLEYİN
    image_hash = Column(String(64), unique=True, index=True, nullable=False)
    file_size_kb = Column(Float, nullable=False)
    image_format = Column(String(10), nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    
    # ✅ Timestamps
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # ✅ Analysis results
    relevance_score = Column(Float, nullable=True)
    avg_confidence = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)  # ✅ BU SATIRI EKLEYİN
    status = Column(String(50), default="pending", nullable=False)
    extracted_entities = Column(JSON, nullable=True)
    model_version = Column(String(50), nullable=True)
    latency_ms = Column(Float, nullable=True)
    qa_summary = Column(Text, nullable=True)
    
    # ✅ Additional fields for admin panel
    analysis_duration_ms = Column(Float, nullable=True)
    ocr_text_preview = Column(Text, nullable=True)
    entities_json = Column(JSON, nullable=True)
    
    # ✅ User tracking (KVKK compliant - anonymized)
    user_id = Column(String(64), nullable=True)  # Hashed user ID, not personal data
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Analysis(id={self.id}, filename='{self.filename}', status='{self.status}')>"