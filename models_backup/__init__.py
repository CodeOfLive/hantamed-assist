from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

__all__ = ["User", "Drug", "Analysis", "SystemLog"]

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), server_default="user")
    password_change_required = Column(Boolean, server_default="true")

class Drug(Base):
    __tablename__ = "drugs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    active_ingredient = Column(String(100))
    indication = Column(Text)
    side_effects = Column(Text)
    source = Column(String(200))

class Analysis(Base):
    __tablename__ = "analyses"
    id = Column(Integer, primary_key=True, index=True)
    image_hash = Column(String(64), nullable=False, index=True)
    file_size_kb = Column(Float)
    image_format = Column(String(10))
    width = Column(Integer)
    height = Column(Integer)
    upload_timestamp = Column(DateTime, index=True)
    relevance_score = Column(Float)
    avg_confidence = Column(Float)
    status = Column(String(20), server_default="accepted", index=True)
    extracted_entities = Column(Text)
    model_version = Column(String(20))
    latency_ms = Column(Float)
    qa_summary = Column(Text)

class SystemLog(Base):
    __tablename__ = "system_logs"
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(10), server_default="INFO")
    message = Column(Text)
    timestamp = Column(DateTime, index=True)
    endpoint = Column(String(50))
    latency_ms = Column(Float)
