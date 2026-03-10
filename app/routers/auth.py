import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

# Import library resmi Google untuk verifikasi token
from google.oauth2 import id_token
from google.auth.transport import requests

from app.database import get_db
from app.models.user import User
from app.core import settings, create_access_token
from app.core.request_context import get_request_id

logger = logging.getLogger(__name__)

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/auth", tags=["Auth"])

# --- KONFIGURASI ---
# Kita hanya butuh CLIENT ID Backend (Web) untuk memverifikasi token dari Flutter
if not settings.GOOGLE_CLIENT_ID:
    raise RuntimeError("FATAL: GOOGLE_CLIENT_ID belum di-set di .env!")

# Buat model Pydantic untuk menangkap JSON body dari Flutter
class GoogleLoginRequest(BaseModel):
    id_token: str

@router.post("/google/login")
@limiter.limit("10/minute")
async def google_login(request: Request, data: GoogleLoginRequest, db: Session = Depends(get_db)):
    """Menerima id_token dari Flutter, memverifikasi ke Google, dan membuat sesi lokal"""
    logger.info("Memulai verifikasi token Google dari mobile app...")
    
    try:
        # 1. Verifikasi token ke server Google
        # Pastikan settings.GOOGLE_CLIENT_ID adalah Web Client ID kamu
        idinfo = id_token.verify_oauth2_token(
            data.id_token, 
            requests.Request(), 
            settings.GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10 # Toleransi delay waktu antar server
        )

        email = idinfo.get('email')
        full_name = idinfo.get('name', '')
        picture = idinfo.get('picture', '')

        if not email:
            raise ValueError("Email tidak ditemukan dalam payload token Google.")

        logger.info(f"Token valid untuk email: {email}")

        # 2. Cek User di DB (Logika aslimu)
        user_db = db.query(User).filter(User.email == email).first()
        
        if not user_db:
            # Logic register user baru
            logger.info(f"User baru terdaftar via Google: {email}")
            new_user = User(
                email=email, 
                full_name=full_name, 
                picture=picture, 
                provider="google"
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user_db = new_user
        else:
            logger.info(f"User existing login: {email}")
        
        # 3. Buat Access Token (JWT)
        access_token = create_access_token(
            data={"sub": str(user_db.id), "email": user_db.email}
        )
        
        logger.info(f"Login SUKSES - Token JWT dibuat untuk {user_db.email}")
        
        # 4. Return Token ke Frontend
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_info": { 
                "email": user_db.email,
                "full_name": user_db.full_name,
                "picture": user_db.picture
            }
        }

    except ValueError as e:
        # Menangkap error jika token dari Flutter palsu atau expired
        logger.error(f"Google Token Invalid: {str(e)}")
        raise HTTPException(status_code=401, detail="Token Google tidak valid atau sudah kedaluwarsa.")
        
    except Exception as e:
        logger.error(f"Login GAGAL: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Terjadi kesalahan internal server saat login.")

# NOTE: Endpoint /google/callback DIHAPUS karena Flutter tidak butuh callback web.