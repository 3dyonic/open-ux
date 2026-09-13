from __future__ import annotations

import base64
import hashlib
import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

from open_ux.settings import RATE_PER_DAY, RATE_PER_MINUTE, RETENTION_DAYS, Settings

_local = threading.local()

WAITLIST_PAGE_SIZE = 100
CALLERS_PAGE_SIZE = 100
SESSION_GAP_MINUTES = 30


def content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _encode_keyset_cursor(created_at: str, row_id: int) -> str:
    raw = f"{created_at}|{row_id}".encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def _decode_keyset_cursor(cursor: str) -> tuple[str, int] | None:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8")
        created_at, row_id = raw.rsplit("|", 1)
        return created_at, int(row_id)
    except (ValueError, UnicodeDecodeError, base64.binascii.Error):
        return None


def _encode_str_cursor(sort_key: str, tie_key: str) -> str:
    raw = f"{sort_key}|{tie_key}".encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def _decode_str_cursor(cursor: str) -> tuple[str, str] | None:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8")
        sort_key, tie_key = raw.rsplit("|", 1)
        return sort_key, tie_key
    except (ValueError, UnicodeDecodeError, base64.binascii.Error):
        return None


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
                    target_id TEXT,
                    req_offset INTEGER,
                    req_limit INTEGER,
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
            existing_cols = {
                row["name"]
                for row in cur.execute("PRAGMA table_info(telemetry)").fetchall()
            }
            for column, ddl in (
                ("target_id", "ALTER TABLE telemetry ADD COLUMN target_id TEXT"),
                ("req_offset", "ALTER TABLE telemetry ADD COLUMN req_offset INTEGER"),
                ("req_limit", "ALTER TABLE telemetry ADD COLUMN req_limit INTEGER"),
            ):
                if column not in existing_cols:
                    cur.execute(ddl)

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

    def list_waitlist(
        self, *, limit: int = WAITLIST_PAGE_SIZE, before: str | None = None
    ) -> dict[str, Any]:
        """Waitlist emails newest first, keyset-paged. Email and created_at only.

        No OFFSET: cost stays O(log n + limit) at any page depth. `before` is an
        opaque cursor from a previous page's `next_cursor`; a missing/invalid
        cursor just returns the first page.
        """
        limit = max(1, min(limit, WAITLIST_PAGE_SIZE))
        where = ""
        params: list[Any] = []
        cursor = _decode_keyset_cursor(before) if before else None
        if cursor is not None:
            cursor_created_at, cursor_id = cursor
            where = "WHERE (created_at < ?) OR (created_at = ? AND id < ?)"
            params.extend([cursor_created_at, cursor_created_at, cursor_id])
        params.append(limit + 1)
        with self.cursor() as cur:
            rows = cur.execute(
                f"SELECT id, email, created_at FROM waitlist {where} "
                "ORDER BY created_at DESC, id DESC LIMIT ?",
                params,
            ).fetchall()
        has_more = len(rows) > limit
        rows = rows[:limit]
        next_cursor = (
            _encode_keyset_cursor(rows[-1]["created_at"], rows[-1]["id"])
            if has_more and rows
            else None
        )
        return {
            "items": [{"email": r["email"], "created_at": r["created_at"]} for r in rows],
            "next_cursor": next_cursor,
        }

    def list_invites(
        self, *, limit: int = WAITLIST_PAGE_SIZE, before: str | None = None
    ) -> dict[str, Any]:
        """Issued invites newest first, keyset-paged. No token — issued/expiry/redeemed only.

        One row per issue_invite call; re-approving the same email adds a new
        row rather than replacing the old one, so a redeemed or expired row
        stays visible as history.
        """
        limit = max(1, min(limit, WAITLIST_PAGE_SIZE))
        where = ""
        params: list[Any] = []
        cursor = _decode_keyset_cursor(before) if before else None
        if cursor is not None:
            cursor_created_at, cursor_id = cursor
            where = "WHERE (created_at < ?) OR (created_at = ? AND id < ?)"
            params.extend([cursor_created_at, cursor_created_at, cursor_id])
        params.append(limit + 1)
        with self.cursor() as cur:
            rows = cur.execute(
                f"SELECT id, email, created_at, expires_at, redeemed_at FROM invites {where} "
                "ORDER BY created_at DESC, id DESC LIMIT ?",
                params,
            ).fetchall()
        has_more = len(rows) > limit
        rows = rows[:limit]
        next_cursor = (
            _encode_keyset_cursor(rows[-1]["created_at"], rows[-1]["id"])
            if has_more and rows
            else None
        )
        return {
            "items": [
                {
                    "email": r["email"],
                    "created_at": r["created_at"],
                    "expires_at": r["expires_at"],
                    "redeemed_at": r["redeemed_at"],
                }
                for r in rows
            ],
            "next_cursor": next_cursor,
        }

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
        target_id: str | None = None,
        req_offset: int | None = None,
        req_limit: int | None = None,
    ) -> None:
        cutoff = _iso(_utcnow() - timedelta(days=RETENTION_DAYS))
        with self.cursor() as cur:
            cur.execute("DELETE FROM telemetry WHERE created_at < ?", (cutoff,))
            cur.execute(
                "INSERT INTO telemetry("
                "key_hash, tool, target_type, target_id, req_offset, req_limit, "
                "content_length, content_hash, guideline_ids, verdicts, created_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    key_hash,
                    tool,
                    target_type,
                    target_id,
                    req_offset,
                    req_limit,
                    content_length,
                    content_hash,
                    json.dumps(guideline_ids) if guideline_ids is not None else None,
                    json.dumps(verdicts) if verdicts is not None else None,
                    _iso(_utcnow()),
                ),
            )

    def consume_rate(
        self,
        key_hash: str,
        *,
        per_minute: int = RATE_PER_MINUTE,
        per_day: int = RATE_PER_DAY,
    ) -> tuple[bool, str | None]:
        now = _utcnow()
        minute = f"min:{now.strftime('%Y-%m-%dT%H:%M')}"
        day = f"day:{now.strftime('%Y-%m-%d')}"
        with self.cursor() as cur:
            for window, limit, label in (
                (minute, per_minute, "minute"),
                (day, per_day, "day"),
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

    def telemetry_summary(self, *, window_days: int = RETENTION_DAYS) -> dict[str, Any]:
        """Aggregate stats over the telemetry table, plus account/invite/waitlist counts.

        key_hash never appears in the output — only a count of distinct callers.
        """
        cutoff = _iso(_utcnow() - timedelta(days=window_days))
        with self.cursor() as cur:
            total_requests = cur.execute(
                "SELECT COUNT(*) AS n FROM telemetry WHERE created_at >= ?", (cutoff,)
            ).fetchone()["n"]
            unique_keys = cur.execute(
                "SELECT COUNT(DISTINCT key_hash) AS n FROM telemetry WHERE created_at >= ?",
                (cutoff,),
            ).fetchone()["n"]
            by_tool = cur.execute(
                "SELECT tool, COUNT(*) AS n FROM telemetry WHERE created_at >= ? "
                "GROUP BY tool ORDER BY n DESC, tool ASC",
                (cutoff,),
            ).fetchall()
            by_day = cur.execute(
                "SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS n FROM telemetry "
                "WHERE created_at >= ? GROUP BY day ORDER BY day ASC",
                (cutoff,),
            ).fetchall()
            guideline_rows = cur.execute(
                "SELECT guideline_ids FROM telemetry "
                "WHERE created_at >= ? AND guideline_ids IS NOT NULL",
                (cutoff,),
            ).fetchall()
            accounts = cur.execute("SELECT COUNT(*) AS n FROM accounts").fetchone()["n"]
            invites = cur.execute("SELECT COUNT(*) AS n FROM invites").fetchone()["n"]
            waitlist = cur.execute("SELECT COUNT(*) AS n FROM waitlist").fetchone()["n"]

        guideline_counts: dict[str, int] = {}
        for row in guideline_rows:
            try:
                ids = json.loads(row["guideline_ids"])
            except (TypeError, ValueError):
                continue
            for gid in ids or []:
                guideline_counts[gid] = guideline_counts.get(gid, 0) + 1
        top_guideline_ids = [
            {"id": gid, "count": n}
            for gid, n in sorted(
                guideline_counts.items(), key=lambda kv: (-kv[1], kv[0])
            )[:20]
        ]

        counted_by_day = {r["day"]: int(r["n"]) for r in by_day}
        today = _utcnow().date()
        requests_by_day = {
            (today - timedelta(days=offset)).isoformat(): 0
            for offset in range(window_days - 1, -1, -1)
        }
        requests_by_day.update(counted_by_day)

        return {
            "window_days": window_days,
            "total_requests": int(total_requests),
            "unique_keys": int(unique_keys),
            "requests_by_tool": {r["tool"]: int(r["n"]) for r in by_tool},
            "requests_by_day": requests_by_day,
            "top_guideline_ids": top_guideline_ids,
            "accounts": int(accounts),
            "invites": int(invites),
            "waitlist": int(waitlist),
        }

    def list_callers(
        self,
        *,
        limit: int = CALLERS_PAGE_SIZE,
        before: str | None = None,
        session_gap_minutes: int = SESSION_GAP_MINUTES,
    ) -> dict[str, Any]:
        """Per-key_hash rollup: session_count (gap-heuristic), call_count,
        first/last seen, and the target_id that key_hash hit most. Newest
        (by last_seen) first, keyset-paged. Never joined to email — key_hash
        only.
        """
        limit = max(1, min(limit, CALLERS_PAGE_SIZE))
        where = ""
        params: list[Any] = [session_gap_minutes]
        cursor = _decode_str_cursor(before) if before else None
        if cursor is not None:
            cursor_last_seen, cursor_key_hash = cursor
            where = "WHERE (agg.last_seen < ?) OR (agg.last_seen = ? AND agg.key_hash < ?)"
            params.extend([cursor_last_seen, cursor_last_seen, cursor_key_hash])
        params.append(limit + 1)
        query = f"""
            WITH ordered AS (
                SELECT key_hash, created_at, id,
                    LAG(created_at) OVER (PARTITION BY key_hash ORDER BY created_at, id) AS prev_at
                FROM telemetry
            ),
            agg AS (
                SELECT key_hash,
                    COUNT(*) AS call_count,
                    MIN(created_at) AS first_seen,
                    MAX(created_at) AS last_seen,
                    SUM(
                        CASE WHEN prev_at IS NULL
                            OR (julianday(created_at) - julianday(prev_at)) * 1440.0 > ?
                        THEN 1 ELSE 0 END
                    ) AS session_count
                FROM ordered
                GROUP BY key_hash
            ),
            target_counts AS (
                SELECT key_hash, target_id, COUNT(*) AS n
                FROM telemetry
                WHERE target_id IS NOT NULL
                GROUP BY key_hash, target_id
            ),
            ranked_targets AS (
                SELECT key_hash, target_id,
                    ROW_NUMBER() OVER (
                        PARTITION BY key_hash ORDER BY n DESC, target_id ASC
                    ) AS rn
                FROM target_counts
            )
            SELECT agg.key_hash, agg.call_count, agg.first_seen, agg.last_seen,
                agg.session_count, rt.target_id AS top_target
            FROM agg
            LEFT JOIN ranked_targets rt ON rt.key_hash = agg.key_hash AND rt.rn = 1
            {where}
            ORDER BY agg.last_seen DESC, agg.key_hash DESC
            LIMIT ?
        """
        with self.cursor() as cur:
            rows = cur.execute(query, params).fetchall()
        has_more = len(rows) > limit
        rows = rows[:limit]
        next_cursor = (
            _encode_str_cursor(rows[-1]["last_seen"], rows[-1]["key_hash"])
            if has_more and rows
            else None
        )
        return {
            "items": [
                {
                    "key_hash": r["key_hash"],
                    "session_count": int(r["session_count"]),
                    "call_count": int(r["call_count"]),
                    "first_seen": r["first_seen"],
                    "last_seen": r["last_seen"],
                    "top_target": r["top_target"],
                }
                for r in rows
            ],
            "next_cursor": next_cursor,
        }

    def get_caller_sessions(
        self,
        key_hash: str,
        *,
        limit: int = CALLERS_PAGE_SIZE,
        before: str | None = None,
        session_gap_minutes: int = SESSION_GAP_MINUTES,
    ) -> dict[str, Any]:
        """One caller's calls, grouped into sessions by an idle-gap heuristic
        (there is no real MCP session id on stateless HTTP). Newest session
        first; `before` pages by session index, not by raw row.
        """
        limit = max(1, min(limit, CALLERS_PAGE_SIZE))
        with self.cursor() as cur:
            rows = cur.execute(
                "SELECT tool, target_type, target_id, req_offset, req_limit, "
                "verdicts, created_at FROM telemetry WHERE key_hash = ? "
                "ORDER BY created_at ASC, id ASC",
                (key_hash,),
            ).fetchall()

        sessions: list[dict[str, Any]] = []
        gap = timedelta(minutes=session_gap_minutes)
        prev_at: datetime | None = None
        for row in rows:
            created_at = datetime.fromisoformat(row["created_at"])
            step = {
                "tool": row["tool"],
                "target_type": row["target_type"],
                "target_id": row["target_id"],
                "req_offset": row["req_offset"],
                "req_limit": row["req_limit"],
                "verdicts": json.loads(row["verdicts"]) if row["verdicts"] else None,
                "created_at": row["created_at"],
            }
            if prev_at is None or (created_at - prev_at) > gap:
                started_at = row["created_at"]
                session_id = "sess_" + hashlib.sha256(
                    f"{key_hash}|{started_at}".encode("utf-8")
                ).hexdigest()[:8]
                sessions.append(
                    {
                        "session_id": session_id,
                        "started_at": started_at,
                        "ended_at": started_at,
                        "call_count": 0,
                        "steps": [],
                    }
                )
            sessions[-1]["ended_at"] = row["created_at"]
            sessions[-1]["call_count"] += 1
            sessions[-1]["steps"].append(step)
            prev_at = created_at

        for session in sessions:
            session["tool_sequence"] = "→".join(s["tool"] for s in session["steps"])
            started = datetime.fromisoformat(session["started_at"])
            ended = datetime.fromisoformat(session["ended_at"])
            session["duration_seconds"] = round((ended - started).total_seconds())
            session_target_counts: dict[str, int] = {}
            for s in session["steps"]:
                if s["target_id"]:
                    session_target_counts[s["target_id"]] = (
                        session_target_counts.get(s["target_id"], 0) + 1
                    )
            session["target_id"] = (
                sorted(session_target_counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
                if session_target_counts
                else None
            )

        target_counts: dict[str, int] = {}
        for row in rows:
            if row["target_id"]:
                target_counts[row["target_id"]] = target_counts.get(row["target_id"], 0) + 1
        top_target = (
            sorted(target_counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
            if target_counts
            else None
        )
        summary = {
            "key_hash": key_hash,
            "call_count": len(rows),
            "session_count": len(sessions),
            "first_seen": rows[0]["created_at"] if rows else None,
            "last_seen": rows[-1]["created_at"] if rows else None,
            "top_target": top_target,
        }

        sessions.reverse()  # newest session first
        start_index = 0
        if before is not None:
            for i, session in enumerate(sessions):
                if session["session_id"] == before:
                    start_index = i + 1
                    break
        page = sessions[start_index : start_index + limit]
        next_cursor = (
            page[-1]["session_id"]
            if start_index + limit < len(sessions) and page
            else None
        )
        return {"summary": summary, "items": page, "next_cursor": next_cursor}


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
