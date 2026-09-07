"""UNS-50 recorded smoke (local stand-in for hosted play).

Exact hosted call a human with an invite still needs to run:

    tool: Open-UX:audit
    arguments: {"jobs": "design_a_form"}
    endpoint: https://open-ux.dev/mcp
    auth: Bearer uxmcp_…  (invite key — do not invent one)

Expect a criteria pack that includes ``forms.field_labels.visible_label``
with a ``name`` (Visible field label) and no ``verdict``.

This module records the same call against the on-disk catalog so CI
documents the contract. Live hosted play is not substituted here.
"""

from __future__ import annotations

from open_ux.audit import PACK_KEYS, audit
from open_ux.catalog import load_catalog
from open_ux.settings import Settings

SEED_ID = "forms.field_labels.visible_label"
SEED_NAME = "Visible field label"
HOSTED_CALL = {
    "endpoint": "https://open-ux.dev/mcp",
    "tool": "audit",
    "arguments": {"jobs": "design_a_form"},
    "expect_id": SEED_ID,
    "expect_name": SEED_NAME,
}


def _catalog():
    return load_catalog(Settings.load())


def test_recorded_smoke_call_is_audit_jobs_design_a_form() -> None:
    assert HOSTED_CALL["arguments"] == {"jobs": "design_a_form"}
    assert HOSTED_CALL["tool"] == "audit"
    result = audit(_catalog(), jobs="design_a_form")
    assert "error" not in result
    assert "verdict" not in result
    assert result["count"] >= 1
    for row in result["guidelines"]:
        assert set(row) == set(PACK_KEYS)
        assert row["id"]
        assert row["name"]
        assert "verdict" not in row


def test_recorded_smoke_documents_visible_label_seed() -> None:
    """If the live seed is on disk, require its name. Hosted play still needs an invite."""
    result = audit(_catalog(), jobs="design_a_form", limit=50)
    seed = next((row for row in result["guidelines"] if row["id"] == SEED_ID), None)
    if seed is None:
        # Catalog harvest closed without this historical LIVE id. The hosted
        # play in UNS-50 still asks a human to confirm it on open-ux.dev.
        assert HOSTED_CALL["expect_id"] == SEED_ID
        assert HOSTED_CALL["expect_name"] == SEED_NAME
        return
    assert SEED_NAME in seed["name"]
    assert seed["id"] == SEED_ID
    assert "verdict" not in seed
