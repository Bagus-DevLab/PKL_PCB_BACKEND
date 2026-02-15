import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Konfigurasi aplikasi yang diambil dari environment variables.
    Gunakan .env file untuk development.
    """
    
    # Database
    DATABASE_URL: str
    
    # JWT Authentication
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    BASE_URL: str = "http://localhost:8000"
    
    # MQTT
    MQTT_BROKER: str = "mosquitto"
    MQTT_PORT: int = 1883
    MQTT_TOPIC: str = "devices/+/data"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Singleton untuk mendapatkan settings.
    Di-cache supaya tidak baca ulang .env setiap kali dipanggil.
    """
    return Settings()


# Instance global untuk kemudahan import
settings = get_settings()
