from textblob import TextBlob
from typing import Dict, Any

def analyze_sentiment(text: str) -> Dict[str, Any]:
    """
    Analyze sentiment of the given text using TextBlob.
    
    Returns:
        {
            'sentiment_score': float (0–10 scale),
            'sentiment_label': str (Negative, Neutral, Positive)
        }
    """
    if not text or len(text.strip()) < 50:
        return {
            "sentiment_score": 0.0,
            "sentiment_label": "Not enough text"
        }

    blob = TextBlob(text)
    polarity = blob.sentiment.polarity  # Range: -1.0 to 1.0

    # Normalize polarity (-1 to 1) → (0 to 10)
    sentiment_score = round((polarity + 1) * 5, 2)

    # Label
    if polarity < -0.2:
        label = "Negative"
    elif polarity > 0.2:
        label = "Positive"
    else:
        label = "Neutral"

    return {
        "sentiment_score": sentiment_score,
        "sentiment_label": label
    }
