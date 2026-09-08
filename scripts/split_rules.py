#!/usr/bin/env python3
"""One-shot cutover: lane blobs + placement CSV → catalog/rules/{id}.json + index.

After this lands, catalog/rules/*.json is SoT. Do not re-run against deleted blobs.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog"
RULES = CATALOG / "rules"
LANE_SKIP = frozenset({"schema.json", "index.json", "guidelines.json", "jobs.json"})
LIVE_SEED = (
    "forms.field_labels.visible_label",
    "forms.field_labels.label_stays_visible",
    "forms.field_labels.error_identifies_and_fixes",
)
MULTI_HOME_PICK = {
    "fluent.validation-messages-brief-no-end-punctuation": "explain_failure_next_to_cause",
    "ant.inline-input-feedback-does-not-auto-dismiss": "explain_failure_next_to_cause",
    "govuk.error-summary-plus-per-field": "explain_failure_next_to_cause",
    "suomi.errorsummary-link-text-equals-field-error": "explain_failure_next_to_cause",
    "polar.long-form-errors-banner-plus-inline": "explain_failure_next_to_cause",
    "nl.native-required-bubbles-not-error-ui": "explain_failure_next_to_cause",
}
AGENT_FIELD_KEYS = (
    "overview",
    "apply_when",
    "not_when",
    "agent_hint",
    "description",
)
LIVE_AGENT = {
    "forms.field_labels.visible_label": {
        "overview": "A lasting label outside the field names what the input is for.",
        "apply_when": "Labeling signup, settings, or checkout fields.",
        "not_when": (
            "Button/CTA wording — use action-label rules. "
            "Inline validation after submit — that is handle_form_errors."
        ),
        "agent_hint": "Require a visible label outside the field. Placeholder is not the name.",
        "description": (
            "A field must keep saying what belongs in it the whole time someone uses it. "
            "A label outside the control stays visible while they type; placeholder-only "
            "(or a floating label that vanishes when filled) stops naming the field at the "
            "moment it matters. Use this for text inputs, selects, and similar data-entry "
            "controls — not for button/CTA wording."
        ),
    },
    "forms.field_labels.label_stays_visible": {
        "overview": "The field name stays on screen while the user types and checks the value.",
        "apply_when": "Labeling signup, settings, or checkout fields.",
        "not_when": "Button/CTA wording. Inline validation after submit — that is handle_form_errors.",
        "agent_hint": "Keep the label visible while the field has a value. Do not rely on text that disappears inside the field.",
        "description": (
            "A label has to remain readable after the user starts typing. "
            "While the field has focus or a value, the naming text stays on screen. "
            "It fails when only the value remains and the naming text has disappeared. "
            "Use this next to visible_label — not for button copy."
        ),
    },
    "forms.field_labels.error_identifies_and_fixes": {
        "overview": "Error text says what is wrong and how to fix it.",
        "apply_when": "Composing validation or inline form errors after submit.",
        "not_when": "Page-level empty, 404, or hard error — that is compose_feedback.",
        "agent_hint": "Identify the problem and give constructive advice next to the field.",
        "description": (
            "A rejected field needs a message that names the problem and the next step. "
            "On error, visible text says what is wrong and how to fix it. "
            "Generic copy, or copy that never identifies the field, fails this rule. "
            "This checks the message, not whether the typed value was wiped."
        ),
    },
}
CLUSTER_AGENT = {
    "nng.modal-and-nonmodal-dialogs": {
        "overview": "A modal is only for a required finish-or-cancel; other layers stay nonmodal.",
        "apply_when": "Choosing modal vs accordion, tooltip, or side panel.",
        "not_when": "The destructive decision inside a dialog — that is protect_destructive_and_leave.",
        "agent_hint": "Pick the layer for the content. Do not treat every dialog as modal.",
        "description": (
            "Use a modal only when the user must finish or cancel before continuing. "
            "The overlay type should match whether they may keep working in the background. "
            "A modal that blocks the page for content that is not a required decision fails. "
            "This is about the layer, not the destructive copy inside it."
        ),
    },
}


def _lane_guidelines() -> list[dict]:
    out: list[dict] = []
    for path in sorted(CATALOG.glob("*.json")):
        if path.name in LANE_SKIP:
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        out.extend(data.get("guidelines") or [])
    return out


def _tree_maps() -> tuple[dict, dict, dict]:
    jobs = json.loads((CATALOG / "jobs.json").read_text(encoding="utf-8"))
    cards = {c["id"]: c for c in jobs["cards"]}
    facet_home: dict[str, dict] = {}
    leaf_home: dict[str, dict] = {}
    cluster_ids: set[str] = set()
    for card in jobs["cards"]:
        for facet in card["facets"]:
            leaves = facet.get("leaves") or []
            facet_home[facet["id"]] = {
                "container": card["container"],
                "card": card["id"],
                "facet": facet["id"],
                "has_leaves": bool(leaves),
                "when": list(card.get("when") or []),
                "reject": list(card.get("reject") or []),
            }
            if not leaves:
                cluster_ids.update(facet.get("guideline_ids") or [])
            for leaf in leaves:
                leaf_home[leaf["id"]] = {
                    "container": card["container"],
                    "card": card["id"],
                    "facet": facet["id"],
                    "leaf": leaf["id"],
                    "when": list(card.get("when") or []),
                    "reject": list(card.get("reject") or []),
                }
    return facet_home, leaf_home, cluster_ids


def _load_placement(csv_path: Path) -> dict[str, dict]:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return {row["id"]: row for row in csv.DictReader(handle)}


def _first_sentence(text: str) -> str:
    raw = " ".join((text or "").split())
    if not raw:
        return ""
    for sep in (". ", "; ", " — ", " – "):
        if sep in raw:
            return raw.split(sep, 1)[0].rstrip(" .;") + "."
    return raw if raw.endswith(".") else raw + "."


def _cluster_agent(guideline: dict, home: dict) -> dict[str, str]:
    gid = guideline["id"]
    if gid in CLUSTER_AGENT:
        return CLUSTER_AGENT[gid]
    when = home["when"][0] if home["when"] else home["card"].replace("_", " ")
    reject = home["reject"][0]["why"] if home["reject"] else "a different Situation Card"
    rule = guideline["rule"]
    pass_when = (guideline.get("pass_when") or [""])[0]
    fail_when = (guideline.get("fail_when") or [""])[0]
    return {
        "overview": _first_sentence(pass_when or rule),
        "apply_when": when[0].upper() + when[1:] if when else when,
        "not_when": f"Not for {reject.rstrip('.')}." if not reject.lower().startswith("not ") else reject,
        "agent_hint": _first_sentence(rule),
        "description": (
            f"{_first_sentence(rule)} "
            f"{_first_sentence(pass_when)} "
            f"It fails when {_first_sentence(fail_when).rstrip('.').lstrip('It fails when ').lstrip('when ')}."
        ),
    }


def _waive_reason(row: dict, harvest_leaves: list[str], home_leaf: str) -> str:
    bits = ["agent_fields pending — do not invent from harvest stencil"]
    if row.get("placement_status", "").startswith("MULTI_HOME"):
        leftover = [leaf for leaf in harvest_leaves if leaf != home_leaf]
        bits.append(
            f"MULTI_HOME picked {home_leaf}"
            + (f"; leftover harvest tag {', '.join(leftover)}" if leftover else "")
        )
    elif harvest_leaves and home_leaf and set(harvest_leaves) != {home_leaf}:
        bits.append(
            f"harvest tags {', '.join(harvest_leaves)} superseded by home {home_leaf or 'cluster'}"
        )
    elif harvest_leaves and not home_leaf:
        bits.append(f"harvest tags {', '.join(harvest_leaves)} superseded by cluster home")
    return "; ".join(bits)


def _ordered(guideline: dict) -> dict:
    order = [
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
        "waive_reason",
        "jobs",
        "patterns",
        "ux_dimensions",
        "source_scheme",
        "do_not_claim",
    ]
    out = {}
    for key in order:
        if key in guideline:
            out[key] = guideline[key]
    for key, value in guideline.items():
        if key not in out:
            out[key] = value
    return out


def _index_row(guideline: dict) -> dict:
    leaf = guideline.get("leaf")
    jobs = [leaf] if leaf else []
    lane = str(guideline["id"]).split(".", 1)[0]
    row = {
        "id": guideline["id"],
        "title": guideline.get("title") or "",
        "jobs": jobs,
        "lane": lane,
        "container": guideline["container"],
        "card": guideline["card"],
        "facet": guideline["facet"],
    }
    if leaf:
        row["leaf"] = leaf
    return row


def main() -> int:
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/filled.csv")
    if not csv_path.is_file():
        raise SystemExit(f"placement CSV not found: {csv_path}")

    facet_home, leaf_home, cluster_ids = _tree_maps()
    placement = _load_placement(csv_path)
    guidelines = _lane_guidelines()
    if len(guidelines) != 309:
        raise SystemExit(f"expected 309 lane guidelines, got {len(guidelines)}")

    RULES.mkdir(exist_ok=True)
    written: list[dict] = []
    working = set(leaf_home)

    for src in guidelines:
        gid = src["id"]
        row = placement.get(gid)
        if row is None:
            raise SystemExit(f"missing placement row: {gid}")

        harvest_leaves = [
            job
            for job in (src.get("jobs") or [])
            if job in working
        ]
        status = row.get("placement_status") or ""
        kind = row.get("placement_kind") or ""

        if status.startswith("MULTI_HOME"):
            leaf_id = MULTI_HOME_PICK[gid]
            home = leaf_home[leaf_id]
        elif kind == "cluster" or gid in cluster_ids:
            facet_id = row["facet_id"]
            home = dict(facet_home[facet_id])
            home["leaf"] = ""
        elif kind == "leaf":
            leaf_id = row["leaf_id"]
            home = leaf_home[leaf_id]
        else:
            raise SystemExit(f"unplaced {gid} status={status!r} kind={kind!r}")

        out = {
            key: value
            for key, value in src.items()
            if key != "jobs"
        }
        out["container"] = home["container"]
        out["card"] = home["card"]
        out["facet"] = home["facet"]
        if home.get("leaf"):
            out["leaf"] = home["leaf"]

        if gid in LIVE_AGENT:
            out.update(LIVE_AGENT[gid])
        elif gid in cluster_ids:
            out.update(_cluster_agent(src, home))
        else:
            out["waive_reason"] = _waive_reason(row, harvest_leaves, home.get("leaf") or "")

        out = _ordered(out)
        (RULES / f"{gid}.json").write_text(
            json.dumps(out, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        written.append(out)

    by_id = {item["id"]: item for item in written}
    ordered_ids = [gid for gid in LIVE_SEED] + sorted(
        gid for gid in by_id if gid not in LIVE_SEED
    )
    index = {
        "guidelines": [_index_row(by_id[gid]) for gid in ordered_ids],
    }
    (CATALOG / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    blobs = [p for p in CATALOG.glob("*.json") if p.name not in LANE_SKIP]
    for path in blobs:
        path.unlink()

    print(f"wrote {len(written)} rules and index; deleted {len(blobs)} lane blobs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
