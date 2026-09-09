from __future__ import annotations

import os

import uvicorn
from starlette.middleware import Middleware

from open_ux.health import HealthErrorMiddleware
from open_ux.rate_limit import RateLimitMiddleware
from open_ux.server import create_mcp, server_error_response
from open_ux.settings import Settings
from open_ux.store import get_store


def build_app():
    mcp = create_mcp(hosted=True)
    settings = Settings.load(hosted=True)
    store = get_store(settings)
    return mcp.http_app(
        path="/mcp",
        stateless_http=True,
        transport="http",
        middleware=[
            Middleware(RateLimitMiddleware, settings=settings, store=store),
            Middleware(
                HealthErrorMiddleware,
                state=mcp.health_state,
                render_500=server_error_response,
            ),
        ],
    )


def serve_http(*, host: str, port: int) -> None:
    uvicorn.run(
        "open_ux.http_app:app",
        host=host,
        port=port,
        proxy_headers=True,
        factory=False,
    )


# ASGI entry for uvicorn / Fly / Railway: `open_ux.http_app:app`
app = build_app()
