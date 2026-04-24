# ============================================================
# STAGE 1: Build React Frontend
# ============================================================
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend

# Copy package files dulu (layer caching)
COPY pcb-landing-page/package*.json ./

# Install dependencies
RUN npm ci --production=false

# Copy source code
COPY pcb-landing-page/ ./

# API base URL (selalu /api di production — Nginx proxy ke same origin)
ENV VITE_API_BASE_URL=/api

# Firebase config via build args (di-pass dari docker-compose.yml)
ARG VITE_FIREBASE_API_KEY
ARG VITE_FIREBASE_AUTH_DOMAIN
ARG VITE_FIREBASE_PROJECT_ID
ARG VITE_FIREBASE_STORAGE_BUCKET
ARG VITE_FIREBASE_MESSAGING_SENDER_ID
ARG VITE_FIREBASE_APP_ID

ENV VITE_FIREBASE_API_KEY=$VITE_FIREBASE_API_KEY
ENV VITE_FIREBASE_AUTH_DOMAIN=$VITE_FIREBASE_AUTH_DOMAIN
ENV VITE_FIREBASE_PROJECT_ID=$VITE_FIREBASE_PROJECT_ID
ENV VITE_FIREBASE_STORAGE_BUCKET=$VITE_FIREBASE_STORAGE_BUCKET
ENV VITE_FIREBASE_MESSAGING_SENDER_ID=$VITE_FIREBASE_MESSAGING_SENDER_ID
ENV VITE_FIREBASE_APP_ID=$VITE_FIREBASE_APP_ID

# Build untuk production (output di /app/frontend/dist)
RUN npm run build


# ============================================================
# STAGE 2: Install Python Dependencies
# ============================================================
FROM python:3.11-slim AS backend-build

WORKDIR /app

# Install build dependencies untuk psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dan install Python dependencies
COPY requirements.txt .
RUN pip install --default-timeout=100 --no-cache-dir -r requirements.txt


# ============================================================
# STAGE 3: Production Image (Nginx + Uvicorn via Supervisor)
# ============================================================
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies: Nginx, Supervisor, libpq (untuk psycopg2)
RUN apt-get update && apt-get install -y \
    nginx \
    supervisor \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Buat user non-root untuk keamanan (Uvicorn jalan sebagai user ini)
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Copy Python packages dari stage 2
COPY --from=backend-build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-build /usr/local/bin /usr/local/bin

# Copy React build dari stage 1 ke Nginx html directory
COPY --from=frontend-build /app/frontend/dist /usr/share/nginx/html

# Hapus default Nginx config
RUN rm -f /etc/nginx/sites-enabled/default /etc/nginx/conf.d/default.conf

# Copy custom Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy Supervisor config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy backend source code
COPY app/ /app/app/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/alembic.ini

# Buat folder logs dan set ownership
RUN mkdir -p /app/logs && chown -R appuser:appgroup /app/logs

# Expose port 80 (Nginx)
EXPOSE 80

# Jalankan Supervisor (mengelola Nginx + Uvicorn)
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
