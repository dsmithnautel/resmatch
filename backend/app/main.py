"""FastAPI application entry point for ResMatch."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import cors_origins, get_settings
from app.routers import job, master, resume

settings = get_settings()

app = FastAPI(
    title="ResMatch API",
    description="Truth-first resume tailoring engine - compiles verified experience into job-targeted resumes",
    version="1.0.0",
)

# CORS middleware for frontend
print(f"CORS origins configured: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
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
