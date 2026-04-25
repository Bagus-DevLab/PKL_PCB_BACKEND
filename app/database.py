import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

logger = logging.getLogger(__name__)

logger.info(f"Connecting to database...")

# Pool parameters optimized for 2GB VPS with 2 Uvicorn workers.
# SQLite (used in tests) doesn't support QueuePool parameters,
# so only apply them for PostgreSQL.
_engine_kwargs = {"pool_pre_ping": True}

if settings.DATABASE_URL.startswith("postgresql"):
    _engine_kwargs.update({
        "pool_size": 3,         # 3 persistent connections per worker (default: 5)
        "max_overflow": 7,      # Up to 10 total per worker under burst (default: 10)
        "pool_timeout": 10,     # Fail fast if pool exhausted (default: 30)
        "pool_recycle": 1800,   # Recycle connections every 30 min
    })

engine = create_engine(settings.DATABASE_URL, **_engine_kwargs)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

logger.info("Database engine created successfully")


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        db.close()
