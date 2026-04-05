from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.database import Base, engine
from app.models import User, Note, Folder
from app.routers import users, auth, notes, sync, storage, stats
import logging
import traceback

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers must be registered BEFORE middleware so they are wired
# into ServerErrorMiddleware when build_middleware_stack() fires on the first request.

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return JSON with details on request body / query validation failures (422)."""
    logger.warning("Validation error on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=422,
        content={"error": "Validation Error", "detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all: returns JSON with full traceback instead of Starlette's text/plain."""
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    logger.error("Unhandled exception on %s %s:\n%s", request.method, request.url.path, tb)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": str(exc), "traceback": tb},
    )


# Middleware: log every request and catch any exception so we return JSON (with traceback)
# instead of Starlette's default text/plain 500 (which was bypassing our exception handler).
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("Request: %s %s", request.method, request.url.path)
    try:
        response = await call_next(request)
        logger.info("Response: %s %s → %s", request.method, request.url.path, response.status_code)
        return response
    except Exception as exc:
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        logger.error("Unhandled exception on %s %s:\n%s", request.method, request.url.path, tb)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error", "detail": str(exc), "traceback": tb},
        )


# Include routers
app.include_router(users.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(notes.router, prefix="/api")
app.include_router(sync.router, prefix="/api")
app.include_router(storage.router, prefix="/api")
app.include_router(stats.router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "Smart Notebook API",
        "status": "ok",
        "endpoints": {
            "docs": "/docs",
            "auth": "/api/login",
            "users": "/api/register",
            "notes": "/api/notes",
        },
    }


# Force Starlette to use our JSON 500 handler: wrap the app in ServerErrorMiddleware
# with our handler so any uncaught exception returns JSON (with traceback) instead of text/plain.
from starlette.middleware.errors import ServerErrorMiddleware

app = ServerErrorMiddleware(app, handler=global_exception_handler)
