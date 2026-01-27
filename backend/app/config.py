"""Configuration settings for the ResMatch backend."""

import json
import os
import sys
from functools import lru_cache

from pydantic_settings import BaseSettings


def parse_cors_origins() -> list[str]:
    """Parse CORS_ORIGINS from environment, handling various formats."""
    default = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://restailor.vercel.app",
        "https://www.resmatch.app",
        "https://resmatch.app",
    ]

    raw = os.environ.get("CORS_ORIGINS", "")
    if not raw:
        return default

    # Try JSON array first
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass

    # Try comma-separated
    if "," in raw:
        return [origin.strip() for origin in raw.split(",")]

    # Single origin
    return [raw.strip()]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    gemini_api_key: str = ""
    elevenlabs_api_key: str = ""  # Stretch goal

    # MongoDB Atlas
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "resume_compile"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Environment
    environment: str = "development"  # development, staging, production

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "https://restailor.vercel.app"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


def validate_settings(settings: Settings) -> list[str]:
    """Validate that required settings are configured. Returns list of warnings."""
    warnings = []
    errors = []

    # Check Gemini API key (required for core functionality)
    if not settings.gemini_api_key:
        errors.append(
            "GEMINI_API_KEY is not set. Get one at https://aistudio.google.com/app/apikey"
        )

    # Check MongoDB URI (warn if using localhost in production)
    if settings.environment == "production":
        if "localhost" in settings.mongodb_uri or "127.0.0.1" in settings.mongodb_uri:
            warnings.append(
                "MONGODB_URI points to localhost in production. "
                "Use MongoDB Atlas: https://cloud.mongodb.com"
            )

    # Print warnings
    for warning in warnings:
        print(f"⚠️  WARNING: {warning}")

    # Exit on errors in production
    if errors:
        for error in errors:
            print(f"❌ ERROR: {error}")
        if settings.environment == "production":
            print("\n💡 Set these in your environment or .env file")
            sys.exit(1)
        else:
            print("\n💡 Running in development mode - some features may not work")

    return warnings


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance with validation."""
    settings = Settings()
    validate_settings(settings)
    return settings


# Parse CORS origins separately to handle various formats
cors_origins = parse_cors_origins()
