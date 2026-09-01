from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from open_ux.auth import KEY_PREFIX, hash_key
from open_ux.settings import Settings
from open_ux.store import Store


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Soft hosted limits: ~60/min and ~1k/day per key_hash."""

    def __init__(self, app, settings: Settings, store: Store) -> None:
        super().__init__(app)
        self.settings = settings
        self.store = store

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path.rstrip("/") != "/mcp":
            return await call_next(request)
        header = request.headers.get("authorization") or ""
        if not header.lower().startswith("bearer "):
            return await call_next(request)
        token = header.split(" ", 1)[1].strip()
        if not token.startswith(KEY_PREFIX):
            return await call_next(request)
        digest = hash_key(token, self.settings.pepper)
        if not self.store.lookup_key(digest):
            return await call_next(request)
        ok, window = self.store.consume_rate(digest)
        if not ok:
            return JSONResponse(
                {"error": "rate_limited", "window": window},
                status_code=429,
            )
        return await call_next(request)
