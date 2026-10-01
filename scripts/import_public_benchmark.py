"""Import a public fact-verification dataset without conflating it with quality labels.

FEVER is Apache-2.0 code/data infrastructure and publishes Supported,
Refuted, and NotEnoughInfo factuality labels. Those labels remain in a
separate dataset because factuality is not the same as editorial quality.
"""
import argparse
import json
import os
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parents[1]


def normalize(record: dict) -> dict:
    return {
        "id": f"fever-{record.get('id', '')}",
        "claim": record.get("claim", ""),
        "label": record.get("label", ""),
        "evidence": record.get("evidence", []),
        "dataset": "FEVER",
        "task": "factuality",
        "source_url": "https://github.com/awslabs/fever",
    }


def import_dataset(url: str, output: Path, limit: int | None = None) -> int:
    response = httpx.get(url, timeout=60, follow_redirects=True)
    response.raise_for_status()
    records = []
    for line in response.text.splitlines():
        if not line.strip():
            continue
        records.append(normalize(json.loads(line)))
        if limit and len(records) >= limit:
            break
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")
    return len(records)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="Verified public JSONL URL for the benchmark")
    parser.add_argument("--output", default=str(ROOT / "data" / "public_factuality_benchmark.jsonl"))
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    print(f"imported={import_dataset(args.url, Path(args.output), args.limit)} output={args.output}")
