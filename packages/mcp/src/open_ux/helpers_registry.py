"""Helper catalog bundled with pip install open-ux."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any


def _repo_registry() -> Path:
    return Path(__file__).resolve().parents[3] / "helpers" / "registry.json"


def load_helpers_registry() -> dict[str, Any]:
    try:
        raw = resources.files("open_ux.data.helpers").joinpath("registry.json").read_text(
            encoding="utf-8"
        )
    except (FileNotFoundError, ModuleNotFoundError, TypeError):
        path = _repo_registry()
        if not path.is_file():
            raise FileNotFoundError("helpers/registry.json not found in package or repo.")
        raw = path.read_text(encoding="utf-8")
    return json.loads(raw)
