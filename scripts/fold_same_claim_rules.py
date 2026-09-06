#!/usr/bin/env python3
"""Fold same-claim rule files onto one survivor.

Citation is always an array of one or many {source, url}. Extra URLs mean
those pages support this one claim. Survivor rule text stays as written.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog"
RULES = CATALOG / "rules"
LIVE_SEED = (
    "forms.field_labels.visible_label",
    "forms.field_labels.label_stays_visible",
    "forms.field_labels.error_identifies_and_fixes",
)

# Only families where every URL supports the survivor pass/fail.
# Cutoff fights, date-type slices, and “preselect when possible” stay as
# their own files — those are adjacent claims, not more sources.
FOLDS: dict[str, list[str]] = {
    "forms.inputs.forgiving_format_autoformat": [
        "nl.dont-reject-valid-variants",
        "nl.no-forced-input-patterns-or-masks",
        "forms.inputs.allow_typos_abbreviations",
    ],
    "forms.fields.distinguish_optional_required": [
        "fluent.required-asterisk-or-one-instruction",
        "suomi.default-required-optional-in-parentheses",
        "nl.mark-optional-niet-verplicht-above-form",
    ],
    "ant.checkbox-vs-switch": [
        "suomi.toggle-button-immediate-input-submit",
    ],
}

ORDER = [
    "id",
    "category",
    "segment",
    "title",
    "rule",
    "rationale",
    "citation",
    "applies_to",
    "check",
    "pass_when",
    "fail_when",
    "examples",
    "severity",
    "container",
    "card",
    "facet",
    "leaf",
    "overview",
    "apply_when",
    "not_when",
    "agent_hint",
    "description",
    "jobs",
    "patterns",
    "ux_dimensions",
    "source_scheme",
    "do_not_claim",
]


def folded_ids() -> set[str]:
    return {gid for folds in FOLDS.values() for gid in folds}


def _ordered(guideline: dict) -> dict:
    out = {key: guideline[key] for key in ORDER if key in guideline}
    for key, value in guideline.items():
        if key not in out:
            out[key] = value
    return out


def _as_cites(raw) -> list[dict]:
    if raw is None:
        return []
    items = raw if isinstance(raw, list) else [raw]
    out = []
    for item in items:
        if not isinstance(item, dict):
            continue
        source = str(item.get("source") or "").strip()
        url = str(item.get("url") or "").strip()
        if source and url:
            out.append({"source": source, "url": url})
    return out


def _citation_field(cites: list[dict]) -> list[dict]:
    if not cites:
        raise SystemExit("citation must have at least one {source, url}")
    return cites


def _index_row(guideline: dict) -> dict:
    leaf = guideline.get("leaf")
    row = {
        "id": guideline["id"],
        "title": guideline.get("title") or "",
        "jobs": [leaf] if leaf else [],
        "lane": str(guideline["id"]).split(".", 1)[0],
        "container": guideline["container"],
        "card": guideline["card"],
        "facet": guideline["facet"],
    }
    if leaf:
        row["leaf"] = leaf
    return row


def _rewrite_ids(ids: list[str], fold_to_keep: dict[str, str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for gid in ids:
        mapped = fold_to_keep.get(gid, gid)
        if mapped in seen:
            continue
        seen.add(mapped)
        out.append(mapped)
    return out


def apply_folds(catalog: Path | None = None) -> dict:
    catalog = catalog or CATALOG
    rules = catalog / "rules"
    fold_to_keep = {fold: keep for keep, folds in FOLDS.items() for fold in folds}

    for keep, folds in FOLDS.items():
        keep_path = rules / f"{keep}.json"
        if not keep_path.is_file():
            raise SystemExit(f"missing keep file {keep}")
        keep_data = json.loads(keep_path.read_text(encoding="utf-8"))
        cites = _as_cites(keep_data.get("citation"))
        seen_urls = {item["url"] for item in cites}
        fences: list[str] = []
        if keep_data.get("do_not_claim"):
            fences.append(str(keep_data["do_not_claim"]).strip())
        for fold in folds:
            fold_path = rules / f"{fold}.json"
            if not fold_path.is_file():
                raise SystemExit(f"missing fold file {fold}")
            fold_data = json.loads(fold_path.read_text(encoding="utf-8"))
            for cite in _as_cites(fold_data.get("citation")):
                if cite["url"] in seen_urls:
                    continue
                seen_urls.add(cite["url"])
                cites.append(cite)
            fence = str(fold_data.get("do_not_claim") or "").strip()
            if fence and fence not in fences:
                fences.append(fence)
        keep_data["citation"] = _citation_field(cites)
        if fences:
            keep_data["do_not_claim"] = " ".join(fences)
        keep_path.write_text(
            json.dumps(_ordered(keep_data), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    removed: list[str] = []
    for gid in sorted(fold_to_keep):
        path = rules / f"{gid}.json"
        if path.is_file():
            path.unlink()
            removed.append(gid)

    jobs_path = catalog / "jobs.json"
    jobs = json.loads(jobs_path.read_text(encoding="utf-8"))
    for card in jobs.get("cards") or []:
        for facet in card.get("facets") or []:
            if "guideline_ids" in facet:
                facet["guideline_ids"] = _rewrite_ids(
                    facet.get("guideline_ids") or [], fold_to_keep
                )
            for leaf in facet.get("leaves") or []:
                leaf["guideline_ids"] = _rewrite_ids(
                    leaf.get("guideline_ids") or [], fold_to_keep
                )
    jobs_path.write_text(
        json.dumps(jobs, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    remaining = []
    for path in sorted(rules.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        data["citation"] = _citation_field(_as_cites(data.get("citation")))
        path.write_text(
            json.dumps(_ordered(data), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        remaining.append(data)
    by_id = {item["id"]: item for item in remaining}
    leftover = [gid for gid in fold_to_keep if gid in by_id]
    if leftover:
        raise SystemExit(f"folded ids still on disk: {leftover}")
    missing_keep = [gid for gid in FOLDS if gid not in by_id]
    if missing_keep:
        raise SystemExit(f"keep ids missing after fold: {missing_keep}")

    ordered_ids = list(LIVE_SEED) + sorted(gid for gid in by_id if gid not in LIVE_SEED)
    index = {
        "version": "0.3.0",
        "guidelines": [_index_row(by_id[gid]) for gid in ordered_ids],
    }
    (catalog / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    size = sum(p.stat().st_size for p in rules.glob("*.json"))
    stats = {
        "kept": len(FOLDS),
        "folded": len(removed),
        "rules": len(remaining),
        "bytes": size,
        "removed": removed,
    }
    print(
        f"folded {stats['folded']} into {stats['kept']} survivors; "
        f"rules={stats['rules']} bytes={stats['bytes']}"
    )
    return stats


def main() -> int:
    apply_folds()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
