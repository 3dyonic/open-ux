"""Guardrails for publish.yml changed-file filtering (see .github/workflows/publish.yml)."""

from __future__ import annotations

import re

_PUBLISH_EXCLUDE = re.compile(
    r"^packages/mcp/tests/"
    r"|^packages/mcp/src/open_ux/static/"
    r"|^packages/mcp/src/open_ux/mail\.py$"
    r"|^packages/mcp/src/open_ux/public_html\.py$"
    r"|^packages/mcp/src/open_ux/settings\.py$"
)

_PUBLISH_INCLUDE = re.compile(
    r"^(catalog/|packages/mcp/pyproject\.toml|packages/mcp/hatch_build\.py|"
    r"packages/mcp/hatch_metadata\.py|packages/mcp/src/)"
)


def pypi_relevant_paths(changed: list[str]) -> list[str]:
    return [path for path in changed if not _PUBLISH_EXCLUDE.search(path)]


def should_publish(changed: list[str]) -> bool:
    if ".github/workflows/publish.yml" in changed:
        return True
    return any(_PUBLISH_INCLUDE.search(path) for path in pypi_relevant_paths(changed))


def test_pypi_filter_keeps_mcp_src_not_tests() -> None:
    changed = [
        "packages/mcp/src/open_ux/server.py",
        "packages/mcp/tests/test_pack.py",
        "docs/TOOLS.md",
    ]
    assert pypi_relevant_paths(changed) == [
        "packages/mcp/src/open_ux/server.py",
        "docs/TOOLS.md",
    ]
    assert should_publish(changed)


def test_workflow_only_change_still_publishes() -> None:
    assert should_publish([".github/workflows/publish.yml"])


def test_plugin_only_change_skips_publish() -> None:
    changed = ["clients/plugin/skills/open-ux/SKILL.md"]
    assert not should_publish(changed)
