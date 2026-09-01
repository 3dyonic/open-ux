from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


KEY_PREFIX = "uxmcp_"
INVITE_PREFIX = "inv_"
INVITE_TTL_DAYS = 14
SOFT_CATALOG_BYTES = 100 * 1024
HARD_CATALOG_BYTES = 256 * 1024
RATE_PER_MINUTE = 60
RATE_PER_DAY = 1000
RETENTION_DAYS = 30


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (candidate / "catalog" / "guidelines.json").is_file():
            return candidate
    return Path.cwd()


@dataclass(frozen=True)
class Settings:
    hosted: bool
    catalog_path: Path
    schema_path: Path
    database_path: Path
    pepper: str
    admin_token: str
    telemetry: bool
    public_url: str

    @classmethod
    def load(cls, *, hosted: bool | None = None) -> Settings:
        root = _repo_root()
        if hosted is None:
            hosted = os.environ.get("OPEN_UX_MODE", "stdio") == "hosted" or os.environ.get(
                "OPEN_UX_HOSTED", ""
            ).lower() in {"1", "true", "yes"}
        catalog = Path(
            os.environ.get("OPEN_UX_CATALOG", root / "catalog" / "guidelines.json")
        )
        schema = Path(
            os.environ.get("OPEN_UX_SCHEMA", catalog.parent / "schema.json")
        )
        data_dir = Path(os.environ.get("OPEN_UX_DATA_DIR", root / "data"))
        database = Path(
            os.environ.get("OPEN_UX_DATABASE", data_dir / "open-ux.sqlite")
        )
        telemetry_env = os.environ.get("OPEN_UX_TELEMETRY")
        if telemetry_env is None:
            telemetry = hosted
        else:
            telemetry = telemetry_env.lower() in {"1", "true", "yes"}
        return cls(
            hosted=hosted,
            catalog_path=catalog,
            schema_path=schema,
            database_path=database,
            pepper=os.environ.get("OPEN_UX_PEPPER", ""),
            admin_token=os.environ.get("OPEN_UX_ADMIN_TOKEN", ""),
            telemetry=telemetry and hosted,
            public_url=os.environ.get("OPEN_UX_PUBLIC_URL", "").rstrip("/"),
        )
