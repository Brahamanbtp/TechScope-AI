import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from storage.review_repo import list_reviews


reviews = defaultdict(list)
for review in list_reviews():
    reviews[review["article_id"]].append(review["label"])

items = [labels for labels in reviews.values() if len(labels) >= 2]
unanimous = sum(len(set(labels)) == 1 for labels in items)
print(json.dumps({
    "articles_with_multiple_reviews": len(items),
    "unanimous_articles": unanimous,
    "agreement_rate": round(unanimous / len(items), 3) if items else 0.0,
    "status": "needs-more-reviews" if not items else "measured",
}, indent=2))
