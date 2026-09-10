# Catalog

Cited UX guidelines. One claim per file.

```
catalog/rules/{category}/{source}/{file}.json
```

Example: `copy/polar/dont-duplicate-content.json` still has `"id": "polar.dont-duplicate-content"`. The folders are browse layout. The `id` field is the key.

- **Category** (Actions, Forms, Content, …) is the kind of problem on the rule. It is not a Situation Card and not a container. `content/` on disk is just that field.
- **Source** (Ant, Polaris, …) is who is cited. Actions is a category; Ant is a source. NN/g is not a published source until it is added back.
- **Filename** is the `id` without the harvest prefix.

`citation` is always an array of one or many `{source, url}`. Extra URLs are more sources for this one claim, not more claims.

## What’s here

| File | Role |
| --- | --- |
| `rules/` | 203 guideline files |
| `jobs.json` | 7 containers, 13 Situation Cards, Facet → Leaf map. Pointers only |
| `components.json` | Closed widget registry `{id, title, path}` |
| `components/` | 38 widget records (keywords, vs, variants, accessibility, keyboard) |
| `index.json` | Generated `{id,title,name,jobs,lane,container,card,facet,leaf?}` |
| `manifest.json` / `MANIFEST.md` | Generated category → source map for agents. No rule bodies |
| `schema.json` | One guideline object |

Placement on every rule: `container`, `card`, `facet`, and `leaf` when that Facet has working leaves. Cluster-only Facets omit `leaf` and list the id in that Facet’s `guideline_ids[]`. Agent-facing fields (`overview`, `apply_when`, `not_when`, `agent_hint`, `description`) are required on the rule, never in SKILL.md. `waive_reason` is the only way to omit them; published files do not use it.

## Pack row vs cite file

`Open-UX:pack` returns a **browse slice** per cite — not the full record. Rows include `overview`, `apply_when`, `not_when`, `rule`, `leaf`, `card`, `facet`, plus `hints` and `component` (arrays).

**Today:** **52** cites carry authored `hints[]` where host language diverges from skim; **151** omit the key. Pack omits `hints` when the cite omits it. `component[]` is stamped on 131 cites and all 13 Cards where the widget applies; pack echoes cite ids; `get_situation`, scoped `list_situations`, and the suggest map echo Card ids (omit the key when empty).

**Do not bridge `agent_hint` → `hints`.** They are different grains:

| Field | Where | Meaning |
| --- | --- | --- |
| `overview`, `apply_when`, `not_when` | cite file; on pack row | Skim layer: what this cite is and when it fits |
| `agent_hint` | cite file only (`get_guideline`) | Short how-to while composing |
| `hints` | cite file; on pack row | Host-language extras this row’s skim does not already say. Omit the key when there are none — do not ship `[]`. |
| `component` | Card in `jobs.json`; cite file; on pack row | Closed widget ids. Join key only (`button`). Not a variant list. |
| `hints` on a Card | `jobs.json` | Situation-map scan today. Do not copy component `keywords` here. |

Browse works without cite-level tags: use the pack row, then `get_guideline` when you need `agent_hint` or `description`. Optional local reorder: `helpers/rank_pack.py` (BM25 over pack scan fields; host does not rank). See [`helpers/registry.json`](../helpers/registry.json).

**Hints pass:** add cite `hints[]` only when the row needs host words skim does not already say; omit the key when it does not. Manifest: `scripts/cite_hints.json`.

## Component (locked)

A component is a named widget (`button`). It is a matching dimension, not a Card and not a cite. JSON cannot hold an object pointer. Store the id; resolve the record at load time — same join as `card`, `leaf`, and `guideline_ids`.

**Stamp `component[]` only on the Card and the cite.**

| Grain | `component[]` | Why |
| --- | --- | --- |
| Card | yes | Does this job use the widget? |
| Cite | yes | Is this claim about the widget? |
| Facet / Leaf | no | Inherit from the Card. Do not restamp. |
| Container | no | A union of widgets is not a match. |

Pack echoes the cite’s `component[]` (ids only). Do not put `variant`, `size`, `state`, `accessibility`, or `keyboard` on the pack row — a row can list more than one widget, so those axes have no owner. Open the component record for that shape via `Open-UX:get_component` (section switches omit keys when false; `keywords` and `used_on` are opt-in). Index: `Open-UX:list_components`.

**Keywords stay on the component record.** Do not copy them into `jobs.json`. Do not echo them onto every pack row. Inside a Card page, every cite that stamped the same widget would repeat the same four words; that adds no rank.

Cite `hints[]` are host words this claim needs that `overview` / `apply_when` / `rule` / `component[]` do not already say. Omit the key when you have none — `govuk.button-types-named` omits. Do not add sibling-source synonyms (`emphasis`, `loudness`). Do not ship `[]`. Do not fill from `agent_hint`. Do not fill from component `keywords`.

`lane` on the index is the harvest prefix of the `id`. It is not a folder and not a placement key.

The loader walks `catalog/rules/**/*.json`. Hard ceiling ~768 KB.

## Situation Cards

The picker is a Card — one compose job. Containers are how the skill lists them. There are seven containers and thirteen Cards:

| Container | Cards |
| --- | --- |
| Forms & input | `design_a_form`, `handle_form_errors`, `compose_sign_in` |
| Actions & decisions | `design_actions_and_ctas`, `protect_destructive_and_leave` |
| Feedback & status | `compose_feedback` |
| Navigation & wayfinding | `orient_in_the_place`, `compose_search` |
| Layout & data display | `compose_a_data_display`, `compose_the_layout`, `write_the_interface` |
| Overlays & content structure | `choose_an_overlay` |
| Multi-step flows | `build_a_multi_step_flow` |

`write_the_interface` is for page voice and link-destination text. Button verbs still go to `design_actions_and_ctas`; field labels still go to `design_a_form`.

## Harvest rows that are not files

The harvest had 309 rows. 200 files were published after dropping primary Apple HIG and NN/g cites. Three GOV.UK password-input claims were added later for `compose_sign_in` (OUX-25), so 203 files are on disk. The other 14 harvest rows were never files; they are listed here so a missing id is explained, not silent.

### No published file

These rows had no honest home on a working Leaf (domain-specific, essay-level, or no matching compose job yet):

| id | Why |
| --- | --- |
| `canada.functional-alt-140-decorative-empty` | Alt / decorative image |
| `canada.tables-no-blank-cells` | Table cell completeness |
| `nl.last-step-is-send-not-volgende` | Last-step send label |
| `nng.eas-framework` | Framework essay, not a compose rule |
| `nng.guest-checkout-prominent` | Guest checkout (ecommerce), out of v1 |
| `polar.be-consistent-no-synonyms` | Voice consistency without a Leaf |
| `uswds.search-min-27-chars-persist-query` | Search-box geometry |

### Same claim, one file

These seven rows support the same pass/fail as an existing rule. Their URLs live on the survivor `citation[]`. Survivor text is unchanged.

| Folded into | From |
| --- | --- |
| `forms.inputs.forgiving_format_autoformat` | `nl.dont-reject-valid-variants`, `nl.no-forced-input-patterns-or-masks`, `forms.inputs.allow_typos_abbreviations` |
| `forms.fields.distinguish_optional_required` | `fluent.required-asterisk-or-one-instruction`, `suomi.default-required-optional-in-parentheses`, `nl.mark-optional-niet-verplicht-above-form` |
| `ant.checkbox-vs-switch` | `suomi.toggle-button-immediate-input-submit` |

Adjacent claims (select cutoffs, date-type slices, default-when-possible) stay as their own files.
