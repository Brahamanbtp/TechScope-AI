import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from pydantic import ValidationError

from api.serve import ArticleInput, UrlInput, app
from storage import schema
from utils.rate_limit import RateLimiter
from utils.credibility import assess_content_quality
from utils.save_data import load_articles
from utils.url_fetcher import FetchError, fetch_article, validate_public_url


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


class Phase2Tests(unittest.TestCase):
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