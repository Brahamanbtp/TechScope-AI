import re


def extract_evidence(text: str) -> list[dict]:
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text or "") if part.strip()]
    evidence = []
    for sentence in sentences:
        urls = re.findall(r"https?://[^\s)]+", sentence)
        attribution = re.search(r"\b(according to|reported by|source:|citing)\b", sentence, re.IGNORECASE)
        if urls or attribution:
            evidence.append({"text": sentence, "urls": urls, "type": "attribution" if attribution else "link"})
    return evidence[:20]