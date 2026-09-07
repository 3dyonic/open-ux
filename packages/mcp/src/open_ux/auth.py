from __future__ import annotations

import hashlib
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from fastmcp.server.auth import AccessToken, TokenVerifier

from open_ux.settings import INVITE_PREFIX, INVITE_TTL_DAYS, KEY_PREFIX, Settings
from open_ux.store import Store, get_store


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()

# ASCII addr-spec only. Rejects markup, quotes, whitespace, and control
# octets so a waitlist email cannot carry script or header injection.
_EMAIL_MAX_RAW = 320
_EMAIL_MAX = 254
_EMAIL_RE = re.compile(
    r"^[a-z0-9](?:[a-z0-9._+-]{0,62}[a-z0-9])?"
    r"@(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)
_INVITE_TOKEN_RE = re.compile(r"^inv_[A-Za-z0-9_-]{16,64}$")
_INVITE_TOKEN_MAX_RAW = 80

__all__ = [
    "AuthError",
    "HashedKeyVerifier",
    "IssuedInvite",
    "IssuedKey",
    "INVITE_PREFIX",
    "KEY_PREFIX",
    "approve_invite",
    "generate_key",
    "hash_key",
    "normalize_email",
    "normalize_invite_token",
    "redeem_invite",
    "register",
    "request_invite",
    "revoke_account",
]


class AuthError(ValueError):
    pass


def normalize_email(email: object) -> str:
    if not isinstance(email, str) or len(email) > _EMAIL_MAX_RAW:
        raise AuthError("A valid email is required.")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in email):
        raise AuthError("A valid email is required.")
    value = email.strip().lower()
    if ".." in value or len(value) > _EMAIL_MAX or not _EMAIL_RE.fullmatch(value):
        raise AuthError("A valid email is required.")
    return value


def normalize_invite_token(token: object) -> str:
    if not isinstance(token, str) or len(token) > _INVITE_TOKEN_MAX_RAW:
        raise AuthError("Invite invalid or already used. Request a new one if needed.")
    raw = token.strip()
    if not _INVITE_TOKEN_RE.fullmatch(raw):
        raise AuthError("Invite invalid or already used. Request a new one if needed.")
    return raw


def hash_key(raw: str, pepper: str) -> str:
    return hashlib.sha256(f"{pepper}{raw}".encode("utf-8")).hexdigest()


def generate_key() -> str:
    return KEY_PREFIX + secrets.token_urlsafe(32)


def generate_invite_token() -> str:
    return INVITE_PREFIX + secrets.token_urlsafe(24)


@dataclass(frozen=True)
class IssuedKey:
    email: str
    key: str
    key_hash: str


@dataclass(frozen=True)
class IssuedInvite:
    email: str
    token: str
    token_hash: str
    expires_at: str
    redeem_url: str


def request_invite(
    email: str, *, settings: Settings | None = None, store: Store | None = None
) -> str:
    settings = settings or Settings.load()
    store = store or get_store(settings)
    normalized = normalize_email(email)
    store.add_waitlist(normalized)
    return normalized


def approve_invite(
    email: str, *, settings: Settings | None = None, store: Store | None = None
) -> IssuedInvite:
    settings = settings or Settings.load()
    store = store or get_store(settings)
    normalized = normalize_email(email)
    raw = generate_invite_token()
    digest = hash_key(raw, settings.pepper)
    expires_at = _iso(_utcnow() + timedelta(days=INVITE_TTL_DAYS))
    store.issue_invite(normalized, digest, expires_at)
    base = settings.public_url
    path = f"/invite/redeem?token={quote(raw, safe='')}"
    redeem_url = f"{base}{path}" if base else path
    return IssuedInvite(
        email=normalized,
        token=raw,
        token_hash=digest,
        expires_at=expires_at,
        redeem_url=redeem_url,
    )


def redeem_invite(
    token: str, *, settings: Settings | None = None, store: Store | None = None
) -> IssuedKey:
    settings = settings or Settings.load()
    store = store or get_store(settings)
    raw = normalize_invite_token(token)
    digest = hash_key(raw, settings.pepper)
    key_raw = generate_key()
    key_digest = hash_key(key_raw, settings.pepper)
    email = store.redeem_invite(digest, key_digest)
    if not email:
        raise AuthError("Invite invalid or already used. Request a new one if needed.")
    return IssuedKey(email=email, key=key_raw, key_hash=key_digest)


def register(email: str, *, settings: Settings | None = None, store: Store | None = None) -> IssuedKey:
    """Mint a hashed key (tests / account delete). HTTP invite redeem is the hosted path."""
    settings = settings or Settings.load()
    store = store or get_store(settings)
    normalized = normalize_email(email)
    raw = generate_key()
    digest = hash_key(raw, settings.pepper)
    store.issue_key(normalized, digest)
    return IssuedKey(email=normalized, key=raw, key_hash=digest)


def revoke_account(
    email: str, *, settings: Settings | None = None, store: Store | None = None
) -> bool:
    settings = settings or Settings.load()
    store = store or get_store(settings)
    return store.delete_account(normalize_email(email))


class HashedKeyVerifier(TokenVerifier):
    """Bearer `uxmcp_` keys, hashed at rest. Never compare plaintext."""

    def __init__(self, settings: Settings, store: Store) -> None:
        super().__init__()
        self.settings = settings
        self.store = store

    async def verify_token(self, token: str) -> AccessToken | None:
        if not token or not token.startswith(KEY_PREFIX):
            return None
        digest = hash_key(token, self.settings.pepper)
        row = self.store.lookup_key(digest)
        if not row:
            return None
        return AccessToken(
            token=token,
            client_id=digest,
            scopes=["open-ux"],
            claims={"key_hash": digest},
        )
