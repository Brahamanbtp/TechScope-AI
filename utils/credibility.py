import re
from collections import Counter
from typing import Any, Dict


QUALITY_MODEL_VERSION = "heuristic-v1"
CLICKBAIT_PHRASES = (
    "you won't believe",
    "shocking",
    "top secret",
    "exposed",
    "miracle",
    "will blow your mind",
    "never seen before",
    "what happens next",
)


def assess_content_quality(text: str) -> Dict[str, Any]:
    """Return an explainable content-quality signal, not a factuality claim."""
    normalized = (text or "").lower().strip()
    words = re.findall(r"\b\w+\b", normalized)
    word_count = len(words)
    signals = []
    score = 0.5

    if word_count >= 300:
        score += 0.2
        signals.append("Article has substantial text length")
    elif word_count >= 100:
        score += 0.1
        signals.append("Article has moderate text length")
    else:
        score -= 0.15
        signals.append("Article is very short")

    has_source_language = "according to" in normalized or "source:" in normalized
    if has_source_language:
        score += 0.15
        signals.append("Contains source-attribution language")
    else:
        signals.append("No common source-attribution language detected")

    clickbait_count = sum(phrase in normalized for phrase in CLICKBAIT_PHRASES)
    if clickbait_count:
        score -= min(clickbait_count * 0.08, 0.24)
        signals.append(f"Contains {clickbait_count} clickbait phrase(s)")

    excessive_punctuation = len(re.findall(r"[!?]{2,}", normalized))
    if excessive_punctuation:
        score -= min(excessive_punctuation * 0.04, 0.16)
        signals.append("Contains excessive punctuation")

    repeated_words = sum(
        frequency - 5
        for _, frequency in Counter(words).most_common(3)
        if frequency > 5
    )
    if repeated_words:
        score -= min(repeated_words * 0.01, 0.15)
        signals.append("Contains unusually repetitive wording")

    bounded_score = round(min(max(score, 0.0), 1.0), 2)
    if bounded_score >= 0.7:
        label = "Higher quality signals"
    elif bounded_score >= 0.4:
        label = "Mixed quality signals"
    else:
        label = "Lower quality signals"

    return {
        "score": bounded_score,
        "label": label,
        "signals": signals,
        "method": QUALITY_MODEL_VERSION,
        "reliability": "experimental",
    }


def score_credibility(text: str) -> float:
    """Compatibility wrapper; this is a content-quality heuristic, not fact checking."""
    return assess_content_quality(text)["score"]
