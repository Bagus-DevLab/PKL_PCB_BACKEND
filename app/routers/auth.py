import logging
import os
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

# Import library Firebase Admin
import firebase_admin
from firebase_admin import credentials, auth

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.config import settings
# Sesuaikan import dari security.py yang baru kita buat
from app.core.security import create_access_token, get_password_hash, verify_password

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

# ==========================================
# 1. ENDPOINT REGISTRASI MANUAL
# ==========================================
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Mendaftar user baru menggunakan Email dan Password"""
    # Cek apakah email sudah terdaftar (baik via Firebase atau Lokal)
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email sudah terdaftar. Silakan login.")
    
    # Hash password
    hashed_password = get_password_hash(user.password)
    
    # Simpan user baru dengan provider "local"
    new_user = User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        provider="local" 
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "Registrasi berhasil, silakan login", "user_id": str(new_user.id)}

# ==========================================
# 2. ENDPOINT LOGIN MANUAL
# ==========================================
@router.post("/login")
@limiter.limit("10/minute")
def login_local(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login menggunakan Email dan Password"""
    # Form data bawaan Swagger menganggap email sebagai 'username'
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email atau password salah")
        
    # Cegah user Firebase login pakai form ini jika dia belum set password
    if user.provider == "firebase" and not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Akun ini terdaftar menggunakan Google. Silakan gunakan tombol Login with Google."
        )
    
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email atau password salah")
    
    # Buat JWT Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_info": {
            "email": user.email,
            "full_name": user.full_name,
            "picture": user.picture
        }
    }

# ==========================================
# 3. ENDPOINT LOGIN FIREBASE (GOOGLE OAUTH)
# ==========================================
@router.post("/firebase/login")
@limiter.limit("10/minute")
async def firebase_login(request: Request, data: FirebaseLoginRequest, db: Session = Depends(get_db)):
    """Menerima id_token dari Flutter (Firebase), memverifikasi, dan membuat sesi lokal"""
    logger.info("Memulai verifikasi token Firebase dari mobile app...")
    
    try:
        # Verifikasi token ke server Firebase
        decoded_token = auth.verify_id_token(data.id_token)

        email = decoded_token.get('email')
        full_name = decoded_token.get('name', '')
        picture = decoded_token.get('picture', '')

        if not email:
            raise ValueError("Email tidak ditemukan dalam payload token Firebase.")

        logger.info(f"Token valid untuk email: {email}")

        # Cek User di DB
        user_db = db.query(User).filter(User.email == email).first()
        
        if not user_db:
            logger.info(f"User baru terdaftar via Firebase: {email}")
            new_user = User(
                email=email, 
                full_name=full_name, 
                picture=picture, 
                provider="firebase",
                hashed_password=None # Pastikan kosong karena login via Google
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user_db = new_user
        else:
            logger.info(f"User existing login: {email}")
        
        # Buat Access Token (JWT Lokal)
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user_db.id), "email": user_db.email},
            expires_delta=access_token_expires
        )
        
        logger.info(f"Login SUKSES - Token JWT dibuat untuk {user_db.email}")
        
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