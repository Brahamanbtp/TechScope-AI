import sqlite3
from storage.schema import DB_PATH, init_db
from storage.database import connect, execute, rows


def get_article(article_id: int) -> dict | None:
    init_db()
    with connect(DB_PATH) as connection:
        return next(iter(rows(execute(connection, "SELECT * FROM articles WHERE id = ?", (article_id,)))), None)