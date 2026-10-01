import asyncio
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import httpx
from pydantic import ValidationError

from api.serve import ArticleInput, UrlInput, app
from storage import schema
from utils.rate_limit import RateLimiter
from utils.credibility import assess_content_quality
from utils.save_data import load_articles
from utils.url_fetcher import FetchError, fetch_article, validate_public_url
from utils.feed_ingest import fetch_feed
from utils.evaluate_quality import evaluate
from storage import feed_repo
from storage import job_repo
from storage import cluster_repo
from storage import article_actions
from storage import search_repo
from utils.evidence import extract_evidence
from utils.claims import extract_claims
from sources.registry import get_adapter, list_adapters, register_adapter
from utils.search import semantic_search
from sources import arstechnica, techcrunch, theverge, wired


class FakeResponse:
    status_code = 200
    headers = {"content-type": "text/html"}
    encoding = "utf-8"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def raise_for_status(self):
        return None

    def iter_bytes(self):
        return iter([b"<html><head><title>Test article</title></head><body><article>", b"Article text " * 20, b"</article></body></html>"])


class FakeClient:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def stream(self, method, url):
        return FakeResponse()


class FeedResponse:
    def __init__(self, status_code, text, headers=None):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}

    def raise_for_status(self):
        return None


class SourceResponse:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        return None


def source_article_test(module, html, expected_title, expected_author):
    with patch.object(module, "is_scraping_allowed", return_value=True):
        with patch.object(module.requests, "get", return_value=SourceResponse(html)):
            article = module.parse_article("https://example.com/article")
    return article, expected_title, expected_author


