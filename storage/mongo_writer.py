from datetime import datetime

try:
    from pymongo import MongoClient
except ImportError:
    MongoClient = None


collection = None
if MongoClient is not None:
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
    collection = client.techscope.articles

def write_to_mongo(data):
    if collection is None:
        raise RuntimeError("pymongo is not installed")
    data["timestamp"] = datetime.utcnow().isoformat()
    try:
        collection.insert_one(data)
    except Exception as e:
        raise RuntimeError(f"MongoDB write failed: {e}")
