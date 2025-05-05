from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
import os  


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL")  # 'DBLINK' should match your App Service setting

if not SQLALCHEMY_DATABASE_URL:
    logger.error("Environment variable DATABASE_URL is not set!")
    raise ValueError("DATABASE_URL environment variable is required but not found.")

try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    logger.info("Database connection successful")
except Exception as e:
    logger.error(f"Database connection error: {e}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
