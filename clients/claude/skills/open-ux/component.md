---
name: open-ux-component
description: >-
  Use when opening one Open UX widget record (Open-UX:get_component) after
  seeing component[] on a pack row or Card. Field guide for the widget JSON —
  variants and accessibility, not cited criteria. After you read, go back to
  the pack.
---

# Open UX component

`Open-UX:get_component` opens one widget record. This is anatomy and variants, not a cite score. Open only for ids already on a pack row or Card — not all 38 upfront. Then return to `Open-UX:pack`.

## Shape

```json
{
  "found": true,
  "component": {
    "id": "",
    "title": "",
    "overview": "",
    "apply_when": "",
    "not_when": "",
    "vs": [],
    "variants": {},
    "accessibility": [],
    "keyboard": []
  }
}
```

Section switches omit keys when false (like pack `hints`). Default fetch includes `vs`, `variants`, `accessibility`, and `keyboard`. `keywords` and `used_on` are opt-in.

## Fields

**`overview`** — Short definition of what this widget is. Same grab as the index row. Start here.

| Field | What it gives | How to use it |
| --- | --- | --- |
| `overview` | Short definition | Fast confidence. Not a grade. |
| `apply_when` | When this widget fits | Button vs link vs toggle |
| `not_when` | Closest wrong widget | Set aside if that is your case |
| `vs` | Near-neighbor contrasts | Pick the right control |
| `variants` | Named axes (role, size, …) | Match design-system names |
| `accessibility` | A11y notes for this widget | Compose accessible markup |
| `keyboard` | Keyboard behavior | Focus and activation |
| `keywords` | Synonyms (opt-in) | Local search only; not on pack rows |
| `used_on` | Cards and cites that stamp this id (opt-in) | See where the widget appears |

## Pack browse row

`Open-UX:pack` echoes `component[]` as closed ids only (`button`). Variants and `keywords` live here — do not expect them on the pack row. Skim cites on the pack; open `get_component` when you need variant names or accessibility notes. Open `get_guideline` for the cited claim.

The decision is yours.
