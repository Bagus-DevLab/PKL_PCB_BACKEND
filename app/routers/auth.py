import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi_sso.sso.google import GoogleSSO
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.core import settings, create_access_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])

# --- KONFIGURASI ---
if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
    raise RuntimeError("FATAL: GOOGLE_CLIENT_ID atau GOOGLE_CLIENT_SECRET belum di-set di .env!")

CALLBACK_PATH = "/auth/google/callback"
REDIRECT_URI = f"{settings.BASE_URL.rstrip('/')}{CALLBACK_PATH}"

# Setup SSO
sso = GoogleSSO(
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    allow_insecure_http=True 
)

@router.get("/google/login")
async def google_login():
    """Mengarahkan user ke halaman login Google"""
    # PERBAIKAN: Pakai context manager
    async with sso:
        return await sso.get_login_redirect()

@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    try:
        # PERBAIKAN: Pakai context manager disini juga
        async with sso:
            # 1. Terima data dari Google
            user_google = await sso.verify_and_process(request)
        
        # 2. Cek User di DB
        user_db = db.query(User).filter(User.email == user_google.email).first()
        
        if not user_db:
            # Logic register user baru
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
        
        # 3. Buat Access Token (JWT)
        access_token = create_access_token(
            data={"sub": str(user_db.id), "email": user_db.email}
        )
        
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

    except Exception as e:
        logger.error(f"ERROR LOGIN: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login Gagal: {str(e)}")