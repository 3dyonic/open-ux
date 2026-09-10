"""UNS-93: delete rules whose primary citation is Apple HIG or NN/g."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "packages" / "mcp" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "packages" / "mcp" / "src"))

from open_ux.manifest import build_manifest, render_manifest_markdown  # noqa: E402
from open_ux.rule_paths import iter_rule_files, rule_file_stem  # noqa: E402

CATALOG = ROOT / "catalog"
RULES = CATALOG / "rules"
INDEX = CATALOG / "index.json"
MANIFEST_JSON = CATALOG / "manifest.json"
MANIFEST_MD = CATALOG / "MANIFEST.md"
JOBS = CATALOG / "jobs.json"


def primary_source(guideline: dict) -> str:
    cites = guideline.get("citation") or []
    if not cites:
        return ""
    first = cites[0] if isinstance(cites, list) else cites
    if isinstance(first, dict):
        blob = str(first.get("source") or "")
    else:
        blob = str(first)
    return blob.split(";")[0].strip()


def is_drop(guideline: dict) -> bool:
    primary = primary_source(guideline)
    return primary.startswith("Apple HIG") or primary.startswith("NN/g")


def _index_row(guideline: dict) -> dict:
    leaf = guideline.get("leaf")
    row = {
        "id": guideline["id"],
        "title": guideline.get("title") or "",
        "name": guideline.get("name") or "",
        "jobs": [leaf] if leaf else [],
        "lane": str(guideline["id"]).split(".", 1)[0],
        "container": guideline.get("container"),
        "card": guideline.get("card"),
        "facet": guideline.get("facet"),
    }
    if leaf:
        row["leaf"] = leaf
    return row


def _prune_empty(root: Path) -> None:
    for folder in sorted((p for p in root.rglob("*") if p.is_dir()), reverse=True):
        if folder.is_dir() and not any(folder.iterdir()):
            folder.rmdir()


def _prune_jobs(deleted: set[str]) -> int:
    data = json.loads(JOBS.read_text(encoding="utf-8"))
    removed = 0

    def filter_ids(raw: object) -> list:
        nonlocal removed
        if not isinstance(raw, list):
            return []
        kept = []
        for gid in raw:
            if gid in deleted:
                removed += 1
            else:
                kept.append(gid)
        return kept

    for card in data.get("cards") or []:
        for facet in card.get("facets") or []:
            if "guideline_ids" in facet:
                facet["guideline_ids"] = filter_ids(facet.get("guideline_ids"))
            for leaf in facet.get("leaves") or []:
                if isinstance(leaf, dict) and "guideline_ids" in leaf:
                    leaf["guideline_ids"] = filter_ids(leaf.get("guideline_ids"))
    JOBS.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return removed


def main() -> int:
    existing = {p.resolve() for p in iter_rule_files(RULES)}
    by_id: dict[str, dict] = {}
    paths: dict[str, Path] = {}
    for path in existing:
        data = json.loads(path.read_text(encoding="utf-8"))
        gid = str(data["id"])
        by_id[gid] = data
        paths[gid] = path

    drop = {gid for gid, row in by_id.items() if is_drop(row)}
    apple = [gid for gid in drop if primary_source(by_id[gid]).startswith("Apple HIG")]
    nng = [gid for gid in drop if primary_source(by_id[gid]).startswith("NN/g")]
    print(f"drop {len(drop)} (apple {len(apple)}, nng {len(nng)}) of {len(by_id)}")

    for gid in drop:
        paths[gid].unlink()
    _prune_empty(RULES)

    leftover_source_dirs = [
        p
        for p in RULES.rglob("*")
        if p.is_dir() and p.name in {"apple", "nng"}
    ]
    for folder in leftover_source_dirs:
        print(f"leftover source dir still present: {folder}")

    kept_ids = [gid for gid in by_id if gid not in drop]
    index_data = json.loads(INDEX.read_text(encoding="utf-8"))
    old_order = [row["id"] for row in index_data["guidelines"]]
    ordered_ids = [gid for gid in old_order if gid in set(kept_ids)]
    extra = sorted(set(kept_ids) - set(ordered_ids))
    ordered_ids.extend(extra)
    kept = [by_id[gid] for gid in ordered_ids]
    INDEX.write_text(
        json.dumps(
            {
                "guidelines": [_index_row(row) for row in kept],
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    manifest = build_manifest(kept)
    MANIFEST_JSON.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    MANIFEST_MD.write_text(render_manifest_markdown(manifest), encoding="utf-8")
    pruned = _prune_jobs(drop)
    remaining_files = list(iter_rule_files(RULES))
    print(f"remaining files {len(remaining_files)}; jobs pointers removed {pruned}")
    print(f"index {len(ordered_ids)}; stems ok {all(p.stem == rule_file_stem(json.loads(p.read_text())['id']) for p in remaining_files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
