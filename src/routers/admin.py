from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from src.database import get_db
from src.auth import authenticate_user, create_access_token, require_admin, get_current_user
from src.models import User, Analysis, Drug
from passlib.context import CryptContext
from src.config import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES
import os
import json

router = APIRouter(tags=["admin"])
templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    # If already authenticated, redirect to admin
    try:
        token = request.cookies.get("access_token") or request.headers.get("Authorization", "").replace("Bearer ", "")
        if token:
            from jose import jwt
            from src.config import SECRET_KEY, ALGORITHM
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("sub"):
                return RedirectResponse(url="/admin", status_code=303)
    except:
        pass
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Admin login - returns JWT token via JSON + HttpOnly cookie.
    Supports both API clients (JSON response) and browser navigation (cookie).
    """
    try:
        user = authenticate_user(username, password, db)
        if not user:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Geçersiz kullanıcı adı veya şifre."},
                headers={"X-Legal-Disclaimer": "true", "Content-Type": "application/json"}
            )
        
        token_data = {"sub": user.username, "role": user.role}
        access_token = create_access_token(data=token_data)
        
        # Create response with JSON for API clients
        response = JSONResponse(
            content={"access_token": access_token, "token_type": "bearer"},
            headers={"X-Legal-Disclaimer": "true", "Content-Type": "application/json"}
        )
        
        # Set HttpOnly cookie for browser navigation compatibility
        is_https = request.url.scheme == "https" or os.getenv("RENDER", "false") == "true"
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=is_https,
            samesite="lax",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            path="/"
        )
        
        return response
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Sistem hatası: {str(e)}"},
            headers={"X-Legal-Disclaimer": "true", "Content-Type": "application/json"}
        )

@router.get("/admin", response_class=HTMLResponse)
async def dashboard(request: Request, user: User = Depends(require_admin)):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "user": user})

@router.post("/admin/drugs", response_model=None)
async def add_drug(request: Request, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    """Admin paneli: Yeni ilaç ekle (JSON body ile)"""
    try:
        body = await request.json()
        required = ["name", "active_ingredient"]
        if not all(k in body for k in required):
            raise HTTPException(400, "name ve active_ingredient zorunludur.")
        
        new_drug = Drug(
            name=body["name"],
            active_ingredient=body.get("active_ingredient", ""),
            indication=body.get("indication", ""),
            side_effects=body.get("side_effects", ""),
            source=body.get("source", "manual")
        )
        db.add(new_drug)
        db.commit()
        db.refresh(new_drug)
        return JSONResponse(
            content={"message": "İlaç eklendi.", "id": new_drug.id},
            headers={"X-Legal-Disclaimer": "true"}
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"İlaç eklenemedi: {str(e)}")

@router.post("/admin/logout")
async def logout(request: Request):
    """Logout: Clear auth cookie"""
    response = JSONResponse(content={"message": "Çıkış başarılı."})
    response.delete_cookie(key="access_token", path="/")
    return response