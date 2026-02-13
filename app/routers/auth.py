import os
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi_sso.sso.google import GoogleSSO
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User # Pastikan path import ini benar sesuai struktur folder lo

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
    """Menerima balikan dari Google dan proses login/register"""
    try:
        # 1. Ambil data user dari Google
        user_google = await sso.verify_and_process(request)
        
        if not user_google:
            raise HTTPException(status_code=400, detail="Gagal login dengan Google")

        # 2. Cek apakah user sudah ada di database kita?
        user_db = db.query(User).filter(User.email == user_google.email).first()

        if not user_db:
            # --- SKENARIO REGISTER (User Baru) ---
            print(f"User baru terdeteksi: {user_google.email}. Membuat akun...")
            new_user = User(
                email=user_google.email,
                full_name=user_google.display_name,
                picture=user_google.picture, # Pastikan kolom ini sudah ada di model User lo
                provider="google"
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user_db = new_user
        else:
            # --- SKENARIO LOGIN (User Lama) ---
            print(f"User lama login kembali: {user_google.email}")
            # Opsional: Update foto/nama kalau berubah di Google
            if user_db.picture != user_google.picture:
                user_db.picture = user_google.picture
                db.commit()

        # 3. TODO: Nanti disini kita generate JWT Token buat Flutter
        # Untuk sekarang, kita return data mentahnya dulu buat ngetes
        return {
            "status": "success",
            "message": "Login berhasil",
            "user": {
                "id": str(user_db.id),
                "email": user_db.email,
                "full_name": user_db.full_name,
                "picture": user_db.picture
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))