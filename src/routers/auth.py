from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import timedelta
import logging

from src.database import get_db
from src.auth import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from src.models import User

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login endpoint - returns JWT token or redirects"""
    try:
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            # Form submit: show error on login page
            if "text/html" in request.headers.get("accept", ""):
                return templates.TemplateResponse(
                    "login.html", 
                    {"request": request, "error": "Kullanıcı adı veya şifre hatalı."},
                    status_code=401
                )
            # API call: return JSON error
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Kullanıcı adı veya şifre hatalı.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "role": user.role}, 
            expires_delta=access_token_expires
        )
        
        # Form submit: redirect with cookie
        if "text/html" in request.headers.get("accept", ""):
            response = RedirectResponse(url="/admin", status_code=303)
            response.set_cookie(
                key="access_token", 
                value=access_token, 
                httponly=True, 
                max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                samesite="lax"
            )
            return response
        
        # API call: return JSON token
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        # Form submit: show generic error
        if "text/html" in request.headers.get("accept", ""):
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "error": "İşlem tamamlanamadı. Lütfen tekrar deneyin."},
                status_code=500
            )
        # API call: return JSON error
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "İşlem tamamlanamadı. Lütfen tekrar deneyin.",
                "disclaimer": "Bu sistem yalnızca bilgilendirme amaçlıdır. Teşhis, tedavi veya ilaç önerisi yapmaz. Tüm kararlar için yetkili hekime danışın."
            }
        )

@router.get("/admin/logout")
async def logout(request: Request):
    """Logout - clear cookie and redirect"""
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="access_token")
    return response