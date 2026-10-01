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
    counts = {label: {"actual": 0, "predicted": 0, "correct": 0} for label in {"higher", "mixed", "lower"}}
    score_targets = {"lower": 0.0, "mixed": 0.5, "higher": 1.0}
    squared_error = 0.0
    for row in rows:
        predicted = assess_content_quality(row["text"])["label"].split()[0].lower()
        squared_error += (assess_content_quality(row["text"])["score"] - score_targets[row["label"]]) ** 2
        counts[row["label"]]["actual"] += 1
        counts[predicted]["predicted"] += 1
        if predicted == row["label"]:
            correct += 1
            counts[row["label"]]["correct"] += 1
    per_class = {
        label: {
            "precision": round(values["correct"] / values["predicted"], 3) if values["predicted"] else 0.0,
            "recall": round(values["correct"] / values["actual"], 3) if values["actual"] else 0.0,
        }
        for label, values in counts.items()
    }
    macro_f1 = 0.0
    for label, values in per_class.items():
        precision, recall = values["precision"], values["recall"]
        macro_f1 += (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    macro_f1 /= len(per_class)
    calibration_bins = []
    for lower, upper in ((0.0, 0.33), (0.34, 0.66), (0.67, 1.0)):
        bucket = [row for row in rows if lower <= assess_content_quality(row["text"])["score"] <= upper]
        calibration_bins.append({"range": [lower, upper], "examples": len(bucket), "observed_accuracy": round(sum(assess_content_quality(row["text"])["label"].split()[0].lower() == row["label"] for row in bucket) / len(bucket), 3) if bucket else 0.0})
    return {
        "examples": len(rows),
        "accuracy": round(correct / len(rows), 3) if rows else 0.0,
        "per_class": per_class,
        "macro_f1": round(macro_f1, 3),
        "brier_score": round(squared_error / len(rows), 3) if rows else 0.0,
        "calibration_bins": calibration_bins,
        "status": "experimental",
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
