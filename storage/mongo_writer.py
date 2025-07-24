from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/")
db = client.techscope
collection = db.articles

def write_to_mongo(data):
    data["timestamp"] = datetime.utcnow().isoformat()
    try:
        collection.insert_one(data)
    except Exception as e:
        raise RuntimeError(f"MongoDB write failed: {e}")
