from __future__ import annotations

import importlib.util
import io
import json
from email.message import Message
from pathlib import Path
from types import ModuleType
from typing import Any
from urllib.error import HTTPError

import pytest

ROOT = Path(__file__).resolve().parents[3]
HELPER = ROOT / "scripts" / "mcp_call.py"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("open_ux_mcp_call", HELPER)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def helper() -> ModuleType:
    return _load()


def test_hosted_http_requires_key(helper: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPEN_UX_API_KEY", raising=False)
    monkeypatch.delenv("OPEN_UX_URL", raising=False)
    monkeypatch.setenv("OPEN_UX_TRANSPORT", "http")
    with pytest.raises(helper.McpError, match="OPEN_UX_API_KEY"):
        helper.call_tool("audit", {"jobs": "design_a_form"})


def test_http_helper_unwraps_sse_tool_result(helper: ModuleType) -> None:
    sse = (
        "event: message\n"
        'data: {"jsonrpc":"2.0","id":1,"result":{"structuredContent":{"ok":true}}}\n\n'
    ).encode("utf-8")
    msg = helper._parse_rpc_body("text/event-stream", sse)
    assert helper._unwrap_tool_result(msg["result"]) == {"ok": True}


def test_http_helper_maps_401(helper: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_args: Any, **_kwargs: Any) -> Any:
        raise HTTPError(
            "https://open-ux.dev/mcp",
            401,
            "Unauthorized",
            hdrs=Message(),
            fp=io.BytesIO(b'{"error":"no"}'),
        )

    monkeypatch.setattr(helper.urllib.request, "urlopen", boom)
    with pytest.raises(helper.McpError, match="OPEN_UX_API_KEY"):
        helper._http_post("https://open-ux.dev/mcp", {"jsonrpc": "2.0"}, {}, None)


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
    assert "catalog/rules" not in source
    assert "from open_ux.audit import" not in source
    assert "load_catalog" not in source
    assert "tools/list" in source
    assert "tools/call" in source
