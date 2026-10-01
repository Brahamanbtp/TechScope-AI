from storage.database import connect, execute, rows
from storage.schema import DB_PATH, init_db, _utc_now


def submit_review(article_id: int, reviewer_id: int, label: str, notes: str = "") -> dict:
    if label not in {"lower", "mixed", "higher"}:
        raise ValueError("label must be lower, mixed, or higher")
    init_db()
    with connect(DB_PATH) as connection:
        cursor = execute(connection, "INSERT INTO quality_reviews (article_id, reviewer_id, label, notes, created_at) VALUES (?, ?, ?, ?, ?) ON CONFLICT(article_id, reviewer_id) DO UPDATE SET label = excluded.label, notes = excluded.notes", (article_id, reviewer_id, label, notes, _utc_now()))
        review_id = getattr(cursor, "lastrowid", None) or execute(connection, "SELECT id FROM quality_reviews WHERE article_id = ? AND reviewer_id = ?", (article_id, reviewer_id)).fetchone()[0]
    return {"id": review_id, "article_id": article_id, "reviewer_id": reviewer_id, "label": label, "notes": notes}


def list_reviews(article_id: int | None = None) -> list[dict]:
    init_db()
    query = "SELECT * FROM quality_reviews"
    params = ()
    if article_id is not None:
        query += " WHERE article_id = ?"
        params = (article_id,)
    with connect(DB_PATH) as connection:
        return rows(execute(connection, query, params))