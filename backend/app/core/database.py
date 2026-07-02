from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Get database URL from settings
database_url = settings.DATABASE_URL
print(f"DATABASE_URL: {database_url}")

# Configure engine arguments based on database type
connect_args = {}

if "sqlite" in database_url:
    connect_args = {"check_same_thread": False}
    # SQLite doesn't support pool_size/max_overflow/pool_timeout
    engine_kwargs = {
        "echo": settings.DEBUG,
    }
else:
    engine_kwargs = {
        "pool_size": settings.DATABASE_POOL_SIZE,
        "max_overflow": settings.DATABASE_MAX_OVERFLOW,
        "pool_timeout": 30,
        "pool_recycle": 3600,
        "echo": settings.DEBUG,
    }

# Create database engine
engine = create_engine(
    database_url,
    connect_args=connect_args,
    **engine_kwargs
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base model class
Base = declarative_base()

# Dependency: Get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 