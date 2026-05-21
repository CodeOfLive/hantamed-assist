from sqlalchemy import create_engine, inspect, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from src.config import DB_URL, DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_RECYCLE
import os

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
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Tabloları oluştur ve default admin ekle - bcrypt 72-byte limit uyumlu"""
    from src.models import User
    from passlib.hash import bcrypt
    from src.config import DEFAULT_ADMIN_PASS
    
    Base.metadata.create_all(bind=engine)
    
    inspector = inspect(engine)
    if not inspector.has_table("users"):
        return
        
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            # ✅ bcrypt 72-byte limit: şifreyi truncate et
            password_bytes = DEFAULT_ADMIN_PASS.encode("utf-8")[:72]
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
            print(f"✅ Default admin created: admin / {DEFAULT_ADMIN_PASS}")
        else:
            # Mevcut admin'in şifresini güncelle (aynı truncate mantığı)
            password_bytes = DEFAULT_ADMIN_PASS.encode("utf-8")[:72]
            try:
                verified = bcrypt.verify(password_bytes, admin.password_hash)
                if not verified:
                    new_hash = bcrypt.hash(password_bytes)
                    admin.password_hash = new_hash if isinstance(new_hash, str) else new_hash.decode("utf-8")
                    admin.password_change_required = False
                    db.commit()
                    print("✅ Admin password reset to default.")
            except Exception:
                new_hash = bcrypt.hash(password_bytes)
                admin.password_hash = new_hash if isinstance(new_hash, str) else new_hash.decode("utf-8")
                admin.password_change_required = False
                db.commit()
                print("✅ Admin password format updated.")
    except Exception as e:
        db.rollback()
        print(f"⚠️ Admin init error: {e}")
        raise
    finally:
        db.close()