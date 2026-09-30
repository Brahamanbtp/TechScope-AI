import os
import logging

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import openai
except ImportError:
    openai = None

# === CONFIGURATION ===
USE_OPENAI = os.getenv("USE_OPENAI", "true").lower() == "true"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# === SETUP LOGGER ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("summarizer")

# === SETUP MODELS ===
_hf_summarizer = None


def _get_hf_summarizer():
    global _hf_summarizer
    if _hf_summarizer is None:
        from transformers import pipeline

        logger.info("Loading Hugging Face summarization model...")
        _hf_summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    return _hf_summarizer


def _extractive_summary(text: str, max_sentences: int = 3) -> str:
    sentences = [sentence.strip() for sentence in text.replace("\n", " ").split(".")]
    sentences = [sentence for sentence in sentences if sentence]
    return ". ".join(sentences[:max_sentences]) + ("." if sentences else "")

def summarize_with_openai(text: str, max_tokens: int = 300) -> str:
    """Summarize using OpenAI API"""
    try:
        if openai is None:
            raise RuntimeError("The optional openai package is not installed")
        if len(text.split()) > 3000:
            text = " ".join(text.split()[:3000])  # Truncate if too long
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a concise news summarizer."},
                {"role": "user", "content": f"Summarize the following news article:\n\n{text}"}
            ],
            max_tokens=max_tokens,
            temperature=0.5
        )
        summary = response["choices"][0]["message"]["content"].strip()
        return summary
    except Exception as e:
        logger.warning(f"OpenAI summarization failed: {e}")
        return "OpenAI summarization failed."

def summarize_with_hf(text: str) -> str:
    """Summarize using Hugging Face model"""
    try:
        if len(text.split()) > 1024:
            text = " ".join(text.split()[:1024])  # BART input limit
        summary = _get_hf_summarizer()(text, max_length=130, min_length=30, do_sample=False)
        return summary[0]["summary_text"]
    except Exception as e:
        logger.warning(f"HuggingFace summarization failed: {e}")
        return _extractive_summary(text)

def summarize_article(text: str) -> str:
    """Main summarization entry point with fallback"""
    if not text or len(text.strip()) < 100:
        return "Article too short to summarize."

    if USE_OPENAI and OPENAI_API_KEY and openai is not None:
        summary = summarize_with_openai(text)
        if "failed" in summary.lower():
            summary = summarize_with_hf(text)
    else:
        summary = summarize_with_hf(text)

    return summary
