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
JOBS_15 = {
    "name_a_control",
    "avoid_placeholder_as_label",
    "keep_field_purpose_visible_while_filled",
    "recover_from_invalid_input",
    "explain_failure_next_to_cause",
    "choose_control_for_choice",
    "group_related_inputs",
    "announce_system_status",
    "wayfind_after_nav",
    "use_familiar_control",
    "write_empty_state",
    "tone_of_voice_for_failure",
    "pick_primary_action",
    "disable_or_confirm_destructive",
    "keep_hit_target_usable",
}
EXTRA_PREFIXES = ("govuk.", "nng.", "fluent.", "polar.")
HARVEST3_PREFIXES = ("spectrum.", "ant.", "mui.")
INVENTED_FIELDS = {"when_to_use", "when_not", "when-to-use", "when-not"}


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


def test_lanes_load_40_actions_54_forms_extra_73_and_harvest3_56(
    live_catalog: Path,
) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    ids = [g["id"] for g in catalog.guidelines]
    action_ids = [i for i in ids if i.startswith("actions.")]
    form_ids = [i for i in ids if i.startswith("forms.")]
    extra_ids = [i for i in ids if i.startswith(EXTRA_PREFIXES)]
    harvest3_ids = [i for i in ids if i.startswith(HARVEST3_PREFIXES)]
    assert len(action_ids) == 40
    assert len(form_ids) == 54
    assert len(extra_ids) == 73
    assert len(harvest3_ids) == 56
    assert len(ids) == 223
    assert set(ids) == set(action_ids) | set(form_ids) | set(extra_ids) | set(
        harvest3_ids
    )
    for seed in LIVE_SEED:
        assert seed in form_ids
    assert form_ids[:3] == list(LIVE_SEED)
    by_id = {g["id"]: g for g in catalog.guidelines}
    for gid in action_ids:
        assert by_id[gid]["jobs"] == ["actions"]
        assert "do_not_claim" not in by_id[gid]
        assert INVENTED_FIELDS.isdisjoint(by_id[gid])
    for gid in form_ids:
        assert by_id[gid]["jobs"] == ["forms"]
        assert "do_not_claim" not in by_id[gid]
        assert INVENTED_FIELDS.isdisjoint(by_id[gid])
    for gid in extra_ids + harvest3_ids:
        jobs = by_id[gid]["jobs"]
        assert jobs
        assert set(jobs) <= JOBS_15
        assert INVENTED_FIELDS.isdisjoint(by_id[gid])
        assert "do_not_claim" in by_id[gid]
        assert by_id[gid]["do_not_claim"]
    for g in catalog.guidelines:
        assert "lane" not in g
        assert g["citation"]["url"].startswith("https://")
        assert "](<" not in g["citation"]["url"]
        assert g["severity"] == "major"
    assert catalog.size_bytes <= HARD_CATALOG_BYTES


def test_on_disk_index_has_no_rule_bodies(live_catalog: Path) -> None:
    data = json.loads((live_catalog / "index.json").read_text(encoding="utf-8"))
    rows = data["guidelines"]
    assert len(rows) == 223
    extra_ids = [row["id"] for row in rows if row["id"].startswith(EXTRA_PREFIXES)]
    harvest3_ids = [row["id"] for row in rows if row["id"].startswith(HARVEST3_PREFIXES)]
    assert len(extra_ids) == 73
    assert len(harvest3_ids) == 56
    for row in rows:
        assert set(row) == INDEX_KEYS
        assert BODY_KEYS.isdisjoint(row)
        dumped = json.dumps(row)
        assert "pass_when" not in dumped
        assert '"rule"' not in dumped
        assert "do_not_claim" not in dumped
    catalog = load_catalog(Settings.load(hosted=True))
    assert [row["id"] for row in catalog.index] == [g["id"] for g in catalog.guidelines]
    for seed in LIVE_SEED:
        assert seed in {row["id"] for row in catalog.index}
