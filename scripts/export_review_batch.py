import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.save_data import load_articles


parser = argparse.ArgumentParser(description="Export anonymized article review batches")
parser.add_argument("--output", default="data/review_batch.jsonl")
parser.add_argument("--limit", type=int, default=100)
args = parser.parse_args()

articles = load_articles(limit=args.limit)
output = Path(args.output)
output.parent.mkdir(parents=True, exist_ok=True)
with output.open("w", encoding="utf-8") as file:
    for article in articles:
        file.write(json.dumps({
            "article_id": article["id"],
            "title": article.get("title", ""),
            "source": article.get("source", ""),
            "content": article.get("content", ""),
            "label": None,
            "notes": "",
        }) + "\n")
print(f"exported={len(articles)} output={output}")
