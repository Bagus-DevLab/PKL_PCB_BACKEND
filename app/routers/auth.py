import os
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi_sso.sso.google import GoogleSSO
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User # Pastikan path import ini benar sesuai struktur folder lo
from app.utils.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

# Setup Google SSO
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
# Ganti URL ini sesuai environment (Localhost vs Production)
# Ini harus SAMA PERSIS dengan yang didaftarkan di Google Cloud Console
REDIRECT_URI = "http://localhost:8000/auth/google/callback" 

sso = GoogleSSO(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    allow_insecure_http=True # True cuma buat development (localhost), False kalau production (HTTPS)
)

@router.get("/google/login")
async def google_login():
    """Mengarahkan user ke halaman login Google"""
    return await sso.get_login_redirect()

@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    try:
        # 1. Terima data dari Google (SAMA SEPERTI SEBELUMNYA)
        user_google = await sso.verify_and_process(request)
        
        # 2. Cek User di DB (SAMA SEPERTI SEBELUMNYA - JANGAN DIHAPUS)
        user_db = db.query(User).filter(User.email == user_google.email).first()
        if not user_db:
            # Logic register user baru (SAMA SEPERTI SEBELUMNYA)
            new_user = User(
                email=user_google.email, 
                full_name=user_google.display_name, 
                picture=user_google.picture, 
                provider="google"
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user_db = new_user
        
        # --- PERUBAHAN UTAMA DISINI ---
        
        # 3. Buat Access Token (JWT)
        # Kita masukkan ID User dan Email ke dalam token
        access_token = create_access_token(
            data={"sub": str(user_db.id), "email": user_db.email}
        )
        
        # 4. Return Token ke Frontend
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_info": { # Opsional: Data user dikit buat nampilin foto di pojok kanan atas
                "email": user_db.email,
                "full_name": user_db.full_name,
                "picture": user_db.picture
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))