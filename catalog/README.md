# Catalog

Cited UX guidelines. One claim per file.

```
catalog/rules/{category}/{source}/{file}.json
```

Example: `copy/polar/dont-duplicate-content.json` still has `"id": "polar.dont-duplicate-content"`. The folders are browse layout. The `id` field is the key.

- **Category** (Actions, Forms, Content, …) is the kind of problem on the rule. It is not a Situation Card and not a container. `content/` on disk is just that field.
- **Source** (Ant, NN/g, Polaris, …) is who is cited. Actions is a category; Ant is a source.
- **Filename** is the `id` without the harvest prefix.

`citation` is always an array of one or many `{source, url}`. Extra URLs are more sources for this one claim, not more claims.

## What’s here

| File | Role |
| --- | --- |
| `rules/` | 295 guideline files |
| `jobs.json` | 7 containers, 13 Situation Cards, Facet → Leaf map. Pointers only |
| `index.json` | Generated `{id,title,name,jobs,lane,container,card,facet,leaf?}` |
| `manifest.json` / `MANIFEST.md` | Generated category → source map for agents. No rule bodies |
| `schema.json` | One guideline object |

Placement on every rule: `container`, `card`, `facet`, and `leaf` when that Facet has working leaves. Agent-facing fields (`overview`, `apply_when`, `not_when`, `agent_hint`, `description`) live on the rule, never in SKILL.md.

`lane` on the index is the harvest prefix of the `id`. It is not a folder and not a placement key.

The loader walks `catalog/rules/**/*.json`. Soft size ~256 KB. Hard ceiling ~768 KB.

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

The harvest had 309 rows. 295 files are published. The other 14 are listed here so a missing id is explained, not silent.

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
