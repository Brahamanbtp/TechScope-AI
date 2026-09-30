import time
from typing import List, Dict
from datetime import datetime, timedelta, timezone
from utils.detect_duplicates import detect_similar_articles
from utils.save_data import save_articles
from utils.feed_ingest import fetch_feed
from storage.feed_repo import list_feeds
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
        articles.extend(fetch_feed(url).articles)

    return articles


def ingest_feeds_once(feed_urls: List[str] | None = None) -> int:
    """Fetch, deduplicate, and persist one feed-ingestion cycle."""
    configured_urls = feed_urls or [feed["url"] for feed in list_feeds(enabled=True)]
    raw_articles = fetch_articles(configured_urls or TECH_FEEDS)
    unique_articles = filter_duplicates(raw_articles)
    save_articles(unique_articles)
    return len(unique_articles)


def due_feed_urls() -> list[str]:
    now = datetime.now(timezone.utc)
    due = []
    for feed in list_feeds(enabled=True):
        if not feed.get("last_checked"):
            due.append(feed["url"])
            continue
        try:
            last_checked = datetime.fromisoformat(feed["last_checked"])
            if last_checked + timedelta(minutes=feed["interval_minutes"]) <= now:
                due.append(feed["url"])
        except ValueError:
            due.append(feed["url"])
    return due

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
        saved_count = ingest_feeds_once(due_feed_urls() or None)
        logging.info(f" {saved_count} new unique articles saved.")
        logging.info(f" Sleeping for {interval_minutes} minutes...\n")
        time.sleep(interval_minutes * 60)
