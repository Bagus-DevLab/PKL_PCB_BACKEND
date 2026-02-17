from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from app.core.config import settings


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Membuat JWT access token.
    
    Args:
        data: Dictionary data yang akan di-encode ke token (biasanya user_id, email)
        expires_delta: Custom waktu expired (opsional)
    
    Returns:
        String JWT token yang sudah di-encode
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Memverifikasi dan mendecode JWT token.
    
    Args:
        token: String JWT token
    
    Returns:
        Dictionary payload jika valid, None jika tidak valid
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None
