import re
from textblob import TextBlob
from typing import Dict, Any

# A set of phrases and words often associated with biased reporting
BIAS_CUES = {
    "loaded_phrases": [
        "obviously", "clearly", "undoubtedly", "needless to say", "without a doubt",
        "no one can deny", "there is no doubt", "as everyone knows", "it is a fact that"
    ],
    "emotion_words": [
        "disaster", "outrage", "scandal", "tragic", "heroic", "evil", "corrupt",
        "shocking", "chaotic", "miracle", "devastating", "brutal", "cowardly"
    ]
}

def clean_text(text: str) -> str:
    """Clean and normalize article text for analysis"""
    text = re.sub(r"http\S+|www.\S+", "", text)
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    return text.strip().lower()

def count_bias_cues(text: str) -> int:
    """Count the presence of known biased cues in the text"""
    cue_count = 0
    for category in BIAS_CUES.values():
        for phrase in category:
            occurrences = text.count(phrase.lower())
            cue_count += occurrences
    return cue_count

def detect_sentiment_bias(text: str) -> float:
    """Estimate article polarity using sentiment (proxy for emotional framing)"""
    blob = TextBlob(text)
    return blob.sentiment.polarity  # -1 (negative) to +1 (positive)

def calculate_bias_score(text: str) -> float:
    """Combine cues and sentiment into a simple bias score"""
    cleaned = clean_text(text)
    cue_score = count_bias_cues(cleaned)
    polarity_score = abs(detect_sentiment_bias(cleaned))
    
    # Weighted sum: cues + sentiment bias
    bias_score = (cue_score * 0.7) + (polarity_score * 10 * 0.3)
    return round(bias_score, 2)

def label_bias(score: float) -> str:
    """Return a label for the given bias score"""
    if score < 2:
        return "Low Bias"
    elif score < 4:
        return "Moderate Bias"
    else:
        return "High Bias"

def analyze_bias(text: str) -> Dict[str, Any]:
    """Main function to analyze bias in a news article"""
    if not text or len(text.strip()) < 100:
        return {"bias_score": 0.0, "bias_label": "Not enough text"}

    score = calculate_bias_score(text)
    label = label_bias(score)

    return {
        "bias_score": score,
        "bias_label": label
    }
