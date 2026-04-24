import json
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
from typing import List, Union


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
    
    # Device Online Timeout (detik)
    # Device dianggap online jika heartbeat terakhir dalam rentang ini.
    # Default 120 detik (2 menit) — toleransi 2x interval heartbeat normal (60 detik).
    DEVICE_ONLINE_TIMEOUT_SECONDS: int = 120
    
    # Admin Seed - Email yang otomatis dijadikan admin saat pertama kali login
    # Digunakan untuk bootstrap admin pertama (chicken-and-egg problem)
    INITIAL_ADMIN_EMAIL: str = ""

    POSTGRES_USER: str 
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    
    # CORS Origins — mendukung 3 format di .env:
    #   1. JSON array:    CORS_ORIGINS=["https://pcb.my.id","https://api.pcb.my.id"]
    #   2. Comma-separated: CORS_ORIGINS=https://pcb.my.id,https://api.pcb.my.id
    #   3. Single origin:   CORS_ORIGINS=https://pcb.my.id
    CORS_ORIGINS: Union[str, List[str]]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Abaikan variabel yang tidak didefinisikan (misal VITE_FIREBASE_*)
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS dari berbagai format string di .env"""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            # Coba parse sebagai JSON array dulu
            if v.startswith("["):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return parsed
                except json.JSONDecodeError:
                    pass
            # Fallback: split by comma
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return [str(v)]


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
