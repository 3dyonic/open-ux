from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path


KEY_PREFIX = "uxmcp_"
INVITE_PREFIX = "inv_"
INVITE_TTL_DAYS = 14
SOFT_CATALOG_BYTES = 256 * 1024
HARD_CATALOG_BYTES = 768 * 1024
RATE_PER_MINUTE = 60
RATE_PER_DAY = 1000
MCP_IP_PER_MINUTE = 30
MCP_IP_PER_DAY = 300
INVITE_REQUEST_RATE_PER_MINUTE = 5
INVITE_REQUEST_RATE_PER_DAY = 30
INVITE_REDEEM_RATE_PER_MINUTE = 10
INVITE_REDEEM_RATE_PER_DAY = 50
RETENTION_DAYS = 30
DEFAULT_GTM_ID = "GTM-N3BL3G9K"
_GTM_ID_RE = re.compile(r"^GTM-[A-Z0-9]+$")


def gtm_container_id() -> str:
    raw = os.environ.get("OPEN_UX_GTM_ID", "").strip()
    if raw and _GTM_ID_RE.fullmatch(raw):
        return raw
    return DEFAULT_GTM_ID


def _repo_root() -> Path | None:
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (candidate / "catalog" / "schema.json").is_file():
            return candidate
    return None


def _packaged_catalog() -> Path | None:
    packaged = Path(__file__).resolve().parent / "data" / "catalog"
    if (packaged / "schema.json").is_file():
        return packaged
    return None


def _default_catalog() -> Path:
    env = os.environ.get("OPEN_UX_CATALOG")
    if env:
        return Path(env)
    root = _repo_root()
    if root is not None:
        return root / "catalog"
    packaged = _packaged_catalog()
    if packaged is not None:
        return packaged
    return Path.cwd() / "catalog"


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
        root = _repo_root() or Path.cwd()
        if hosted is None:
            hosted = os.environ.get("OPEN_UX_MODE", "stdio") == "hosted" or os.environ.get(
                "OPEN_UX_HOSTED", ""
            ).lower() in {"1", "true", "yes"}
        catalog = _default_catalog()
        schema_default = (
            catalog / "schema.json" if catalog.is_dir() else catalog.parent / "schema.json"
        )
        schema = Path(os.environ.get("OPEN_UX_SCHEMA", schema_default))
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
