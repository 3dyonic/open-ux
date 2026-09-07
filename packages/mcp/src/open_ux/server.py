from __future__ import annotations

import secrets
from typing import Annotated, Any

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_access_token
from pydantic import Field
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
from open_ux.catalog import EMPTY_NOTE, get_by_id, list_index, load_catalog
from open_ux.catalog_page import (
    render_catalog_list,
    render_catalog_not_found,
    render_catalog_rule,
)
from open_ux.invite_page import REQUESTED_HTML, REDEEM_HTML, render_invite_request
from open_ux.jobs import (
    DEFAULT_LIMIT,
    JOB_FIELD_DESCRIPTION,
    JobId,
    MAX_LIMIT,
    load_job_tree,
)
from open_ux.landing import render_landing
from open_ux.public_html import (
    CONSENT_COOKIE,
    FAVICON_PATH,
    ROBOTS_TXT,
    render_privacy_page,
    render_sitemap,
)
from open_ux.situations import (
    get_situation as run_get_situation,
    list_situations as run_list_situations,
    suggest_situations as run_suggest_situations,
)
from open_ux.settings import Settings
from open_ux.store import get_store


def _consent_cookie(request: Request) -> str | None:
    return request.cookies.get(CONSENT_COOKIE)


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
    job_tree = load_job_tree(settings)

    auth = HashedKeyVerifier(settings, store) if hosted else None
    mcp = FastMCP(
        name="Open UX",
        instructions=(
            "Open UX: cited UX rules agents audit against. "
            "Find a Situation Card with list_situations, get_situation, or "
            "suggest_situations, then get_guideline or audit. "
            "No server LLM. "
            "audit: say one Card or container as jobs; returns cited rule "
            "criteria. Does not take a file. Does not return pass or fail. "
            "Leaf ids and Surfaces are not needs. "
            "If the catalog is empty, return empty; do not invent rules."
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
        """Rank Situation Cards from a vague task or pasted UI. Allowlist only.

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
                    "Optional words to narrow within that job. Not a substitute for jobs."
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

        Returns cited rule criteria. Does not take a file. Does not return
        pass or fail. Required: jobs or guideline_ids. Leaf ids are not needs.
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

    @mcp.custom_route("/", methods=["GET"])
    async def landing(request: Request) -> Response:
        return HTMLResponse(render_landing(consent=_consent_cookie(request)))

    @mcp.custom_route("/catalog", methods=["GET"])
    async def catalog_list(request: Request) -> Response:
        container = str(request.query_params.get("container") or "")
        query = str(request.query_params.get("q") or "")
        try:
            page = int(str(request.query_params.get("page") or "1"))
        except ValueError:
            page = 1
        return HTMLResponse(
            render_catalog_list(
                catalog,
                job_tree,
                container=container,
                query=query,
                page=page,
                consent=_consent_cookie(request),
            )
        )

    @mcp.custom_route("/catalog/{guideline_id}", methods=["GET"])
    async def catalog_rule(request: Request) -> Response:
        guideline_id = str(request.path_params.get("guideline_id") or "")
        consent = _consent_cookie(request)
        html = render_catalog_rule(catalog, guideline_id, job_tree, consent=consent)
        if html is None:
            return HTMLResponse(
                render_catalog_not_found(guideline_id, consent=consent),
                status_code=404,
            )
        return HTMLResponse(html)

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

    @mcp.custom_route("/privacy", methods=["GET"])
    async def privacy(request: Request) -> Response:
        return HTMLResponse(render_privacy_page(consent=_consent_cookie(request)))

    @mcp.custom_route("/invite", methods=["GET"])
    async def invite_request_page(request: Request) -> Response:
        return HTMLResponse(render_invite_request(consent=_consent_cookie(request)))

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
