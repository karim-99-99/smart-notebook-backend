from fastapi import FastAPI
from app.database import Base, engine
from app.models import User, Note, Folder
from app.routers import users, auth, notes, sync, storage
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Error creating database tables: {e}")

app = FastAPI(title="Smart Notebook API", version="1.0.0")

# Include routers
app.include_router(users.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(notes.router, prefix="/api")
app.include_router(sync.router, prefix="/api")
app.include_router(storage.router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "Smart Notebook API",
        "status": "ok",
        "endpoints": {
            "docs": "/docs",
            "auth": "/api/login",
            "users": "/api/users/register",
            "notes": "/api/notes"
        }
    }
