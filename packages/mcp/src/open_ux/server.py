from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Annotated, Any

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_access_token
from pydantic import Field
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, RedirectResponse, Response
from starlette.staticfiles import StaticFiles

from open_ux.audit import audit as run_audit
from open_ux.auth import (
    AuthError,
    HashedKeyVerifier,
    approve_invite,
    hash_key,
    normalize_email,
    redeem_invite,
    request_invite,
)
from open_ux import __version__
from open_ux.catalog import EMPTY_NOTE, get_by_id, list_index, load_catalog
from open_ux.health import health_payload
from open_ux.jobs import (
    DEFAULT_LIMIT,
    JOB_FIELD_DESCRIPTION,
    JobId,
    JobTree,
    MAX_LIMIT,
    load_job_tree,
)
from open_ux.public_html import FAVICON_PATH, ROBOTS_TXT, render_sitemap
from open_ux.situations import (
    get_situation as run_get_situation,
    list_situations as run_list_situations,
    suggest_situations as run_suggest_situations,
)
from open_ux.settings import (
    INVITE_REDEEM_RATE_PER_DAY,
    INVITE_REDEEM_RATE_PER_MINUTE,
    INVITE_REQUEST_RATE_PER_DAY,
    INVITE_REQUEST_RATE_PER_MINUTE,
    Settings,
)
from open_ux.rate_limit import client_ip
from open_ux.store import get_store

SPA_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Cache-Control": "no-cache",
}


def web_dist() -> Path | None:
    raw = os.environ.get("OPEN_UX_WEB_DIST", "").strip()
    path = Path(raw) if raw else Path(__file__).resolve().parents[2].parent / "web" / "dist"
    if (path / "index.html").is_file():
        return path
    return None


def _app_page() -> Response:
    dist = web_dist()
    if dist is None:
        return JSONResponse({"error": "Not found."}, status_code=404)
    return FileResponse(
        dist / "index.html",
        media_type="text/html; charset=utf-8",
        headers=SPA_HEADERS,
    )


def _jobs_payload(tree: JobTree) -> dict[str, Any]:
    return {
        "version": tree.version,
        "containers": [{"id": c.id, "title": c.title} for c in tree.containers],
        "cards": [
            {
                "id": card.id,
                "title": card.title,
                "container": card.container,
                "facets": [{"id": facet.id, "title": facet.title} for facet in card.facets],
            }
            for card in tree.cards
        ],
    }


def _catalog_index_payload(catalog, job_tree: JobTree) -> dict[str, Any]:
    items, total = list_index(catalog, limit=max(len(catalog.index), 1))
    bodies = {str(row.get("id") or ""): row for row in catalog.guidelines}
    guidelines: list[dict[str, Any]] = []
    for item in items:
        row = dict(item)
        body = bodies.get(str(row.get("id") or ""))
        if body is not None and body.get("rule") is not None:
            row["rule"] = str(body["rule"]).strip()
        guidelines.append(row)
    return {
        "guidelines": guidelines,
        "total": total,
        "catalog": {
            "status": "empty" if catalog.empty else "ok",
            "guideline_count": len(catalog.guidelines),
            "version": catalog.version,
        },
        "jobs": _jobs_payload(job_tree),
    }


