"""FastAPI application entry point for ResMatch."""

import logging
import re
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from starlette.responses import JSONResponse

from app.config import cors_origins, get_settings
from app.db.mongodb import close_database
from app.routers import job, master, resume

logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_database()


app = FastAPI(
    title="ResMatch API",
    description="Truth-first resume tailoring engine - compiles verified experience into job-targeted resumes",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = "; ".join(
        f"{'.'.join(str(loc) for loc in e['loc'])}: {e['msg']}" for e in exc.errors()
    )
    return JSONResponse(
        status_code=422,
        content={"error": "validation_error", "detail": details},
    )


@app.exception_handler(ServerSelectionTimeoutError)
async def mongo_timeout_handler(request: Request, exc: ServerSelectionTimeoutError):
    logger.error("MongoDB server selection timeout: %s", exc)
    return JSONResponse(
        status_code=503,
        content={"error": "db_unavailable", "detail": "Database is temporarily unavailable."},
    )


@app.exception_handler(ConnectionFailure)
async def mongo_connection_handler(request: Request, exc: ConnectionFailure):
    logger.error("MongoDB connection failure: %s", exc)
    return JSONResponse(
        status_code=503,
        content={"error": "db_unavailable", "detail": "Database is temporarily unavailable."},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    if re.search(r"rate limit", str(exc), re.IGNORECASE):
        return JSONResponse(
            status_code=429,
            content={"error": "rate_limit", "detail": str(exc), "retry_after": 60},
        )
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "detail": "An unexpected error occurred. Please try again.",
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "detail": "An unexpected error occurred. Please try again.",
        },
    )


print(f"CORS origins configured: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(master.router, prefix="/master", tags=["Master Resume"])
app.include_router(job.router, prefix="/job", tags=["Job Description"])
app.include_router(resume.router, prefix="/resume", tags=["Resume Compilation"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"service": "ResMatch API", "status": "healthy", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",  # TODO: Add actual DB check
        "gemini": "configured" if settings.gemini_api_key else "not configured",
    }
