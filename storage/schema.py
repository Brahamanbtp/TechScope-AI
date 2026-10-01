import os
import json
import shutil
import sqlite3
from datetime import datetime, timezone

from storage.database import connect, execute, rows


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "techscope.db")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    if os.getenv("DATABASE_URL", "").startswith(("postgresql://", "postgres://")):
        _init_postgres()
        return

    try:
        with sqlite3.connect(DB_PATH) as connection:
            connection.execute("PRAGMA user_version")
    except sqlite3.DatabaseError:
        backup_path = f"{DB_PATH}.invalid-{int(datetime.now().timestamp())}"
        shutil.move(DB_PATH, backup_path)

    with sqlite3.connect(DB_PATH) as connection:
        execute(connection,
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
                cluster_id TEXT,
                cluster_version TEXT NOT NULL DEFAULT '',
                evidence_json TEXT NOT NULL DEFAULT '[]',
                keywords TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS feed_sources (
                url TEXT PRIMARY KEY,
                etag TEXT,
                last_modified TEXT,
                last_checked TEXT,
                last_error TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS feeds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL DEFAULT '',
                enabled INTEGER NOT NULL DEFAULT 1,
                interval_minutes INTEGER NOT NULL DEFAULT 30,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                status TEXT NOT NULL,
                result_json TEXT NOT NULL DEFAULT '{}',
                error TEXT,
                created_at TEXT NOT NULL,
                started_at TEXT,
                finished_at TEXT
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
            ("cluster_id", "TEXT"),
            ("cluster_version", "TEXT NOT NULL DEFAULT ''"),
            ("evidence_json", "TEXT NOT NULL DEFAULT '[]'"),
        ):
            if column not in existing_columns:
                connection.execute(f"ALTER TABLE articles ADD COLUMN {column} {definition}")
        connection.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS bookmarks (user_id INTEGER NOT NULL, article_id INTEGER NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY (user_id, article_id))"
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS read_states (user_id INTEGER NOT NULL, article_id INTEGER NOT NULL, read_at TEXT NOT NULL, PRIMARY KEY (user_id, article_id))"
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS saved_searches (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT NOT NULL, query_json TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(user_id, name))"
        )
        connection.execute("CREATE TABLE IF NOT EXISTS claims (id INTEGER PRIMARY KEY AUTOINCREMENT, article_id INTEGER NOT NULL, claim_text TEXT NOT NULL, claim_type TEXT NOT NULL DEFAULT 'candidate', evidence_json TEXT NOT NULL DEFAULT '[]', created_at TEXT NOT NULL)")
        connection.execute("CREATE TABLE IF NOT EXISTS source_reputation (source TEXT PRIMARY KEY, article_count INTEGER NOT NULL, average_quality REAL, attribution_rate REAL, updated_at TEXT NOT NULL)")
        connection.execute(
            "INSERT OR IGNORE INTO schema_migrations (version, applied_at) VALUES (1, ?)",
            (_utc_now(),),
        )
        connection.commit()


