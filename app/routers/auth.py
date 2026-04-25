import logging
import os
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import firebase_admin
from firebase_admin import credentials, auth

from app.database import get_db
from app.models.user import User, UserRole
from app.core.config import settings
from app.core.security import create_access_token
from app.core.limiter import limiter

logger = logging.getLogger(__name__)

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
    id_token: str = Field(max_length=4096)

@router.post("/firebase/login")
@limiter.limit("10/minute")
async def firebase_login(request: Request, data: FirebaseLoginRequest, db: Session = Depends(get_db)):
    """Menerima id_token dari Flutter (Firebase), memverifikasi, dan membuat/melanjutkan sesi lokal"""
    try:
        # 1. Verifikasi token ke server Firebase
        decoded_token = auth.verify_id_token(data.id_token)

        email = decoded_token.get('email')
        if not email:
            raise ValueError("Email tidak ditemukan dalam payload token Firebase.")

        # Ambil nama dari Firebase, kalau kosong pakai nama depan dari email
        full_name = decoded_token.get('name') or email.split('@')[0]
        picture = decoded_token.get('picture', '')

        # 2. Cek User di DB PostgreSQL kita
        user_db = db.query(User).filter(User.email == email).first()

        # 2.5 Cek apakah akun masih aktif (jika user sudah ada)
        if user_db and not user_db.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Akun telah dinonaktifkan. Hubungi admin."
            )

        # 3. Kalau belum ada (User Baru Register di Flutter), kita otomatis simpan ke DB
        if not user_db:
            # Tentukan role: jika email cocok dengan INITIAL_ADMIN_EMAIL, jadikan super_admin
            initial_role = UserRole.USER.value
            if settings.INITIAL_ADMIN_EMAIL and email == settings.INITIAL_ADMIN_EMAIL:
                initial_role = UserRole.SUPER_ADMIN.value
                logger.info(f"User baru {email} otomatis dijadikan super_admin (INITIAL_ADMIN_EMAIL)")
            
            logger.info(f"User baru terdaftar via Firebase: {email} (role: {initial_role})")
            new_user = User(
                email=email, 
                full_name=full_name, 
                picture=picture, 
                provider="firebase",
                role=initial_role
            )
            db.add(new_user)
            try:
                db.commit()
                db.refresh(new_user)
                user_db = new_user
            except IntegrityError:
                db.rollback()
                logger.warning(f"Race condition pada login pertama {email} — user sudah dibuat oleh request lain")
                # Request lain sudah berhasil INSERT — ambil user yang sudah ada
                user_db = db.query(User).filter(User.email == email).first()
                if not user_db:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Terjadi kesalahan internal server."
                    )
                if not user_db.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Akun telah dinonaktifkan. Hubungi admin."
                    )
        
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
                "picture": user_db.picture,
                "role": user_db.role
            }
        }

    except auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="Token Firebase tidak valid.")
    except auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Token Firebase sudah kedaluwarsa.")
    except HTTPException:
        raise  # Propagate intentional HTTP errors (403 deactivated, etc.)
    except Exception as e:
        logger.error(f"Login GAGAL: {str(e)}")
        raise HTTPException(status_code=500, detail="Terjadi kesalahan internal server.")