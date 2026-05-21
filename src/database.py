from sqlalchemy import create_engine, inspect, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from src.config import DB_URL, DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_RECYCLE
import os

# SQLAlchemy Base tanımı
Base = declarative_base()

# ✅ PostgreSQL vs SQLite için optimize edilmiş engine ayarları
def create_database_engine():
    """Database engine'ı PostgreSQL veya SQLite'a göre yapılandır"""
    
    if DB_URL.startswith("postgresql"):
        # ✅ PostgreSQL production ayarları
        connect_args = {"sslmode": "require"}
        
        # Render environment'ında channel_binding ekle
        if os.getenv("RENDER") == "true":
            connect_args["channel_binding"] = "require"
        
        return create_engine(
            DB_URL,
            poolclass=QueuePool,
            pool_size=DB_POOL_SIZE,
            max_overflow=DB_MAX_OVERFLOW,
            pool_recycle=DB_POOL_RECYCLE,
            pool_pre_ping=True,  # Connection health check before use
            connect_args=connect_args,
            echo=False  # Production'da SQL loglarını kapat
        )
    else:
        # ✅ SQLite fallback (local development)
        return create_engine(
            DB_URL, 
            connect_args={"check_same_thread": False},
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            echo=os.getenv("DEBUG") == "true"
        )

# Engine ve session factory
engine = create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """FastAPI dependency injection için session provider"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Tabloları oluştur ve default admin ekle - bcrypt uyumlu"""
    from src.models import User
    from passlib.hash import bcrypt
    from src.config import DEFAULT_ADMIN_PASS
    
    # Tüm modellerin metadata'sını register et
    Base.metadata.create_all(bind=engine)
    
    # Admin kullanıcısı oluştur (sadece ilk çalıştırmada)
    inspector = inspect(engine)
    if not inspector.has_table("users"):
        return
        
    db = SessionLocal()
    try:
        # Önce mevcut admin var mı kontrol et
        admin = db.query(User).filter(User.username == "admin").first()
        
        if not admin:
            # bcrypt ile doğru hashleme (utf-8 encode/decode)
            password_bytes = DEFAULT_ADMIN_PASS.encode("utf-8")
            hashed = bcrypt.hash(password_bytes)
            password_hash = hashed if isinstance(hashed, str) else hashed.decode("utf-8")
            
            new_admin = User(
                username="admin",
                password_hash=password_hash,
                role="admin",
                password_change_required=True
            )
            db.add(new_admin)
            db.commit()
            print(f"✅ Default admin created: admin / {DEFAULT_ADMIN_PASS}")
        else:
            # Mevcut admin'in şifresini test et, gerekirse resetle
            password_bytes = DEFAULT_ADMIN_PASS.encode("utf-8")
            try:
                verified = bcrypt.verify(password_bytes, admin.password_hash)
                if not verified:
                    # Hash uyumsuz, resetle
                    new_hash = bcrypt.hash(password_bytes)
                    admin.password_hash = new_hash if isinstance(new_hash, str) else new_hash.decode("utf-8")
                    admin.password_change_required = True
                    db.commit()
                    print("✅ Admin password reset to default.")
            except Exception:
                # Eski hash formatı, resetle
                new_hash = bcrypt.hash(password_bytes)
                admin.password_hash = new_hash if isinstance(new_hash, str) else new_hash.decode("utf-8")
                admin.password_change_required = True
                db.commit()
                print("✅ Admin password format updated.")
    except Exception as e:
        db.rollback()
        print(f"⚠️ Admin init error: {e}")
        raise
    finally:
        db.close()