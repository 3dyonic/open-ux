from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from open_ux.store import reset_store_for_tests


@pytest.fixture()
def tmp_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    catalog_src = Path(__file__).resolve().parents[3] / "catalog"
    catalog_dir = tmp_path / "catalog"
    catalog_dir.mkdir()
    (catalog_dir / "schema.json").write_bytes(
        (catalog_src / "schema.json").read_bytes()
    )
    (catalog_dir / "guidelines.json").write_text(
        json.dumps(
            {"version": "0.0.0", "guidelines": [], "jobs": [], "patterns": []}
        ),
        encoding="utf-8",
    )
    db = tmp_path / "open-ux.sqlite"
    monkeypatch.setenv("OPEN_UX_CATALOG", str(catalog_dir / "guidelines.json"))
    monkeypatch.setenv("OPEN_UX_SCHEMA", str(catalog_dir / "schema.json"))
    monkeypatch.setenv("OPEN_UX_DATABASE", str(db))
    monkeypatch.setenv("OPEN_UX_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("OPEN_UX_TELEMETRY", "1")
    monkeypatch.setenv("OPEN_UX_HOSTED", "1")
    monkeypatch.setenv("OPEN_UX_PEPPER", "test-pepper")
    monkeypatch.setenv("OPEN_UX_ADMIN_TOKEN", "test-admin-token")
    monkeypatch.setenv("OPEN_UX_PUBLIC_URL", "https://open-ux.test")
    reset_store_for_tests()
    yield tmp_path
    reset_store_for_tests()


@pytest.fixture()
def catalog_dir(tmp_env: Path) -> Path:
    return tmp_env / "catalog"
