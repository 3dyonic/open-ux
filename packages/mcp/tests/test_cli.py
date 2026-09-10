from __future__ import annotations

import json
from pathlib import Path

import pytest

from open_ux.cli import main
from open_ux.jobs import CARD_IDS

ROOT = Path(__file__).resolve().parents[3]


def test_cli_pack_prints_pack(
    live_catalog: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["pack", "--jobs", "design_a_form"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["count"] >= 1
    assert "verdict" not in payload
    assert payload["host"] == "citations_only"
    assert "guidelines" in payload


def test_cli_unknown_job_lists_cards(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["pack", "--jobs", "not_a_card"]) == 2
    err = capsys.readouterr().err
    assert "unknown" in err.lower()
    assert "design_a_form" in err
    for card_id in CARD_IDS:
        assert card_id in err


def test_cli_unknown_get_lists_cards(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["get", "not_a_card"]) == 2
    err = capsys.readouterr().err
    assert "unknown" in err.lower()
    assert "design_a_form" in err


def test_cli_cards_lists_situations(
    live_catalog: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["cards"]) == 0
    payload = json.loads(capsys.readouterr().out)
    blob = json.dumps(payload)
    assert "design_a_form" in blob


def test_cli_get_and_cite(
    live_catalog: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["get", "design_a_form"]) == 0
    card = json.loads(capsys.readouterr().out)
    assert "design_a_form" in json.dumps(card)
    assert main(["cite", "govuk.button-types-named"]) == 0
    cited = json.loads(capsys.readouterr().out)
    assert cited["found"] is True
    assert cited["guideline"]["id"] == "govuk.button-types-named"
    assert "verdict" not in cited


def test_cli_components_and_component(
    live_catalog: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["components"]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed["count"] == 38
    assert main(["component", "button"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["found"] is True
    assert payload["component"]["id"] == "button"
    assert main(["component", "button", "--include-used-on"]) == 0
    with_used_on = json.loads(capsys.readouterr().out)
    assert with_used_on["component"]["used_on"]["cites_total"] == 31


def test_helpers_have_no_path_hacks() -> None:
    for name in ("pack.py", "mcp_call.py", "get_component.py"):
        source = (ROOT / "helpers" / name).read_text(encoding="utf-8")
        assert "sys.path.insert" not in source
        assert "from open_ux.cli import main" in source


def test_client_has_no_catalog_import() -> None:
    from open_ux import client

    source = Path(client.__file__).read_text(encoding="utf-8")
    assert "load_catalog" not in source
    assert "from open_ux.pack import" not in source
