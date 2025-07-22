import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import time
import logging

# --------------------------
# Configuration
# --------------------------
BASE_URL = "https://www.theverge.com/"
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
        logging.warning(f"robots.txt check failed: {e}")
        return False


# --------------------------
# Extract article links
# --------------------------
def get_article_links() -> list:
    if not is_scraping_allowed("/"):
        logging.warning("Scraping homepage disallowed by robots.txt")
        return []

    try:
        res = requests.get(BASE_URL, headers=HEADERS, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        links = []
        for a in soup.select("a[href^='https://www.theverge.com/']"):
            href = a.get("href")
            if href and href.startswith("https://www.theverge.com/") and "/202" in href:
                links.append(href.split("?")[0])  # remove URL params

        return list(set(links))  # deduplicate

    except Exception as e:
        logging.error(f"Failed to fetch homepage: {e}")
        return []


# --------------------------
# Parse single article
# --------------------------
def parse_article(url: str) -> dict:
    path = "/" + "/".join(urlparse(url).path.split("/")[1:])
    if not is_scraping_allowed(path):
        logging.warning(f"Disallowed by robots.txt: {url}")
        return None

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        title = soup.find("h1").get_text(strip=True) if soup.find("h1") else "No title"
        author_tag = soup.find("span", class_="byline__name")
        author = author_tag.get_text(strip=True) if author_tag else "Unknown"
        published = soup.find("time")
        published_date = published["datetime"] if published and published.has_attr("datetime") else None
        article_body = soup.find("div", class_="duet--article--article-body-components-container")
        content = "\n".join(p.get_text(strip=True) for p in article_body.find_all("p")) if article_body else ""

        return {
            "url": url,
            "title": title,
            "author": author,
            "published": published_date,
            "content": content
        }

    except Exception as e:
        logging.error(f"Failed to parse article: {url} | {e}")
        return None


# --------------------------
# Main scraper function
# --------------------------
def scrape_theverge(limit: int = ARTICLE_LIMIT, delay: int = REQUEST_DELAY) -> list:
    logging.info(" Fetching articles from The Verge...")
    articles = []
    links = get_article_links()[:limit]

    for i, url in enumerate(links):
        logging.info(f"[{i+1}/{len(links)}] Scraping: {url}")
        article = parse_article(url)
        if article:
            articles.append(article)
        time.sleep(delay)

    logging.info(f" Done. {len(articles)} articles scraped.")
    return articles


# --------------------------
# Run standalone
# --------------------------
if __name__ == "__main__":
    data = scrape_theverge()
    for art in data:
        print(f"\n {art['title']}\n {art['url']}\n {art['published']}\n {art['author']}\n---\n{art['content'][:300]}...\n")
