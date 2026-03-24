from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Use PostgreSQL if POSTGRES_HOST is set (e.g. "db" for Docker)
    db_host = os.getenv("POSTGRES_HOST")
    if db_host:
        db_user = os.getenv("POSTGRES_USER", "kareem")
        db_password = os.getenv("POSTGRES_PASSWORD", "secret123")
        db_name = os.getenv("POSTGRES_DB", "smart_note")
        db_port = os.getenv("POSTGRES_PORT", "5432")
        DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    else:
        # Default: SQLite so backend runs without installing PostgreSQL
        _backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        _db_path = os.path.join(_backend_root, "smart_notebook.db")
        DATABASE_URL = f"sqlite:///{_db_path}"

# SQLite needs check_same_thread=False; PostgreSQL uses pool_pre_ping
kwargs = {"pool_pre_ping": True} if DATABASE_URL.startswith("postgresql") else {"connect_args": {"check_same_thread": False}}
engine = create_engine(DATABASE_URL, **kwargs)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