def _init_postgres() -> None:
    with connect(DB_PATH) as connection:
        execute(connection, """
            CREATE TABLE IF NOT EXISTS articles (
                id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                url TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL DEFAULT '', source TEXT NOT NULL DEFAULT '',
                author TEXT NOT NULL DEFAULT '', date_published TEXT,
                content TEXT NOT NULL DEFAULT '', summary TEXT NOT NULL DEFAULT '',
                credibility DOUBLE PRECISION, quality_score DOUBLE PRECISION,
                quality_explanation TEXT NOT NULL DEFAULT '',
                analysis_version TEXT NOT NULL DEFAULT '', keywords TEXT NOT NULL DEFAULT '',
                cluster_id TEXT, cluster_version TEXT NOT NULL DEFAULT '',
                evidence_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            )
        """)
        execute(connection, """
            CREATE TABLE IF NOT EXISTS feed_sources (
                url TEXT PRIMARY KEY, etag TEXT, last_modified TEXT,
                last_checked TEXT, last_error TEXT
            )
        """)
        execute(connection, """
            CREATE TABLE IF NOT EXISTS feeds (
                id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                url TEXT NOT NULL UNIQUE, name TEXT NOT NULL DEFAULT '',
                enabled BOOLEAN NOT NULL DEFAULT TRUE, interval_minutes INTEGER NOT NULL DEFAULT 30,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            )
        """)
        execute(connection, """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY, kind TEXT NOT NULL, status TEXT NOT NULL,
                result_json TEXT NOT NULL DEFAULT '{}', error TEXT,
                created_at TEXT NOT NULL, started_at TEXT, finished_at TEXT
            )
        """)
        execute(connection, "CREATE INDEX IF NOT EXISTS idx_articles_date ON articles(date_published DESC)")
        execute(connection, "CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)")
        execute(connection, """
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user', active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TEXT NOT NULL
            )
        """)
        execute(connection, """
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                expires_at TEXT NOT NULL, created_at TEXT NOT NULL
            )
        """)
        execute(connection, "CREATE TABLE IF NOT EXISTS bookmarks (user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE, article_id BIGINT NOT NULL REFERENCES articles(id) ON DELETE CASCADE, created_at TEXT NOT NULL, PRIMARY KEY (user_id, article_id))")
        execute(connection, "CREATE TABLE IF NOT EXISTS read_states (user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE, article_id BIGINT NOT NULL REFERENCES articles(id) ON DELETE CASCADE, read_at TEXT NOT NULL, PRIMARY KEY (user_id, article_id))")
        execute(connection, "CREATE TABLE IF NOT EXISTS saved_searches (id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE, name TEXT NOT NULL, query_json TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(user_id, name))")
        execute(connection, "CREATE TABLE IF NOT EXISTS claims (id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY, article_id BIGINT NOT NULL REFERENCES articles(id) ON DELETE CASCADE, claim_text TEXT NOT NULL, claim_type TEXT NOT NULL DEFAULT 'candidate', evidence_json TEXT NOT NULL DEFAULT '[]', created_at TEXT NOT NULL)")
        execute(connection, "CREATE TABLE IF NOT EXISTS source_reputation (source TEXT PRIMARY KEY, article_count INTEGER NOT NULL, average_quality DOUBLE PRECISION, attribution_rate DOUBLE PRECISION, updated_at TEXT NOT NULL)")
        execute(connection, "INSERT INTO schema_migrations (version, applied_at) VALUES (1, %s) ON CONFLICT (version) DO NOTHING", (_utc_now(),))


def get_feed_state(url: str) -> dict | None:
    init_db()
    with connect(DB_PATH) as connection:
        row = execute(connection,
            "SELECT url, etag, last_modified, last_checked, last_error FROM feed_sources WHERE url = ?",
            (url,),
        ).fetchone()
        if not row:
            return None
        if isinstance(row, sqlite3.Row):
            return dict(row)
        return dict(zip([column.name for column in connection.execute("SELECT * FROM feed_sources LIMIT 0").description], row))


def save_feed_state(url: str, etag: str | None, last_modified: str | None, error: str | None) -> None:
    init_db()
    with connect(DB_PATH) as connection:
        execute(connection,
            """
            INSERT INTO feed_sources (url, etag, last_modified, last_checked, last_error)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                etag = excluded.etag,
                last_modified = excluded.last_modified,
                last_checked = excluded.last_checked,
                last_error = excluded.last_error
            """,
            (url, etag, last_modified, _utc_now(), error),
        )


def write_article(article: dict) -> None:
    init_db()
    now = _utc_now()
    keywords = article.get("keywords", [])
    if isinstance(keywords, list):
        keywords = ",".join(str(keyword) for keyword in keywords)
    explanation = article.get("quality_explanation", "")
    if isinstance(explanation, list):
        explanation = json.dumps(explanation)
    evidence = article.get("evidence", [])
    if isinstance(evidence, list):
        evidence = json.dumps(evidence)

    with connect(DB_PATH) as connection:
        execute(connection,
            """
            INSERT INTO articles (
                url, title, source, author, date_published, content,
                summary, credibility, keywords, created_at, updated_at
                , quality_score, quality_explanation, analysis_version
                , evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                evidence_json = excluded.evidence_json,
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
                evidence,
            ),
        )
    if article.get("claims"):
        from storage.claim_repo import save_claims
        with connect(DB_PATH) as connection:
            article_id = execute(connection, "SELECT id FROM articles WHERE url = ?", (article.get("url", ""),)).fetchone()[0]
        save_claims(article_id, article["claims"])