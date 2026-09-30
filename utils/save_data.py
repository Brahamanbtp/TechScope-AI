import sqlite3
from typing import List, Dict
from storage.schema import DB_PATH, init_db

def load_articles() -> List[Dict]:
    """
    Load all articles from the 'articles' table and return as a list of dicts.
    Each dict has keys: id, title, url, summary, source, date_published
    """
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM articles ORDER BY date_published DESC")
        rows = cursor.fetchall()

        articles = [dict(row) for row in rows]

        return articles


def save_articles(articles: List[Dict]) -> None:
    from storage.schema import write_article

    for article in articles:
        write_article(article)
