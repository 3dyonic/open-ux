from __future__ import annotations

import hashlib
import re
import secrets
from dataclasses import dataclass

from fastmcp.server.auth import AccessToken, TokenVerifier

from open_ux.settings import KEY_PREFIX, Settings
from open_ux.store import Store, get_store

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

__all__ = [
    "AuthError",
    "HashedKeyVerifier",
    "IssuedKey",
    "KEY_PREFIX",
    "generate_key",
    "hash_key",
    "normalize_email",
    "register",
    "revoke_account",
]


class AuthError(ValueError):
    pass


def normalize_email(email: str) -> str:
    value = email.strip().lower()
    if not _EMAIL_RE.match(value) or len(value) > 254:
        raise AuthError("A valid email is required to register.")
    return value


def hash_key(raw: str, pepper: str) -> str:
    return hashlib.sha256(f"{pepper}{raw}".encode("utf-8")).hexdigest()


def generate_key() -> str:
    return KEY_PREFIX + secrets.token_urlsafe(32)


@dataclass(frozen=True)
class IssuedKey:
    email: str
    key: str
    key_hash: str


def register(email: str, *, settings: Settings | None = None, store: Store | None = None) -> IssuedKey:
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
