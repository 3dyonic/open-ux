from __future__ import annotations

import os
import re
import secrets
from html import escape
from pathlib import Path
from typing import Annotated, Any

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_access_token
from pydantic import Field
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response
from starlette.staticfiles import StaticFiles

from open_ux.pack import pack as run_pack
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
from open_ux.catalog import EMPTY_NOTE, catalog_status, get_by_id, list_index, load_catalog
from open_ux.components import (
    build_component_usage,
    get_component as run_get_component,
    list_components as run_list_components,
    load_components,
)
from open_ux.health import HealthState, health_payload
from open_ux.mail import send_invite_email
from open_ux.jobs import (
    DEFAULT_LIMIT,
    JOB_FIELD_DESCRIPTION,
    JobId,
    JobTree,
    MAX_LIMIT,
    load_job_tree,
)
from open_ux.public_html import (
    FAVICON_PATH,
    ICON_PNG_PATH,
    PIP_SVG_PATH,
    ICON_PNG_PATH,
    ROBOTS_TXT,
    render_sitemap,
    sitemap_lastmods,
)
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
    gtm_container_id,
)
from open_ux.rate_limit import client_ip
from open_ux.store import get_store

SPA_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Cache-Control": "no-cache",
}
ASSET_HEADERS = {
    "Cache-Control": "public, max-age=31536000, immutable",
    "X-Content-Type-Options": "nosniff",
}
_SHELL_CACHE: dict[str, tuple[float, str]] = {}
_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]+$")
_PAGE_FILES = {
    "/": "index.html",
    "/catalog": "catalog/index.html",
    "/health": "health/index.html",
    "/privacy": "privacy/index.html",
    "/sources": "sources/index.html",
    "/invite": "invite/index.html",
    "/invite/requested": "invite/requested/index.html",
    "/invite/redeem": "invite/redeem/index.html",
}


def web_dist() -> Path | None:
    raw = os.environ.get("OPEN_UX_WEB_DIST", "").strip()
    path = Path(raw) if raw else Path(__file__).resolve().parents[2].parent / "web" / "dist"
    if (path / "index.html").is_file():
        return path
    return None


def _dist_file(rel: str) -> Path | None:
    dist = web_dist()
    if dist is None:
        return None
    path = (dist / rel).resolve()
    if dist.resolve() not in path.parents and path != dist.resolve():
        return None
    return path if path.is_file() else None


def _read_dist(rel: str) -> str | None:
    path = _dist_file(rel)
    if path is None:
        return None
    key = str(path)
    mtime = path.stat().st_mtime
    cached = _SHELL_CACHE.get(key)
    if cached is None or cached[0] != mtime:
        text = path.read_text(encoding="utf-8")
        _SHELL_CACHE[key] = (mtime, text)
        return text
    return cached[1]


def _html_file(
    rel: str,
    *,
    status_code: int = 200,
    replace: dict[str, str] | None = None,
) -> Response:
    html = _read_dist(rel)
    if html is None:
        html = _read_dist("index.html")
    if html is None:
        if status_code < 400:
            status_code = 404
        message = (
            "This page could not be loaded."
            if status_code >= 500
            else "Not found."
        )
        return JSONResponse({"error": message}, status_code=status_code)
    if replace:
        for token, value in replace.items():
            html = html.replace(token, value)
    return Response(
        html,
        status_code=status_code,
        media_type="text/html; charset=utf-8",
        headers=SPA_HEADERS,
    )


def _html_page(path: str, *, status_code: int = 200) -> Response:
    rel = _PAGE_FILES.get(path or "/")
    return _html_file(rel or "index.html", status_code=status_code)


def server_error_response(path: str = "/") -> Response:
    clean = path or "/"
    if clean.startswith(("/api", "/mcp", "/admin", "/account")):
        return JSONResponse(
            {"error": "This page could not be loaded."},
            status_code=500,
        )
    return _html_file(
        "500.html",
        status_code=500,
        replace={"{{path}}": escape(clean, quote=True)},
    )


def not_found_response(*, kind: str = "page", detail: str = "", path: str = "/") -> Response:
    token = escape((detail or path or "").strip() or "/", quote=True)
    rel = "404-rule.html" if kind == "rule" else "404.html"
    return _html_file(rel, status_code=404, replace={"{{detail}}": token})


