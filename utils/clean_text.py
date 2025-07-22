import re
from bs4 import BeautifulSoup

def clean_html(raw_html: str) -> str:
    """Remove HTML tags and scripts from the raw HTML content."""
    soup = BeautifulSoup(raw_html, "html.parser")

    # Remove script and style tags
    for tag in soup(["script", "style", "noscript", "iframe"]):
        tag.decompose()

    cleaned_text = soup.get_text(separator=" ", strip=True)
    return cleaned_text

def normalize_text(text: str) -> str:
    """Normalize whitespace, remove non-printable characters and fix unicode."""
    # Replace multiple whitespace with a single space
    text = re.sub(r"\s+", " ", text)
    # Remove control characters
    text = re.sub(r"[\x00-\x1F\x7F]", "", text)
    return text.strip()

def clean_article_text(html: str) -> str:
    """Clean and normalize raw HTML article content."""
    text = clean_html(html)
    normalized = normalize_text(text)
    return normalized
