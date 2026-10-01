import re


def extract_claims(text: str, evidence: list[dict]) -> list[dict]:
    evidence_by_text = {item["text"]: item for item in evidence}
    claims = []
    for sentence in (part.strip() for part in re.split(r"(?<=[.!?])\s+", text or "")):
        words = sentence.split()
        if len(words) < 8 or len(words) > 80:
            continue
        if not re.search(r"\b(is|are|was|were|will|can|may|shows|reports|increases|reduces|launched|announced)\b", sentence, re.IGNORECASE):
            continue
        claims.append({
            "text": sentence,
            "type": "candidate",
            "evidence": [evidence_by_text[sentence]] if sentence in evidence_by_text else [],
        })
    return claims[:30]