def _invite_allowed(
    request: Request,
    store,
    bucket: str,
    *,
    per_minute: int,
    per_day: int,
) -> bool:
    ok, _window = store.consume_rate(
        f"{bucket}:{client_ip(request)}",
        per_minute=per_minute,
        per_day=per_day,
    )
    return ok


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
    guideline_ids: list[str] | None = None,
) -> None:
    if not settings.telemetry:
        return
    key_hash = _key_hash_or_none()
    if not key_hash:
        return
    get_store(settings).record_telemetry(
        key_hash=key_hash,
        tool=tool,
        target_type=None,
        content_length=None,
        content_hash=None,
        guideline_ids=guideline_ids,
        verdicts=None,
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
    if not _invite_allowed(
        request,
        store,
        "invite:request",
        per_minute=INVITE_REQUEST_RATE_PER_MINUTE,
        per_day=INVITE_REQUEST_RATE_PER_DAY,
    ):
        return JSONResponse(
            {"error": "Enter a valid email to request an invite."},
            status_code=429,
        )
    try:
        body = await request.json()
    except Exception:
        body = {}
    email = body.get("email") if isinstance(body, dict) else ""
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
    job_tree = load_job_tree(settings)
    dist = web_dist()

    auth = HashedKeyVerifier(settings, store) if hosted else None
    mcp = FastMCP(
        name="Open UX",
        instructions=(
            "Open UX: cited UX rules agents audit against. "
            "Find a Situation Card with list_situations, get_situation, or "
            "suggest_situations, then get_guideline or audit. "
            "No server LLM. "
            "audit: say one Card or container as jobs; returns a stratified "
            "sample of cited rule criteria. query is optional attention. "
            "Does not take a file. Does not return pass or fail. "
            "Leaf ids and Surfaces are not needs. "
            "If the catalog is empty, return empty; do not invent rules."
        ),
        version=__version__,
        website_url="https://github.com/3dyonic/open-ux",
        auth=auth,
    )

    @mcp.tool
    def list_guidelines(
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Paged index only: id, title, name, jobs, lane, placement. No rule bodies."""
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
    def list_situations(
        container: Annotated[
            str | None,
            Field(
                description=(
                    "Optional container id or alias (forms_and_input / forms, "
                    "actions_and_decisions / actions, feedback_and_status / "
                    "feedback, navigation_and_wayfinding, layout_and_data_display, "
                    "overlays_and_content_structure, multi_step_flows)."
                )
            ),
        ] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List Situation Cards — the compose jobs you pick. No rule bodies."""
        result = run_list_situations(
            job_tree, container=container, limit=limit, offset=offset
        )
        _maybe_telemetry(settings, tool="list_situations")
        return result

    @mcp.tool
    def get_situation(
        id: Annotated[
            str,
            Field(description="A Situation Card id. A Leaf id fails."),
        ],
    ) -> dict[str, Any]:
        """Fetch one Situation Card: when, reject, facets, leaf pointers.

        Fails on a Leaf id. Does not invent a Card. No rule bodies.
        """
        result = run_get_situation(id, job_tree)
        _maybe_telemetry(settings, tool="get_situation")
        return result

    @mcp.tool
    def suggest_situations(
        task_text: Annotated[
            str,
            Field(
                description=(
                    "What you are composing, in task language. "
                    "Fallback when you cannot pick a Card from the skill table."
                )
            ),
        ],
        surface: Annotated[
            str | None,
            Field(
                description=(
                    "Optional page/flow context (home, cart, checkout). "
                    "Ranking bias only. Never an id."
                )
            ),
        ] = None,
    ) -> dict[str, Any]:
        """Return every Situation Card, ordered from a vague task or pasted UI.

        Always returns the complete 13-card allowlist -- never a filtered
        subset. Order is a heuristic hint, not a verdict: pick the fitting
        Card yourself from the full set rather than trusting position alone.
        Surface is ranking bias, never returned as an id. No server LLM.
        """
        result = run_suggest_situations(task_text, surface, job_tree)
        _maybe_telemetry(settings, tool="suggest_situations")
        return result

    @mcp.tool
    def audit(
        jobs: Annotated[JobId | None, Field(description=JOB_FIELD_DESCRIPTION)] = None,
        query: Annotated[
            str | None,
            Field(
                description=(
                    "Optional words to rank within that job. Not a substitute for jobs. "
                    "Never drops rules to zero -- reorders best matches first and falls "
                    "back to the full set already in scope if nothing matches."
                )
            ),
        ] = None,
        guideline_ids: Annotated[
            list[str] | None,
            Field(description="Use only if ids are already known from search or get."),
        ] = None,
        limit: Annotated[
            int,
            Field(
                ge=1,
                le=MAX_LIMIT,
                description="Max rules to return. Default 10. Never the whole catalog.",
            ),
        ] = DEFAULT_LIMIT,
    ) -> dict[str, Any]:
        """Say the UX need as one Situation Card or container.

        jobs= is a stratified Card sample, not every rule. query is optional
        attention. Returns cited rule criteria. Does not take a file. Does not return pass or fail.
        Required: jobs or guideline_ids. Leaf ids are not needs.
        """
        result = run_audit(
            catalog,
            jobs=jobs,
            query=query,
            guideline_ids=guideline_ids,
            limit=limit,
        )
        _maybe_telemetry(
            settings,
            tool="audit",
            guideline_ids=[row.get("id") for row in result.get("guidelines") or [] if row.get("id")],
        )
        return result

    @mcp.custom_route("/api/catalog", methods=["GET"])
    async def catalog_index(_request: Request) -> Response:
        return JSONResponse(_catalog_index_payload(catalog, job_tree))

    @mcp.custom_route("/api/catalog/{guideline_id}", methods=["GET"])
    async def catalog_item(request: Request) -> Response:
        guideline_id = str(request.path_params.get("guideline_id") or "")
        found = get_by_id(catalog, guideline_id)
        if found is None:
            return JSONResponse({"found": False, "id": guideline_id}, status_code=404)
        return JSONResponse(found)

    @mcp.custom_route("/health.json", methods=["GET"])
    async def health_json(_request: Request) -> Response:
        return JSONResponse(health_payload(catalog, hosted=hosted))

    @mcp.custom_route("/", methods=["GET"])
    async def landing(_request: Request) -> Response:
        return _app_page()

    @mcp.custom_route("/catalog", methods=["GET"])
    async def catalog_list(_request: Request) -> Response:
        return _app_page()

    @mcp.custom_route("/catalog/{guideline_id}", methods=["GET"])
    async def catalog_rule(_request: Request) -> Response:
        return _app_page()

    @mcp.custom_route("/health", methods=["GET"])
    async def health_page(_request: Request) -> Response:
        return _app_page()

    @mcp.custom_route("/privacy", methods=["GET"])
    async def privacy(_request: Request) -> Response:
        return _app_page()

    @mcp.custom_route("/invite", methods=["GET"])
    async def invite_request_page(_request: Request) -> Response:
        return _app_page()

    @mcp.custom_route("/invite/requested", methods=["GET"])
    async def invite_requested_page(_request: Request) -> Response:
        return _app_page()

    @mcp.custom_route("/robots.txt", methods=["GET"])
    async def robots(_request: Request) -> Response:
        return Response(ROBOTS_TXT, media_type="text/plain; charset=utf-8")

    @mcp.custom_route("/sitemap.xml", methods=["GET"])
    async def sitemap(_request: Request) -> Response:
        ids = [str(row["id"]) for row in catalog.index if row.get("id")]
        return Response(render_sitemap(ids), media_type="application/xml")

    @mcp.custom_route("/logo-mark.svg", methods=["GET"])
    async def logo_mark(_request: Request) -> Response:
        return Response(FAVICON_PATH.read_bytes(), media_type="image/svg+xml")

    @mcp.custom_route("/favicon.svg", methods=["GET"])
    async def favicon(_request: Request) -> Response:
        return Response(FAVICON_PATH.read_bytes(), media_type="image/svg+xml")

    if dist is not None and (dist / "assets").is_dir():
        static_assets = StaticFiles(directory=dist / "assets")

        @mcp.custom_route("/assets/{path:path}", methods=["GET"])
        async def web_assets(request: Request) -> Response:
            rel = str(request.path_params.get("path") or "")
            return await static_assets.get_response(rel, request.scope)

    @mcp.custom_route("/invite/request", methods=["POST"])
    async def invite_request_route(request: Request) -> Response:
        if not hosted:
            return JSONResponse(
                {"error": "Invites are hosted-only. Self-host stdio needs no key."},
                status_code=400,
            )
        return await _waitlist_request(request, settings=settings, store=store)

    @mcp.custom_route("/invite/redeem", methods=["GET", "POST"])
    async def invite_redeem_route(request: Request) -> Response:
        if request.method == "GET":
            return _app_page()
        if not hosted:
            return JSONResponse(
                {"error": "Invites are hosted-only. Self-host stdio needs no key."},
                status_code=400,
            )
        if not _invite_allowed(
            request,
            store,
            "invite:redeem",
            per_minute=INVITE_REDEEM_RATE_PER_MINUTE,
            per_day=INVITE_REDEEM_RATE_PER_DAY,
        ):
            return JSONResponse(
                {"error": "Invite invalid or already used. Request a new one if needed."},
                status_code=429,
            )
        try:
            body = await request.json()
        except Exception:
            body = {}
        token = body.get("token") if isinstance(body, dict) else ""
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
        email = body.get("email") if isinstance(body, dict) else ""
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
        email = body.get("email") if isinstance(body, dict) else ""
        key = body.get("key") if isinstance(body, dict) else ""
        try:
            normalized = normalize_email(email)
        except AuthError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        if not isinstance(key, str):
            return JSONResponse({"error": "Email and key do not match."}, status_code=401)
        digest = hash_key(key, settings.pepper)
        row = store.lookup_key(digest)
        if not row or row["email"] != normalized:
            return JSONResponse({"error": "Email and key do not match."}, status_code=401)
        store.delete_account(normalized)
        return JSONResponse({"deleted": True, "email": normalized})

    return mcp
