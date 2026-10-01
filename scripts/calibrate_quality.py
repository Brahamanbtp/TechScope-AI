import json
import os
from collections import defaultdict

from storage.review_repo import list_reviews
from utils.credibility import assess_content_quality
from utils.save_data import load_articles


def calibrate() -> dict:
    articles = {article["id"]: article for article in load_articles(limit=100_000)}
    reviews = list_reviews()
    grouped = defaultdict(list)
    for review in reviews:
        if review["article_id"] in articles:
            grouped[review["article_id"]].append(review["label"])
    rows = []
    for article_id, labels in grouped.items():
        if len(set(labels)) != 1:
            continue
        assessment = assess_content_quality(articles[article_id].get("content", ""))
        rows.append({"article_id": article_id, "label": labels[0], "score": assessment["score"]})
    return {"reviewed_articles": len(rows), "calibration_rows": rows, "status": "human-reviewed" if rows else "needs-production-reviews"}


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output = os.path.join(root, "data", "quality_calibration.json")
    with open(output, "w", encoding="utf-8") as report:
        json.dump(calibrate(), report, indent=2)
    print(output)