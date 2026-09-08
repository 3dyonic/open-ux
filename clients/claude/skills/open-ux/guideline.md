---
name: open-ux-guideline
description: >-
  Use when opening one Open UX guideline (Open-UX:get_guideline) or
  reading a full cited record. Field guide for the guideline JSON —
  what each field gives and how to use it. Not a grade. After you
  read, go back to the audit shelf.
---

# Open UX guideline

`Open-UX:get_guideline` opens one full cite. This is the record, not a score. We are a catalog. They choose what to take — including which fields. Then return to `Open-UX:audit`.

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
| `citation` | Who said it, with URL | Show the house |
| `name` | Claim + house | Who published it; two houses can disagree |
| `id` | Key | Already used to fetch this record |
| `title` | Slug | Skip on a scan |
| `facet` / `card` / `container` | Place in the tree | Sibling cites or another Card |

The decision is yours.
