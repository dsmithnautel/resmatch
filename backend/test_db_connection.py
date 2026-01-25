"""Test MongoDB connection."""

import asyncio

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings


async def test_connection():
    """Test MongoDB Atlas connection."""
    settings = get_settings()

    print("Testing MongoDB connection...")
    print(f"Database: {settings.mongodb_database}")

    # Check if password is placeholder
    if "<db_password>" in settings.mongodb_uri:
        print("❌ ERROR: MongoDB URI contains placeholder '<db_password>'")
        print("Please update your .env file with the actual MongoDB password")
        return False

    # Mask password for display
    uri_display = settings.mongodb_uri
    if "@" in uri_display:
        parts = uri_display.split("@")
        if ":" in parts[0]:
            user_pass = parts[0].split("://")[-1]
            user = user_pass.split(":")[0]
            uri_display = uri_display.replace(user_pass, f"{user}:****")

    print(f"URI: {uri_display}")

    try:
        # Add SSL bypass parameters
        mongodb_uri = settings.mongodb_uri
        if "tlsAllowInvalidCertificates" not in mongodb_uri:
            separator = "&" if "?" in mongodb_uri else "?"
            mongodb_uri = f"{mongodb_uri}{separator}tlsAllowInvalidCertificates=true"

        client = AsyncIOMotorClient(
            mongodb_uri, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=5000
        )

        # Test connection
        print("\nAttempting to connect...")
        await client.admin.command("ping")
        print("✅ Successfully connected to MongoDB!")

        # Test database access
        db = client[settings.mongodb_database]
        collections = await db.list_collection_names()
        print(f"✅ Database '{settings.mongodb_database}' accessible")
        print(f"Collections: {collections if collections else 'No collections yet'}")

        client.close()
        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nPossible issues:")
        print("1. MongoDB password is incorrect")
        print("2. IP address not whitelisted in MongoDB Atlas")
        print("3. Database user doesn't have proper permissions")
        return False


if __name__ == "__main__":
    asyncio.run(test_connection())
