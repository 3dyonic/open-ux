"""JSON health payload. No HTML."""

from __future__ import annotations

from typing import Any

from open_ux.catalog import Catalog


def health_payload(catalog: Catalog, *, hosted: bool) -> dict[str, Any]:
    return {
        "ok": True,
        "name": "Open UX",
        "hosted": hosted,
        "catalog": {
            "status": "empty" if catalog.empty else "ok",
            "guideline_count": len(catalog.guidelines),
            "version": catalog.version,
        },
    }
