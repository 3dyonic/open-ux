"""Health status for /health and /health.json. HTTP stays 200; ok is computed."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Lock
from collections.abc import Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from open_ux import __version__
from open_ux.catalog import Catalog, catalog_status

_SKIP_PATHS = frozenset({"/health", "/health.json"})
_PATH_MAX = 200


@dataclass(frozen=True)
class LastError:
    status: int
    path: str
    at: str

    def as_dict(self) -> dict[str, Any]:
        return {"status": self.status, "path": self.path, "at": self.at}


class HealthState:
    """Process-local last 5xx. Restart clears it."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._error: LastError | None = None

    def note_server_error(self, *, status: int, path: str) -> None:
        if status < 500:
            return
        clean = _clean_path(path)
        if clean in _SKIP_PATHS:
            return
        now = datetime.now(UTC).replace(microsecond=0).isoformat()
        with self._lock:
            self._error = LastError(status=status, path=clean, at=now)

    def snapshot(self) -> dict[str, Any] | None:
        with self._lock:
            return None if self._error is None else self._error.as_dict()


class HealthErrorMiddleware(BaseHTTPMiddleware):
    """Record 5xx responses and unhandled exceptions onto HealthState."""

    def __init__(
        self,
        app,
        state: HealthState,
        render_500: Callable[[str], Response] | None = None,
    ) -> None:
        super().__init__(app)
        self.state = state
        self.render_500 = render_500

    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            response = await call_next(request)
        except Exception:
            self.state.note_server_error(status=500, path=request.url.path)
            if self.render_500 is not None:
                try:
                    return self.render_500(request.url.path)
                except Exception:
                    return Response(
                        "This page could not be loaded.",
                        status_code=500,
                        media_type="text/plain; charset=utf-8",
                    )
            raise
        if response.status_code >= 500:
            self.state.note_server_error(
                status=response.status_code, path=request.url.path
            )
        return response


def _clean_path(path: str) -> str:
    raw = (path or "/").split("?", 1)[0]
    if not raw.startswith("/"):
        raw = f"/{raw}"
    return raw[:_PATH_MAX]


def _copy(*, catalog_ok: bool, error: dict[str, Any] | None) -> tuple[str, str]:
    if error:
        return (
            "Error: a request failed",
            "A page could not be loaded. Try that page again.",
        )
    if not catalog_ok:
        return (
            "Error: catalog is not loaded",
            "The host is up. The catalog has no cited rules yet. Browse the catalog when rules land.",
        )
    return (
        "Success: host and catalog are up",
        "The hosted service is running. The catalog is loaded.",
    )


def health_payload(
    catalog: Catalog,
    *,
    hosted: bool,
    state: HealthState | None = None,
) -> dict[str, Any]:
    catalog_info = catalog_status(catalog)
    catalog_ok = catalog_info["status"] == "ok"
    error = state.snapshot() if state is not None else None
    ok = catalog_ok and error is None
    title, body = _copy(catalog_ok=catalog_ok, error=error)
    return {
        "ok": ok,
        "name": "Open UX",
        "hosted": hosted,
        "version": __version__,
        "catalog": catalog_info,
        "error": error,
        "title": title,
        "body": body,
    }
