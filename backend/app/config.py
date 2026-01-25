"""Configuration settings for the Resume.compile() backend."""

import json
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


def parse_cors_origins() -> list[str]:
    """Parse CORS_ORIGINS from environment, handling various formats."""
    default = ["http://localhost:3000", "https://restailor.vercel.app"]
    
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
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Parse CORS origins separately to handle various formats
cors_origins = parse_cors_origins()
