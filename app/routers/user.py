import logging
from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.models.user import User
from app.dependencies import get_current_user
from app.core.request_context import get_request_id

logger = logging.getLogger(__name__)

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(
    prefix="/users", 
    tags=["Users"]
)

# 1. Endpoint Update Nama
@router.patch("/me", response_model=UserResponse)
def update_user_me(full_name: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user.full_name = full_name
    db.commit()
    db.refresh(current_user)
    return current_user

# 2. Endpoint Hapus Akun
@router.delete("/me")
def delete_user_me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.delete(current_user)
    db.commit()
    return {"message": "Akun berhasil dihapus dari database lokal"}