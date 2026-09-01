from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import ValidationError

from open_ux.catalog import CatalogError, load_catalog
from open_ux.settings import HARD_CATALOG_BYTES, Settings


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
