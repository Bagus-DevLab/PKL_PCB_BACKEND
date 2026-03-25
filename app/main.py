import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from app.database import Base, engine, get_db
from app.routers import auth_router, user_router, device_router
from app.core.logging_config import setup_logging
from app.core.config import settings
from app.core.request_context import request_id_var, generate_request_id

# ==========================================
# 1. SETUP LOGGING & RATE LIMITER
# ==========================================
setup_logging()
logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

# ==========================================
# 2. LIFESPAN (STARTUP & SHUTDOWN)
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown events"""
    logger.info("=" * 50)
    logger.info("PKL PCB IoT Backend Starting...")
    logger.info("=" * 50)
    
    # Verifikasi Database
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    
    # Cek Environment & Logging Docs
    if settings.ENVIRONMENT == "production":
        logger.info("Environment: PRODUCTION (API Docs DISABLED)")
    else:
        logger.info("Environment: DEVELOPMENT")
        logger.info("API Docs available at: /docs")
        
    logger.info("Server ready to accept connections")
    
    yield  # Server berjalan
    
    logger.info("Server shutting down...")

# ==========================================
# 3. APP INITIALIZATION
# ==========================================
app = FastAPI(
    title="PKL PCB API",
    description="API untuk monitoring kandang ayam berbasis IoT",
    version="1.0.0",
    lifespan=lifespan,
    # Keamanan: Matikan URL dokumentasi jika di Production
    docs_url=None if settings.ENVIRONMENT == "production" else "/docs",
    redoc_url=None if settings.ENVIRONMENT == "production" else "/redoc",
    openapi_url=None if settings.ENVIRONMENT == "production" else "/openapi.json"
)

# ==========================================
# 4. EXCEPTION HANDLERS
# ==========================================
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Tangkap semua unhandled exception agar detail internal tidak bocor ke client"""
    logger.error(f"Unhandled error pada {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Terjadi kesalahan internal. Silakan coba lagi."}
    )

# ==========================================
# 5. MIDDLEWARE
# ==========================================
class RequestIdMiddleware(BaseHTTPMiddleware):
    """Generate request_id unik untuk tracing setiap request."""
    async def dispatch(self, request: Request, call_next):
        rid = generate_request_id()
        request_id_var.set(rid)
        
        logger.info(f"{request.method} {request.url.path}")
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        logger.info(f"{request.method} {request.url.path} -> {response.status_code}")
        
        return response

# Catatan: FastAPI/Starlette mengeksekusi middleware dari yang paling terakhir ditambahkan.
# Kita tambahkan Request ID lebih dulu...
app.add_middleware(RequestIdMiddleware)

# ...lalu CORS ditambahkan terakhir, agar dieksekusi PERTAMA KALI saat request masuk.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 6. ROUTERS & ENDPOINTS
# ==========================================
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(device_router)

@app.get("/", tags=["Health"])
@limiter.limit("60/minute")
def health_check(request: Request, db: Session = Depends(get_db)):
    """Health check endpoint untuk memastikan database berjalan"""
    try:
        result = db.execute(text("SELECT 1")).scalar()
        logger.debug("Health check: Database OK")
        return {"status": "healthy", "database_alive": bool(result)}
    except Exception as e:
        logger.error(f"Health check GAGAL - Database error: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "database_alive": False}
        )