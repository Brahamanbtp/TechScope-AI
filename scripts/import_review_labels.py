import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from storage.review_repo import submit_review


parser = argparse.ArgumentParser(description="Import independent quality labels")
parser.add_argument("input", help="JSONL review batch")
parser.add_argument("--reviewer-id", type=int, required=True)
args = parser.parse_args()

valid = {"lower", "mixed", "higher"}
count = 0
with open(args.input, encoding="utf-8") as file:
    for line in file:
        row = json.loads(line)
        if row.get("label") not in valid:
            raise ValueError(f"Invalid label for article {row.get('article_id')}: {row.get('label')}")
        submit_review(row["article_id"], args.reviewer_id, row["label"], row.get("notes", ""))
        count += 1
print(f"imported={count} reviewer_id={args.reviewer_id}")
