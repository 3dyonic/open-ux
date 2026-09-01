from __future__ import annotations

import secrets
from typing import Any, Literal

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_access_token
from pydantic import BaseModel, Field
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, Response

from open_ux.audit import audit as run_audit
from open_ux.auth import (
    AuthError,
    HashedKeyVerifier,
    approve_invite,
    hash_key,
    redeem_invite,
    request_invite,
)
from open_ux.catalog import EMPTY_NOTE, content_hash, get_by_id, list_index, load_catalog
from open_ux.invite_page import REQUEST_HTML, REQUESTED_HTML, REDEEM_HTML
from open_ux.landing import LANDING_HTML
from open_ux.settings import Settings
from open_ux.store import get_store

class AuditTarget(BaseModel):
    type: Literal["html", "jsx", "description"]
    content: str = Field(description="Snippet to audit. Never persisted raw.")


def _key_hash_or_none() -> str | None:
    token = get_access_token()
    if token is None:
        return None
    claims = getattr(token, "claims", None) or {}
    return claims.get("key_hash") or getattr(token, "client_id", None)


def _maybe_telemetry(
    settings: Settings,
    *,
    tool: str,
    target_type: str | None = None,
    content: str | None = None,
    guideline_ids: list[str] | None = None,
    verdicts: dict[str, Any] | None = None,
) -> None:
    if not settings.telemetry:
        return
    key_hash = _key_hash_or_none()
    if not key_hash:
        return
    length = len(content.encode("utf-8")) if content is not None else None
    digest = content_hash(content) if content is not None else None
    get_store(settings).record_telemetry(
        key_hash=key_hash,
        tool=tool,
        target_type=target_type,
        content_length=length,
        content_hash=digest,
        guideline_ids=guideline_ids,
        verdicts=verdicts,
    )


def _admin_authorized(request: Request, settings: Settings) -> bool:
    expected = settings.admin_token
    if not expected:
        return False
    header = request.headers.get("authorization") or ""
    if not header.lower().startswith("bearer "):
        return False
    got = header.split(" ", 1)[1].strip()
    if not got:
        return False
    return secrets.compare_digest(
        hash_key("admin:" + got, settings.pepper),
        hash_key("admin:" + expected, settings.pepper),
    )


async def _waitlist_request(request: Request, *, settings: Settings, store) -> Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    email = ""
    if isinstance(body, dict):
        email = str(body.get("email") or "")
    try:
        normalized = request_invite(email, settings=settings, store=store)
    except AuthError:
        return JSONResponse(
            {"error": "Enter a valid email to request an invite."},
            status_code=400,
        )
    return JSONResponse({"ok": True, "email": normalized, "status": "waitlisted"})


