from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.routers import auth
from app.routers import user as user_router
from app.database import  Base, engine, get_db
from app.models import user as user_model  # import semua model supaya ter-register
from app.models import device as device_model  # import semua model supaya ter-register
from app.routers import device as device_router

app = FastAPI()
app.include_router(auth.router)
app.include_router(user_router.router)
app.include_router(device_router.router)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def health_check(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1")).scalar()
    return {"database_alive": bool(result)}
