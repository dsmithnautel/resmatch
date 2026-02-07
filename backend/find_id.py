
import asyncio
import os
import sys

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.mongodb import get_database

async def find_master_id():
    try:
        db = await get_database()
        print("Searching for Master ID for 'Xalan Dames'...")

        # Find header unit containing the name
        query = {"text": {"$regex": "Xalan Dames", "$options": "i"}}
        cursor = db.atomic_units.find(query)
        
        found_versions = set()
        async for doc in cursor:
            version = doc.get("version")
            if version and version not in found_versions:
                print(f"FOUND MATCH: {version}")
                print(f"  - Unit ID: {doc.get('id')}")
                print(f"  - Text Snippet: {doc.get('text')[:100]}...")
                found_versions.add(version)
        
        if not found_versions:
            print("No master resume found containing 'Xalan Dames'.")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(find_master_id())
