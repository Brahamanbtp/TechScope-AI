import re
import logging
from typing import List
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

try:
    from keybert import KeyBERT
    from rake_nltk import Rake
except ImportError:
    KeyBERT = None
    Rake = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("keywords")

# === MODEL SETUP ===
kw_model = None


def _get_keybert_model():
    global kw_model
    if kw_model is None and KeyBERT is not None:
        try:
            kw_model = KeyBERT(model="all-MiniLM-L6-v2")
        except Exception as e:
            logger.warning(f"KeyBERT model load failed: {e}")
    return kw_model

def clean_for_keywords(text: str) -> str:
    """Preprocess text for keyword extraction"""
    text = re.sub(r"http\S+|www.\S+", "", text)  # remove URLs
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)   # remove punctuation
    text = re.sub(r"\s+", " ", text)             # normalize spaces
    return text.strip().lower()

def extract_with_keybert(text: str, top_n: int = 10) -> List[str]:
    """Extract keywords using KeyBERT"""
    model = _get_keybert_model()
    if not model:
        return []
    try:
        keywords = model.extract_keywords(text, top_n=top_n, stop_words="english")
        return [kw[0] for kw in keywords]
    except Exception as e:
        logger.warning(f"KeyBERT extraction failed: {e}")
        return []

def extract_with_rake(text: str, top_n: int = 10) -> List[str]:
    """Fallback method using RAKE"""
    try:
        if Rake is None:
            return []
        rake = Rake()
        rake.extract_keywords_from_text(text)
        return rake.get_ranked_phrases()[:top_n]
    except Exception as e:
        logger.warning(f"RAKE extraction failed: {e}")
        return []

def post_process_keywords(keywords: List[str]) -> List[str]:
    """Remove duplicates, stopwords, short phrases"""
    cleaned = set()
    for kw in keywords:
        if len(kw) < 3:
            continue
        terms = [word for word in kw.split() if word not in ENGLISH_STOP_WORDS]
        if terms:
            cleaned.add(" ".join(terms))
    return sorted(cleaned, key=lambda k: (-len(k), k))[:10]

def extract_keywords(text: str, top_n: int = 10) -> List[str]:
    """Main keyword extraction function with fallback"""
    if not text or len(text) < 100:
        return []

    cleaned_text = clean_for_keywords(text)

    keywords = extract_with_keybert(cleaned_text, top_n)
    if not keywords:
        keywords = extract_with_rake(cleaned_text, top_n)

    if not keywords:
        words = [word for word in cleaned_text.split() if word not in ENGLISH_STOP_WORDS]
        frequencies = {}
        for word in words:
            frequencies[word] = frequencies.get(word, 0) + 1
        keywords = [word for word, _ in sorted(frequencies.items(), key=lambda item: (-item[1], item[0]))[:top_n]]

    return post_process_keywords(keywords)
