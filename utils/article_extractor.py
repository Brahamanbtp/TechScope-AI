from bs4 import BeautifulSoup


def extract_article_text(html: str) -> str:
    """Extract readable article text, preferring Trafilatura when installed."""
    try:
        import trafilatura

        extracted = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            favor_precision=True,
        )
        if extracted and len(extracted.strip()) >= 100:
            return " ".join(extracted.split())
    except ImportError:
        pass

    soup = BeautifulSoup(html, "html.parser")
    container = soup.select_one(
        '[itemprop="articleBody"], [class*="article-body"], [class*="article-content"]'
    ) or soup.find("article")
    if container is None:
        article_type = soup.find("meta", attrs={"property": "og:type"})
        if article_type and article_type.get("content", "").lower() == "article":
            container = soup.find("main") or soup.find(attrs={"role": "main"})
    if container is None:
        raise ValueError("The URL does not appear to contain an article")

    for tag in container(["script", "style", "noscript", "iframe"]):
        tag.decompose()
    paragraphs = [
        paragraph.get_text(" ", strip=True)
        for paragraph in container.find_all("p")
        if paragraph.get_text(" ", strip=True)
    ]
    text = " ".join(paragraphs) if paragraphs else container.get_text(" ", strip=True)
    text = " ".join(text.split())
    if len(text) < 100:
        raise ValueError("The fetched page does not contain enough article text")
    return text