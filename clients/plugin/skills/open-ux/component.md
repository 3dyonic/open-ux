# Open UX component

Component records live in `catalog/components/`: a context helper joined to Cards and cites by **`component[]`**. They do not replace **`pack`** or **`get_guideline`**.

`Open-UX:get_component` opens one component record; variants, accessibility, keyboard; not a cite score. Open only for ids already on a pack row or Card: not all 38 upfront. Usually after **`get_guideline`** on the same row. Then return to `Open-UX:pack`.

## Parameters

| Param | Default | Section |
| --- | --- | --- |
| `id` |: | Closed id from `component[]` |
| `include_vs` | true | Near-neighbor contrasts |
| `include_variants` | true | Named axes (role, size, …) |
| `include_accessibility` | true | A11y notes |
| `include_keyboard` | true | Keyboard behavior |
| `include_keywords` | false | Synonyms (local search only) |
| `include_used_on` | false | Cards and cites that stamp this id |

False omits the key from the response (like pack `hints`).

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

**`overview`:** Short definition of what this component is. Same grab as the index row. Start here.

| Field | What it gives | How to use it |
| --- | --- | --- |
| `overview` | Short definition | Fast confidence. Not a grade. |
| `apply_when` | When this component fits | Button vs link vs toggle |
| `not_when` | Closest wrong control | Set aside if that is your case |
| `vs` | Near-neighbor contrasts | Pick the right control |
| `variants` | Named axes (role, size, …) | Match design system names |
| `accessibility` | A11y notes for this component | Compose accessible markup |
| `keyboard` | Keyboard behavior | Focus and activation |
| `keywords` | Synonyms (opt-in) | Local search only; not on pack rows |
| `used_on` | Cards and cites that stamp this id (opt-in) | See where the component appears |

## Pack browse row

`Open-UX:pack` echoes `component[]` as closed ids only (`button`). Variants and `keywords` live here: do not expect them on the pack row. Skim cites on the pack; open `get_component` when you need variant names or accessibility notes. Open `get_guideline` for the cited claim.

The decision is yours.
