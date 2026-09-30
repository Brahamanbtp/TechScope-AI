from storage.database import connect, execute, rows
from storage.schema import DB_PATH, init_db, _utc_now


def set_bookmark(user_id: int, article_id: int, enabled: bool) -> bool:
    init_db()
    with connect(DB_PATH) as connection:
        if enabled:
            execute(connection, "INSERT INTO bookmarks (user_id, article_id, created_at) VALUES (?, ?, ?) ON CONFLICT DO NOTHING", (user_id, article_id, _utc_now()))
        else:
            execute(connection, "DELETE FROM bookmarks WHERE user_id = ? AND article_id = ?", (user_id, article_id))
    return enabled


def list_bookmarks(user_id: int, limit: int = 100) -> list[dict]:
    init_db()
    with connect(DB_PATH) as connection:
        return rows(execute(connection, "SELECT articles.*, bookmarks.created_at AS bookmarked_at FROM bookmarks JOIN articles ON articles.id = bookmarks.article_id WHERE bookmarks.user_id = ? ORDER BY bookmarks.created_at DESC LIMIT ?", (user_id, limit)))


def mark_read(user_id: int, article_id: int) -> None:
    init_db()
    with connect(DB_PATH) as connection:
        execute(connection, "INSERT INTO read_states (user_id, article_id, read_at) VALUES (?, ?, ?) ON CONFLICT(user_id, article_id) DO UPDATE SET read_at = excluded.read_at", (user_id, article_id, _utc_now()))