from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, session
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://user:password@localhost/dbname")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

sessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False, 
    bind=engine
)

base = declarative_base()

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()