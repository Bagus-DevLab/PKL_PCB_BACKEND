import logging
import os
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

# Import library Firebase Admin
import firebase_admin
from firebase_admin import credentials, auth

from app.database import get_db
from app.models.user import User
from app.core import settings, create_access_token
from app.core.request_context import get_request_id

logger = logging.getLogger(__name__)

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/auth", tags=["Auth"])

# --- KONFIGURASI FIREBASE ---
# Pastikan lu udah naruh file JSON dari Firebase di root folder backend lu
# Kasih if check biar gak bentrok kalau FastAPI di-reload (Hot Reload)
FIREBASE_CREDENTIALS_FILE = "firebase-adminsdk.json"

if not firebase_admin._apps:
    if not os.path.exists(FIREBASE_CREDENTIALS_FILE):
        raise RuntimeError(f"FATAL: File {FIREBASE_CREDENTIALS_FILE} tidak ditemukan! Download dari Firebase Console.")
    
    cred = credentials.Certificate(FIREBASE_CREDENTIALS_FILE)
    firebase_admin.initialize_app(cred)


# Buat model Pydantic untuk menangkap JSON body dari Flutter
class FirebaseLoginRequest(BaseModel):
    id_token: str

# Endpoint kita ganti namanya biar rapi
@router.post("/firebase/login")
@limiter.limit("10/minute")
async def firebase_login(request: Request, data: FirebaseLoginRequest, db: Session = Depends(get_db)):
    """Menerima id_token dari Flutter (Firebase), memverifikasi, dan membuat sesi lokal"""
    logger.info("Memulai verifikasi token Firebase dari mobile app...")
    
    try:
        # 1. Verifikasi token ke server Firebase
        decoded_token = auth.verify_id_token(data.id_token)

        email = decoded_token.get('email')
        full_name = decoded_token.get('name', '')
        picture = decoded_token.get('picture', '')
        # firebase_uid = decoded_token.get('uid') # Bisa lu simpen ke DB kalau butuh

        if not email:
            raise ValueError("Email tidak ditemukan dalam payload token Firebase.")

        logger.info(f"Token valid untuk email: {email}")

        # 2. Cek User di DB PostgreSQL lu
        user_db = db.query(User).filter(User.email == email).first()
        
        if not user_db:
            # Logic register user baru
            logger.info(f"User baru terdaftar via Firebase: {email}")
            new_user = User(
                email=email, 
                full_name=full_name, 
                picture=picture, 
                provider="firebase" # Ubah providernya biar ketahuan
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user_db = new_user
        else:
            logger.info(f"User existing login: {email}")
        
        # 3. Buat Access Token (JWT Lokal punya lu)
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

    except auth.InvalidIdTokenError as e:
        logger.error(f"Firebase Token Invalid: {str(e)}")
        raise HTTPException(status_code=401, detail="Token Firebase tidak valid.")
        
    except auth.ExpiredIdTokenError as e:
        logger.error(f"Firebase Token Expired: {str(e)}")
        raise HTTPException(status_code=401, detail="Token Firebase sudah kedaluwarsa.")
        
    except Exception as e:
        logger.error(f"Login GAGAL: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Terjadi kesalahan internal server saat login.")