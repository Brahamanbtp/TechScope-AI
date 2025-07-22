import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import logging
import time

# --------------------------
# Configuration
# --------------------------
BASE_URL = "https://arstechnica.com/"
ROBOTS_URL = urljoin(BASE_URL, "robots.txt")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; TechScopeBot/1.0; +https://github.com/Brahamanbtp/TechScope-AI)"
}
ARTICLE_LIMIT = 5
REQUEST_DELAY = 2  # seconds

# --------------------------
# Setup Logging
# --------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# --------------------------
# robots.txt Permission Check
# --------------------------
def is_scraping_allowed(path: str = "/") -> bool:
    try:
        rp = RobotFileParser()
        rp.set_url(ROBOTS_URL)
        rp.read()
        return rp.can_fetch(HEADERS["User-Agent"], urljoin(BASE_URL, path))
    except Exception as e:
        logging.warning(f"Failed to read robots.txt: {e}")
        return False


# --------------------------
# Get Article Links
# --------------------------
def get_article_links() -> list:
    if not is_scraping_allowed("/"):
        logging.warning("Scraping disallowed by robots.txt")
        return []

    try:
        res = requests.get(BASE_URL, headers=HEADERS, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/202" in href and href.startswith("/"):  # likely article
                full_url = urljoin(BASE_URL, href)
                links.append(full_url)

        return list(set(links))

    except Exception as e:
        logging.error(f"Failed to fetch homepage: {e}")
        return []


# --------------------------
# Parse Single Article
# --------------------------
def parse_article(url: str) -> dict:
    path = "/" + urlparse(url).path.lstrip("/")
    if not is_scraping_allowed(path):
        logging.warning(f"Skipping (robots.txt): {url}")
        return None

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else "No Title"

        author_tag = soup.find("a", rel="author")
        author = author_tag.get_text(strip=True) if author_tag else "Unknown"

        date_tag = soup.find("time")
        published = date_tag["datetime"] if date_tag and date_tag.has_attr("datetime") else None

        content_div = soup.find("div", class_="article-content")
        paragraphs = content_div.find_all("p") if content_div else []
        content = "\n".join(p.get_text(strip=True) for p in paragraphs)

        return {
            "url": url,
            "title": title,
            "author": author,
            "published": published,
            "content": content
        }

    except Exception as e:
        logging.error(f"Failed to parse article: {url} | {e}")
        return None


# --------------------------
# Main Scraper
# --------------------------
def scrape_arstechnica(limit: int = ARTICLE_LIMIT, delay: int = REQUEST_DELAY) -> list:
    logging.info(" Scraping Ars Technica for recent articles...")
    articles = []
    links = get_article_links()[:limit]

    for i, link in enumerate(links):
        logging.info(f"[{i+1}/{len(links)}] Scraping: {link}")
        article = parse_article(link)
        if article:
            articles.append(article)
        time.sleep(delay)

    logging.info(f" Completed. Scraped {len(articles)} articles.")
    return articles


# --------------------------
# CLI/Test Entry
# --------------------------
if __name__ == "__main__":
    data = scrape_arstechnica()
    for art in data:
        print(f"\n {art['title']}\n {art['url']}\n {art['published']}\n {art['author']}\n---\n{art['content'][:300]}...\n")
