import json
from datetime import datetime

def write_to_json(data, filename="articles.json"):
    data["timestamp"] = datetime.utcnow().isoformat()
    try:
        with open(filename, "a", encoding="utf-8") as f:
            json.dump(data, f)
            f.write("\n")
    except Exception as e:
        raise RuntimeError(f"Error writing to JSON: {e}")
