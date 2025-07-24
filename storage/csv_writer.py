import csv
import os
from datetime import datetime

def write_to_csv(data, filename="articles.csv"):
    data["timestamp"] = datetime.utcnow().isoformat()
    file_exists = os.path.isfile(filename)
    
    try:
        with open(filename, mode="a", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)
    except Exception as e:
        raise RuntimeError(f"Error writing to CSV: {e}")
