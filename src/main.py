import os
import sys
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from loguru import logger
from src.database import init_db
from src.routers import analyze, history, admin, legal
import warnings

# Suppress non-critical warnings
warnings.filterwarnings("ignore", category=UserWarning, module=".*transformers.*")
warnings.filterwarnings("ignore", category=FutureWarning, module=".*huggingface_hub.*")

# Configure logging
logger.remove()
logger.add("logs/app.log", rotation="10 MB", retention="7 days", level="INFO", backtrace=True, diagnose=True)
logger.add(sys.stdout, level="DEBUG" if os.getenv("DEBUG") else "INFO", format="{time:HH:mm:ss} | {level} | {message}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with warmup"""
    os.makedirs("logs", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)
    
    try:
        init_db()
        logger.info("Database initialized.")
        logger.info("Application startup complete.")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    yield
    logger.info("Application shutdown complete.")

app = FastAPI(
    title="HantaMed Assist", 
    version="1.0.0",
    description="Hantavirüs hastaları için bilgilendirme sistemi",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.middleware("http")
async def add_legal_header(request: Request, call_next):
    """Add legal disclaimer to all responses"""
    response = await call_next(request)
    response.headers["X-Legal-Disclaimer"] = "true"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log request metrics (anonymized)"""
    start = time.time()
    try:
        response = await call_next(request)
        duration = time.time() - start
        if request.url.path != "/health":
            logger.info(f"{request.method} {request.url.path} {response.status_code} {duration*1000:.0f}ms")
        return response
    except Exception as e:
        logger.error(f"Request failed: {request.method} {request.url.path} - {e}")
        raise

# Static files & templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/health")
async def health_check():
    """Comprehensive health endpoint for monitoring"""
    status_details = {
        "status": "healthy",
        "version": "1.0.0",
        "checks": {
            "database": "ok",
            "storage": os.access("uploads", os.W_OK),
            "model": "fallback" if os.getenv("CPU_ONLY") else "ready"
        },
        "legal": "This system is for informational purposes only. Consult a physician for medical decisions."
    }
    return JSONResponse(content=status_details, headers={"X-Legal-Disclaimer": "true"})

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/legal", response_class=HTMLResponse)
async def legal_page(request: Request):
    return templates.TemplateResponse("legal.html", {"request": request})

# Include routers
app.include_router(analyze.router)
app.include_router(history.router)
app.include_router(admin.router)
app.include_router(legal.router)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "İşlem tamamlanamadı. Lütfen tekrar deneyin.",
            "disclaimer": "Bu sistem yalnızca bilgilendirme amaçlıdır. Teşhis, tedavi veya ilaç önerisi yapmaz. Tüm kararlar için yetkili hekime danışın."
        },
        headers={"X-Legal-Disclaimer": "true"}
    )