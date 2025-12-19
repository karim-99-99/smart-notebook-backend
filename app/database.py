from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Default to Docker database connection if DATABASE_URL is not set
    db_user = os.getenv("POSTGRES_USER", "kareem")
    db_password = os.getenv("POSTGRES_PASSWORD", "secret123")
    db_name = os.getenv("POSTGRES_DB", "smart_note")
    # Use "db" for Docker Compose, "localhost" for local development
    db_host = os.getenv("POSTGRES_HOST", "db")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Add connection pool settings
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True  # Verify connections before using them
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
