from storage.database import connect, execute, rows
import json
from storage.schema import DB_PATH, init_db, _utc_now


def create_webhook(user_id: int, url: str, event: str, adapter: str = "generic") -> dict:
    init_db()
    with connect(DB_PATH) as connection:
        cursor = execute(connection, "INSERT INTO webhooks (user_id, url, event, adapter, created_at) VALUES (?, ?, ?, ?, ?) ON CONFLICT(user_id, url, event) DO UPDATE SET active = 1, adapter = excluded.adapter", (user_id, url, event, adapter, _utc_now()))
        webhook_id = getattr(cursor, "lastrowid", None)
        if webhook_id is None:
            webhook_id = execute(connection, "SELECT id FROM webhooks WHERE user_id = ? AND url = ? AND event = ?", (user_id, url, event)).fetchone()[0]
    return {"id": webhook_id, "user_id": user_id, "url": url, "event": event, "adapter": adapter, "active": True}


def list_webhooks(user_id: int) -> list[dict]:
    init_db()
    with connect(DB_PATH) as connection:
        return rows(execute(connection, "SELECT * FROM webhooks WHERE user_id = ? AND active = 1 ORDER BY id", (user_id,)))


def delete_webhook(user_id: int, webhook_id: int) -> bool:
    init_db()
    with connect(DB_PATH) as connection:
        cursor = execute(connection, "UPDATE webhooks SET active = 0 WHERE id = ? AND user_id = ?", (webhook_id, user_id))
    return cursor.rowcount > 0


def create_delivery(webhook_id: int, event: str, payload: dict) -> int:
    init_db()
    with connect(DB_PATH) as connection:
        cursor = execute(connection, "INSERT INTO webhook_deliveries (webhook_id, event, payload_json, created_at) VALUES (?, ?, ?, ?)", (webhook_id, event, json.dumps(payload), _utc_now()))
        return getattr(cursor, "lastrowid", None) or execute(connection, "SELECT MAX(id) FROM webhook_deliveries").fetchone()[0]


def update_delivery(delivery_id: int, attempts: int, status: str, error: str | None = None) -> None:
    init_db()
    with connect(DB_PATH) as connection:
        execute(connection, "UPDATE webhook_deliveries SET attempts = ?, status = ?, last_error = ?, delivered_at = CASE WHEN ? = 'delivered' THEN ? ELSE delivered_at END WHERE id = ?", (attempts, status, error, status, _utc_now(), delivery_id))