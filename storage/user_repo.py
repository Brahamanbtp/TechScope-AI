import hashlib
import hmac
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

from storage.database import connect, execute, rows
from storage.schema import DB_PATH, init_db


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"{salt.hex()}${digest.hex()}"


def _verify_password(password: str, encoded: str) -> bool:
    salt_hex, digest_hex = encoded.split("$", 1)
    candidate = _hash_password(password, bytes.fromhex(salt_hex)).split("$", 1)[1]
    return hmac.compare_digest(candidate, digest_hex)


def create_user(username: str, password: str, role: str = "user") -> dict:
    init_db()
    created_at = _now().isoformat()
    with connect(DB_PATH) as connection:
        cursor = execute(
            connection,
            "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
            (username, _hash_password(password), role, created_at),
        )
        user_id = getattr(cursor, "lastrowid", None)
        if user_id is None:
            user_id = execute(connection, "SELECT id FROM users WHERE username = ?", (username,)).fetchone()[0]
    return {"id": user_id, "username": username, "role": role}


def count_users() -> int:
    init_db()
    with connect(DB_PATH) as connection:
        return execute(connection, "SELECT COUNT(*) FROM users").fetchone()[0]


def authenticate_user(username: str, password: str) -> dict | None:
    init_db()
    with connect(DB_PATH) as connection:
        user = next(iter(rows(execute(connection, "SELECT * FROM users WHERE username = ? AND active = 1", (username,)))), None)
    if not user or not _verify_password(password, user["password_hash"]):
        return None
    return user


def create_session(user_id: int, hours: int = 24) -> str:
    init_db()
    token = secrets.token_urlsafe(32)
    now = _now()
    with connect(DB_PATH) as connection:
        execute(
            connection,
            "INSERT INTO sessions (token_hash, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (hashlib.sha256(token.encode()).hexdigest(), user_id, (now + timedelta(hours=hours)).isoformat(), now.isoformat()),
        )
    return token


def get_session(token: str) -> dict | None:
    init_db()
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    with connect(DB_PATH) as connection:
        user = next(iter(rows(execute(
            connection,
            "SELECT users.id, users.username, users.role FROM sessions JOIN users ON users.id = sessions.user_id WHERE sessions.token_hash = ? AND sessions.expires_at > ? AND users.active = 1",
            (token_hash, _now().isoformat()),
        ))), None)
    return user