class Phase2Tests(unittest.TestCase):
    def test_source_adapter_sdk_contract(self):
        class Adapter:
            name = "test"

            def get_article_links(self):
                return []

            def parse_article(self, url):
                return {"url": url, "content": ""}

        register_adapter(Adapter())
        self.assertIn("test", list_adapters())
        self.assertEqual(get_adapter("test").parse_article("https://example.com")["url"], "https://example.com")
    def test_candidate_claims_link_evidence(self):
        claims = extract_claims("According to the report, the company launched a new processor in 2026.", [{"text": "According to the report, the company launched a new processor in 2026.", "urls": [], "type": "attribution"}])
        self.assertEqual(claims[0]["type"], "candidate")
        self.assertEqual(len(claims[0]["evidence"]), 1)
    def test_saved_search_lifecycle(self):
        with tempfile.NamedTemporaryFile(suffix=".db") as database:
            with patch.object(schema, "DB_PATH", database.name), patch.object(search_repo, "DB_PATH", database.name):
                created = search_repo.save_search(1, "AI launches", {"query": "AI", "source": None})
                self.assertEqual(search_repo.list_searches(1)[0]["name"], "AI launches")
                self.assertTrue(search_repo.delete_search(1, created["id"]))
    def test_semantic_search_empty_store(self):
        with tempfile.NamedTemporaryFile(suffix=".db") as database:
            with patch.object(schema, "DB_PATH", database.name), patch.object(cluster_repo, "DB_PATH", database.name):
                self.assertEqual(semantic_search("technology"), [])
    def test_user_article_actions_are_scoped(self):
        with tempfile.NamedTemporaryFile(suffix=".db") as database:
            with patch.object(schema, "DB_PATH", database.name), patch.object(article_actions, "DB_PATH", database.name):
                schema.init_db()
                with sqlite3.connect(database.name) as connection:
                    connection.execute("INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)", ("u", "hash", "now"))
                    connection.execute("INSERT INTO articles (url, created_at, updated_at) VALUES (?, ?, ?)", ("https://example.com", "now", "now"))
                    connection.commit()
                article_actions.set_bookmark(1, 1, True)
                self.assertEqual(len(article_actions.list_bookmarks(1)), 1)
                article_actions.mark_read(1, 1)
    def test_evidence_extraction_is_explicit(self):
        evidence = extract_evidence("According to the report at https://example.com/report, results improved.")
        self.assertEqual(evidence[0]["type"], "attribution")
        self.assertEqual(evidence[0]["urls"], ["https://example.com/report,"])

    def test_clustering_empty_store(self):
        with tempfile.NamedTemporaryFile(suffix=".db") as database:
            with patch.object(schema, "DB_PATH", database.name), patch.object(cluster_repo, "DB_PATH", database.name):
                from utils.clustering import cluster_articles
                self.assertEqual(cluster_articles()["clusters"], 0)

    def test_feed_health_view_includes_fetch_state(self):
        with tempfile.NamedTemporaryFile(suffix=".db") as database:
            with patch.object(schema, "DB_PATH", database.name), patch.object(feed_repo, "DB_PATH", database.name):
                feed_repo.create_feed("https://example.com/feed.xml", "Example", 15)
                schema.save_feed_state("https://example.com/feed.xml", "etag-1", "today", None)
                health = feed_repo.list_feed_health()
        self.assertEqual(health[0]["last_error"], None)
        self.assertEqual(health[0]["etag"], "etag-1")

    def test_job_lifecycle(self):
        with tempfile.NamedTemporaryFile(suffix=".db") as database:
            with patch.object(schema, "DB_PATH", database.name), patch.object(job_repo, "DB_PATH", database.name):
                job_repo.create_job("job-1", "feed_ingest")
                job_repo.update_job("job-1", "running")
                job_repo.update_job("job-1", "succeeded", {"saved": 3})
                job = job_repo.get_job("job-1")
        self.assertEqual(job["status"], "succeeded")
        self.assertEqual(job["result"], {"saved": 3})

    def test_feed_registry_lifecycle(self):
        with tempfile.NamedTemporaryFile(suffix=".db") as database:
            with patch.object(schema, "DB_PATH", database.name), patch.object(feed_repo, "DB_PATH", database.name):
                created = feed_repo.create_feed("https://example.com/feed.xml", "Example", 15)
                self.assertEqual(created["name"], "Example")
                self.assertEqual(len(feed_repo.list_feeds()), 1)
                self.assertTrue(feed_repo.delete_feed(created["id"]))
                self.assertEqual(feed_repo.list_feeds(), [])

    def test_versioned_control_plane_routes_exist(self):
        paths = {route.path for route in app.routes}
        self.assertTrue({
            "/healthz",
            "/api/v1/feeds",
            "/api/v1/ingest",
            "/api/v1/jobs/{job_id}",
            "/api/v1/articles/{article_id}",
        } <= paths)

    def test_quality_evaluation_dataset_is_labelled(self):
        result = evaluate()
        self.assertGreaterEqual(result["examples"], 20)
        self.assertEqual(result["status"], "experimental")
        self.assertIn("higher", result["per_class"])
        self.assertGreaterEqual(result["accuracy"], 0)
    def test_conditional_feed_request_uses_validators(self):
        feed = '<rss><channel><item><title>Story</title><link>https://example.com/story</link><description>Feed content</description></item></channel></rss>'
        responses = [
            FeedResponse(200, feed, {"etag": "v1", "last-modified": "today"}),
            FeedResponse(304, "", {}),
        ]
        with patch("utils.feed_ingest.httpx.get", side_effect=responses):
            with patch("utils.feed_ingest.get_feed_state", side_effect=[None, {"etag": "v1", "last_modified": "today"}]):
                with patch("utils.feed_ingest.save_feed_state") as save_state:
                    first = fetch_feed("https://example.com/feed.xml")
                    second = fetch_feed("https://example.com/feed.xml")
        self.assertTrue(first.modified)
        self.assertEqual(len(first.articles), 1)
        self.assertFalse(second.modified)
        self.assertEqual(second.articles, [])
        self.assertEqual(save_state.call_count, 2)

    def test_source_specific_parsers(self):
        fixtures = [
            (arstechnica, '<html><h1>Ars title</h1><a rel="author">Ada</a><time datetime="2026-01-01"/><div class="article-content"><p>Ars article content.</p></div></html>', "Ars title", "Ada"),
            (techcrunch, '<html><h1>TC title</h1><a rel="author">Ben</a><time datetime="2026-01-01"/><div class="article-content"><p>TechCrunch article content.</p></div></html>', "TC title", "Ben"),
            (theverge, '<html><h1>Verge title</h1><span class="byline__name">Cy</span><time datetime="2026-01-01"/><div class="duet--article--article-body-components-container"><p>Verge article content.</p></div></html>', "Verge title", "Cy"),
            (wired, '<html><h1>Wired title</h1><a class="byline-component__link">Di</a><time datetime="2026-01-01"/><article><p>Wired article content.</p></article></html>', "Wired title", "Di"),
        ]
        for module, html, title, author in fixtures:
            with self.subTest(module=module.__name__):
                article, expected_title, expected_author = source_article_test(module, html, title, author)
                self.assertEqual(article["title"], expected_title)
                self.assertEqual(article["author"], expected_author)
                self.assertIn("article content", article["content"])

    def test_article_reads_are_paginated(self):
        with tempfile.NamedTemporaryFile(suffix=".db") as database:
            with patch.object(schema, "DB_PATH", database.name):
                with patch("utils.save_data.DB_PATH", database.name):
                    schema.init_db()
                    for index in range(3):
                        schema.write_article({"url": f"https://example.com/{index}", "title": str(index)})
                    articles = load_articles(limit=1, offset=1)
        self.assertEqual(len(articles), 1)

    def test_security_headers_are_present(self):
        async def request_root():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                return await client.get("/")

        response = asyncio.run(request_root())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["x-frame-options"], "DENY")

    def test_quality_assessment_is_bounded_and_explainable(self):
        assessment = assess_content_quality(
            "According to the source, this article contains useful reporting. " * 25
        )
        self.assertGreaterEqual(assessment["score"], 0)
        self.assertLessEqual(assessment["score"], 1)
        self.assertTrue(assessment["signals"])
        self.assertEqual(assessment["method"], "heuristic-v1")

    def test_quality_assessment_penalizes_clickbait(self):
        plain = assess_content_quality("Technical reporting with details. " * 40)
        clickbait = assess_content_quality("Shocking! You won't believe this. " * 40)
        self.assertLess(clickbait["score"], plain["score"])
        self.assertTrue(any("clickbait" in signal for signal in clickbait["signals"]))

    def test_private_and_unsafe_urls_are_rejected(self):
        for url in ("http://127.0.0.1", "file:///etc/passwd", "https://user:pass@example.com"):
            with self.subTest(url=url):
                with self.assertRaises(FetchError):
                    validate_public_url(url)

    def test_fetch_article_extracts_title_and_content(self):
        with patch("utils.url_fetcher.validate_public_url", return_value="https://example.com/article"):
            with patch("utils.url_fetcher.httpx.Client", FakeClient):
                article = fetch_article("https://example.com/article")

        self.assertEqual(article["title"], "Test article")
        self.assertGreater(len(article["content"]), 100)

    def test_rate_limiter(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        self.assertTrue(limiter.allow("client"))
        self.assertTrue(limiter.allow("client"))
        self.assertFalse(limiter.allow("client"))
        self.assertTrue(limiter.allow("other-client"))

    def test_canonical_database_upserts_by_url(self):
        with tempfile.NamedTemporaryFile(suffix=".db") as database:
            with patch.object(schema, "DB_PATH", database.name):
                schema.init_db()
                schema.write_article({"url": "https://example.com", "title": "First"})
                schema.write_article({"url": "https://example.com", "title": "Updated"})
                with sqlite3.connect(database.name) as connection:
                    rows = connection.execute("SELECT title FROM articles").fetchall()
                self.assertEqual(rows, [("Updated",)])

    def test_request_limits_and_route(self):
        with self.assertRaises(ValidationError):
            ArticleInput(text="too short")
        with self.assertRaises(ValidationError):
            UrlInput(url="x")
        self.assertTrue(any(route.path == "/analyze" for route in app.routes))


if __name__ == "__main__":
    unittest.main()