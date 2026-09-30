import os
import json
import shutil
import sqlite3
from datetime import datetime, timezone


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "techscope.db")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    try:
        with sqlite3.connect(DB_PATH) as connection:
            connection.execute("PRAGMA user_version")
    except sqlite3.DatabaseError:
        backup_path = f"{DB_PATH}.invalid-{int(datetime.now().timestamp())}"
        shutil.move(DB_PATH, backup_path)

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT '',
                author TEXT NOT NULL DEFAULT '',
                date_published TEXT,
                content TEXT NOT NULL DEFAULT '',
                summary TEXT NOT NULL DEFAULT '',
                credibility REAL,
                quality_score REAL,
                quality_explanation TEXT NOT NULL DEFAULT '',
                analysis_version TEXT NOT NULL DEFAULT '',
                keywords TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_articles_date ON articles(date_published DESC)"
        )
        existing_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(articles)")
        }
        for column, definition in (
            ("quality_score", "REAL"),
            ("quality_explanation", "TEXT NOT NULL DEFAULT ''"),
            ("analysis_version", "TEXT NOT NULL DEFAULT ''"),
        ):
            if column not in existing_columns:
                connection.execute(f"ALTER TABLE articles ADD COLUMN {column} {definition}")
        connection.commit()


def write_article(article: dict) -> None:
    init_db()
    now = _utc_now()
    keywords = article.get("keywords", [])
    if isinstance(keywords, list):
        keywords = ",".join(str(keyword) for keyword in keywords)
    explanation = article.get("quality_explanation", "")
    if isinstance(explanation, list):
        explanation = json.dumps(explanation)

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            INSERT INTO articles (
                url, title, source, author, date_published, content,
                summary, credibility, keywords, created_at, updated_at
                , quality_score, quality_explanation, analysis_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                title = excluded.title,
                source = excluded.source,
                author = excluded.author,
                date_published = excluded.date_published,
                content = excluded.content,
                summary = excluded.summary,
                credibility = excluded.credibility,
                quality_score = excluded.quality_score,
                quality_explanation = excluded.quality_explanation,
                analysis_version = excluded.analysis_version,
                keywords = excluded.keywords,
                updated_at = excluded.updated_at
            """,
            (
                article.get("url", ""),
                article.get("title", ""),
                article.get("source", ""),
                article.get("author", ""),
                article.get("date_published") or article.get("published"),
                article.get("content", ""),
                article.get("summary", ""),
                article.get("credibility"),
                keywords,
                article.get("created_at", now),
                now,
                article.get("quality_score", article.get("credibility")),
                explanation,
                article.get("analysis_version", ""),
            ),
        )
        connection.commit()