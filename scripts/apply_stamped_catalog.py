#!/usr/bin/env python3
"""Apply the stamped UNS-91 consolidate CSV: 302 rules + 13-card tree.

Drops 7 UNMAPPED leftovers. Regenerates jobs.json, rules/{category}/{source}/*.json, index.json, manifest.
Then folds the three verified same-claim families. Citation is always
an array of one or many {source, url}.

Fails closed unless --rewrite-tree is passed (OUX-25): a bare run would
overwrite live jobs.json, including cited leaves filled after the stamp.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "packages" / "mcp" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from open_ux.rule_paths import find_rule_file, iter_rule_files, rule_dest  # noqa: E402

CATALOG = ROOT / "catalog"
RULES = CATALOG / "rules"
REWRITE_FLAG = "--rewrite-tree"
LIVE_SEED = (
    "forms.field_labels.visible_label",
    "forms.field_labels.label_stays_visible",
    "forms.field_labels.error_identifies_and_fixes",
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
ORDER = [
    "id",
    "category",
    "segment",
    "title",
    "name",
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


def _ordered(guideline: dict) -> dict:
    out = {key: guideline[key] for key in ORDER if key in guideline}
    for key, value in guideline.items():
        if key not in out:
            out[key] = value
    return out


def _index_row(guideline: dict) -> dict:
    leaf = guideline.get("leaf")
    row = {
        "id": guideline["id"],
        "title": guideline.get("title") or "",
        "name": guideline.get("name") or guideline.get("title") or "",
        "jobs": [leaf] if leaf else [],
        "lane": str(guideline["id"]).split(".", 1)[0],
        "container": guideline["container"],
        "card": guideline["card"],
        "facet": guideline["facet"],
    }
    if leaf:
        row["leaf"] = leaf
    return row


def _leaf(leaf_id: str, ids: list[str]) -> dict:
    return {"id": leaf_id, "guideline_ids": ids}


def _parse_args(argv: list[str] | None = None) -> tuple[Path | None, bool]:
    args = list(sys.argv[1:] if argv is None else argv)
    rewrite = REWRITE_FLAG in args
    rest = [item for item in args if item != REWRITE_FLAG]
    csv_path = Path(rest[0]) if rest else None
    return csv_path, rewrite


def main(argv: list[str] | None = None) -> int:
    csv_path, rewrite = _parse_args(argv)
    if not rewrite:
        print(
            "apply_stamped_catalog.py rewrites jobs.json from the harvest CSV. "
            "Refusing without --rewrite-tree (OUX-25).",
            file=sys.stderr,
        )
        return 2
    if csv_path is None or not csv_path.is_file():
        print(
            "usage: apply_stamped_catalog.py --rewrite-tree <consolidated-309.csv>",
            file=sys.stderr,
        )
        return 2
    with csv_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 309:
        raise SystemExit(f"expected 309 CSV rows, got {len(rows)}")

    placed: list[dict] = []
    dropped: list[str] = []
    by_leaf: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        gid = row["id"]
        leaf = (row.get("leaf_id") or "").strip()
        status = (row.get("placement_status") or "").strip()
        if not leaf or status == "UNMAPPED":
            dropped.append(gid)
            continue
        placed.append(row)
        by_leaf[leaf].append(gid)

    if len(placed) != 302 or len(dropped) != 7:
        raise SystemExit(f"expected 302/7, got {len(placed)}/{len(dropped)}: {dropped}")

    def ids(leaf_id: str) -> list[str]:
        return sorted(by_leaf.get(leaf_id, []))

    jobs = {
        "containers": json.loads((CATALOG / "jobs.json").read_text(encoding="utf-8"))[
            "containers"
        ],
        "cards": [
            {
                "id": "design_a_form",
                "title": "Design a form",
                "container": "forms_and_input",
                "overview": "Compose the fields: names, controls, grouping, helpers.",
                "when": [
                    "design or build signup, settings, or checkout fields",
                    "label these fields",
                    "pick a control for a choice",
                    "group related inputs",
                    "mark required",
                    "helper text",
                ],
                "reject": [
                    {"id": "handle_form_errors", "why": "validation / inline errors after submit"},
                    {"id": "compose_sign_in", "why": "password / login / forgot-password"},
                    {"id": "build_a_multi_step_flow", "why": "wizard / step splitting"},
                    {"id": "design_actions_and_ctas", "why": "button wording / primary vs secondary"},
                    {"id": "compose_a_data_display", "why": "table or dashboard, not a form"},
                ],
                "hints": [
                    "form",
                    "signup",
                    "settings",
                    "label",
                    "placeholder",
                    "required",
                    "dropdown",
                    "checkbox",
                    "radio",
                    "fieldset",
                    "typeahead",
                    "autocomplete",
                    "suggestions as you type",
                ],
                "facets": [
                    {
                        "id": "field_has_no_lasting_name",
                        "title": "Field has no lasting name",
                        "leaves": [
                            _leaf("avoid_placeholder_as_label", ids("avoid_placeholder_as_label")),
                            _leaf("name_a_control", ids("name_a_control")),
                        ],
                    },
                    {
                        "id": "wrong_control_for_the_choice",
                        "title": "Wrong control for the choice",
                        "leaves": [
                            _leaf("choose_control_for_choice", ids("choose_control_for_choice")),
                            _leaf("use_familiar_control", ids("use_familiar_control")),
                        ],
                    },
                    {
                        "id": "related_inputs_feel_scattered",
                        "title": "Related inputs feel scattered",
                        "leaves": [_leaf("group_related_inputs", ids("group_related_inputs"))],
                    },
                    {
                        "id": "requirements_are_a_surprise",
                        "title": "Requirements are a surprise",
                        "leaves": [
                            _leaf("mark_requirements_up_front", ids("mark_requirements_up_front"))
                        ],
                    },
                    {
                        "id": "field_and_helper_wording",
                        "title": "Field and helper wording",
                        "leaves": [_leaf("word_the_field_help", ids("word_the_field_help"))],
                    },
                ],
            },
            {
                "id": "handle_form_errors",
                "title": "Handle form errors",
                "container": "forms_and_input",
                "overview": "Compose validation and recover from a rejected form submit.",
                "when": [
                    "composing validation",
                    "inline or summary errors",
                    "submit-failure messaging on a form",
                ],
                "reject": [
                    {
                        "id": "compose_feedback",
                        "why": "page-level empty / 404 / hard error, or silent save / toast",
                    },
                    {"id": "design_a_form", "why": "unmarked required before anyone submits"},
                ],
                "hints": ["validation", "invalid", "inline error", "form error", "fix this field"],
                "facets": [
                    {
                        "id": "errors_dont_point_to_the_fix",
                        "title": "Errors don't point to the fix",
                        "leaves": [
                            _leaf(
                                "explain_failure_next_to_cause",
                                ids("explain_failure_next_to_cause"),
                            )
                        ],
                    },
                    {
                        "id": "invalid_input_has_no_recovery",
                        "title": "Invalid input has no recovery",
                        "leaves": [
                            _leaf(
                                "recover_from_invalid_input",
                                ids("recover_from_invalid_input"),
                            )
                        ],
                    },
                ],
            },
            {
                "id": "compose_sign_in",
                "title": "Compose sign-in",
                "container": "forms_and_input",
                "overview": "Compose credential entry so people can get in.",
                "when": [
                    "login or sign-in fields",
                    "show password",
                    "forgot-password link",
                    "password creation",
                ],
                "reject": [
                    {"id": "design_a_form", "why": "ordinary non-credential fields"},
                    {"id": "handle_form_errors", "why": "inline validation after submit"},
                ],
                "hints": ["login", "sign in", "password", "credentials", "forgot"],
                "facets": [
                    {
                        "id": "credentials_are_hard_to_enter",
                        "title": "Credentials are hard to enter",
                        "leaves": [_leaf("show_the_password", ids("show_the_password"))],
                    }
                ],
            },
            {
                "id": "design_actions_and_ctas",
                "title": "Design actions and CTAs",
                "container": "actions_and_decisions",
                "overview": "Make the next step obvious and hittable.",
                "when": [
                    "primary vs secondary",
                    "label this submit or continue",
                    "toolbar actions",
                    "these buttons are too small on mobile",
                    "command panel or menus",
                ],
                "reject": [
                    {
                        "id": "protect_destructive_and_leave",
                        "why": "delete / discard / confirm, or unsaved leave",
                    },
                    {"id": "design_a_form", "why": "field labels"},
                    {"id": "write_the_interface", "why": "page voice or link destination text"},
                    {
                        "id": "compose_feedback",
                        "why": "spinner / loading on the control itself",
                    },
                ],
                "hints": [
                    "button",
                    "cta",
                    "submit",
                    "primary",
                    "secondary",
                    "hit target",
                    "tap",
                    "menu",
                    "toolbar",
                ],
                "facets": [
                    {
                        "id": "no_clear_primary",
                        "title": "No clear primary",
                        "leaves": [_leaf("pick_primary_action", ids("pick_primary_action"))],
                    },
                    {
                        "id": "action_wording_hides_the_outcome",
                        "title": "Action wording hides the outcome",
                        "leaves": [_leaf("word_the_action", ids("word_the_action"))],
                    },
                    {
                        "id": "command_surface_is_opaque",
                        "title": "Command surface is opaque",
                        "leaves": [
                            _leaf(
                                "compose_the_command_surface",
                                ids("compose_the_command_surface"),
                            )
                        ],
                    },
                    {
                        "id": "controls_are_hard_to_hit",
                        "title": "Controls are hard to hit",
                        "leaves": [_leaf("keep_hit_target_usable", ids("keep_hit_target_usable"))],
                    },
                ],
            },
            {
                "id": "protect_destructive_and_leave",
                "title": "Protect destructive and leave",
                "container": "actions_and_decisions",
                "overview": "Stop destroy or discard from being one easy click.",
                "when": [
                    "add a delete confirmation",
                    "discard",
                    "navigate away from unsaved work",
                    "confirm or undo",
                ],
                "reject": [
                    {"id": "design_actions_and_ctas", "why": "unclear Continue / Submit label"},
                    {"id": "compose_feedback", "why": "destructive copy tone after it already fired"},
                ],
                "hints": [
                    "delete",
                    "destroy",
                    "discard",
                    "unsaved",
                    "confirm",
                    "undo",
                    "leave",
                    "teammate",
                    "member",
                    "subscription",
                    "cancel",
                ],
                "facets": [
                    {
                        "id": "destructive_is_too_easy",
                        "title": "Destructive is too easy",
                        "leaves": [
                            _leaf(
                                "disable_or_confirm_destructive",
                                ids("disable_or_confirm_destructive"),
                            )
                        ],
                    },
                    {
                        "id": "leaving_discards_work",
                        "title": "Leaving discards work",
                        "leaves": [_leaf("warn_before_leave", ids("warn_before_leave"))],
                    },
                ],
            },
            {
                "id": "compose_feedback",
                "title": "Compose feedback",
                "container": "feedback_and_status",
                "overview": "Say what happened or what is happening.",
                "when": [
                    "toast after save",
                    "loading state",
                    "spinner on a button",
                    "design a 404",
                    "error message for a failed payment or hard error",
                    "tone on failure",
                ],
                "reject": [
                    {"id": "handle_form_errors", "why": "inline field errors"},
                    {"id": "build_a_multi_step_flow", "why": "progress inside a wizard"},
                ],
                "hints": [
                    "toast",
                    "404",
                    "loading",
                    "spinner",
                    "saved",
                    "status",
                    "alert",
                ],
                "facets": [
                    {
                        "id": "system_stayed_quiet_after_change",
                        "title": "System stayed quiet after change",
                        "leaves": [_leaf("announce_system_status", ids("announce_system_status"))],
                    },
                    {
                        "id": "tone_fights_the_moment",
                        "title": "Tone fights the moment",
                        "leaves": [
                            _leaf("tone_of_voice_for_failure", ids("tone_of_voice_for_failure"))
                        ],
                    },
                ],
            },
            {
                "id": "orient_in_the_place",
                "title": "Orient in the place",
                "container": "navigation_and_wayfinding",
                "overview": "Know where you are and how to move between places.",
                "when": [
                    "design the sidebar",
                    "add breadcrumbs",
                    "tabs or a menu",
                    "how does the user know which section they are in",
                    "structure the top nav",
                ],
                "reject": [
                    {"id": "build_a_multi_step_flow", "why": "step indicators inside a wizard"},
                    {"id": "compose_search", "why": "search control placement"},
                ],
                "hints": [
                    "sidebar",
                    "breadcrumb",
                    "tabs",
                    "nav",
                    "menu",
                    "wayfinding",
                    "section",
                ],
                "facets": [
                    {
                        "id": "user_cant_tell_where_they_are",
                        "title": "User can't tell where they are",
                        "leaves": [_leaf("wayfind_after_nav", ids("wayfind_after_nav"))],
                    }
                ],
            },
            {
                "id": "compose_search",
                "title": "Compose search",
                "container": "navigation_and_wayfinding",
                "overview": "Place and compose search so people can find it and use it.",
                "when": [
                    "header or homepage search",
                    "search box vs search link",
                    "place the search control",
                ],
                "reject": [
                    {"id": "orient_in_the_place", "why": "site chrome / which section you are in"},
                    {"id": "write_the_interface", "why": "link destination wording"},
                ],
                "hints": ["search", "find", "query", "magnifying"],
                "facets": [
                    {
                        "id": "search_is_hard_to_find",
                        "title": "Search is hard to find",
                        "leaves": [
                            _leaf("place_the_search_control", ids("place_the_search_control"))
                        ],
                    }
                ],
            },
            {
                "id": "compose_a_data_display",
                "title": "Compose a data display",
                "container": "layout_and_data_display",
                "overview": "Arrange data so it can be scanned — table, grid, chart.",
                "when": [
                    "table or card grid for this data",
                    "compose a dashboard",
                    "make this table scannable",
                    "chart vs table",
                ],
                "reject": [
                    {"id": "design_a_form", "why": "controls inside a form, or density on a form"},
                    {"id": "compose_the_layout", "why": "page scan path, not a data widget"},
                    {"id": "choose_an_overlay", "why": "overlays on top"},
                ],
                "hints": ["table", "dashboard", "chart", "grid", "scannable", "density"],
                "facets": [
                    {
                        "id": "data_is_unscannable",
                        "title": "Data is unscannable",
                        "leaves": [
                            _leaf("chart_has_a_story", ids("chart_has_a_story")),
                            _leaf("map_is_not_the_only_channel", ids("map_is_not_the_only_channel")),
                        ],
                    }
                ],
            },
            {
                "id": "compose_the_layout",
                "title": "Compose the layout",
                "container": "layout_and_data_display",
                "overview": "Give the page a scan path.",
                "when": [
                    "page structure and headings",
                    "inverted pyramid",
                    "keep the page scannable",
                ],
                "reject": [
                    {"id": "compose_a_data_display", "why": "table, chart, or map"},
                    {"id": "write_the_interface", "why": "voice or link wording"},
                ],
                "hints": ["layout", "scan", "heading", "h1", "pyramid"],
                "facets": [
                    {
                        "id": "page_has_no_scan_path",
                        "title": "Page has no scan path",
                        "leaves": [_leaf("keep_the_page_scannable", ids("keep_the_page_scannable"))],
                    }
                ],
            },
            {
                "id": "write_the_interface",
                "title": "Write the interface",
                "container": "layout_and_data_display",
                "overview": "Word the interface so it talks to the person and names destinations.",
                "when": [
                    "link text",
                    "you / your voice",
                    "page copy that is not a button or field label",
                ],
                "reject": [
                    {"id": "design_actions_and_ctas", "why": "button / command verbs"},
                    {"id": "design_a_form", "why": "field labels"},
                    {"id": "orient_in_the_place", "why": "section chrome"},
                ],
                "hints": ["link text", "click here", "you", "your", "plain language"],
                "facets": [
                    {
                        "id": "link_text_hides_destination",
                        "title": "Link text hides destination",
                        "leaves": [
                            _leaf(
                                "name_the_link_by_destination",
                                ids("name_the_link_by_destination"),
                            )
                        ],
                    },
                    {
                        "id": "voice_talks_about_the_system",
                        "title": "Voice talks about the system",
                        "leaves": [_leaf("write_to_you", ids("write_to_you"))],
                    },
                ],
            },
            {
                "id": "choose_an_overlay",
                "title": "Choose an overlay",
                "container": "overlays_and_content_structure",
                "overview": "Pick the layer that holds the content.",
                "when": [
                    "modal vs accordion",
                    "tooltip or inline help",
                    "hide advanced options",
                    "design this side panel",
                ],
                "reject": [
                    {
                        "id": "protect_destructive_and_leave",
                        "why": "the destructive decision inside a dialog",
                    },
                    {"id": "design_a_form", "why": "fields inside a modal"},
                    {"id": "compose_the_layout", "why": "page layout"},
                ],
                "hints": [
                    "modal",
                    "dialog",
                    "accordion",
                    "tooltip",
                    "disclosure",
                    "side panel",
                    "drawer",
                ],
                "facets": [
                    {
                        "id": "wrong_layer_for_the_content",
                        "title": "Wrong layer for the content",
                        "leaves": [
                            _leaf(
                                "pick_modal_only_when_blocking",
                                ids("pick_modal_only_when_blocking"),
                            ),
                            _leaf("disclose_instead_of_dump", ids("disclose_instead_of_dump")),
                        ],
                    }
                ],
            },
            {
                "id": "build_a_multi_step_flow",
                "title": "Build a multi-step flow",
                "container": "multi_step_flows",
                "overview": "Split one task across steps and keep the user oriented.",
                "when": [
                    "build a checkout flow",
                    "split this long form into steps",
                    "add a progress indicator",
                    "what happens if they leave mid-flow",
                    "go back to an earlier step",
                    "change a previous answer",
                    "design the onboarding sequence",
                ],
                "reject": [
                    {"id": "design_a_form", "why": "single form on one screen"},
                    {"id": "orient_in_the_place", "why": "site-level nav chrome"},
                    {"id": "protect_destructive_and_leave", "why": "leave-warn as the only ask"},
                ],
                "hints": [
                    "wizard",
                    "steps",
                    "onboarding",
                    "checkout flow",
                    "progress",
                    "sequence",
                    "go back",
                    "earlier step",
                    "previous answer",
                ],
                "facets": [
                    {
                        "id": "too_much_on_one_step",
                        "title": "Too much on one step / lost in steps",
                        "leaves": [_leaf("show_step_progress", ids("show_step_progress"))],
                    }
                ],
            },
        ],
    }

    (CATALOG / "jobs.json").write_text(
        json.dumps(jobs, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    written: list[dict] = []
    keep_ids = {row["id"] for row in placed}
    for row in placed:
        gid = row["id"]
        path = find_rule_file(RULES, gid)
        if path is None:
            raise SystemExit(f"missing rule file {gid}")
        data = json.loads(path.read_text(encoding="utf-8"))
        data["container"] = row["container_id"]
        data["card"] = row["card_id"]
        data["facet"] = row["facet_id"]
        data["leaf"] = row["leaf_id"]
        if gid in LIVE_AGENT:
            data.update(LIVE_AGENT[gid])
        else:
            data["overview"] = row["overview"]
            data["apply_when"] = row["apply_when"]
            data["not_when"] = row["not_when"]
            data["agent_hint"] = row["agent_hint"]
            data["description"] = row["description"]
        data.pop("waive_reason", None)
        data = _ordered(data)
        dest = rule_dest(RULES, data)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if path.resolve() != dest.resolve():
            path.unlink()
        written.append(data)

    removed = []
    for path in iter_rule_files(RULES):
        gid = json.loads(path.read_text(encoding="utf-8")).get("id")
        if gid not in keep_ids:
            path.unlink()
            removed.append(gid)
    leftover = [gid for gid in dropped if find_rule_file(RULES, gid) is not None]
    if leftover:
        raise SystemExit(f"failed to drop UNMAPPED files: {leftover}")

    by_id = {item["id"]: item for item in written}
    ordered_ids = list(LIVE_SEED) + sorted(gid for gid in by_id if gid not in LIVE_SEED)
    index = {"guidelines": [_index_row(by_id[gid]) for gid in ordered_ids]}
    (CATALOG / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    size = sum(p.stat().st_size for p in iter_rule_files(RULES))
    print(f"wrote {len(written)} rules; dropped {removed}; catalog bytes {size}")
    print("leaf counts", {k: len(v) for k, v in sorted(by_leaf.items(), key=lambda x: -len(x[1]))})
    from fold_same_claim_rules import apply_folds

    apply_folds(CATALOG)
    from apply_rule_names import main as apply_names

    apply_names()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
