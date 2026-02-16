import logging
from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import Base, engine, get_db
from app.routers import auth_router, user_router, device_router
from app.models import User, Device, SensorLog
from app.core.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PKL PCB API",
    description="API untuk monitoring kandang ayam berbasis IoT",
    version="1.0.0"
)

# Include Routers
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(device_router)
    
@app.on_event("startup")
def on_startup():
    """Create database tables on startup"""
    logger.info("=" * 50)
    logger.info("PKL PCB IoT Backend Starting...")
    logger.info("=" * 50)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    logger.info(f"API Docs available at: /docs")
    logger.info("Server ready to accept connections")

@app.on_event("shutdown")
def on_shutdown():
    """Cleanup on shutdown"""
    logger.info("Server shutting down...")

@app.get("/", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint untuk memastikan database berjalan"""
    try:
        result = db.execute(text("SELECT 1")).scalar()
        logger.debug("Health check: Database OK")
        return {"status": "healthy", "database_alive": bool(result)}
    except Exception as e:
        logger.error(f"Health check GAGAL - Database error: {str(e)}")
        return {"status": "unhealthy", "database_alive": False, "error": str(e)}

