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
from app.models import User, Device, SensorLog
from app.core.logging_config import setup_logging
from app.core.config import settings
from app.core.request_context import request_id_var, generate_request_id, get_request_id

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown events"""
    # Startup
    logger.info("=" * 50)
    logger.info("PKL PCB IoT Backend Starting...")
    logger.info("=" * 50)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    logger.info(f"API Docs available at: /docs")
    logger.info(f"Environment: {'PRODUCTION' if settings.ENVIRONMENT == 'production' else 'DEVELOPMENT'}")
    logger.info("Server ready to accept connections")
    
    yield  # Server berjalan
    
    # Shutdown
    logger.info("Server shutting down...")

app = FastAPI(
    title="PKL PCB API",
    description="API untuk monitoring kandang ayam berbasis IoT",
    version="1.0.0",
    lifespan=lifespan
)

# Rate Limiter State
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Global Exception Handler ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Tangkap semua unhandled exception agar detail internal tidak bocor ke client"""
    logger.error(f"Unhandled error pada {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Terjadi kesalahan internal. Silakan coba lagi."}
    )

# --- MIDDLEWARE: Request ID ---
class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware yang generate request_id unik untuk setiap request.
    Request ID ditambahkan ke response header 'X-Request-ID' juga.
    """
    async def dispatch(self, request: Request, call_next):
        # Generate ID unik untuk request ini
        rid = generate_request_id()
        # Simpan ke contextvars (bisa diakses dari mana saja)
        request_id_var.set(rid)
        
        logger.info(f"{request.method} {request.url.path}")
        
        response = await call_next(request)
        
        # Tambahkan ke response header (berguna untuk debugging frontend)
        response.headers["X-Request-ID"] = rid
        
        logger.info(f"{request.method} {request.url.path} -> {response.status_code}")
        return response

app.add_middleware(RequestIdMiddleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
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

