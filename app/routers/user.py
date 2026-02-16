import logging
from fastapi import APIRouter, Depends
from app.models.user import User
from app.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users", 
    tags=["Users"]
)

@router.get("/me")
async def read_current_user(current_user: User = Depends(get_current_user)):
    """
    Endpoint ini TERKUNCI.
    Cuma bisa dibuka kalau bawa Token JWT yang valid.
    """
    logger.debug(f"User {current_user.email} mengakses profile")
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "picture": current_user.picture,
        "status": "Kamu berhasil masuk area rahasia! 🎉"
    }