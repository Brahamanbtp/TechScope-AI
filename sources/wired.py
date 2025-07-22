import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import time
import logging

# --------------------------
# Configuration
# --------------------------
BASE_URL = "https://www.wired.com/"
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
# Check robots.txt permission
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
# Get article links
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
        for a in soup.select("a[data-test-id='article-link']"):
            href = a.get("href")
            if href:
                full_url = urljoin(BASE_URL, href)
                if '/202' in full_url:
                    links.append(full_url)

        return list(set(links))

    except Exception as e:
        logging.error(f"Failed to fetch homepage: {e}")
        return []


# --------------------------
# Parse an individual article
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

        author_tag = soup.find("a", class_="byline-component__link")
        author = author_tag.get_text(strip=True) if author_tag else "Unknown"

        time_tag = soup.find("time")
        published = time_tag["datetime"] if time_tag and time_tag.has_attr("datetime") else None

        article_body = soup.find("article")
        paragraphs = article_body.select("p") if article_body else []
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
# Main scraper
# --------------------------
def scrape_wired(limit: int = ARTICLE_LIMIT, delay: int = REQUEST_DELAY) -> list:
    logging.info(" Scraping Wired for recent articles...")
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
# Run as standalone
# --------------------------
if __name__ == "__main__":
    data = scrape_wired()
    for art in data:
        print(f"\n {art['title']}\n {art['url']}\n {art['published']}\n {art['author']}\n---\n{art['content'][:300]}...\n")
