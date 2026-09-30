from storage.database import connect, execute, rows
from storage.schema import DB_PATH, init_db


CLUSTER_VERSION = "tfidf-v1"


def load_cluster_documents() -> list[dict]:
    init_db()
    with connect(DB_PATH) as connection:
        return rows(execute(connection, "SELECT id, title, content, summary FROM articles"))


def save_cluster_assignments(assignments: dict[int, str]) -> None:
    init_db()
    with connect(DB_PATH) as connection:
        for article_id, cluster_id in assignments.items():
            execute(
                connection,
                "UPDATE articles SET cluster_id = ?, cluster_version = ? WHERE id = ?",
                (cluster_id, CLUSTER_VERSION, article_id),
            )


def list_clusters() -> list[dict]:
    init_db()
    with connect(DB_PATH) as connection:
        return rows(execute(
            connection,
            "SELECT cluster_id, cluster_version, COUNT(*) AS article_count FROM articles WHERE cluster_id IS NOT NULL GROUP BY cluster_id, cluster_version ORDER BY article_count DESC",
        ))