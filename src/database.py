"""
Database configuration and initialization for HantaMed Assist
"""
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from src.config import DB_URL, DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_RECYCLE
import os
import logging

# ✅ Logger tanımla
logger = logging.getLogger(__name__)

# ✅ Base'i BURADA tanımla (src/models.py'den import ETME!)
Base = declarative_base()


def create_database_engine():
    """Database engine'ı PostgreSQL veya SQLite'a göre yapılandır"""
    if DB_URL.startswith("postgresql"):
        connect_args = {"sslmode": "require"}
        if os.getenv("RENDER") == "true":
            connect_args["channel_binding"] = "require"
        return create_engine(
            DB_URL,
            poolclass=QueuePool,
            pool_size=DB_POOL_SIZE,
            max_overflow=DB_MAX_OVERFLOW,
            pool_recycle=DB_POOL_RECYCLE,
            pool_pre_ping=True,
            connect_args=connect_args,
            echo=False
        )
    else:
        return create_engine(
            DB_URL, 
            connect_args={"check_same_thread": False},
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            echo=os.getenv("DEBUG") == "true"
        )


engine = create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def add_missing_columns():
    """Mevcut tablolara eksik kolonları ekle"""
    try:
        with engine.connect() as conn:
            columns_to_add = [
                ("filename", "VARCHAR(255)"),
                ("confidence_score", "FLOAT"),
                ("analysis_duration_ms", "INTEGER"),
                ("ocr_text_preview", "TEXT"),
                ("entities_json", "JSON"),
                ("upload_timestamp", "TIMESTAMP"),
            ]
            
            for col_name, col_type in columns_to_add:
                try:
                    if engine.dialect.name == 'postgresql':
                        conn.execute(text(
                            f"ALTER TABLE analyses ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
                        ))
                    else:
                        try:
                            conn.execute(text(
                                f"ALTER TABLE analyses ADD COLUMN {col_name} {col_type}"
                            ))
                        except Exception:
                            pass
                    logger.info(f"✅ Column check: analyses.{col_name}")
                except Exception as e:
                    logger.warning(f"⚠️ Column {col_name} may already exist: {e}")
            
            conn.commit()
            logger.info("✅ All missing columns checked/added to analyses table")
            
    except Exception as e:
        logger.error(f"❌ Error adding missing columns: {e}", exc_info=True)


def init_db():
    """Initialize database with error handling"""
    # ✅ Import'ları fonksiyon İÇİNDE yap (circular import önler)
    from src.models import User, Analysis, SystemLog
    from passlib.hash import bcrypt
    from src.config import ADMIN_PASSWORD
    
    # ✅ 1. Tabloları oluştur
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created/verified")
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        return
    
    # ✅ 2. Eksik kolonları ekle
    try:
        add_missing_columns()
    except Exception as e:
        logger.error(f"⚠️ Error adding columns: {e}")
    
    # ✅ 3. Admin kullanıcı oluştur
    try:
        inspector = inspect(engine)
        if not inspector.has_table("users"):
            logger.warning("⚠️ users table not found")
            return
        
        db = SessionLocal()
        try:
            admin = db.query(User).filter(User.username == "admin").first()
            if not admin:
                password_bytes = ADMIN_PASSWORD.encode("utf-8")[:72]
                hashed = bcrypt.hash(password_bytes)
                password_hash = hashed if isinstance(hashed, str) else hashed.decode("utf-8")
                new_admin = User(
                    username="admin",
                    password_hash=password_hash,
                    role="admin",
                    password_change_required=False
                )
                db.add(new_admin)
                db.commit()
                logger.info(f"✅ Default admin created: admin / {ADMIN_PASSWORD}")
            else:
                logger.info("✅ Admin user already exists")
        except Exception as e:
            logger.error(f"⚠️ Admin init error: {e}")
            db.rollback()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"⚠️ Error in admin init: {e}")