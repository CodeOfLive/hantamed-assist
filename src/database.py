from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config import DB_URL
import os

# SQLAlchemy Base tanımı
Base = declarative_base()

# Database engine ve session
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
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
    finally:
        db.close()
