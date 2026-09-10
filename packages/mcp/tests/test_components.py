from __future__ import annotations

from pathlib import Path

import pytest

from open_ux.catalog import CatalogError, load_catalog
from open_ux.catalog import load_catalog
from open_ux.components import (
    build_component_usage,
    get_component,
    list_components,
    load_components,
    validate_component_refs,
)
from open_ux.jobs import JobTreeError, empty_job_tree, load_job_tree
from open_ux.settings import Settings


def test_live_registry_loads_all(live_catalog: Path) -> None:
    registry = load_components(Settings.load(hosted=True))
    assert len(registry.ids) == 38
    assert "button" in registry.ids
    assert "link" in registry.ids
    record = registry.records["button"]
    assert record["title"] == "Button"
    assert "cta" in record["keywords"]
    assert record["variants"]["role"][0]["id"] == "primary"


def test_live_catalog_validates_component_cite(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    cited = catalog.by_id["govuk.button-types-named"]
    assert cited["component"] == ["button"]


def test_unknown_cite_component_rejected(live_catalog: Path) -> None:
    registry = load_components(Settings.load(hosted=True))
    tree = load_job_tree(Settings.load(hosted=True))
    guideline = {"id": "t.test", "component": ["not_a_widget"]}
    with pytest.raises(CatalogError, match="not_a_widget"):
        validate_component_refs(tree, [guideline], registry)


def test_unknown_card_component_rejected(live_catalog: Path) -> None:
    registry = load_components(Settings.load(hosted=True))
    tree = load_job_tree(Settings.load(hosted=True))
    cards = list(tree.cards)
    first = cards[0]
    bad = first.__class__(
        id=first.id,
        title=first.title,
        container=first.container,
        overview=first.overview,
        when=first.when,
        reject=first.reject,
        hints=first.hints,
        component=("not_a_widget",),
        facets=first.facets,
        provisional=first.provisional,
    )
    bad_tree = tree.__class__(containers=tree.containers, cards=(bad,) + tree.cards[1:])
    with pytest.raises(JobTreeError, match="not_a_widget"):
        validate_component_refs(bad_tree, [], registry)


def test_empty_registry_allows_no_refs() -> None:
    registry = load_components(Settings.load(hosted=True))
    validate_component_refs(empty_job_tree(), [], registry)


def test_list_components_returns_index(live_catalog: Path) -> None:
    registry = load_components(Settings.load(hosted=True))
    payload = list_components(registry)
    assert payload["count"] == 38
    assert payload["total"] == 38
    assert len(payload["components"]) == 38
    row = payload["components"][0]
    assert set(row) == {"id", "title", "overview"}


def test_get_component_default_sections(live_catalog: Path) -> None:
    registry = load_components(Settings.load(hosted=True))
    tree = load_job_tree(Settings.load(hosted=True))
    catalog = load_catalog(Settings.load(hosted=True))
    usage = build_component_usage(tree, catalog.guidelines)
    payload = get_component(registry, usage, "button")
    assert payload["found"] is True
    component = payload["component"]
    assert component["id"] == "button"
    assert "vs" in component
    assert "variants" in component
    assert "accessibility" in component
    assert "keyboard" in component
    assert "keywords" not in component
    assert "used_on" not in component


def test_get_component_switches_omit_keys(live_catalog: Path) -> None:
    registry = load_components(Settings.load(hosted=True))
    tree = load_job_tree(Settings.load(hosted=True))
    catalog = load_catalog(Settings.load(hosted=True))
    usage = build_component_usage(tree, catalog.guidelines)
    payload = get_component(
        registry,
        usage,
        "button",
        include_vs=False,
        include_variants=False,
        include_accessibility=False,
        include_keyboard=False,
        include_keywords=True,
    )
    component = payload["component"]
    assert "vs" not in component
    assert "variants" not in component
    assert "accessibility" not in component
    assert "keyboard" not in component
    assert "keywords" in component


def test_get_component_used_on_button(live_catalog: Path) -> None:
    registry = load_components(Settings.load(hosted=True))
    tree = load_job_tree(Settings.load(hosted=True))
    catalog = load_catalog(Settings.load(hosted=True))
    usage = build_component_usage(tree, catalog.guidelines)
    payload = get_component(registry, usage, "button", include_used_on=True)
    used_on = payload["component"]["used_on"]
    assert used_on["cards_total"] == 8
    assert used_on["cites_total"] == 31
    assert len(used_on["cards"]) == 8
    assert len(used_on["cites"]) == 31
    cite = used_on["cites"][0]
    assert set(cite) == {"id", "overview", "card", "facet", "leaf"}


def test_get_component_unknown_id(live_catalog: Path) -> None:
    registry = load_components(Settings.load(hosted=True))
    payload = get_component(registry, {}, "not_a_widget")
    assert payload["found"] is False
    assert "not_a_widget" in payload["error"]
