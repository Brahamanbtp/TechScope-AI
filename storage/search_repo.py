import json

from storage.database import connect, execute, rows
from storage.schema import DB_PATH, init_db, _utc_now


def save_search(user_id: int, name: str, query: dict) -> dict:
    init_db()
    with connect(DB_PATH) as connection:
        cursor = execute(connection, "INSERT INTO saved_searches (user_id, name, query_json, created_at) VALUES (?, ?, ?, ?) ON CONFLICT(user_id, name) DO UPDATE SET query_json = excluded.query_json", (user_id, name, json.dumps(query), _utc_now()))
        search_id = getattr(cursor, "lastrowid", None)
        if search_id is None:
            search_id = execute(connection, "SELECT id FROM saved_searches WHERE user_id = ? AND name = ?", (user_id, name)).fetchone()[0]
    return {"id": search_id, "user_id": user_id, "name": name, "query": query}


def list_searches(user_id: int) -> list[dict]:
    init_db()
    with connect(DB_PATH) as connection:
        result = rows(execute(connection, "SELECT * FROM saved_searches WHERE user_id = ? ORDER BY name", (user_id,)))
    for item in result:
        item["query"] = json.loads(item.pop("query_json"))
    return result


def delete_search(user_id: int, search_id: int) -> bool:
    init_db()
    with connect(DB_PATH) as connection:
        cursor = execute(connection, "DELETE FROM saved_searches WHERE id = ? AND user_id = ?", (search_id, user_id))
    return cursor.rowcount > 0