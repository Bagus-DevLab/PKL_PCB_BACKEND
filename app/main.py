from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import Base, engine, get_db
from app.routers import auth_router, user_router, device_router
from app.models import User, Device, SensorLog
from app.core.logging_config import setup_logging

# Setup logging
logger = setup_logging()

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
    Base.metadata.create_all(bind=engine)

@app.get("/", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint untuk memastikan database berjalan"""
    result = db.execute(text("SELECT 1")).scalar()
    return {"status": "healthy", "database_alive": bool(result)}

