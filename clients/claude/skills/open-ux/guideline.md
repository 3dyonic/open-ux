---
name: open-ux-guideline
description: >-
  Use when opening one Open UX guideline (Open-UX:get_guideline) or
  reading a full cited record. Field guide for the guideline JSON —
  what each field gives and how to use it. Not a grade. After you
  read, go back to the pack.
---

# Open UX guideline

`Open-UX:get_guideline` opens one full cite. This is the record, not a score. We are a catalog. They choose what to take — including which fields. Then return to `Open-UX:pack`.

## Shape

```json
{
  "found": true,
  "guideline": {
    "id": "",
    "title": "",
    "name": "",
    "overview": "",
    "rule": "",
    "apply_when": "",
    "not_when": "",
    "agent_hint": "",
    "description": "",
    "pass_when": [],
    "fail_when": [],
    "citation": [{ "source": "", "url": "" }],
    "facet": "",
    "card": "",
    "container": ""
  }
}
```

## Fields

**`overview`** — Short definition of what this guideline is. Same grab as the browse row. Start here. Confirm you opened the right cite.

| Field | What it gives | How to use it |
| --- | --- | --- |
| `overview` | Short definition | Fast confidence. Not a grade. |
| `apply_when` | When to use, in task language | See if this cite fits the work in hand |
| `not_when` | Closest wrong use | Set aside if that is your case — not a host fail |
| `agent_hint` | Short how-to while composing | Use when making the UI |
| `description` | Half-paragraph | When `overview` is not enough |
| `rule` | The cited claim | The sentence you can cite |
| `pass_when` / `fail_when` | The cite’s own criteria | Yours to apply; not a host score of the UI |
| `citation` | Who said it, with URL | Show the source |
| `name` | Claim + source | Who published it; two sources can disagree |
| `id` | Key | Already used to fetch this record |
| `title` | Slug | Skip on a scan |
| `facet` / `card` / `container` | Place in the tree | Sibling cites or another Card |

## Pack browse row

`Open-UX:pack` returns a slice of each cite — not this full shape. The row has `overview`, `apply_when`, `not_when`, `rule`, placement keys, and `hints` / `component` (arrays).

`component[]` is closed widget ids (`button`) — join only, authored on the Card and the cite. Variants and `keywords` live on the component record; do not expect them on this row. Open `Open-UX:get_component` for variant names and accessibility notes when `component[]` names a widget. `hints[]` are host extras this skim does not already say; omit the key when there are none. Do not expect `agent_hint` there — that stays on this full record. Skim on the pack; open `get_guideline` when you need the how-to.

The decision is yours.