def create_mcp(*, hosted: bool) -> FastMCP:
    settings = Settings.load(hosted=hosted)
    store = get_store(settings)
    catalog = load_catalog(settings)

    auth = HashedKeyVerifier(settings, store) if hosted else None
    mcp = FastMCP(
        name="Open UX",
        instructions=(
            "Open UX: cited UX rules agents audit against. "
            "Tools: list_guidelines, search_guidelines, get_guideline, audit. "
            "Hybrid C — no server LLM. "
            "list/search return a paged index (id, title, jobs, lane) only. "
            "audit requires jobs or guideline_ids; never the whole catalog. "
            "If the catalog is empty, return empty/incomplete; do not invent rules."
        ),
        version="0.1.0",
        website_url="https://github.com/3dyonic/open-ux",
        auth=auth,
    )

    @mcp.tool
    def list_guidelines(
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Paged index only: id, title, jobs, lane. No rule bodies."""
        items, total = list_index(catalog, limit=limit, offset=offset)
        _maybe_telemetry(settings, tool="list_guidelines")
        payload: dict[str, Any] = {
            "guidelines": items,
            "count": len(items),
            "total": total,
            "limit": limit,
            "offset": offset,
            "catalog": {
                "status": "empty" if catalog.empty else "ok",
                "guideline_count": len(catalog.guidelines),
                "version": catalog.version,
            },
        }
        if catalog.empty:
            payload["note"] = EMPTY_NOTE
        return payload

    @mcp.tool
    def search_guidelines(
        query: str | None = None,
        jobs: str | None = None,
        lane: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Search the paged index by query and/or jobs and/or lane. No rule bodies."""
        items, total = list_index(
            catalog,
            query=query,
            jobs=jobs,
            lane=lane,
            limit=limit,
            offset=offset,
        )
        _maybe_telemetry(settings, tool="search_guidelines")
        payload: dict[str, Any] = {
            "guidelines": items,
            "count": len(items),
            "total": total,
            "limit": limit,
            "offset": offset,
            "catalog": {
                "status": "empty" if catalog.empty else "ok",
                "guideline_count": len(catalog.guidelines),
                "version": catalog.version,
            },
        }
        if catalog.empty:
            payload["note"] = EMPTY_NOTE
        return payload

    @mcp.tool
    def get_guideline(id: str) -> dict[str, Any]:
        """Fetch one full guideline body by id. Does not invent missing rules."""
        found = get_by_id(catalog, id)
        _maybe_telemetry(
            settings,
            tool="get_guideline",
            guideline_ids=[id],
        )
        if found is None:
            return {
                "found": False,
                "id": id,
                "error": (
                    f"No guideline with id {id!r}."
                    + (" " + EMPTY_NOTE if catalog.empty else "")
                ),
            }
        return {"found": True, "guideline": found}

    @mcp.tool
    def audit(
        target: AuditTarget,
        guideline_ids: list[str] | None = None,
        jobs: str | None = None,
    ) -> dict[str, Any]:
        """Audit html | jsx | description. Deterministic Hybrid C. No server LLM.

        Requires jobs or guideline_ids — never runs the whole catalog.
        reasons[] reuse catalog pass_when / fail_when plus the rule id.
        Raw content is never persisted (length + optional hash only).
        """
        result = run_audit(
            catalog,
            target_type=target.type,
            content=target.content,
            guideline_ids=guideline_ids,
            jobs=jobs,
        )
        _maybe_telemetry(
            settings,
            tool="audit",
            target_type=target.type,
            content=target.content,
            guideline_ids=guideline_ids
            or [r.get("guideline_id") for r in result.get("results") or [] if r.get("guideline_id")],
            verdicts=result.get("summary"),
        )
        return result

    @mcp.custom_route("/", methods=["GET"])
    async def landing(_request: Request) -> Response:
        return HTMLResponse(LANDING_HTML)

    @mcp.custom_route("/health", methods=["GET"])
    async def health(_request: Request) -> Response:
        return JSONResponse(
            {
                "ok": True,
                "name": "Open UX",
                "hosted": hosted,
                "catalog": {
                    "status": "empty" if catalog.empty else "ok",
                    "guideline_count": len(catalog.guidelines),
                    "version": catalog.version,
                },
            }
        )

    @mcp.custom_route("/invite", methods=["GET"])
    async def invite_request_page(_request: Request) -> Response:
        return HTMLResponse(REQUEST_HTML)

    @mcp.custom_route("/invite/request", methods=["POST"])
    async def invite_request_route(request: Request) -> Response:
        if not hosted:
            return JSONResponse(
                {"error": "Invites are hosted-only. Self-host stdio needs no key."},
                status_code=400,
            )
        return await _waitlist_request(request, settings=settings, store=store)

    @mcp.custom_route("/invite/requested", methods=["GET"])
    async def invite_requested_page(_request: Request) -> Response:
        return HTMLResponse(REQUESTED_HTML)

    @mcp.custom_route("/invite/redeem", methods=["GET", "POST"])
    async def invite_redeem_route(request: Request) -> Response:
        if request.method == "GET":
            return HTMLResponse(REDEEM_HTML)
        if not hosted:
            return JSONResponse(
                {"error": "Invites are hosted-only. Self-host stdio needs no key."},
                status_code=400,
            )
        try:
            body = await request.json()
        except Exception:
            body = {}
        token = ""
        if isinstance(body, dict):
            token = str(body.get("token") or "")
        try:
            issued = redeem_invite(token, settings=settings, store=store)
        except AuthError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        return JSONResponse(
            {
                "key": issued.key,
                "prefix": "uxmcp_",
                "email": issued.email,
                "note": "Store this bearer in client settings. It is not shown again.",
            }
        )

    @mcp.custom_route("/admin/invite/waitlist", methods=["GET"])
    async def admin_invite_waitlist(request: Request) -> Response:
        if not hosted:
            return JSONResponse({"error": "Hosted-only."}, status_code=400)
        if not _admin_authorized(request, settings):
            return JSONResponse({"error": "Unauthorized."}, status_code=401)
        return JSONResponse({"items": store.list_waitlist()})

    @mcp.custom_route("/admin/invite/approve", methods=["POST"])
    async def admin_invite_approve(request: Request) -> Response:
        if not hosted:
            return JSONResponse({"error": "Hosted-only."}, status_code=400)
        if not _admin_authorized(request, settings):
            return JSONResponse({"error": "Unauthorized."}, status_code=401)
        try:
            body = await request.json()
        except Exception:
            body = {}
        email = ""
        if isinstance(body, dict):
            email = str(body.get("email") or "")
        try:
            issued = approve_invite(email, settings=settings, store=store)
        except AuthError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        return JSONResponse(
            {
                "email": issued.email,
                "token": issued.token,
                "token_prefix": "inv_",
                "redeem_url": issued.redeem_url,
                "expires_at": issued.expires_at,
            }
        )

    @mcp.custom_route("/register", methods=["GET", "POST"])
    async def register_compat(request: Request) -> Response:
        if request.method == "GET":
            return RedirectResponse("/invite", status_code=302)
        if not hosted:
            return JSONResponse(
                {"error": "Invites are hosted-only. Self-host stdio needs no key."},
                status_code=400,
            )
        return await _waitlist_request(request, settings=settings, store=store)

    @mcp.custom_route("/account/delete", methods=["POST"])
    async def delete_account(request: Request) -> Response:
        if not hosted:
            return JSONResponse({"error": "Hosted-only."}, status_code=400)
        try:
            body = await request.json()
        except Exception:
            body = {}
        email = str((body or {}).get("email") or "")
        key = str((body or {}).get("key") or "")
        from open_ux.auth import hash_key, normalize_email

        try:
            normalized = normalize_email(email)
        except AuthError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        digest = hash_key(key, settings.pepper)
        row = store.lookup_key(digest)
        if not row or row["email"] != normalized:
            return JSONResponse({"error": "Email and key do not match."}, status_code=401)
        store.delete_account(normalized)
        return JSONResponse({"deleted": True, "email": normalized})

    return mcp
