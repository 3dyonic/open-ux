from __future__ import annotations

import io
import json
from email.message import Message
from pathlib import Path
from types import ModuleType
from typing import Any
from urllib.error import HTTPError

import pytest

from open_ux import client as ux_client
from open_ux.client import McpError, _http_post, _parse_rpc_body, _unwrap_tool_result, call_tool

ROOT = Path(__file__).resolve().parents[3]
HELPER = ROOT / "scripts" / "mcp_call.py"
AUDIT_SCRIPT = ROOT / "scripts" / "audit.py"


def _load(path: Path, name: str) -> ModuleType:
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def helper() -> ModuleType:
    return _load(HELPER, "open_ux_mcp_call")


@pytest.fixture()
def audit_mod() -> ModuleType:
    return _load(AUDIT_SCRIPT, "open_ux_audit_helper")


def test_hosted_http_requires_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPEN_UX_API_KEY", raising=False)
    monkeypatch.delenv("OPEN_UX_URL", raising=False)
    monkeypatch.setenv("OPEN_UX_TRANSPORT", "http")
    with pytest.raises(McpError, match="OPEN_UX_API_KEY"):
        call_tool("audit", {"jobs": "design_a_form"})


def test_http_helper_unwraps_sse_tool_result() -> None:
    sse = (
        "event: message\n"
        'data: {"jsonrpc":"2.0","id":1,"result":{"structuredContent":{"ok":true}}}\n\n'
    ).encode("utf-8")
    msg = _parse_rpc_body("text/event-stream", sse)
    assert _unwrap_tool_result(msg["result"]) == {"ok": True}


def test_http_helper_maps_401(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_args: Any, **_kwargs: Any) -> Any:
        raise HTTPError(
            "https://open-ux.dev/mcp",
            401,
            "Unauthorized",
            hdrs=Message(),
            fp=io.BytesIO(b'{"error":"no"}'),
        )

    monkeypatch.setattr(ux_client.urllib.request, "urlopen", boom)
    with pytest.raises(McpError, match="OPEN_UX_API_KEY"):
        _http_post("https://open-ux.dev/mcp", {"jsonrpc": "2.0"}, {}, None)


def test_mcp_call_inprocess_list_and_audit(
    live_catalog: Path,
    helper: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("OPEN_UX_TRANSPORT", "inprocess")
    assert helper.main(["list"]) == 0
    names = {row["name"] for row in json.loads(capsys.readouterr().out)}
    assert "audit" in names
    assert helper.main(["audit", '{"jobs":"design_a_form"}']) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["count"] >= 1
    assert "verdict" not in payload


def test_helper_never_imports_catalog() -> None:
    source = HELPER.read_text(encoding="utf-8")
    client = Path(ux_client.__file__).read_text(encoding="utf-8")
    assert "catalog/rules" not in source
    assert "from open_ux.audit import" not in source
    assert "load_catalog" not in source
    assert "sys.path.insert" not in source
    assert "tools/list" in source
    assert "tools/call" in source
    assert "load_catalog" not in client
    assert "from open_ux.audit import" not in client
    assert "catalog/rules" not in client


def test_audit_script_requires_jobs_or_ids(
    audit_mod: ModuleType, capsys: pytest.CaptureFixture[str]
) -> None:
    assert audit_mod.main([]) == 2
    err = capsys.readouterr().err
    assert "jobs" in err or "guideline" in err


@pytest.mark.parametrize(
    "argv",
    (
        ["--file", "form.html"],
        ["--content", "<form></form>"],
        ["--target", "ui.png"],
        ["--verdict", "fail"],
        ["--upload", "ui.png"],
    ),
)
def test_audit_script_rejects_file_and_verdict(
    audit_mod: ModuleType, argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    assert audit_mod.main(argv) == 2
    err = capsys.readouterr().err.lower()
    assert "file" in err or "verdict" in err or "content" in err or "target" in err


def test_audit_script_prints_pack(
    live_catalog: Path,
    audit_mod: ModuleType,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert audit_mod.main(["--jobs", "design_a_form"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["count"] >= 1
    assert "verdict" not in payload
    row = payload["guidelines"][0]
    assert {"id", "title", "name", "overview", "rule", "facet"} <= set(row)
    assert "pass_when" not in row
    assert "fail_when" not in row


def test_audit_script_uses_shared_helper() -> None:
    source = AUDIT_SCRIPT.read_text(encoding="utf-8")
    assert "from open_ux.cli import main" in source
    assert "load_catalog" not in source
    assert "from open_ux.audit import" not in source
    assert "sys.path.insert" not in source
    assert "--jobs" in source
    assert "--guideline-ids" in source
    assert "not required" in source.lower()
    assert "must run" not in source.lower()
