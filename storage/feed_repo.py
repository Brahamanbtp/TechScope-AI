from typing import Optional

from storage.schema import DB_PATH, init_db
from storage.database import connect, execute, rows


def list_feeds(enabled: Optional[bool] = None) -> list[dict]:
    init_db()
    query = "SELECT * FROM feeds"
    parameters = []
    if enabled is not None:
        query += " WHERE enabled = ?"
        parameters.append(int(enabled))
    query += " ORDER BY name, url"
    with connect(DB_PATH) as connection:
        return rows(execute(connection, query, parameters))


def list_feed_health() -> list[dict]:
    init_db()
    query = """
        SELECT feeds.*, feed_sources.etag, feed_sources.last_modified,
               feed_sources.last_checked, feed_sources.last_error
        FROM feeds
        LEFT JOIN feed_sources ON feed_sources.url = feeds.url
        ORDER BY feeds.name, feeds.url
    """
    with connect(DB_PATH) as connection:
        return rows(execute(connection, query))


def create_feed(url: str, name: str, interval_minutes: int) -> dict:
    from storage.schema import _utc_now

    init_db()
    now = _utc_now()
    with connect(DB_PATH) as connection:
        cursor = execute(connection,
            "INSERT INTO feeds (url, name, interval_minutes, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (url, name or url, interval_minutes, now, now),
        )
        feed_id = cursor.lastrowid
        if feed_id is None:
            feed_id = execute(connection, "SELECT id FROM feeds WHERE url = ?", (url,)).fetchone()[0]
    return get_feed(feed_id)


def get_feed(feed_id: int) -> dict | None:
    init_db()
    with connect(DB_PATH) as connection:
        return next(iter(rows(execute(connection, "SELECT * FROM feeds WHERE id = ?", (feed_id,)))), None)


def delete_feed(feed_id: int) -> bool:
    init_db()
    with connect(DB_PATH) as connection:
        cursor = execute(connection, "DELETE FROM feeds WHERE id = ?", (feed_id,))
    return cursor.rowcount > 0