"""
Database connection and session management
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv
from .models import Base

# Load environment variables
load_dotenv()

# Database URL from environment variable or default for local development
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/draftsensei"
)

# Handle Render/Railway PostgreSQL URL format
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=os.getenv("DEBUG", "false").lower() == "true"
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """
    Create all database tables
    """
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """
    Drop all database tables (use with caution!)
    """
    Base.metadata.drop_all(bind=engine)

def reset_database():
    """
    Reset database by dropping and recreating tables
    """
    drop_tables()
    create_tables()

# Initialize database tables on import
def init_db():
    """
    Initialize database with tables and basic data
    """
    create_tables()
    
    # Check if we need to seed initial data
    db = SessionLocal()
    try:
        from .models import Hero
        hero_count = db.query(Hero).count()
        if hero_count == 0:
            print("Database is empty, consider running the patch updater to populate heroes")
    except Exception as e:
        print(f"Could not check initial data: {e}")
    finally:
        db.close()

# Database connection test
def test_connection():
    """
    Test database connection
    """
    try:
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False