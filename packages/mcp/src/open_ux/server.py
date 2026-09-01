from __future__ import annotations

from typing import Any, Literal

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_access_token
from pydantic import BaseModel, Field
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response

from open_ux.audit import audit as run_audit
from open_ux.auth import AuthError, HashedKeyVerifier, register, revoke_account
from open_ux.catalog import EMPTY_NOTE, content_hash, get_by_id, list_index, load_catalog
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


def create_mcp(*, hosted: bool) -> FastMCP:
    settings = Settings.load(hosted=hosted)
    store = get_store(settings)
    catalog = load_catalog(settings)

    auth = HashedKeyVerifier(settings, store) if hosted else None
    mcp = FastMCP(
        name="Open UX",
        instructions=(
            "Open UX: cited UX rules agents audit against. "
            "Tools: list_guidelines, get_guideline, audit. Hybrid C — no server LLM. "
            "If the catalog is empty, return empty/incomplete; do not invent rules."
        ),
        version="0.1.0",
        website_url="https://github.com/3dyonic/open-ux",
        auth=auth,
    )

    @mcp.tool
    def list_guidelines(
        category: str | None = None,
        segment: str | None = None,
    ) -> dict[str, Any]:
        """Thin index of catalog guidelines. Empty until cited seed rules land."""
        items = list_index(catalog, category=category, segment=segment)
        _maybe_telemetry(settings, tool="list_guidelines")
        payload: dict[str, Any] = {
            "guidelines": items,
            "count": len(items),
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
        """Fetch one guideline by id. Does not invent missing rules."""
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
    ) -> dict[str, Any]:
        """Audit html | jsx | description. Deterministic Hybrid C. No server LLM.

        reasons[] reuse catalog pass_when / fail_when plus the rule id.
        Raw content is never persisted (length + optional hash only).
        """
        result = run_audit(
            catalog,
            target_type=target.type,
            content=target.content,
            guideline_ids=guideline_ids,
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

    @mcp.custom_route("/register", methods=["POST"])
    async def register_route(request: Request) -> Response:
        if not hosted:
            return JSONResponse(
                {"error": "Registration is hosted-only. Self-host stdio needs no key."},
                status_code=400,
            )
        try:
            body = await request.json()
        except Exception:
            body = {}
        email = ""
        if isinstance(body, dict):
            email = str(body.get("email") or "")
        try:
            issued = register(email, settings=settings, store=store)
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
