import os
import json
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """
    Konfigurasi aplikasi yang diambil dari environment variables.
    Semua konfigurasi HARUS ada di .env file - tidak ada hardcoded values!
    """
    
    # Environment
    ENVIRONMENT: str  # Wajib dari .env: development / production
    
    # Database
    DATABASE_URL: str  # Wajib dari .env
    
    # JWT Authentication
    SECRET_KEY: str  # Wajib dari .env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int  # Wajib dari .env (sesuai .env: 10080)
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str  # Wajib dari .env
    GOOGLE_CLIENT_SECRET: str  # Wajib dari .env
    BASE_URL: str  # Wajib dari .env (jangan hardcoded localhost!)
    
    # MQTT
    MQTT_BROKER: str
    MQTT_PORT: int = 1883
    MQTT_TOPIC: str
    MQTT_USERNAME: str  # Wajib dari .env
    MQTT_PASSWORD: str  # Wajib dari .env

    # Alert Thresholds (configurable via .env)
    ALERT_TEMP_MAX: float = 35.0  # Suhu maksimum (°C)
    ALERT_TEMP_MIN: float = 20.0  # Suhu minimum (°C)
    ALERT_AMMONIA_MAX: float = 20.0  # Amonia maksimum (ppm)

    POSTGRES_USER: str 
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    
    # CORS - Parse JSON string dari .env
    CORS_ORIGINS: List[str]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS dari JSON string di .env"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Fallback jika format bukan JSON, split by comma
                return [origin.strip() for origin in v.split(",")]
        return v
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache()
def get_settings() -> Settings:
    """
    Singleton untuk mendapatkan settings.
    Di-cache supaya tidak baca ulang .env setiap kali dipanggil.
    Akan throw error jika ada .env variable yang required tapi kosong.
    """
    try:
        return Settings()
    except ValueError as e:
        raise RuntimeError(
            f"❌ FATAL: Ada .env variable yang missing atau invalid!\n{str(e)}\n"
            f"Pastikan semua required variables di .env sudah lengkap!"
        ) from e


# Instance global untuk kemudahan import
settings = get_settings()
