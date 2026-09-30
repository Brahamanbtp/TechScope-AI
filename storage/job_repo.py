import json
from datetime import datetime, timezone

from storage.schema import DB_PATH, init_db
from storage.database import connect, execute, rows


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_job(job_id: str, kind: str) -> dict:
    init_db()
    with connect(DB_PATH) as connection:
        execute(connection,
            "INSERT INTO jobs (id, kind, status, created_at) VALUES (?, ?, ?, ?)",
            (job_id, kind, "queued", _now()),
        )
    return get_job(job_id)


def get_job(job_id: str) -> dict | None:
    init_db()
    with connect(DB_PATH) as connection:
        result = next(iter(rows(execute(connection, "SELECT * FROM jobs WHERE id = ?", (job_id,)))), None)
    if not result:
        return None
    result["result"] = json.loads(result.pop("result_json") or "{}")
    return result


def update_job(job_id: str, status: str, result: dict | None = None, error: str | None = None) -> None:
    init_db()
    started_at = _now() if status == "running" else None
    finished_at = _now() if status in {"succeeded", "failed"} else None
    with connect(DB_PATH) as connection:
        execute(connection,
            """
            UPDATE jobs SET status = ?, result_json = ?, error = ?,
                started_at = COALESCE(?, started_at),
                finished_at = COALESCE(?, finished_at)
            WHERE id = ?
            """,
            (status, json.dumps(result or {}), error, started_at, finished_at, job_id),
        )