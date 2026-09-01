from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

from open_ux.settings import RATE_PER_DAY, RATE_PER_MINUTE, RETENTION_DAYS, Settings

_local = threading.local()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()


class Store:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = getattr(_local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self.path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            _local.conn = conn
        return conn

    @contextmanager
    def cursor(self) -> Iterator[sqlite3.Cursor]:
        conn = self._connect()
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def _init(self) -> None:
        with self.cursor() as cur:
            cur.executescript(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY,
                    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
                    key_hash TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    revoked_at TEXT
                );
                CREATE TABLE IF NOT EXISTS telemetry (
                    id INTEGER PRIMARY KEY,
                    key_hash TEXT NOT NULL,
                    tool TEXT NOT NULL,
                    target_type TEXT,
                    content_length INTEGER,
                    content_hash TEXT,
                    guideline_ids TEXT,
                    verdicts TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS rate_buckets (
                    key_hash TEXT NOT NULL,
                    window TEXT NOT NULL,
                    count INTEGER NOT NULL,
                    PRIMARY KEY (key_hash, window)
                );
                CREATE TABLE IF NOT EXISTS waitlist (
                    id INTEGER PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS invites (
                    id INTEGER PRIMARY KEY,
                    email TEXT NOT NULL,
                    token_hash TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    redeemed_at TEXT
                );
                CREATE INDEX IF NOT EXISTS telemetry_created_at ON telemetry(created_at);
                CREATE INDEX IF NOT EXISTS telemetry_key_hash ON telemetry(key_hash);
                CREATE INDEX IF NOT EXISTS invites_email ON invites(email);
                CREATE INDEX IF NOT EXISTS invites_token_hash ON invites(token_hash);
                """
            )

    def issue_key(self, email: str, key_hash: str) -> None:
        now = _iso(_utcnow())
        with self.cursor() as cur:
            cur.execute(
                "INSERT INTO accounts(email, created_at) VALUES (?, ?) "
                "ON CONFLICT(email) DO NOTHING",
                (email, now),
            )
            account_id = cur.execute(
                "SELECT id FROM accounts WHERE email = ?", (email,)
            ).fetchone()["id"]
            cur.execute(
                "UPDATE api_keys SET revoked_at = ? "
                "WHERE account_id = ? AND revoked_at IS NULL",
                (now, account_id),
            )
            cur.execute(
                "INSERT INTO api_keys(account_id, key_hash, created_at) VALUES (?, ?, ?)",
                (account_id, key_hash, now),
            )

    def add_waitlist(self, email: str) -> None:
        now = _iso(_utcnow())
        with self.cursor() as cur:
            cur.execute(
                "INSERT INTO waitlist(email, created_at) VALUES (?, ?) "
                "ON CONFLICT(email) DO NOTHING",
                (email, now),
            )

    def waitlist_has(self, email: str) -> bool:
        with self.cursor() as cur:
            row = cur.execute(
                "SELECT 1 FROM waitlist WHERE email = ?", (email,)
            ).fetchone()
        return row is not None

    def waitlist_count(self) -> int:
        with self.cursor() as cur:
            row = cur.execute("SELECT COUNT(*) AS n FROM waitlist").fetchone()
        return int(row["n"])

    def issue_invite(self, email: str, token_hash: str, expires_at: str) -> None:
        now = _iso(_utcnow())
        with self.cursor() as cur:
            cur.execute(
                "UPDATE invites SET expires_at = ? "
                "WHERE email = ? AND redeemed_at IS NULL AND expires_at > ?",
                (now, email, now),
            )
            cur.execute(
                "INSERT INTO invites(email, token_hash, created_at, expires_at) "
                "VALUES (?, ?, ?, ?)",
                (email, token_hash, now, expires_at),
            )

    def create_invite(self, email: str, token_hash: str, expires_at: str) -> None:
        """Insert one invite row without expiring others — tests / expiry fixtures."""
        now = _iso(_utcnow())
        with self.cursor() as cur:
            cur.execute(
                "INSERT INTO invites(email, token_hash, created_at, expires_at) "
                "VALUES (?, ?, ?, ?)",
                (email, token_hash, now, expires_at),
            )

    def redeem_invite(self, token_hash: str, key_hash: str) -> str | None:
        """Burn a valid invite and mint a hashed key. Returns email, or None if invalid."""
        now = _iso(_utcnow())
        with self.cursor() as cur:
            row = cur.execute(
                "SELECT email, expires_at, redeemed_at FROM invites WHERE token_hash = ?",
                (token_hash,),
            ).fetchone()
            if row is None or row["redeemed_at"] is not None or row["expires_at"] <= now:
                return None
            cur.execute(
                "UPDATE invites SET redeemed_at = ? "
                "WHERE token_hash = ? AND redeemed_at IS NULL",
                (now, token_hash),
            )
            if cur.rowcount != 1:
                return None
            email = row["email"]
            cur.execute(
                "INSERT INTO accounts(email, created_at) VALUES (?, ?) "
                "ON CONFLICT(email) DO NOTHING",
                (email, now),
            )
            account_id = cur.execute(
                "SELECT id FROM accounts WHERE email = ?", (email,)
            ).fetchone()["id"]
            cur.execute(
                "UPDATE api_keys SET revoked_at = ? "
                "WHERE account_id = ? AND revoked_at IS NULL",
                (now, account_id),
            )
            cur.execute(
                "INSERT INTO api_keys(account_id, key_hash, created_at) VALUES (?, ?, ?)",
                (account_id, key_hash, now),
            )
            return email

    def lookup_key(self, key_hash: str) -> dict[str, Any] | None:
        with self.cursor() as cur:
            row = cur.execute(
                "SELECT k.key_hash, k.account_id, a.email "
                "FROM api_keys k JOIN accounts a ON a.id = k.account_id "
                "WHERE k.key_hash = ? AND k.revoked_at IS NULL",
                (key_hash,),
            ).fetchone()
        return dict(row) if row else None

    def delete_account(self, email: str) -> bool:
        with self.cursor() as cur:
            hashes = [
                r["key_hash"]
                for r in cur.execute(
                    "SELECT k.key_hash FROM api_keys k "
                    "JOIN accounts a ON a.id = k.account_id WHERE a.email = ?",
                    (email,),
                ).fetchall()
            ]
            if not hashes:
                exists = cur.execute(
                    "SELECT 1 FROM accounts WHERE email = ?", (email,)
                ).fetchone()
                if not exists:
                    return False
            for h in hashes:
                cur.execute("DELETE FROM telemetry WHERE key_hash = ?", (h,))
                cur.execute("DELETE FROM rate_buckets WHERE key_hash = ?", (h,))
            cur.execute("DELETE FROM accounts WHERE email = ?", (email,))
        return True

    def record_telemetry(
        self,
        *,
        key_hash: str,
        tool: str,
        target_type: str | None,
        content_length: int | None,
        content_hash: str | None,
        guideline_ids: list[str] | None,
        verdicts: dict[str, Any] | None,
    ) -> None:
        cutoff = _iso(_utcnow() - timedelta(days=RETENTION_DAYS))
        with self.cursor() as cur:
            cur.execute("DELETE FROM telemetry WHERE created_at < ?", (cutoff,))
            cur.execute(
                "INSERT INTO telemetry("
                "key_hash, tool, target_type, content_length, content_hash, "
                "guideline_ids, verdicts, created_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    key_hash,
                    tool,
                    target_type,
                    content_length,
                    content_hash,
                    json.dumps(guideline_ids) if guideline_ids is not None else None,
                    json.dumps(verdicts) if verdicts is not None else None,
                    _iso(_utcnow()),
                ),
            )

    def consume_rate(self, key_hash: str) -> tuple[bool, str | None]:
        now = _utcnow()
        minute = f"min:{now.strftime('%Y-%m-%dT%H:%M')}"
        day = f"day:{now.strftime('%Y-%m-%d')}"
        with self.cursor() as cur:
            for window, limit, label in (
                (minute, RATE_PER_MINUTE, "minute"),
                (day, RATE_PER_DAY, "day"),
            ):
                row = cur.execute(
                    "SELECT count FROM rate_buckets WHERE key_hash = ? AND window = ?",
                    (key_hash, window),
                ).fetchone()
                count = int(row["count"]) if row else 0
                if count >= limit:
                    return False, label
                if row:
                    cur.execute(
                        "UPDATE rate_buckets SET count = count + 1 "
                        "WHERE key_hash = ? AND window = ?",
                        (key_hash, window),
                    )
                else:
                    cur.execute(
                        "INSERT INTO rate_buckets(key_hash, window, count) VALUES (?, ?, 1)",
                        (key_hash, window),
                    )
        return True, None

    def dump_text(self) -> str:
        """Full sqlite dump as text — used by privacy tests."""
        conn = self._connect()
        return "\n".join(conn.iterdump())

    def telemetry_rows(self) -> list[dict[str, Any]]:
        with self.cursor() as cur:
            rows = cur.execute("SELECT * FROM telemetry").fetchall()
        return [dict(r) for r in rows]


_store: Store | None = None


def get_store(settings: Settings | None = None) -> Store:
    global _store
    settings = settings or Settings.load()
    if _store is None or _store.path != settings.database_path:
        _store = Store(settings.database_path)
    return _store


def reset_store_for_tests() -> None:
    global _store
    _store = None
    conn = getattr(_local, "conn", None)
    if conn is not None:
        conn.close()
        _local.conn = None
