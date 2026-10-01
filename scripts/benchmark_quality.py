import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.evaluate_quality import DEFAULT_DATASET, evaluate


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
output = os.path.join(ROOT, "data", "quality_benchmark.json")
with open(output, "w", encoding="utf-8") as report:
    json.dump(evaluate(DEFAULT_DATASET), report, indent=2)
print(output)