from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import ValidationError, validate

from open_ux.catalog import (
    AGENT_KEYS,
    citations,
    load_catalog,
    validate_apply_when_fit,
    validate_placement,
)
from open_ux.catalog_error import CatalogError
from open_ux.manifest import build_manifest
from open_ux.rule_paths import rule_file_stem, rule_relpath, rule_source
from open_ux.jobs import (
    CARD_IDS,
    CONTAINER_IDS,
    LEAF_IDS,
    Card,
    Facet,
    JobTree,
    Leaf,
    load_job_tree,
)
from open_ux.settings import HARD_CATALOG_BYTES, Settings

REMAINING_SEED = (
    "ant.checkbox-vs-switch",
    "ant.one-cta-per-screen",
    "fluent.multistep-next-not-continue",
    "govuk.date-input-only-memorable",
)
INDEX_REQUIRED = {"id", "title", "name", "jobs", "lane", "container", "card", "facet"}
INDEX_OPTIONAL = {"leaf"}
BODY_KEYS = {"pass_when", "fail_when", "rule", "citation", "check"}
EXTRA_PREFIXES = ("govuk.", "fluent.", "polar.")
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
    "ant.checkbox-vs-switch",
}
CATALOG_COUNT = 203
ACTION_COUNT = 10
FORM_COUNT = 14
EXTRA_COUNT = 46
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
    for seed in REMAINING_SEED:
        assert seed in ids
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
        if "leaf" in g:
            assert g["leaf"] in LEAF_IDS
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
    for seed in REMAINING_SEED:
        assert seed in {row["id"] for row in catalog.index}


