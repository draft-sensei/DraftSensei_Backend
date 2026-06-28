"""
Database configuration and session management for Neon PostgreSQL
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
import logging

logger = logging.getLogger(__name__)

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set. Check your .env file.")

# Create engine with connection pooling for Neon
# NullPool is used because Neon has built-in connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,
    echo=os.getenv("DEBUG", "false").lower() == "true",  # Log SQL in debug mode
    connect_args={
        "connect_timeout": 10,
        "keepalives": 1,
        "keepalives_idle": 30,
    },
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency function for FastAPI to get database session.
    Used in route handlers: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection() -> bool:
    """
    Test database connection.
    Returns True if connection successful, False otherwise.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("✓ Database connection successful")
            return True
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False


def init_db():
    """
    Initialize database by creating all tables.
    Should be called on application startup.
    """
    try:
        # Import models to register them with Base
        from app.db.models import Hero, MatchHistory, PlayerPreference

        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database tables created/verified")

        return True
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        return False


def drop_all_tables():
    """
    Drop all tables. USE WITH CAUTION - development only.
    """
    try:
        from app.db.models import Hero, MatchHistory, PlayerPreference

        logger.warning("⚠️  Dropping all database tables...")
        Base.metadata.drop_all(bind=engine)
        logger.warning("✓ All tables dropped")

        return True
    except Exception as e:
        logger.error(f"✗ Failed to drop tables: {e}")
        return False
