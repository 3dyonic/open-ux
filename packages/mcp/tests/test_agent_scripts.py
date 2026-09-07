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
SCRIPTS = ROOT / "clients" / "claude" / "skills" / "open-ux" / "scripts"


def _load(name: str) -> ModuleType:
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"open_ux_scripts.{name}", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def scripts() -> dict[str, ModuleType]:
    helper = _load("_mcp")
    loaded = {"_mcp": helper}
    for name in ("audit", "get", "list", "suggest"):
        loaded[name] = _load(name)
    return loaded


def test_audit_requires_jobs_or_ids(scripts: dict[str, ModuleType], capsys: pytest.CaptureFixture[str]) -> None:
    assert scripts["audit"].main([]) == 2
    payload = json.loads(capsys.readouterr().out)
    assert "jobs=" in payload["error"]
    assert "guideline-ids" in payload["error"]


@pytest.mark.parametrize(
    "argv",
    (
        ["--file", "form.html"],
        ["--content", "<form></form>"],
        ["--target", "ui.png"],
        ["--verdict", "fail"],
        ["ui.html"],
    ),
)
def test_audit_rejects_a_file(
    scripts: dict[str, ModuleType],
    argv: list[str],
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    if argv[0] == "ui.html":
        (tmp_path / "ui.html").write_text("<form></form>", encoding="utf-8")
    assert scripts["audit"].main(argv) == 2
    payload = json.loads(capsys.readouterr().out)
    assert "never takes a file" in payload["error"] or "never scores" in payload["error"]


def test_audit_parses_jobs_equals(scripts: dict[str, ModuleType], monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[tuple[str, dict[str, Any]]] = []

    def fake(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        seen.append((name, arguments or {}))
        return {"guidelines": [], "count": 0, "total": 0}

    monkeypatch.setattr(scripts["audit"]._mcp, "call_tool", fake)
    assert scripts["audit"].main(["jobs=design_a_form", "--query", "label", "--limit", "3"]) == 0
    assert seen == [
        (
            "audit",
            {"jobs": "design_a_form", "query": "label", "limit": 3},
        )
    ]


def test_get_routes_card_vs_guideline(scripts: dict[str, ModuleType]) -> None:
    assert scripts["get"].route("design_a_form") == ("get_situation", {"id": "design_a_form"})
    assert scripts["get"].route("forms") == ("get_situation", {"id": "forms"})
    assert scripts["get"].route("ant.checkbox-vs-switch") == (
        "get_guideline",
        {"id": "ant.checkbox-vs-switch"},
    )


def test_list_default_is_situations(scripts: dict[str, ModuleType], monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[tuple[str, dict[str, Any]]] = []

    def fake(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        seen.append((name, arguments or {}))
        return {"situations": [{"id": "design_a_form"}], "count": 1}

    monkeypatch.setattr(scripts["list"]._mcp, "call_tool", fake)
    assert scripts["list"].main(["forms"]) == 0
    assert seen == [("list_situations", {"offset": 0, "container": "forms"})]


def test_list_guidelines_uses_search_when_query(
    scripts: dict[str, ModuleType], monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[str] = []

    def fake(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        seen.append(name)
        return {"guidelines": [], "count": 0}

    monkeypatch.setattr(scripts["list"]._mcp, "call_tool", fake)
    assert scripts["list"].main(["--guidelines", "--query", "checkbox"]) == 0
    assert seen == ["search_guidelines"]


def test_suggest_requires_task_text(
    scripts: dict[str, ModuleType], capsys: pytest.CaptureFixture[str]
) -> None:
    assert scripts["suggest"].main([]) == 2
    assert "task text" in json.loads(capsys.readouterr().out)["error"]


def test_hosted_http_requires_key(scripts: dict[str, ModuleType], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPEN_UX_API_KEY", raising=False)
    monkeypatch.delenv("OPEN_UX_URL", raising=False)
    monkeypatch.setenv("OPEN_UX_TRANSPORT", "http")
    with pytest.raises(scripts["_mcp"].McpError, match="OPEN_UX_API_KEY"):
        scripts["_mcp"].call_tool("audit", {"jobs": "design_a_form"})


def test_http_helper_unwraps_sse_tool_result(scripts: dict[str, ModuleType]) -> None:
    helper = scripts["_mcp"]
    sse = (
        "event: message\n"
        'data: {"jsonrpc":"2.0","id":1,"result":{"structuredContent":{"ok":true}}}\n\n'
    ).encode("utf-8")
    msg = helper._parse_rpc_body("text/event-stream", sse)
    assert helper._unwrap_tool_result(msg["result"]) == {"ok": True}


def test_http_helper_maps_401(scripts: dict[str, ModuleType], monkeypatch: pytest.MonkeyPatch) -> None:
    helper = scripts["_mcp"]

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


def test_audit_inprocess_prints_pack(
    live_catalog: Path,
    scripts: dict[str, ModuleType],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("OPEN_UX_TRANSPORT", "inprocess")
    assert scripts["audit"].main(["--jobs", "design_a_form"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["count"] >= 1
    assert "verdict" not in payload
    row = payload["guidelines"][0]
    assert set(row) == {"id", "title", "name", "rule", "pass_when", "fail_when"}


def test_get_inprocess_card_and_guideline(
    live_catalog: Path,
    scripts: dict[str, ModuleType],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("OPEN_UX_TRANSPORT", "inprocess")
    assert scripts["get"].main(["design_a_form"]) == 0
    card = json.loads(capsys.readouterr().out)
    assert card["found"] is True
    assert card["situation"]["id"] == "design_a_form"
    assert "pass_when" not in json.dumps(card)

    assert scripts["get"].main(["ant.checkbox-vs-switch"]) == 0
    body = json.loads(capsys.readouterr().out)
    assert body["found"] is True
    assert body["guideline"]["id"] == "ant.checkbox-vs-switch"


def test_list_and_suggest_inprocess(
    live_catalog: Path,
    scripts: dict[str, ModuleType],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("OPEN_UX_TRANSPORT", "inprocess")
    assert scripts["list"].main(["--situations", "--container", "forms"]) == 0
    listed = json.loads(capsys.readouterr().out)
    ids = {row["id"] for row in listed["situations"]}
    assert "design_a_form" in ids
    assert "rule" not in json.dumps(listed)

    assert scripts["suggest"].main(["signup form field labels", "--surface", "checkout"]) == 0
    suggested = json.loads(capsys.readouterr().out)
    assert suggested["situations"]
    assert suggested["situations"][0]["id"] == "design_a_form"


def test_scripts_never_import_catalog(scripts: dict[str, ModuleType]) -> None:
    for name in ("audit", "get", "list", "suggest", "_mcp"):
        source = (SCRIPTS / f"{name}.py").read_text(encoding="utf-8")
        assert "catalog/rules" not in source
        assert "load_catalog" not in source
