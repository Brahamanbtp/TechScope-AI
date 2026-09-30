import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator


@contextmanager
def connect(sqlite_path: str) -> Iterator[object]:
    database_url = os.getenv("DATABASE_URL", "")
    if database_url.startswith(("postgresql://", "postgres://")):
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError("psycopg is required when DATABASE_URL uses PostgreSQL") from exc
        connection = psycopg.connect(database_url)
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return

    connection = sqlite3.connect(sqlite_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def execute(connection, query: str, parameters=()):
    if connection.__class__.__module__.startswith("psycopg"):
        query = query.replace("?", "%s")
    return connection.execute(query, parameters)


def rows(cursor) -> list[dict]:
    values = cursor.fetchall()
    if not values:
        return []
    if isinstance(values[0], sqlite3.Row):
        return [dict(value) for value in values]
    columns = [column.name if hasattr(column, "name") else column[0] for column in cursor.description]
    return [dict(zip(columns, value)) for value in values]
