"""MongoDB Atlas connection and database operations."""

import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.config import get_settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def get_database() -> AsyncIOMotorDatabase:
    """Get the MongoDB database instance."""
    global _client, _db

    if _db is None:
        settings = get_settings()
        mongodb_uri = settings.mongodb_uri

        if "tlsAllowInvalidCertificates" not in mongodb_uri:
            separator = "&" if "?" in mongodb_uri else "?"
            mongodb_uri = f"{mongodb_uri}{separator}tlsAllowInvalidCertificates=true"

        try:
            _client = AsyncIOMotorClient(
                mongodb_uri,
                tlsAllowInvalidCertificates=True,
                serverSelectionTimeoutMS=5000,
            )
            _db = _client[settings.mongodb_database]
            await _ensure_indexes(_db)
        except ServerSelectionTimeoutError as e:
            logger.error("MongoDB server selection timed out: %s", e)
            _client = None
            _db = None
            raise RuntimeError("Could not connect to MongoDB: server selection timed out") from e
        except ConnectionFailure as e:
            logger.error("MongoDB connection failed: %s", e)
            _client = None
            _db = None
            raise RuntimeError("Could not connect to MongoDB: connection failed") from e

    return _db


async def _ensure_indexes(db: AsyncIOMotorDatabase):
    """Create necessary indexes for performance."""
    # Atomic units - query by version
    await db.atomic_units.create_index("version")
    await db.atomic_units.create_index([("version", 1), ("id", 1)], unique=True)
    await db.atomic_units.create_index("section")

    # Master versions - query by ID
    await db.master_versions.create_index("master_version_id", unique=True)
    await db.master_versions.create_index("created_at")

    # Parsed JDs
    await db.parsed_jds.create_index("jd_id", unique=True)
    await db.parsed_jds.create_index("created_at")

    # Compiles
    await db.compiles.create_index("compile_id", unique=True)
    await db.compiles.create_index("created_at")


async def close_database():
    """Close the database connection."""
    global _client, _db

    if _client is not None:
        _client.close()
        _client = None
        _db = None
