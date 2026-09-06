from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import ValidationError

from open_ux.catalog import AGENT_KEYS, CatalogError, load_catalog
from open_ux.jobs import CARD_IDS, CONTAINER_IDS, LEAF_IDS, load_job_tree
from open_ux.settings import HARD_CATALOG_BYTES, Settings

LIVE_SEED = (
    "forms.field_labels.visible_label",
    "forms.field_labels.label_stays_visible",
    "forms.field_labels.error_identifies_and_fixes",
)
INDEX_REQUIRED = {"id", "title", "jobs", "lane", "container", "card", "facet"}
INDEX_OPTIONAL = {"leaf"}
BODY_KEYS = {"pass_when", "fail_when", "rule", "citation", "check"}
EXTRA_PREFIXES = ("govuk.", "nng.", "fluent.", "polar.")
HARVEST3_PREFIXES = ("spectrum.", "ant.", "mui.")
HARVEST4_PREFIXES = ("uswds.", "canada.", "nsw.")
HARVEST5_PREFIXES = ("gold.", "nl.", "suomi.")
INVENTED_FIELDS = {"when_to_use", "when_not", "when-to-use", "when-not"}
LANE_BLOBS = (
    "actions.json",
    "forms.json",
    "govuk.json",
    "nng.json",
    "fluent.json",
    "polar.json",
    "spectrum.json",
    "ant.json",
    "mui.json",
    "uswds.json",
    "canada.json",
    "nsw.json",
    "gold.json",
    "nl.json",
    "suomi.json",
)
CLUSTER_ONLY = {
    "compose_a_data_display",
    "choose_an_overlay",
    "build_a_multi_step_flow",
}


def _huge_rule() -> dict:
    return {
        "id": "pad.huge",
        "title": "pad",
        "rule": "x" * (HARD_CATALOG_BYTES + 32),
        "citation": {"source": "test", "url": "https://example.com/pad"},
        "check": "deterministic",
        "pass_when": ["ok"],
        "fail_when": ["bad"],
        "severity": "info",
        "container": "forms_and_input",
        "card": "design_a_form",
        "facet": "field_has_no_lasting_name",
        "leaf": "name_a_control",
        "waive_reason": "test pad",
    }


