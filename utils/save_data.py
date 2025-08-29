import sqlite3
from typing import List, Dict

DB_PATH = "techscope.db"  # path to your SQLite database

def load_articles() -> List[Dict]:
    """
    Load all articles from the 'articles' table and return as a list of dicts.
    Each dict has keys: id, title, url, summary, source, date_published
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM articles ORDER BY date_published DESC")
        rows = cursor.fetchall()

        articles = [dict(row) for row in rows]

        conn.close()
        return articles

    except Exception as e:
        print(f"Error loading articles: {e}")
        return []
