from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import ValidationError

from open_ux.catalog import CatalogError, load_catalog
from open_ux.settings import HARD_CATALOG_BYTES, Settings

LIVE_SEED = (
    "forms.field_labels.visible_label",
    "forms.field_labels.label_stays_visible",
    "forms.field_labels.error_identifies_and_fixes",
)
INDEX_KEYS = {"id", "title", "jobs", "lane"}
BODY_KEYS = {"pass_when", "fail_when", "rule", "citation", "check"}


def test_empty_catalog_validates(tmp_env: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    assert catalog.empty
    assert catalog.guidelines == []
    assert catalog.jobs == []
    assert catalog.patterns == []


def test_invalid_catalog_rejected(tmp_env: Path, catalog_dir: Path) -> None:
    (catalog_dir / "guidelines.json").write_text(
        json.dumps({"version": "1", "guidelines": [{"id": "nope"}]}),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_catalog(Settings.load(hosted=True))


def test_hard_size_ceiling(tmp_env: Path, catalog_dir: Path) -> None:
    blob = b'{"version":"x","guidelines":[]}' + b" " * (HARD_CATALOG_BYTES + 8)
    (catalog_dir / "guidelines.json").write_bytes(blob)
    with pytest.raises(CatalogError):
        load_catalog(Settings.load(hosted=True))


def test_lanes_load_40_actions_54_forms_no_extras(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    ids = [g["id"] for g in catalog.guidelines]
    action_ids = [i for i in ids if i.startswith("actions.")]
    form_ids = [i for i in ids if i.startswith("forms.")]
    assert len(action_ids) == 40
    assert len(form_ids) == 54
    assert len(ids) == 94
    assert set(ids) == set(action_ids) | set(form_ids)
    for seed in LIVE_SEED:
        assert seed in form_ids
    assert form_ids[:3] == list(LIVE_SEED)
    for g in catalog.guidelines:
        assert "lane" not in g
        assert g["jobs"] in (["actions"], ["forms"])
        assert g["citation"]["url"].startswith("https://")
        assert "](<" not in g["citation"]["url"]
        assert g["severity"] == "major"
    assert catalog.size_bytes <= HARD_CATALOG_BYTES


def test_on_disk_index_has_no_rule_bodies(live_catalog: Path) -> None:
    data = json.loads((live_catalog / "index.json").read_text(encoding="utf-8"))
    rows = data["guidelines"]
    assert len(rows) == 94
    for row in rows:
        assert set(row) == INDEX_KEYS
        assert BODY_KEYS.isdisjoint(row)
        dumped = json.dumps(row)
        assert "pass_when" not in dumped
        assert '"rule"' not in dumped
    catalog = load_catalog(Settings.load(hosted=True))
    assert [row["id"] for row in catalog.index] == [g["id"] for g in catalog.guidelines]
    for seed in LIVE_SEED:
        assert seed in {row["id"] for row in catalog.index}
