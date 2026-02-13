from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session
from app.database import get_db
from sqlalchemy import text

app = FastAPI()

@app.get("/")
def health_check(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1")).scalar()
    return {"database_alive": bool(result)}
