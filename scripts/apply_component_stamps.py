#!/usr/bin/env python3
"""Copy component records, rebuild registry, stamp Cards and cites."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog"
COMPONENTS = CATALOG / "components"
STAMPS = ROOT / "scripts" / "component_stamps.json"
EXPANDED = Path("/tmp/oux-expanded")


def _title(record: dict[str, object]) -> str:
    return str(record["title"])


def copy_records() -> list[str]:
    COMPONENTS.mkdir(parents=True, exist_ok=True)
    ids: list[str] = ["button"]
    if (COMPONENTS / "button.json").is_file():
        pass  # keep authored button.json
    for path in sorted(EXPANDED.glob("*.json")):
        cid = path.stem
        dest = COMPONENTS / f"{cid}.json"
        shutil.copy2(path, dest)
        ids.append(cid)
    return sorted(set(ids))


def write_registry(ids: list[str]) -> None:
    rows = []
    for cid in ids:
        record = json.loads((COMPONENTS / f"{cid}.json").read_text(encoding="utf-8"))
        rows.append(
            {
                "id": cid,
                "title": _title(record),
                "path": f"components/{cid}.json",
            }
        )
    (CATALOG / "components.json").write_text(
        json.dumps({"components": rows}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def stamp_jobs(cards: dict[str, list[str]]) -> None:
    jobs_path = CATALOG / "jobs.json"
    data = json.loads(jobs_path.read_text(encoding="utf-8"))
    for card in data.get("cards") or []:
        cid = card.get("id")
        comps = cards.get(str(cid))
        if comps:
            card["component"] = sorted(comps)
        else:
            card.pop("component", None)
    jobs_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def stamp_cites(cites: dict[str, list[str]]) -> int:
    by_id: dict[str, Path] = {}
    for path in (CATALOG / "rules").rglob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        gid = str(data.get("id") or "")
        if gid:
            by_id[gid] = path
    missing = sorted(set(cites) - set(by_id))
    if missing:
        raise SystemExit(f"stamp cites missing from catalog: {missing}")
    for gid, comps in cites.items():
        path = by_id[gid]
        data = json.loads(path.read_text(encoding="utf-8"))
        data["component"] = sorted(comps)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return len(cites)


def main() -> int:
    if not STAMPS.is_file():
        print(f"missing {STAMPS}", file=sys.stderr)
        return 2
    if not EXPANDED.is_dir():
        print(f"missing {EXPANDED}; run expand script first", file=sys.stderr)
        return 2
    ids = copy_records()
    write_registry(ids)
    stamps = json.loads(STAMPS.read_text(encoding="utf-8"))
    stamp_jobs(stamps["cards"])
    n = stamp_cites(stamps["cites"])
    print(
        f"components={len(ids)} cards={len(stamps['cards'])} cites={n}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
