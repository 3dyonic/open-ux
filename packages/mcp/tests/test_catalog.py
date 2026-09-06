from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import ValidationError, validate

from open_ux.catalog import (
    AGENT_KEYS,
    CatalogError,
    build_manifest,
    citations,
    load_catalog,
    rule_file_stem,
    rule_relpath,
    source_house,
)
from open_ux.jobs import CARD_IDS, CONTAINER_IDS, LEAF_IDS, load_job_tree
from open_ux.settings import HARD_CATALOG_BYTES, Settings

LIVE_SEED = (
    "forms.field_labels.visible_label",
    "forms.field_labels.label_stays_visible",
    "forms.field_labels.error_identifies_and_fixes",
)
INDEX_REQUIRED = {"id", "title", "name", "jobs", "lane", "container", "card", "facet"}
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
UNMAPPED_DROPPED = {
    "canada.functional-alt-140-decorative-empty",
    "canada.tables-no-blank-cells",
    "nl.last-step-is-send-not-volgende",
    "nng.eas-framework",
    "nng.guest-checkout-prominent",
    "polar.be-consistent-no-synonyms",
    "uswds.search-min-27-chars-persist-query",
}
FOLDED_IDS = {
    "nl.dont-reject-valid-variants",
    "nl.no-forced-input-patterns-or-masks",
    "forms.inputs.allow_typos_abbreviations",
    "fluent.required-asterisk-or-one-instruction",
    "suomi.default-required-optional-in-parentheses",
    "nl.mark-optional-niet-verplicht-above-form",
    "suomi.toggle-button-immediate-input-submit",
}
UNWOUND_IDS = {
    "nng.too-few-options-radios-not-dropdown",
    "nng.prefer-radios-over-dropdowns-when-visible",
    "gold.avoid-select-except-long-lists",
    "govuk.select-last-resort",
    "polar.select-4plus-choice-list-under-4",
    "ant.radio-count-2-to-5",
    "govuk.calendar-control-when",
    "govuk.date-input-only-memorable",
    "uswds.date-picker-when-weekday-always-type",
    "polar.default-option-selected-when-possible",
}
MULTI_CITE_KEEPS = {
    "forms.inputs.forgiving_format_autoformat",
    "forms.fields.distinguish_optional_required",
    "ant.checkbox-vs-switch",
}
CATALOG_COUNT = 295
ACTION_COUNT = 40
FORM_COUNT = 53
EXTRA_COUNT = 69
HARVEST3_COUNT = 56
HARVEST4_COUNT = 43
HARVEST5_COUNT = 34


