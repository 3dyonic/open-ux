#!/usr/bin/env python3
"""Write a human-friendly name on every rule and place it on disk.

Layout: catalog/rules/{category}/{source}/{file}.json
The harvest prefix is in the folder; id stays on the rule.
Name: claim first, source last. Actions is a category; Ant is a source.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "packages" / "mcp" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from open_ux.catalog import (  # noqa: E402
    build_manifest,
    iter_rule_files,
    render_manifest_markdown,
    rule_dest,
    source_house,
)

RULES = ROOT / "catalog" / "rules"
INDEX = ROOT / "catalog" / "index.json"
MANIFEST_JSON = ROOT / "catalog" / "manifest.json"
MANIFEST_MD = ROOT / "catalog" / "MANIFEST.md"
LIVE_SEED = (
    "forms.field_labels.visible_label",
    "forms.field_labels.label_stays_visible",
    "forms.field_labels.error_identifies_and_fixes",
)

# Short display labels. Derived from the existing title/slug, not new claims.
# Do not put the source at the start — display_name appends it.
OVERRIDES = {
    "forms.field_labels.visible_label": "Visible field label",
    "forms.field_labels.label_stays_visible": "Label stays visible",
    "forms.field_labels.error_identifies_and_fixes": "Error identifies and fixes",
    "actions.buttons.follow_platform_ok_cancel_order": "Follow the platform OK/Cancel order",
    "actions.buttons.default_not_destructive": "Default is not destructive",
    "actions.buttons.one_primary": "One primary action",
    "actions.buttons.style_not_size": "Style, not size",
    "actions.close_saves_separate_cancel": "Close saves; Cancel is separate",
    "actions.copy.explicit_verb_not_ok": "Explicit verb, not OK",
    "actions.copy.ellipsis_needs_more_input": "Ellipsis means more input",
    "actions.icons.always_visible_text_label": "Always-visible text label",
    "actions.prominent_done_or_assumed_next": "Prominent Done or assumed next",
    "ant.checkbox-vs-switch": "Checkbox vs switch",
    "ant.dropdown-when-over-5-no-truncate": "Dropdown over 5, no truncate",
    "ant.ok-cancel-default-vs-explicit-verb": "OK/Cancel default vs explicit verb",
    "ant.one-cta-per-screen": "One CTA per screen",
    "ant.radio-count-2-to-5": "Radio count 2 to 5",
    "canada.doormats-max-9": "Doormats max 9",
    "canada.must-need-may-might": "Must, need to, may, might",
    "canada.no-click-here-same-text-same-destination": "No “click here”; same text, same destination",
    "canada.no-eg-ie-spell-out-and": "No e.g. or i.e.; spell out and",
    "canada.you-your-never-i-my": "You/your, never I/my",
    "canada.unique-title-one-h1-heading-every-200-words": "Unique title, one H1, heading every 200 words",
    "fluent.create-labels-new-thing": "Create labels: New {thing}",
    "fluent.ios-chrome-back-done-cancel": "iOS chrome: Back, Done, Cancel",
    "fluent.multistep-next-not-continue": "Multistep: Next, not Continue",
    "fluent.split-button-dont-repeat-primary": "Split button: don't repeat primary",
    "forms.copy.no_double_barreled": "No double-barreled questions",
    "forms.errors.next_to_field_not_summary_only": "Next to the field, not summary only",
    "forms.errors.not_color_only": "Not color only",
    "forms.errors.not_tooltip_only": "Not tooltip only",
    "forms.errors.modal_not_only_copy": "Modal is not the only copy",
    "forms.inputs.html_autocomplete_and_name": "HTML autocomplete and name",
    "forms.inputs.forgiving_format_autoformat": "Forgiving format, autoformat",
    "gold.no-abbr-expand-on-first-mention": "No abbr; expand on first mention",
    "govuk.dob-autocomplete-tokens": "Date-of-birth autocomplete tokens",
    "govuk.dont-assume-single-vs-multi-from-visuals": "Don't assume single vs multi from visuals",
    "govuk.dont-use-disabled-buttons": "Don't use disabled buttons",
    "govuk.radio-divider-or": "Radio divider “or”",
    "mui.dont-type-number": "Don't use type=number",
    "mui.most-alerts-dont-need-titles": "Most alerts don't need titles",
    "nl.dont-auto-dismiss-status-announce-complete": "Don't auto-dismiss status; announce complete",
    "nl.no-select-multiple": "No select multiple",
    "nl.step-n-of-m-in-title-and-above-form": "Step n of m in the title and above the form",
    "nng.dont-repeat-password-email-fields": "Don't repeat password or email fields",
    "nng.too-few-options-radios-not-dropdown": "Too few options: radios, not dropdown",
    "nng.too-many-combobox-not-long-dropdown": "Too many: combobox, not a long dropdown",
    "nsw.100pct-stacked-show-absolute-totals": "100% stacked: show absolute totals",
    "nsw.privacy-by-design-pia-security-day-one": "Privacy by design: PIA and security from day one",
    "polar.dont-duplicate-content": "Don't duplicate content",
    "polar.dont-use-modals-for-complex-forms": "Don't use modals for complex forms",
    "polar.encourage-action-cta-verb": "Encourage action: CTA verb",
    "polar.guide-dont-prescribe": "Guide, don't prescribe",
    "polar.labels-1-3-words-sentence-case-i18n": "Labels: 1–3 words, sentence case",
    "polar.plain-language-grade-7": "Plain language, grade 7",
    "polar.select-4plus-choice-list-under-4": "Select for 4+; choice list under 4",
    "spectrum.asterisk-is-icon-not-label-text": "Asterisk is an icon, not label text",
    "spectrum.min-width-1-5x-field-height": "Minimum width 1.5× field height",
    "spectrum.picker-min-width-2x-height": "Picker minimum width 2× height",
    "spectrum.toast-auto-dismiss-min-5s": "Toast auto-dismiss at least 5s",
    "suomi.button-max-three-words-mobile-full-width": "Button: max three words; full width on mobile",
    "suomi.date-hint-ppkkvvvv-calendar-optional-focus-trap": "Date hint always visible; calendar optional",
    "suomi.time-field-60px-hint-tmm-always-visible": "Time field ~60px with a visible t.mm hint",
    "suomi.toast-10s-hover-stick-then-float": "Toast 10s; hover sticks, then floats",
    "uswds.dont-hide-then-reveal-alerts": "Don't hide then reveal alerts",
    "uswds.dont-split-phone-ssn-card": "Don't split phone, SSN, or card",
    "uswds.filled-next-outline-this-page": "Filled Next, outline this page",
    "uswds.real-button-with-type-space-vs-enter": "Real button with type; Space vs Enter",
    "uswds.site-alert-dont-stack-dont-panic": "Site alert: don't stack, don't panic",
    "uswds.banner-gov-mil-https-every-page": ".gov/.mil HTTPS banner on every page",
}

ACRONYM = {
    "cta": "CTA",
    "html": "HTML",
    "url": "URL",
    "js": "JS",
    "ssn": "SSN",
    "pia": "PIA",
    "ok": "OK",
    "ios": "iOS",
    "h1": "H1",
    "gps": "GPS",
    "spa": "SPA",
    "ui": "UI",
    "en": "EN",
    "fr": "FR",
}
SMALL = {"a", "an", "the", "and", "or", "vs", "of", "to", "for", "in", "on", "by", "not", "plus", "per"}
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


def name_from_title(title: str) -> str:
    words = title.replace("_", " ").replace("-", " ").split()
    out: list[str] = []
    for index, raw in enumerate(words):
        low = raw.lower()
        if low == "dont":
            token = "Don't"
        elif low == "doesnt":
            token = "Doesn't"
        elif low in ACRONYM:
            token = ACRONYM[low]
        elif index == 0:
            token = raw[:1].upper() + raw[1:] if raw else raw
        elif low in SMALL:
            token = low
        else:
            token = raw
        out.append(token)
    return " ".join(out)


def display_name(guideline: dict) -> str:
    gid = guideline["id"]
    _slug, house = source_house(guideline)
    base = OVERRIDES[gid] if gid in OVERRIDES else name_from_title(
        guideline.get("title") or gid.split(".")[-1]
    )
    suffix = f" — {house}"
    if base.endswith(suffix):
        return base
    return f"{base}{suffix}"


def _index_row(guideline: dict) -> dict:
    leaf = guideline.get("leaf")
    row = {
        "id": guideline["id"],
        "title": guideline.get("title") or "",
        "name": guideline.get("name") or "",
        "jobs": [leaf] if leaf else [],
        "lane": str(guideline["id"]).split(".", 1)[0],
        "container": guideline["container"],
        "card": guideline["card"],
        "facet": guideline["facet"],
    }
    if leaf:
        row["leaf"] = leaf
    return row


def _prune_empty(root: Path) -> None:
    for folder in sorted((p for p in root.rglob("*") if p.is_dir()), reverse=True):
        if folder.is_dir() and not any(folder.iterdir()):
            folder.rmdir()


def main() -> int:
    written: list[dict] = []
    for path in iter_rule_files(RULES):
        data = json.loads(path.read_text(encoding="utf-8"))
        data["name"] = display_name(data)
        dest = rule_dest(RULES, data)
        dest.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(_ordered(data), indent=2, ensure_ascii=False) + "\n"
        dest.write_text(text, encoding="utf-8")
        if path.resolve() != dest.resolve():
            path.unlink()
        written.append(data)
    _prune_empty(RULES)
    by_id = {item["id"]: item for item in written}
    ordered_ids = list(LIVE_SEED) + sorted(gid for gid in by_id if gid not in LIVE_SEED)
    index = {
        "version": "0.3.0",
        "guidelines": [_index_row(by_id[gid]) for gid in ordered_ids],
    }
    INDEX.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ordered = [by_id[gid] for gid in ordered_ids]
    manifest = build_manifest(ordered)
    MANIFEST_JSON.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    MANIFEST_MD.write_text(render_manifest_markdown(manifest), encoding="utf-8")
    print(f"named {len(written)} rules; wrote manifest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
