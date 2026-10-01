from storage.database import connect, execute, rows
from storage.schema import DB_PATH, init_db, _utc_now


def rebuild_source_reputation() -> int:
    init_db()
    with connect(DB_PATH) as connection:
        sources = rows(execute(connection, "SELECT source, COUNT(*) AS article_count, AVG(COALESCE(quality_score, credibility)) AS average_quality, AVG(CASE WHEN quality_explanation LIKE '%source-attribution%' THEN 1.0 ELSE 0.0 END) AS attribution_rate FROM articles WHERE source != '' GROUP BY source"))
        for item in sources:
            execute(connection, "INSERT INTO source_reputation (source, article_count, average_quality, attribution_rate, updated_at) VALUES (?, ?, ?, ?, ?) ON CONFLICT(source) DO UPDATE SET article_count = excluded.article_count, average_quality = excluded.average_quality, attribution_rate = excluded.attribution_rate, updated_at = excluded.updated_at", (item["source"], item["article_count"], item["average_quality"], item["attribution_rate"], _utc_now()))
    return len(sources)


def list_source_reputation() -> list[dict]:
    init_db()
    with connect(DB_PATH) as connection:
        return rows(execute(connection, "SELECT * FROM source_reputation ORDER BY article_count DESC, source"))
