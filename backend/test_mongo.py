import asyncio

from app.config import get_settings
from app.db.mongodb import close_database, get_database


async def test_connection():
    print("Testing MongoDB connection...")
    try:
        settings = get_settings()
        # Print masked URI to verify it's loaded
        masked_uri = (
            settings.mongodb_uri.replace(
                settings.mongodb_uri.split("@")[0], "mongodb+srv://***:***"
            )
            if "@" in settings.mongodb_uri
            else "mongodb://localhost..."
        )
        print(f"Using URI: {masked_uri}")

        db = await get_database()
        print("Database instance retrieved.")

        # Try a simple command
        print("Pinging database...")
        # Since AsyncIOMotorDatabase doesn't have command directly accessible in the same way as PyMongo,
        # we can list collection names or check a collection.
        # But usually client.admin.command('ping') is the way.
        # Let's try listing collections as a simple read op.
        collections = await db.list_collection_names()
        print(f"Connection successful! Collections: {collections}")

    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        await close_database()


if __name__ == "__main__":
    asyncio.run(test_connection())
