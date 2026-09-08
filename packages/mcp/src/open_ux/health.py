"""JSON health payload. No HTML."""

from __future__ import annotations

from typing import Any

from open_ux import __version__
from open_ux.catalog import Catalog, catalog_status


def health_payload(catalog: Catalog, *, hosted: bool) -> dict[str, Any]:
    return {
        "ok": True,
        "name": "Open UX",
        "hosted": hosted,
        "version": __version__,
        "catalog": catalog_status(catalog),
    }
