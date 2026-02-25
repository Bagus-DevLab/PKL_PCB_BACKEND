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

@router.get("/me")
@limiter.limit("30/minute")
async def read_current_user(
    request: Request,
    current_user: User = Depends(get_current_user)
):
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
        "status": "Kamu berhasil masuk area rahasia!"
    }