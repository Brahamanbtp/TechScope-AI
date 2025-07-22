import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser
import time
import logging

# --------------------------
# Configuration
# --------------------------
BASE_URL = "https://techcrunch.com/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; TechScopeBot/1.0; +https://github.com/Brahamanbtp/TechScope-AI)"
}
ROBOTS_URL = urljoin(BASE_URL, "robots.txt")
ARTICLE_LIMIT = 5
REQUEST_DELAY = 2  # in seconds

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
# Get article links from homepage
# --------------------------
def get_article_links() -> list:
    if not is_scraping_allowed("/"):
        logging.warning("Scraping disallowed by robots.txt")
        return []

    try:
        res = requests.get(BASE_URL, headers=HEADERS, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        links = [
            a["href"]
            for a in soup.select("a.post-block__title__link")
            if a.get("href") and a["href"].startswith("https://techcrunch.com/")
        ]
        return list(set(links))  # deduplicate
    except Exception as e:
        logging.error(f"Failed to fetch homepage: {e}")
        return []


# --------------------------
# Parse individual article
# --------------------------
def parse_article(url: str) -> dict:
    path = url.replace(BASE_URL, "/")
    if not is_scraping_allowed(path):
        logging.warning(f"Skipping (not allowed by robots.txt): {url}")
        return None

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        title = soup.find("h1").get_text(strip=True) if soup.find("h1") else "No title"
        author = soup.find("a", rel="author").get_text(strip=True) if soup.find("a", rel="author") else "Unknown"
        published = soup.find("time")["datetime"] if soup.find("time") else None
        body = soup.find("div", class_="article-content")
        content = "\n".join(p.get_text(strip=True) for p in body.find_all("p")) if body else ""

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
# Main scraper function
# --------------------------
def scrape_techcrunch(limit: int = ARTICLE_LIMIT, delay: int = REQUEST_DELAY) -> list:
    logging.info(" Fetching articles from TechCrunch...")
    articles = []
    links = get_article_links()[:limit]

    for i, link in enumerate(links):
        logging.info(f"[{i+1}/{len(links)}] Scraping: {link}")
        article = parse_article(link)
        if article:
            articles.append(article)
        time.sleep(delay)

    logging.info(f" Done. {len(articles)} articles fetched.")
    return articles


# --------------------------
# Run as standalone
# --------------------------
if __name__ == "__main__":
    data = scrape_techcrunch()
    for art in data:
        print(f"\n {art['title']}\n {art['url']}\n {art['published']}\n {art['author']}\n---\n{art['content'][:300]}...\n")
