import logging
import os
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

import firebase_admin
from firebase_admin import credentials, auth

from app.database import get_db
from app.models.user import User
from app.core.config import settings
from app.core.security import create_access_token

logger = logging.getLogger(__name__)

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# --- KONFIGURASI FIREBASE ---
FIREBASE_CREDENTIALS_FILE = "firebase-adminsdk.json"

if not firebase_admin._apps:
    if not os.path.exists(FIREBASE_CREDENTIALS_FILE):
        logger.warning(f"File {FIREBASE_CREDENTIALS_FILE} tidak ditemukan! Login Firebase mungkin gagal.")
    else:
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_FILE)
        firebase_admin.initialize_app(cred)

class FirebaseLoginRequest(BaseModel):
    id_token: str

@router.post("/firebase/login")
@limiter.limit("10/minute")
async def firebase_login(request: Request, data: FirebaseLoginRequest, db: Session = Depends(get_db)):
    """Menerima id_token dari Flutter (Firebase), memverifikasi, dan membuat/melanjutkan sesi lokal"""
    try:
        # 1. Verifikasi token ke server Firebase
        decoded_token = auth.verify_id_token(data.id_token)

        email = decoded_token.get('email')
        # Ambil nama dari Firebase, kalau kosong pakai nama depan dari email
        full_name = decoded_token.get('name') or email.split('@')[0]
        picture = decoded_token.get('picture', '')

        if not email:
            raise ValueError("Email tidak ditemukan dalam payload token Firebase.")

        # 2. Cek User di DB PostgreSQL kita
        user_db = db.query(User).filter(User.email == email).first()
        
        # 3. Kalau belum ada (User Baru Register di Flutter), kita otomatis simpan ke DB
        if not user_db:
            logger.info(f"User baru terdaftar via Firebase: {email}")
            new_user = User(
                email=email, 
                full_name=full_name, 
                picture=picture, 
                provider="firebase"
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user_db = new_user
        
        # 4. Buat Access Token (JWT Lokal)
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user_db.id), "email": user_db.email},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_info": { 
                "email": user_db.email,
                "full_name": user_db.full_name,
                "picture": user_db.picture
            }
        }

    except auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="Token Firebase tidak valid.")
    except auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Token Firebase sudah kedaluwarsa.")
    except Exception as e:
        logger.error(f"Login GAGAL: {str(e)}")
        raise HTTPException(status_code=500, detail="Terjadi kesalahan internal server.")