def _huge_rule() -> dict:
    return {
        "id": "pad.huge",
        "title": "pad",
        "name": "Pad",
        "rule": "x" * (HARD_CATALOG_BYTES + 32),
        "citation": [{"source": "test", "url": "https://example.com/pad"}],
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


def _assert_citations(guideline: dict) -> None:
    cites = citations(guideline)
    assert cites
    seen_urls: set[str] = set()
    for cite in cites:
        assert cite["source"]
        assert cite["url"].startswith("https://")
        assert "](<" not in cite["url"]
        assert cite["url"] not in seen_urls
        seen_urls.add(cite["url"])


def test_rules_load_harvest_counts_after_same_claim_fold(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    ids = [g["id"] for g in catalog.guidelines]
    action_ids = [i for i in ids if i.startswith("actions.")]
    form_ids = [i for i in ids if i.startswith("forms.")]
    extra_ids = [i for i in ids if i.startswith(EXTRA_PREFIXES)]
    harvest3_ids = [i for i in ids if i.startswith(HARVEST3_PREFIXES)]
    harvest4_ids = [i for i in ids if i.startswith(HARVEST4_PREFIXES)]
    harvest5_ids = [i for i in ids if i.startswith(HARVEST5_PREFIXES)]
    assert len(action_ids) == ACTION_COUNT
    assert len(form_ids) == FORM_COUNT
    assert len(extra_ids) == EXTRA_COUNT
    assert len(harvest3_ids) == HARVEST3_COUNT
    assert len(harvest4_ids) == HARVEST4_COUNT
    assert len(harvest5_ids) == HARVEST5_COUNT
    assert len(ids) == CATALOG_COUNT
    assert UNMAPPED_DROPPED.isdisjoint(ids)
    assert FOLDED_IDS.isdisjoint(ids)
    assert UNWOUND_IDS <= set(ids)
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
    for gid in MULTI_CITE_KEEPS:
        cites = citations(by_id[gid])
        assert len(cites) >= 2
        assert isinstance(by_id[gid]["citation"], list)
    for g in catalog.guidelines:
        assert "lane" not in g
        assert isinstance(g["citation"], list)
        _assert_citations(g)
        assert g["severity"] == "major"
        assert g["container"] in CONTAINER_IDS
        assert g["card"] in CARD_IDS
        assert g.get("leaf") in LEAF_IDS
        assert g["name"]
        assert g["name"] != g["id"]
        for key in AGENT_KEYS:
            assert g[key]
        assert "waive_reason" not in g
        assert INVENTED_FIELDS.isdisjoint(g)
    assert catalog.size_bytes <= HARD_CATALOG_BYTES


def test_no_lane_blobs(live_catalog: Path) -> None:
    for name in LANE_BLOBS:
        assert not (live_catalog / name).exists()
    rules = list((live_catalog / "rules").rglob("*.json"))
    assert list((live_catalog / "rules").glob("*.json")) == []
    assert len(rules) == CATALOG_COUNT
    for path in rules:
        data = json.loads(path.read_text(encoding="utf-8"))
        assert path.stem == rule_file_stem(data["id"])
        assert path.stem != data["id"]
        assert path == live_catalog / "rules" / rule_relpath(data)


def test_on_disk_index_has_no_rule_bodies(live_catalog: Path) -> None:
    data = json.loads((live_catalog / "index.json").read_text(encoding="utf-8"))
    rows = data["guidelines"]
    assert len(rows) == CATALOG_COUNT
    extra_ids = [row["id"] for row in rows if row["id"].startswith(EXTRA_PREFIXES)]
    harvest3_ids = [row["id"] for row in rows if row["id"].startswith(HARVEST3_PREFIXES)]
    harvest4_ids = [row["id"] for row in rows if row["id"].startswith(HARVEST4_PREFIXES)]
    harvest5_ids = [row["id"] for row in rows if row["id"].startswith(HARVEST5_PREFIXES)]
    assert len(extra_ids) == EXTRA_COUNT
    assert len(harvest3_ids) == HARVEST3_COUNT
    assert len(harvest4_ids) == HARVEST4_COUNT
    assert len(harvest5_ids) == HARVEST5_COUNT
    assert FOLDED_IDS.isdisjoint({row["id"] for row in rows})
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
    by_id = {g["id"]: g for g in catalog.guidelines}
    assert by_id["nng.modal-and-nonmodal-dialogs"]["leaf"] == "pick_modal_only_when_blocking"
    assert by_id["nl.step-n-of-m-in-title-and-above-form"]["leaf"] == "show_step_progress"
    assert by_id["nsw.charts-start-with-story"]["leaf"] == "chart_has_a_story"
    assert UNMAPPED_DROPPED.isdisjoint(by_id)
    assert FOLDED_IDS.isdisjoint(by_id)


def test_live_seeds_keep_locked_homes_and_agent_fields(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    by_id = {g["id"]: g for g in catalog.guidelines}
    visible = by_id["forms.field_labels.visible_label"]
    assert visible["card"] == "design_a_form"
    assert visible["leaf"] == "avoid_placeholder_as_label"
    assert visible["name"] == "Visible field label — NN/g"
    assert visible["overview"].startswith("A lasting label")
    stays = by_id["forms.field_labels.label_stays_visible"]
    assert stays["card"] == "design_a_form"
    assert stays["leaf"] == "avoid_placeholder_as_label"
    error = by_id["forms.field_labels.error_identifies_and_fixes"]
    assert error["card"] == "handle_form_errors"
    assert error["leaf"] == "explain_failure_next_to_cause"


def test_schema_citation_is_array_of_one_or_many(live_catalog: Path) -> None:
    schema = json.loads((live_catalog / "schema.json").read_text())
    base = {
        "id": "cite.shape",
        "title": "shape",
        "name": "Shape",
        "rule": "one claim",
        "check": "deterministic",
        "pass_when": ["ok"],
        "fail_when": ["bad"],
        "severity": "major",
        "container": "forms_and_input",
        "card": "design_a_form",
        "facet": "field_has_no_lasting_name",
        "leaf": "name_a_control",
        "waive_reason": "shape probe",
    }
    one = {"source": "A", "url": "https://a.example/x"}
    validate(instance={**base, "citation": [one]}, schema=schema)
    validate(
        instance={**base, "citation": [one, {"source": "B", "url": "https://b.example/y"}]},
        schema=schema,
    )
    with pytest.raises(ValidationError):
        validate(instance={**base, "citation": one}, schema=schema)


def test_citation_is_object_or_array_of_sources() -> None:
    assert citations({"citation": {"source": "A", "url": "https://a.example"}}) == [
        {"source": "A", "url": "https://a.example"}
    ]
    assert citations(
        {"citation": [{"source": "A", "url": "https://a.example"}]}
    ) == [{"source": "A", "url": "https://a.example"}]
    assert citations(
        {
            "citation": [
                {"source": "A", "url": "https://a.example"},
                {"source": "B", "url": "https://b.example"},
            ]
        }
    ) == [
        {"source": "A", "url": "https://a.example"},
        {"source": "B", "url": "https://b.example"},
    ]
    assert citations({}) == []


def test_distinct_claims_are_not_folded(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    ids = {g["id"] for g in catalog.guidelines}
    by_id = {g["id"]: g for g in catalog.guidelines}
    assert "nng.dropdown-ok-narrow-middle" in ids
    assert "nng.too-many-combobox-not-long-dropdown" in ids
    assert "forms.inputs.dropdown_chooser" in ids
    assert "forms.inputs.offer_choices_not_only_text" in ids
    assert "spectrum.asterisk-is-icon-not-label-text" in ids
    assert "nng.always-select-one-radio-by-default" in ids
    assert "govuk.select-preselect-settings-not-questions" in ids
    assert UNWOUND_IDS <= ids
    for gid in (
        "forms.inputs.match_control_and_size",
        "govuk.four-date-types",
        "nng.users-rarely-change-defaults",
    ):
        assert len(citations(by_id[gid])) == 1


def test_jobs_json_is_not_a_lane(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    assert len(catalog.guidelines) == CATALOG_COUNT
    tree = load_job_tree(Settings.load())
    assert [card.id for card in tree.cards] == list(CARD_IDS)
    assert len(CARD_IDS) == 13
    assert len(CONTAINER_IDS) == 7
    assert "write_the_interface" in CARD_IDS
    assert "content" not in CONTAINER_IDS


def test_fourteen_drops_are_listed_and_absent(live_catalog: Path) -> None:
    locks = (live_catalog / "locks.md").read_text(encoding="utf-8")
    catalog = load_catalog(Settings.load(hosted=True))
    ids = {g["id"] for g in catalog.guidelines}
    dropped = UNMAPPED_DROPPED | FOLDED_IDS
    assert len(dropped) == 14
    assert dropped.isdisjoint(ids)
    for gid in sorted(dropped):
        assert f"`{gid}`" in locks
    assert "content/" in locks
    assert "not an 8th container" in locks


def test_names_are_claim_then_source_and_folders_follow_category(
    live_catalog: Path,
) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    by_id = {g["id"]: g for g in catalog.guidelines}
    visible = by_id["forms.field_labels.visible_label"]
    assert visible["name"] == "Visible field label — NN/g"
    assert visible["category"] == "Forms"
    assert (live_catalog / "rules" / "forms" / "nng" / "field_labels.visible_label.json").is_file()

    primary = by_id["actions.buttons.one_primary"]
    assert primary["name"] == "One primary action — NN/g"
    assert primary["category"] == "Actions"
    assert (live_catalog / "rules" / "actions" / "nng" / "buttons.one_primary.json").is_file()

    ant = by_id["ant.one-cta-per-screen"]
    assert ant["name"] == "One CTA per screen — Ant"
    assert ant["category"] == "Actions"
    assert (live_catalog / "rules" / "actions" / "ant" / "one-cta-per-screen.json").is_file()

    for guideline in catalog.guidelines:
        _slug, label = source_house(guideline)
        assert guideline["name"].endswith(f" — {label}")
        assert not guideline["name"].endswith(" — Actions")
        assert not guideline["name"].endswith(" — Forms")


def test_manifest_is_category_then_source_without_bodies(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    data = json.loads((live_catalog / "manifest.json").read_text(encoding="utf-8"))
    markdown = (live_catalog / "MANIFEST.md").read_text(encoding="utf-8")
    assert data["count"] == CATALOG_COUNT
    assert data == build_manifest(catalog.guidelines)
    dumped = json.dumps(data)
    assert "pass_when" not in dumped
    assert "fail_when" not in dumped
    assert "pass_when" not in markdown
    actions = next(item for item in data["categories"] if item["id"] == "actions")
    sources = {item["id"] for item in actions["sources"]}
    assert "ant" in sources
    assert "nng" in sources
    assert "actions" not in sources
    assert "One CTA per screen — Ant" in markdown
    assert "catalog/rules/{category}/{source}/{file}.json" in markdown
