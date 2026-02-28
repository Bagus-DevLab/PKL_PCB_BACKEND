#!/usr/bin/env python3
"""Test config loading dari .env"""

import sys
import os

# Setup path
sys.path.insert(0, '/home/bagus/pkl-pcb')
os.chdir('/home/bagus/pkl-pcb')

try:
    from app.core.config import settings
    
    print("="*60)
    print("✅ CONFIG LOADED SUCCESSFULLY!")
    print("="*60)
    print(f"ENVIRONMENT: {settings.ENVIRONMENT}")
    print(f"BASE_URL: {settings.BASE_URL}")
    print(f"TOKEN EXPIRE: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes (7 hari)")
    print(f"IS PRODUCTION: {settings.is_production}")
    print(f"CORS ORIGINS: {settings.CORS_ORIGINS}")
    print(f"MQTT BROKER: {settings.MQTT_BROKER}:{settings.MQTT_PORT}")
    print("="*60)
    print("\n✅ Semua config berhasil di-load dari .env!")
    
except Exception as e:
    print(f"❌ ERROR loading config: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
