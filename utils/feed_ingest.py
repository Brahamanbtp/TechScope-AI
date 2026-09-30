import json
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

from storage.schema import get_feed_state, save_feed_state
from utils.clean_text import clean_article_text


logger = logging.getLogger(__name__)
FEED_TIMEOUT_SECONDS = 15.0
USER_AGENT = "TechScopeAI/1.0 (+RSS feed reader)"


@dataclass
class FeedResult:
    url: str
    modified: bool
    articles: list[dict]
    etag: str | None = None
    last_modified: str | None = None


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _child_text(element, names: set[str]) -> str:
    for child in element.iter():
        if child is element or _local_name(child.tag) not in names:
            continue
        if child.text:
            return child.text.strip()
    return ""


def _parse_xml(text: str, feed_url: str) -> list[dict]:
    root = ET.fromstring(text)
    entries = [element for element in root.iter() if _local_name(element.tag) in {"item", "entry"}]
    articles = []
    for entry in entries:
        link = _child_text(entry, {"link"})
        if not link:
            for child in entry:
                if _local_name(child.tag) == "link" and child.attrib.get("href"):
                    link = child.attrib["href"]
                    break
        content = _child_text(entry, {"content", "encoded", "description", "summary"})
        articles.append({
            "url": link,
            "title": _child_text(entry, {"title"}),
            "content": clean_article_text(content),
            "date_published": _child_text(entry, {"published", "updated", "pubdate"}),
        })
    return [article for article in articles if article["url"]]


def _parse_json(text: str) -> list[dict]:
    payload = json.loads(text)
    articles = []
    for item in payload.get("items", []):
        content = item.get("content_html") or item.get("content_text") or item.get("summary", "")
        articles.append({
            "url": item.get("url") or item.get("external_url", ""),
            "title": item.get("title", ""),
            "content": clean_article_text(content),
            "date_published": item.get("date_published") or item.get("date_modified"),
        })
    return [article for article in articles if article["url"]]


def fetch_feed(feed_url: str) -> FeedResult:
    state = get_feed_state(feed_url)
    headers = {"User-Agent": USER_AGENT}
    if state and state["etag"]:
        headers["If-None-Match"] = state["etag"]
    if state and state["last_modified"]:
        headers["If-Modified-Since"] = state["last_modified"]

    try:
        response = httpx.get(feed_url, headers=headers, timeout=FEED_TIMEOUT_SECONDS, follow_redirects=True)
        if response.status_code == 304:
            save_feed_state(feed_url, state["etag"], state["last_modified"], None)
            return FeedResult(feed_url, False, [], state["etag"], state["last_modified"])
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").lower()
        if "json" in content_type or response.text.lstrip().startswith("{"):
            articles = _parse_json(response.text)
        else:
            articles = _parse_xml(response.text, feed_url)
        hostname = urlparse(feed_url).hostname or "Unknown"
        for article in articles:
            article["source"] = hostname
        save_feed_state(feed_url, response.headers.get("etag"), response.headers.get("last-modified"), None)
        return FeedResult(feed_url, True, articles, response.headers.get("etag"), response.headers.get("last-modified"))
    except (httpx.HTTPError, ET.ParseError, json.JSONDecodeError, ValueError) as exc:
        save_feed_state(feed_url, state["etag"] if state else None, state["last_modified"] if state else None, str(exc))
        logger.warning("Feed fetch failed for %s: %s", feed_url, exc)
        return FeedResult(feed_url, False, [], state["etag"] if state else None, state["last_modified"] if state else None)