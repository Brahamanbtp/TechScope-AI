from typing import List, Dict, Optional
from storage.schema import DB_PATH, init_db
from storage.database import connect, execute, rows

def _filters(search: Optional[str], source: Optional[str], min_quality: Optional[float]):
    clauses = []
    parameters = []
    if search:
        pattern = f"%{search}%"
        clauses.append("(title LIKE ? OR summary LIKE ? OR content LIKE ? OR keywords LIKE ?)")
        parameters.extend([pattern, pattern, pattern, pattern])
    if source:
        clauses.append("source = ?")
        parameters.append(source)
    if min_quality is not None:
        clauses.append("COALESCE(quality_score, credibility, 0) >= ?")
        parameters.append(min_quality)
    return (f" WHERE {' AND '.join(clauses)}" if clauses else ""), parameters


def load_articles(
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    source: Optional[str] = None,
    min_quality: Optional[float] = None,
) -> List[Dict]:
    """
    Load all articles from the 'articles' table and return as a list of dicts.
    Each dict has keys: id, title, url, summary, source, date_published
    """
    init_db()
    with connect(DB_PATH) as conn:
        where_clause, parameters = _filters(search, source, min_quality)
        cursor = execute(
            conn,
            "SELECT * FROM articles"
            + where_clause
            + " ORDER BY COALESCE(date_published, created_at) DESC LIMIT ? OFFSET ?",
            [*parameters, limit, offset],
        )
        return rows(cursor)


def count_articles(
    search: Optional[str] = None,
    source: Optional[str] = None,
    min_quality: Optional[float] = None,
) -> int:
    init_db()
    where_clause, parameters = _filters(search, source, min_quality)
    with connect(DB_PATH) as conn:
        row = execute(conn,
            "SELECT COUNT(*) FROM articles" + where_clause,
            parameters,
        ).fetchone()
    return row[0]


def save_articles(articles: List[Dict]) -> None:
    from storage.schema import write_article

    for article in articles:
        write_article(article)
