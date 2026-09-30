import json
import os
from typing import Dict, Iterable

from utils.credibility import assess_content_quality


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DATASET = os.path.join(PROJECT_ROOT, "data", "quality_evaluation.jsonl")


def load_dataset(path: str = DEFAULT_DATASET) -> Iterable[Dict]:
    with open(path, encoding="utf-8") as dataset:
        for line in dataset:
            if line.strip():
                yield json.loads(line)


def evaluate(path: str = DEFAULT_DATASET) -> Dict[str, float]:
    rows = list(load_dataset(path))
    correct = 0
    for row in rows:
        predicted = assess_content_quality(row["text"])["label"].split()[0].lower()
        if predicted == row["label"]:
            correct += 1
    return {
        "examples": len(rows),
        "accuracy": round(correct / len(rows), 3) if rows else 0.0,
        "status": "experimental",
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
