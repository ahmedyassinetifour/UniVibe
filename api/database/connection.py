from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://UniVibe:Un1Vibe2025@univibe.mysql.database.azure.com/univibe"
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