import json

from storage.database import connect, execute, rows
from storage.schema import DB_PATH, init_db, _utc_now


def save_claims(article_id: int, claims: list[dict]) -> None:
    init_db()
    with connect(DB_PATH) as connection:
        execute(connection, "DELETE FROM claims WHERE article_id = ?", (article_id,))
        for claim in claims:
            execute(connection, "INSERT INTO claims (article_id, claim_text, claim_type, evidence_json, created_at) VALUES (?, ?, ?, ?, ?)", (article_id, claim["text"], claim.get("type", "candidate"), json.dumps(claim.get("evidence", [])), _utc_now()))


def list_claims(article_id: int) -> list[dict]:
    init_db()
    with connect(DB_PATH) as connection:
        result = rows(execute(connection, "SELECT * FROM claims WHERE article_id = ? ORDER BY id", (article_id,)))
    for claim in result:
        claim["evidence"] = json.loads(claim.pop("evidence_json") or "[]")
    return result
