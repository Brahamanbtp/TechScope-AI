import re
import string
from collections import Counter

def score_credibility(text: str) -> float:
    """
    Heuristic-based credibility scoring of an article.
    Returns a score between 0 (low credibility) and 1 (high credibility).
    """

    # Lowercase and remove extra whitespace
    text = text.lower().strip()

    # 1. Check for clickbait phrases
    clickbait_phrases = [
        "you won't believe", "shocking", "top secret", "exposed", "miracle",
        "will blow your mind", "never seen before", "what happens next"
    ]
    clickbait_score = sum(phrase in text for phrase in clickbait_phrases)

    # 2. Count excessive punctuation (e.g., multiple exclamations)
    exclamations = text.count("!") + text.count("!!!")
    excessive_punct = len(re.findall(r"[!?]{2,}", text))

    # 3. Analyze word repetition (spammy feel)
    words = re.findall(r'\w+', text)
    word_freq = Counter(words)
    top_repeated = word_freq.most_common(3)
    repetition_score = sum(freq for word, freq in top_repeated if freq > 5)

    # 4. Presence of sources or citations
    has_source = "according to" in text or "source:" in text

    # 5. Article length check
    length_score = min(len(words) / 300, 1.0)  # Normalized score (ideal length ≥ 300 words)

    # --- Final credibility calculation ---
    raw_score = (
        length_score * 0.4 +
        int(has_source) * 0.2 +
        (1 / (1 + clickbait_score + exclamations + excessive_punct + repetition_score)) * 0.4
    )

    # Clamp score to [0, 1]
    return round(min(max(raw_score, 0.0), 1.0), 2)
