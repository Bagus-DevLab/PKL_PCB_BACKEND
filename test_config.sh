#!/bin/bash
cd /home/bagus/pkl-pcb
python3 -c "from app.core.config import settings
print('✅ Config loaded successfully!')
print(f'BASE_URL: {settings.BASE_URL}')
print(f'ENVIRONMENT: {settings.ENVIRONMENT}')
print(f'TOKEN EXPIRE: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes')
print(f'CORS: {settings.CORS_ORIGINS}')
print(f'Is Production: {settings.is_production}')
"