def test_empty_catalog_validates(tmp_env: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    assert catalog.empty
    assert catalog.guidelines == []
    assert catalog.jobs == []
    assert catalog.patterns == []


def test_invalid_catalog_rejected(tmp_env: Path, catalog_dir: Path) -> None:
    rules = catalog_dir / "rules"
    rules.mkdir(exist_ok=True)
    (rules / "nope.json").write_text(
        json.dumps({"id": "nope"}),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_catalog(Settings.load(hosted=True))


def test_hard_size_ceiling(tmp_env: Path, catalog_dir: Path) -> None:
    rules = catalog_dir / "rules"
    rules.mkdir(exist_ok=True)
    (rules / "pad.huge.json").write_text(
        json.dumps(_huge_rule()),
        encoding="utf-8",
    )
    with pytest.raises(CatalogError):
        load_catalog(Settings.load(hosted=True))


def test_rules_load_309_and_keep_harvest_counts(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    ids = [g["id"] for g in catalog.guidelines]
    action_ids = [i for i in ids if i.startswith("actions.")]
    form_ids = [i for i in ids if i.startswith("forms.")]
    extra_ids = [i for i in ids if i.startswith(EXTRA_PREFIXES)]
    harvest3_ids = [i for i in ids if i.startswith(HARVEST3_PREFIXES)]
    harvest4_ids = [i for i in ids if i.startswith(HARVEST4_PREFIXES)]
    harvest5_ids = [i for i in ids if i.startswith(HARVEST5_PREFIXES)]
    assert len(action_ids) == 40
    assert len(form_ids) == 54
    assert len(extra_ids) == 73
    assert len(harvest3_ids) == 56
    assert len(harvest4_ids) == 46
    assert len(harvest5_ids) == 40
    assert len(ids) == 309
    assert set(ids) == set(action_ids) | set(form_ids) | set(extra_ids) | set(
        harvest3_ids
    ) | set(harvest4_ids) | set(harvest5_ids)
    for seed in LIVE_SEED:
        assert seed in form_ids
    assert ids[:3] == list(LIVE_SEED)
    by_id = {g["id"]: g for g in catalog.guidelines}
    for gid in extra_ids + harvest3_ids + harvest4_ids + harvest5_ids:
        assert INVENTED_FIELDS.isdisjoint(by_id[gid])
        assert "do_not_claim" in by_id[gid]
        assert by_id[gid]["do_not_claim"]
    for g in catalog.guidelines:
        assert "lane" not in g
        assert g["citation"]["url"].startswith("https://")
        assert "](<" not in g["citation"]["url"]
        assert g["severity"] == "major"
        assert g["container"] in CONTAINER_IDS
        assert g["card"] in CARD_IDS
        assert g.get("leaf") in LEAF_IDS or g.get("leaf") is None
        if g.get("overview"):
            for key in AGENT_KEYS:
                assert g[key]
            assert "waive_reason" not in g
        else:
            assert g.get("waive_reason")
        assert INVENTED_FIELDS.isdisjoint(g)
    assert catalog.size_bytes <= HARD_CATALOG_BYTES


def test_no_lane_blobs(live_catalog: Path) -> None:
    for name in LANE_BLOBS:
        assert not (live_catalog / name).exists()
    rules = list((live_catalog / "rules").glob("*.json"))
    assert len(rules) == 309
    for path in rules:
        data = json.loads(path.read_text(encoding="utf-8"))
        assert path.stem == data["id"]


def test_on_disk_index_has_no_rule_bodies(live_catalog: Path) -> None:
    data = json.loads((live_catalog / "index.json").read_text(encoding="utf-8"))
    rows = data["guidelines"]
    assert len(rows) == 309
    extra_ids = [row["id"] for row in rows if row["id"].startswith(EXTRA_PREFIXES)]
    harvest3_ids = [row["id"] for row in rows if row["id"].startswith(HARVEST3_PREFIXES)]
    harvest4_ids = [row["id"] for row in rows if row["id"].startswith(HARVEST4_PREFIXES)]
    harvest5_ids = [row["id"] for row in rows if row["id"].startswith(HARVEST5_PREFIXES)]
    assert len(extra_ids) == 73
    assert len(harvest3_ids) == 56
    assert len(harvest4_ids) == 46
    assert len(harvest5_ids) == 40
    for row in rows:
        assert INDEX_REQUIRED <= set(row) <= (INDEX_REQUIRED | INDEX_OPTIONAL)
        assert BODY_KEYS.isdisjoint(row)
        dumped = json.dumps(row)
        assert "pass_when" not in dumped
        assert '"rule"' not in dumped
        assert "do_not_claim" not in dumped
    catalog = load_catalog(Settings.load(hosted=True))
    assert [row["id"] for row in catalog.index] == [g["id"] for g in catalog.guidelines]
    for seed in LIVE_SEED:
        assert seed in {row["id"] for row in catalog.index}


def test_every_rule_has_one_home(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    tree = load_job_tree(Settings.load())
    facet_home = {}
    cluster_facets = set()
    for card in tree.cards:
        for facet in card.facets:
            facet_home[facet.id] = (card.container, card.id, bool(facet.leaves))
            if not facet.leaves:
                cluster_facets.add(facet.id)
    unmapped: list[str] = []
    for guideline in catalog.guidelines:
        home = facet_home.get(guideline["facet"])
        if home is None or home[0] != guideline["container"] or home[1] != guideline["card"]:
            unmapped.append(guideline["id"])
            continue
        if home[2] and guideline.get("leaf") not in LEAF_IDS:
            unmapped.append(guideline["id"])
        if not home[2] and guideline.get("leaf"):
            unmapped.append(guideline["id"])
    assert unmapped == []
    for gid in (
        "canada.tables-no-blank-cells",
        "nng.modal-and-nonmodal-dialogs",
        "nl.step-n-of-m-in-title-and-above-form",
    ):
        row = next(g for g in catalog.guidelines if g["id"] == gid)
        assert "leaf" not in row
        assert row["card"] in CLUSTER_ONLY or gid == "nng.modal-and-nonmodal-dialogs"


def test_live_seeds_keep_locked_homes_and_agent_fields(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    by_id = {g["id"]: g for g in catalog.guidelines}
    visible = by_id["forms.field_labels.visible_label"]
    assert visible["card"] == "design_a_form"
    assert visible["leaf"] == "avoid_placeholder_as_label"
    assert visible["overview"].startswith("A lasting label")
    stays = by_id["forms.field_labels.label_stays_visible"]
    assert stays["card"] == "design_a_form"
    assert stays["leaf"] == "keep_field_purpose_visible_while_filled"
    error = by_id["forms.field_labels.error_identifies_and_fixes"]
    assert error["card"] == "handle_form_errors"
    assert error["leaf"] == "explain_failure_next_to_cause"


def test_jobs_json_is_not_a_lane(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    assert len(catalog.guidelines) == 309
    tree = load_job_tree(Settings.load())
    assert [card.id for card in tree.cards] == list(CARD_IDS)
