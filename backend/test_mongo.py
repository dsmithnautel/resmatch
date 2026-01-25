"""Quick MongoDB connection test."""
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

uri = os.getenv("MONGODB_URI")
db_name = os.getenv("MONGODB_DATABASE", "resume_compile")

print(f"Testing connection to: {uri[:50]}...")
print(f"Database: {db_name}")

try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    
    # Force a connection attempt
    client.admin.command('ping')
    print("[OK] Connected successfully!")
    
    # List databases
    dbs = client.list_database_names()
    print(f"Available databases: {dbs}")
    
    # Check our database
    db = client[db_name]
    collections = db.list_collection_names()
    print(f"Collections in '{db_name}': {collections}")
    
    client.close()
    print("[OK] Connection test passed!")
    
except Exception as e:
    print(f"[FAILED] Connection failed: {e}")
