from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status
import os

# Ambil konfigurasi dari .env (yang baru aja lo update)
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

def create_access_token(data: dict):
    """
    Fungsi ini menerima dictionary data user, 
    menambahkan waktu expired, 
    lalu mengenkripsinya menjadi string token.
    """
    to_encode = data.copy()
    
    # Tentukan kapan token ini kadaluarsa
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Masukkan info expired ke dalam data
    to_encode.update({"exp": expire})
    
    # Enkripsi data menggunakan Secret Key
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def verify_token(token: str):
    """
    Fungsi untuk membuka token dan mengecek keasliannya.
    Kalau token palsu atau expired, dia bakal error.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None