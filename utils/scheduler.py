import time
import feedparser
from typing import List, Dict
from utils.clean_text import clean_article_text
from utils.detect_duplicates import detect_similar_articles
from utils.save_data import save_articles
import logging

logging.basicConfig(level=logging.INFO)

# RSS feeds of tech news sites
TECH_FEEDS = [
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://feeds.arstechnica.com/arstechnica/index/",
    "https://www.wired.com/feed/rss",
    "https://www.zdnet.com/news/rss.xml"
]

def fetch_articles(feed_urls: List[str]) -> List[Dict]:
    """Fetch and clean articles from a list of RSS feeds."""
    articles = []

    for url in feed_urls:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            article = {
                "title": entry.get("title", "").strip(),
                "link": entry.get("link", ""),
                "summary": clean_article_text(entry.get("summary", "") or entry.get("content", [{}])[0].get("value", "")),
                "published": entry.get("published", ""),
                "source": feed.feed.get("title", "Unknown")
            }
            articles.append(article)

    return articles

def filter_duplicates(articles: List[Dict]) -> List[Dict]:
    """Remove duplicate articles based on semantic similarity."""
    contents = [article["summary"] for article in articles]
    duplicates = detect_similar_articles(contents)

    unique_indices = set(range(len(articles)))
    for i, j, _ in duplicates:
        # Keep the first, discard the second
        if j in unique_indices:
            unique_indices.remove(j)

    return [articles[i] for i in sorted(unique_indices)]

def run_scheduler(interval_minutes: int = 30):
    """Continuously fetch and update articles at regular intervals."""
    logging.info(" Starting TechScope Scheduler...")
    while True:
        logging.info(" Fetching latest tech articles...")
        raw_articles = fetch_articles(TECH_FEEDS)
        unique_articles = filter_duplicates(raw_articles)
        save_articles(unique_articles)

        logging.info(f" {len(unique_articles)} new unique articles saved.")
        logging.info(f" Sleeping for {interval_minutes} minutes...\n")
        time.sleep(interval_minutes * 60)
