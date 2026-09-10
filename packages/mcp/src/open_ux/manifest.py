"""Category → source map. No rule bodies."""

from __future__ import annotations

from typing import Any

from open_ux.catalog_error import CatalogError
from open_ux.rule_paths import category_folder, rule_relpath, rule_source

_BODY_KEYS = frozenset({"pass_when", "fail_when", "rule"})


def manifest_ids(manifest: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for category in manifest.get("categories") or []:
        for source in category.get("sources") or []:
            for row in source.get("rules") or []:
                if _BODY_KEYS & set(row):
                    raise CatalogError(
                        "catalog/manifest.json must not contain rule bodies."
                    )
                ids.append(row["id"])
    return ids


def build_manifest(guidelines: list[dict[str, Any]]) -> dict[str, Any]:
    """Category → source map. No rule bodies. For skill reference."""
    buckets: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    for guideline in guidelines:
        cat_title = str(guideline.get("category") or "")
        cat_id = category_folder(cat_title)
        src_id, src_title = rule_source(guideline)
        key = (cat_title, cat_id, src_title, src_id)
        rel = rule_relpath(guideline).as_posix()
        buckets.setdefault(key, []).append(
            {
                "id": guideline["id"],
                "name": guideline.get("name") or guideline.get("title") or "",
                "card": guideline.get("card"),
                "path": f"rules/{rel}",
            }
        )
    categories: dict[str, dict[str, Any]] = {}
    for cat_title, cat_id, src_title, src_id in sorted(
        buckets, key=lambda item: (item[0].lower(), item[2].lower())
    ):
        rows = sorted(
            buckets[(cat_title, cat_id, src_title, src_id)],
            key=lambda r: r["name"].lower(),
        )
        cat = categories.setdefault(
            cat_id,
            {"id": cat_id, "title": cat_title, "count": 0, "sources": []},
        )
        cat["sources"].append(
            {"id": src_id, "title": src_title, "count": len(rows), "rules": rows}
        )
        cat["count"] += len(rows)
    return {
        "count": sum(item["count"] for item in categories.values()),
        "note": (
            "Auto-generated. Category folder, then source folder. "
            "No rule bodies. Agents read this map, then fetch one id."
        ),
        "categories": list(categories.values()),
    }


def render_manifest_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        "# Open UX catalog manifest",
        "",
        "Auto-generated. Do not edit by hand. No rule bodies.",
        "",
        "Layout: `catalog/rules/{category}/{source}/{file}.json`. "
        "The harvest prefix is in the folder; `id` stays on the rule.",
        "",
        "Read this map when you need to see what exists. Then call "
        "`Open-UX:get_guideline` or open that one file. "
        "Do not copy guideline ids into SKILL.md.",
        "",
        f"{manifest['count']} rules.",
        "",
    ]
    for category in manifest["categories"]:
        lines.append(f"## {category['title']}")
        lines.append("")
        for source in category["sources"]:
            lines.append(f"### {source['title']}")
            lines.append("")
            for row in source["rules"]:
                card = row.get("card") or ""
                suffix = f" · `{card}`" if card else ""
                lines.append(
                    f"- [{row['name']}]({row['path']}) — `{row['id']}`{suffix}"
                )
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"
