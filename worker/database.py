from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from sqlalchemy import text
from config import Config
from utils.logging_config import setup_logging

logger = setup_logging(__name__)

# Create engine with QueuePool for better concurrent access
engine = create_engine(
    Config.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=Config.DB_POOL_SIZE,  # Number of connections to maintain
    max_overflow=Config.DB_MAX_OVERFLOW,  # Additional connections that can be created
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=Config.DB_POOL_RECYCLE,  # Recycle connections after configured time
    echo=False  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    try: 
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

def test_connection():
    """Test database connection"""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False 