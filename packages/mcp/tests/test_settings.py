from __future__ import annotations

from pathlib import Path

from open_ux.settings import Settings, _default_catalog


def test_env_catalog_wins(monkeypatch, tmp_path: Path) -> None:
    env_catalog = tmp_path / "from-env"
    env_catalog.mkdir()
    (env_catalog / "schema.json").write_text("{}")
    packaged = tmp_path / "packaged" / "catalog"
    packaged.mkdir(parents=True)
    (packaged / "schema.json").write_text("{}")
    monkeypatch.setenv("OPEN_UX_CATALOG", str(env_catalog))
    monkeypatch.setattr("open_ux.settings._repo_root", lambda: tmp_path / "repo")
    monkeypatch.setattr("open_ux.settings._packaged_catalog", lambda: packaged)
    assert _default_catalog() == env_catalog


def test_repo_walk_wins_over_packaged(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "catalog").mkdir(parents=True)
    (repo / "catalog" / "schema.json").write_text("{}")
    packaged = tmp_path / "packaged" / "catalog"
    packaged.mkdir(parents=True)
    (packaged / "schema.json").write_text("{}")
    monkeypatch.delenv("OPEN_UX_CATALOG", raising=False)
    monkeypatch.setattr("open_ux.settings._repo_root", lambda: repo)
    monkeypatch.setattr("open_ux.settings._packaged_catalog", lambda: packaged)
    assert _default_catalog() == repo / "catalog"


def test_packaged_catalog_when_no_repo(monkeypatch, tmp_path: Path) -> None:
    packaged = tmp_path / "packaged" / "catalog"
    packaged.mkdir(parents=True)
    (packaged / "schema.json").write_text("{}")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.delenv("OPEN_UX_CATALOG", raising=False)
    monkeypatch.delenv("OPEN_UX_SCHEMA", raising=False)
    monkeypatch.chdir(elsewhere)
    monkeypatch.setattr("open_ux.settings._repo_root", lambda: None)
    monkeypatch.setattr("open_ux.settings._packaged_catalog", lambda: packaged)
    settings = Settings.load()
    assert settings.catalog_path == packaged
    assert settings.schema_path == packaged / "schema.json"
