"""
HantaMed Assist - Main Application Entry Point
KVKK-compliant medical image analysis system
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text

from src.config import settings
from src.database import engine, SessionLocal, Base, init_db
from src.models import Analysis  # ✅ Model import for startup check
from src.routers import auth, admin, analyze, health

# ✅ Logging config
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # ✅ Startup: Initialize database (creates tables + adds missing columns)
    try:
        logger.info("🚀 Starting database initialization...")
        init_db()  # ✅ Bu fonksiyon:
                   # 1. Tabloları oluşturur (yoksa)
                   # 2. Eksik kolonları ekler (filename, confidence_score, vb.)
                   # 3. Admin kullanıcıyı oluşturur
        logger.info("✅ Database initialization complete")
        
        # Database connection test
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection: OK")
        
        # Model columns test (artık eksik olmamalı)
        if hasattr(Analysis, '__table__'):
            cols = [c.name for c in Analysis.__table__.columns]
            logger.info(f"✅ Analysis columns: {cols}")
            if 'confidence_score' not in cols:
                logger.error("❌ confidence_score column MISSING in Analysis model!")
            else:
                logger.info("✅ confidence_score column: PRESENT")
            if 'filename' not in cols:
                logger.error("❌ filename column MISSING in Analysis model!")
            else:
                logger.info("✅ filename column: PRESENT")
        
        logger.info("✅ Application startup checks complete")
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}", exc_info=True)
        raise
    
    yield  # Application running
    
    # ✅ Shutdown: Cleanup
    logger.info("🛑 Application shutting down...")


# ✅ Create FastAPI app WITH lifespan
app = FastAPI(
    title="HantaMed Assist",
    description="KVKK-compliant medical image analysis system",
    version="1.0.0",
    lifespan=lifespan
)

# ✅ Include routers
app.include_router(auth.router)     # /login, /admin/logout
app.include_router(admin.router)    # /admin/
app.include_router(analyze.router)  # /api/analyze
app.include_router(health.router)   # /health

# ✅ Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ✅ Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root page with redirect to login or health info"""
    return templates.TemplateResponse("index.html", {"request": request})


# ✅ Global exception handler (for generic errors)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors with generic message"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "İşlem tamamlanamadı. Lütfen tekrar deneyin.",
            "disclaimer": "Bu sistem yalnızca bilgilendirme amaçlıdır. Teşhis, tedavi veya ilaç önerisi yapmaz. Tüm kararlar için yetkili hekime danışın."
        }
    )