def _rule_page(guideline_id: str) -> Response:
    gid = guideline_id if _SAFE_ID.fullmatch(guideline_id) else ""
    rel = f"catalog/{gid}/index.html" if gid else ""
    if gid and _dist_file(rel):
        return _html_file(rel)
    return _html_page("/catalog")


def _jobs_payload(tree: JobTree) -> dict[str, Any]:
    return {
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
        "catalog": catalog_status(catalog),
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
    health_state = HealthState()
    job_tree = load_job_tree(settings)
    component_registry = load_components(settings)
    component_usage = build_component_usage(job_tree, catalog.guidelines)
    dist = web_dist()
    catalog_index = _catalog_index_payload(catalog, job_tree)
    guideline_ids = [str(row["id"]) for row in catalog.index if row.get("id")]
    sitemap_xml = render_sitemap(
        guideline_ids,
        lastmods=sitemap_lastmods(
            catalog_path=catalog.path,
            guidelines=catalog.guidelines,
            dist=dist,
        ),
    )

    def current_health() -> dict[str, Any]:
        return health_payload(catalog, hosted=hosted, state=health_state)

    auth = HashedKeyVerifier(settings, store) if hosted else None
    mcp = FastMCP(
        name="Open UX",
        instructions=(
            "Open UX: cited UX rules agents audit against. "
            "First path: (1) ask → suggest_situations(task_text) or "
            "list_situations(container=…); (2) map → get_situation(card_id); "
            "(3) pull → pack(jobs=card|leaf|container) → get_guideline. "
            "No server LLM. "
            "pack: jobs=<card_id>, jobs=<leaf_id>, or jobs=<container> "
            "(container = broad pass, no situation envelope); returns cited rule "
            "criteria so you can make a better decision — the decision is yours. "
            "get_guideline for the full cite. When component[] is on the Card or "
            "pack row, get_component is control context for that job (variants, "
            "a11y, keyboard) — not a second catalog map. "
            "Does not take a file. Does not return pass or fail. "
            "Page with limit/offset; follow next_offset. "
            "Surfaces are not needs. Leaf ids scope one bay. "
            "If the catalog is empty, return empty; do not invent rules. "
            "Helpers (LLM-local): pip install open-ux on the client; "
            "open-ux rank-pack after pack. Host does not execute helpers."
        ),
        version=__version__,
        website_url="https://github.com/3dyonic/open-ux",
        auth=auth,
    )
    mcp.health_state = health_state

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
            "catalog": catalog_status(catalog),
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
        """Scope the paged index by jobs / lane. Catalog order. Query is ignored. No rule bodies."""
        items, total = list_index(
            catalog,
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
            "catalog": catalog_status(catalog),
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
        """When: area known or browsing the Card index. List Situation Cards.

        With container=, return that kind's specs (when / reject). Unscoped is
        the index only. No rule bodies. Response note points to the next step.
        """
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
        """When: a Card is named and you need leaf counts before pack.

        Fetch one Situation Card: when, reject, facets, leaf counts, component.
        Each facet lists leaves as {id, count}. Fails on a Leaf or container id.
        Does not invent a Card. No rule bodies.
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
                    "Returns the catalog map. Does not pick a Card."
                )
            ),
        ],
        surface: Annotated[
            str | None,
            Field(
                description=(
                    "Optional page/flow context (home, cart, checkout). "
                    "Never an id. Does not reorder the map."
                )
            ),
        ] = None,
    ) -> dict[str, Any]:
        """When: the UI ask is vague — returns the full catalog map, not a pick.

        Catalog map in lock order. No ranking. Every Situation Card grouped by
        container — never a filtered subset and never a ranked winner. Order is
        the catalog lock, not a hint. task_text requests the map; it does not
        reorder. Compare jobs with list_situations(container=…) or
        get_situation(card_id), then pack with jobs=<card_id>, jobs=<leaf_id>,
        or jobs=<container> for a broad pass (no situation envelope). Response
        note repeats the next step. Surface is not an id. No server LLM.
        """
        result = run_suggest_situations(task_text, surface, job_tree)
        _maybe_telemetry(settings, tool="suggest_situations")
        return result

    @mcp.tool
    def pack(
        jobs: Annotated[JobId | None, Field(description=JOB_FIELD_DESCRIPTION)] = None,
        query: Annotated[
            str | None,
            Field(
                description=(
                    "Ignored. The host does not rank. Use open-ux rank-pack locally "
                    "on the pack page if you want BM25 (pip install open-ux)."
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
                description="Page size. Default 10. Clamps one page, not how far offset may walk.",
            ),
        ] = DEFAULT_LIMIT,
        offset: Annotated[
            int,
            Field(
                ge=0,
                description="Skip this many in-scope rows. Follow next_offset until it is absent.",
            ),
        ] = 0,
    ) -> dict[str, Any]:
        """When: a job is named on jobs= — pull cited criteria.

        Say the UX need as one Situation Card, Leaf, or container. Returns cited
        rule criteria so you can make a better decision; the decision is yours.
        Card/Leaf pulls include situation (when, reject; leaf when scoped) and
        cite_via get_guideline. Container pulls (jobs=forms, actions, feedback, …)
        are a broad pass: cite_via only, no situation envelope — narrow to a Card
        when the ask sharpens. Rows are browse slices, not full cites. Does not take a file. Does not return pass or fail. Required: jobs or guideline_ids. Missing jobs= error points to map tools first. Prefer a Card; use a Leaf for one bay.
        """
        result = run_pack(
            catalog,
            jobs=jobs,
            query=query,
            guideline_ids=guideline_ids,
            limit=limit,
            offset=offset,
        )
        _maybe_telemetry(
            settings,
            tool="pack",
            guideline_ids=[row.get("id") for row in result.get("guidelines") or [] if row.get("id")],
        )
        return result

    @mcp.tool
    def list_components() -> dict[str, Any]:
        """Component index — context helper for Cards and jobs. Id, title, overview only. One page. No variants."""
        result = run_list_components(component_registry)
        _maybe_telemetry(settings, tool="list_components")
        return result

    @mcp.tool
    def get_component(
        id: Annotated[
            str,
            Field(description="Closed component id from pack component[] or Card component[]."),
        ],
        include_vs: Annotated[
            bool,
            Field(description="Include vs (near-neighbor) section. Default true."),
        ] = True,
        include_variants: Annotated[
            bool,
            Field(description="Include variants section. Default true."),
        ] = True,
        include_accessibility: Annotated[
            bool,
            Field(description="Include accessibility section. Default true."),
        ] = True,
        include_keyboard: Annotated[
            bool,
            Field(description="Include keyboard section. Default true."),
        ] = True,
        include_keywords: Annotated[
            bool,
            Field(description="Include keywords. Default false."),
        ] = False,
        include_used_on: Annotated[
            bool,
            Field(
                description=(
                    "Include Cards and cites that stamp this component. Default false."
                )
            ),
        ] = False,
    ) -> dict[str, Any]:
        """Fetch one component record. Context helper for Cards and jobs.

        Section switches omit keys when false. Open only for ids on a pack row
        or Card component[] — not all 38 upfront. Return to pack after skim.
        """
        result = run_get_component(
            component_registry,
            component_usage,
            id,
            include_vs=include_vs,
            include_variants=include_variants,
            include_accessibility=include_accessibility,
            include_keyboard=include_keyboard,
            include_keywords=include_keywords,
            include_used_on=include_used_on,
        )
        _maybe_telemetry(settings, tool="get_component")
        return result

    @mcp.custom_route("/api/site", methods=["GET"])
    async def site_config(_request: Request) -> Response:
        return JSONResponse({"gtm_id": gtm_container_id()})

    @mcp.custom_route("/api/catalog", methods=["GET"])
    async def catalog_index_route(_request: Request) -> Response:
        return JSONResponse(catalog_index)

    @mcp.custom_route("/api/catalog/{guideline_id}", methods=["GET"])
    async def catalog_item(request: Request) -> Response:
        guideline_id = str(request.path_params.get("guideline_id") or "")
        found = get_by_id(catalog, guideline_id)
        if found is None:
            return JSONResponse({"found": False, "id": guideline_id}, status_code=404)
        return JSONResponse(found)

    @mcp.custom_route("/health.json", methods=["GET"])
    async def health_json(_request: Request) -> Response:
        return JSONResponse(current_health())

    @mcp.custom_route("/", methods=["GET"])
    async def landing(_request: Request) -> Response:
        return _html_page("/")

    @mcp.custom_route("/catalog", methods=["GET"])
    async def catalog_list(_request: Request) -> Response:
        return _html_page("/catalog")

    @mcp.custom_route("/catalog/{guideline_id}", methods=["GET"])
    async def catalog_rule(request: Request) -> Response:
        guideline_id = str(request.path_params.get("guideline_id") or "")
        found = get_by_id(catalog, guideline_id)
        if found is None:
            return not_found_response(
                kind="rule",
                detail=guideline_id,
                path=f"/catalog/{guideline_id}",
            )
        return _rule_page(guideline_id)

    @mcp.custom_route("/health", methods=["GET"])
    async def health_page(_request: Request) -> Response:
        return _html_page("/health")

    @mcp.custom_route("/privacy", methods=["GET"])
    async def privacy(_request: Request) -> Response:
        return _html_page("/privacy")

    @mcp.custom_route("/sources", methods=["GET"])
    async def sources(_request: Request) -> Response:
        return _html_page("/sources")

    @mcp.custom_route("/invite", methods=["GET"])
    async def invite_request_page(_request: Request) -> Response:
        return _html_page("/invite")

    @mcp.custom_route("/invite/requested", methods=["GET"])
    async def invite_requested_page(_request: Request) -> Response:
        return _html_page("/invite/requested")

    @mcp.custom_route("/robots.txt", methods=["GET"])
    async def robots(_request: Request) -> Response:
        return Response(ROBOTS_TXT, media_type="text/plain; charset=utf-8")

    @mcp.custom_route("/sitemap.xml", methods=["GET"])
    async def sitemap(_request: Request) -> Response:
        return Response(sitemap_xml, media_type="application/xml")

    @mcp.custom_route("/logo-mark.svg", methods=["GET"])
    async def logo_mark(_request: Request) -> Response:
        return Response(FAVICON_PATH.read_bytes(), media_type="image/svg+xml")

    @mcp.custom_route("/favicon.svg", methods=["GET"])
    async def favicon(_request: Request) -> Response:
        return Response(FAVICON_PATH.read_bytes(), media_type="image/svg+xml")

    @mcp.custom_route("/icon.png", methods=["GET"])
    async def icon_png(_request: Request) -> Response:
        return Response(ICON_PNG_PATH.read_bytes(), media_type="image/png")

    @mcp.custom_route("/pip.svg", methods=["GET"])
    async def pip_svg(_request: Request) -> Response:
        return Response(PIP_SVG_PATH.read_bytes(), media_type="image/svg+xml")

    if dist is not None and (dist / "assets").is_dir():
        static_assets = StaticFiles(directory=dist / "assets")

        @mcp.custom_route("/assets/{path:path}", methods=["GET"])
        async def web_assets(request: Request) -> Response:
            rel = str(request.path_params.get("path") or "")
            response = await static_assets.get_response(rel, request.scope)
            for key, value in ASSET_HEADERS.items():
                response.headers[key] = value
            return response

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
            return _html_page("/invite/redeem")
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

    @mcp.custom_route("/admin/stats", methods=["GET"])
    async def admin_stats(request: Request) -> Response:
        if not hosted:
            return JSONResponse({"error": "Hosted-only."}, status_code=400)
        if not _admin_authorized(request, settings):
            return JSONResponse({"error": "Unauthorized."}, status_code=401)
        return JSONResponse(store.telemetry_summary())

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
        send_invite_email(issued, settings=settings)
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

    @mcp.custom_route("/{path:path}", methods=["GET"])
    async def public_not_found(request: Request) -> Response:
        raw = str(request.path_params.get("path") or "")
        path = f"/{raw}" if raw else "/"
        if path.startswith(("/api", "/mcp", "/admin", "/account")):
            return JSONResponse({"error": "Not found."}, status_code=404)
        return not_found_response(kind="page", detail=path, path=path)

    return mcp
