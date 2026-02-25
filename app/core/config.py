import os
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """
    Konfigurasi aplikasi yang diambil dari environment variables.
    Gunakan .env file untuk development.
    """
    
    # Environment
    ENVIRONMENT: str = "development"  # development / production
    
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
    MQTT_USERNAME: str = ""
    MQTT_PASSWORD: str = ""

    # Alert Thresholds (configurable via .env)
    ALERT_TEMP_MAX: float = 35.0  # Suhu maksimum (°C)
    ALERT_TEMP_MIN: float = 20.0  # Suhu minimum (°C)
    ALERT_AMMONIA_MAX: float = 20.0  # Amonia maksimum (ppm)

    POSTGRES_USER: str 
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache()
def get_settings() -> Settings:
    """
    Singleton untuk mendapatkan settings.
    Di-cache supaya tidak baca ulang .env setiap kali dipanggil.
    """
    return Settings()


# Instance global untuk kemudahan import
settings = get_settings()