def test_every_rule_has_one_home(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    tree = load_job_tree(Settings.load())
    facet_home = {}
    for card in tree.cards:
        for facet in card.facets:
            facet_home[facet.id] = (
                card.container,
                card.id,
                {leaf.id for leaf in facet.leaves},
            )
    unmapped: list[str] = []
    for guideline in catalog.guidelines:
        home = facet_home.get(guideline["facet"])
        if home is None or home[0] != guideline["container"] or home[1] != guideline["card"]:
            unmapped.append(guideline["id"])
            continue
        leaf_ids = home[2]
        if leaf_ids and guideline.get("leaf") not in leaf_ids:
            unmapped.append(guideline["id"])
        if not leaf_ids and guideline.get("leaf"):
            unmapped.append(guideline["id"])
    assert unmapped == []
    by_id = {g["id"]: g for g in catalog.guidelines}
    assert by_id["mui.non-modal-dialogs-allowed"]["leaf"] == "pick_modal_only_when_blocking"
    assert by_id["nl.step-n-of-m-in-title-and-above-form"]["leaf"] == "show_step_progress"
    assert by_id["nsw.charts-start-with-story"]["leaf"] == "chart_has_a_story"
    assert UNMAPPED_DROPPED.isdisjoint(by_id)
    assert FOLDED_IDS.isdisjoint(by_id)


def test_remaining_seeds_keep_locked_homes_and_agent_fields(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    by_id = {g["id"]: g for g in catalog.guidelines}
    checkbox = by_id["ant.checkbox-vs-switch"]
    assert checkbox["card"] == "design_a_form"
    assert checkbox["leaf"] == "choose_control_for_choice"
    assert checkbox["name"] == "Checkbox vs switch — Ant"
    assert checkbox["overview"].startswith("Switches apply immediately")
    cta = by_id["ant.one-cta-per-screen"]
    assert cta["card"] == "design_actions_and_ctas"
    assert cta["leaf"] == "pick_primary_action"
    error = by_id["govuk.error-summary-plus-per-field"]
    assert error["card"] == "handle_form_errors"


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


def _schema_probe(**overrides: object) -> dict:
    row = {
        "id": "schema.probe",
        "title": "probe",
        "name": "Probe",
        "rule": "one claim",
        "citation": [{"source": "A", "url": "https://a.example/x"}],
        "check": "deterministic",
        "pass_when": ["ok"],
        "fail_when": ["bad"],
        "severity": "major",
        "container": "forms_and_input",
        "card": "design_a_form",
        "facet": "field_has_no_lasting_name",
        "leaf": "name_a_control",
        "overview": "What this is.",
        "apply_when": "When composing this.",
        "not_when": "When it is the wrong job.",
        "agent_hint": "Apply the cited claim.",
        "description": "A half-paragraph so the agent can apply the claim without opening SKILL.md.",
    }
    row.update(overrides)
    return row


def test_schema_requires_agent_fields_unless_waived(live_catalog: Path) -> None:
    schema = json.loads((live_catalog / "schema.json").read_text())
    validate(instance=_schema_probe(), schema=schema)
    waived = _schema_probe()
    for key in AGENT_KEYS:
        waived.pop(key)
    waived["waive_reason"] = "schema probe"
    validate(instance=waived, schema=schema)
    missing = _schema_probe()
    missing.pop("overview")
    with pytest.raises(ValidationError):
        validate(instance=missing, schema=schema)
    silent = _schema_probe()
    for key in AGENT_KEYS:
        silent.pop(key)
    with pytest.raises(ValidationError):
        validate(instance=silent, schema=schema)


def _placement_rule(**overrides: object) -> dict:
    row = {
        "id": "t.rule",
        "container": "forms_and_input",
        "card": "design_a_form",
        "facet": "field_has_no_lasting_name",
        "leaf": "name_a_control",
        "overview": "o",
        "apply_when": "a",
        "not_when": "n",
        "agent_hint": "h",
        "description": "d",
    }
    row.update(overrides)
    return row


def test_leaf_required_iff_facet_has_working_leaves() -> None:
    working = JobTree(
        containers=(),
        cards=(
            Card(
                id="design_a_form",
                title="Design a form",
                container="forms_and_input",
                overview="p",
                when=("w",),
                reject=(),
                hints=(),
                facets=(
                    Facet(
                        id="field_has_no_lasting_name",
                        title="t",
                        leaves=(Leaf(id="name_a_control", guideline_ids=("t.rule",)),),
                    ),
                ),
            ),
        ),
    )
    validate_placement([_placement_rule()], working)
    omitted = _placement_rule()
    omitted.pop("leaf")
    with pytest.raises(CatalogError, match="leaf"):
        validate_placement([omitted], working)

    cluster = JobTree(
        containers=(),
        cards=(
            Card(
                id="design_a_form",
                title="Design a form",
                container="forms_and_input",
                overview="p",
                when=("w",),
                reject=(),
                hints=(),
                facets=(
                    Facet(
                        id="cluster_home",
                        title="t",
                        guideline_ids=("t.cluster",),
                    ),
                ),
            ),
        ),
    )
    clustered = _placement_rule(id="t.cluster", facet="cluster_home")
    clustered.pop("leaf")
    validate_placement([clustered], cluster)
    with pytest.raises(CatalogError, match="cannot have a leaf"):
        validate_placement(
            [_placement_rule(id="t.cluster", facet="cluster_home")],
            cluster,
        )


def test_citation_is_array_of_sources() -> None:
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
    assert "forms.inputs.dropdown_chooser" in ids
    assert "spectrum.asterisk-is-icon-not-label-text" in ids
    assert "govuk.select-preselect-settings-not-questions" in ids
    assert UNWOUND_IDS <= ids
    for gid in (
        "govuk.four-date-types",
        "forms.inputs.dropdown_chooser",
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


def test_unpublished_harvest_ids_are_listed_in_readme(live_catalog: Path) -> None:
    readme = (live_catalog / "README.md").read_text(encoding="utf-8")
    catalog = load_catalog(Settings.load(hosted=True))
    ids = {g["id"] for g in catalog.guidelines}
    unpublished = UNMAPPED_DROPPED | FOLDED_IDS
    assert not (live_catalog / "locks.md").exists()
    assert len(unpublished) == 14
    assert unpublished.isdisjoint(ids)
    for gid in sorted(unpublished):
        assert f"`{gid}`" in readme
    assert "content/" in readme


def test_names_are_claim_then_source_and_folders_follow_category(
    live_catalog: Path,
) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    by_id = {g["id"]: g for g in catalog.guidelines}
    checkbox = by_id["ant.checkbox-vs-switch"]
    assert checkbox["name"] == "Checkbox vs switch — Ant"
    assert checkbox["category"] == "Forms"
    assert (live_catalog / "rules" / "forms" / "ant" / "checkbox-vs-switch.json").is_file()

    clickable = by_id["forms.labels.clickable"]
    assert clickable["name"] == "Clickable — Vercel"
    assert clickable["category"] == "Forms"
    assert (live_catalog / "rules" / "forms" / "vercel" / "labels.clickable.json").is_file()

    ant = by_id["ant.one-cta-per-screen"]
    assert ant["name"] == "One CTA per screen — Ant"
    assert ant["category"] == "Actions"
    assert (live_catalog / "rules" / "actions" / "ant" / "one-cta-per-screen.json").is_file()

    for guideline in catalog.guidelines:
        _slug, label = rule_source(guideline)
        assert guideline["name"].endswith(f" — {label}")
        assert not guideline["name"].endswith(" — Actions")
        assert not guideline["name"].endswith(" — Forms")


TIDWELL_BOOK = (
    "https://www.oreilly.com/library/view/designing-interfaces-3rd/9781492051954/"
)
VERCEL_FORMS = (
    "https://github.com/vercel-labs/web-interface-guidelines/blob/main/README.md#forms"
)
MATERIAL_TEXT_FIELDS = "https://m3.material.io/components/text-fields/guidelines"
SOURCE_CITE_URLS = {
    "tidwell": TIDWELL_BOOK,
    "vercel": VERCEL_FORMS,
    "material": MATERIAL_TEXT_FIELDS,
}


def test_tidwell_vercel_material_cite_the_source_page(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    seen = {slug: [] for slug in SOURCE_CITE_URLS}
    for guideline in catalog.guidelines:
        slug, _label = rule_source(guideline)
        if slug not in SOURCE_CITE_URLS:
            continue
        urls = [cite["url"] for cite in citations(guideline)]
        assert urls == [SOURCE_CITE_URLS[slug]], guideline["id"]
        seen[slug].append(guideline["id"])
    assert len(seen["tidwell"]) == 17
    assert len(seen["vercel"]) == 6
    assert seen["material"] == ["forms.errors.replace_supporting_text"]


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
    assert "nng" not in sources
    assert "apple" not in sources
    assert "actions" not in sources
    assert "One CTA per screen — Ant" in markdown
    assert "catalog/rules/{category}/{source}/{file}.json" in markdown


def _primary_source(guideline: dict) -> str:
    cites = guideline.get("citation") or []
    if not cites:
        return ""
    first = cites[0] if isinstance(cites, list) else cites
    if isinstance(first, dict):
        blob = str(first.get("source") or "")
    else:
        blob = str(first)
    return blob.split(";")[0].strip()


def test_no_primary_apple_or_nng_rules_remain(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    leftover = [
        g["id"]
        for g in catalog.guidelines
        if _primary_source(g).startswith("Apple HIG")
        or _primary_source(g).startswith("NN/g")
    ]
    assert leftover == []
    assert not list((live_catalog / "rules").rglob("nng/*.json"))
    assert not list((live_catalog / "rules").rglob("apple/*.json"))
    source_dirs = [
        path
        for path in (live_catalog / "rules").rglob("*")
        if path.is_dir() and path.name in {"apple", "nng"}
    ]
    assert source_dirs == []
    assert not any(g["id"].startswith(("nng.", "apple.")) for g in catalog.guidelines)
    nng_urls = []
    nng_cite_names = []
    for g in catalog.guidelines:
        for cite in g.get("citation") or []:
            if not isinstance(cite, dict):
                continue
            url = str(cite.get("url") or "").lower()
            source = str(cite.get("source") or "")
            if "nngroup.com" in url:
                nng_urls.append(g["id"])
            if "NN/g" in source or "nngroup" in source.lower() or "Nielsen" in source:
                nng_cite_names.append(g["id"])
    assert nng_urls == []
    assert nng_cite_names == []


def test_every_leaf_has_cites() -> None:
    tree = load_job_tree()
    empty = [
        (card.id, leaf.id)
        for card in tree.cards
        for facet in card.facets
        for leaf in facet.leaves
        if not leaf.guideline_ids
    ]
    assert empty == []


def test_validate_apply_when_fit_skips_non_gate_leaves() -> None:
    rows = validate_apply_when_fit(
        [
            {
                "id": "ant.test",
                "leaf": "avoid_placeholder_as_label",
                "apply_when": "Ant surfaces only.",
                "overview": "Different.",
            }
        ]
    )
    assert rows == []


def test_validate_apply_when_fit_flags_vendor_without_task_frame() -> None:
    rows = validate_apply_when_fit(
        [
            {
                "id": "ant.test",
                "leaf": "choose_control_for_choice",
                "apply_when": "Ant data-entry choices with more than five options.",
                "overview": "Use a dropdown when there are many options.",
                "title": "dropdown when over 5",
                "name": "Dropdown when over 5 — Ant",
            }
        ]
    )
    assert any(row["reason"] == "apply_when names a house or surface" for row in rows)


def test_validate_apply_when_fit_allows_task_framed_vendor_token() -> None:
    rows = validate_apply_when_fit(
        [
            {
                "id": "ant.test",
                "leaf": "pick_primary_action",
                "apply_when": "Choosing Ant button types for actions in a group.",
                "overview": "Map button types to roles.",
                "title": "named button type map",
                "name": "Named button type map — Ant",
            }
        ]
    )
    assert rows == []


def test_validate_apply_when_fit_flags_overview_restatement() -> None:
    overview = "Switches apply immediately; checkboxes wait for submit."
    rows = validate_apply_when_fit(
        [
            {
                "id": "ant.test",
                "leaf": "choose_control_for_choice",
                "apply_when": overview,
                "overview": overview,
                "title": "checkbox vs switch",
                "name": "Checkbox vs switch — Ant",
            }
        ]
    )
    assert any(row["reason"] == "apply_when equals overview" for row in rows)


def test_validate_catalog_strict_fit_exits_nonzero(live_catalog: Path) -> None:
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[3]
    proc = subprocess.run(
        [sys.executable, "-m", "open_ux", "validate-catalog", "--strict-fit"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1
    assert "apply_when fit:" in proc.stderr


def test_validate_catalog_default_reports_fit_but_exits_zero(live_catalog: Path) -> None:
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[3]
    proc = subprocess.run(
        [sys.executable, "-m", "open_ux", "validate-catalog"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "catalog ok" in proc.stdout
    if "apply_when fit:" in proc.stderr:
        assert '"reason"' in proc.stderr
