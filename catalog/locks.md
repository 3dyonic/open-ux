# Catalog locks (UNS-91)

Answers the three review holds. Do not treat the Architect CSV as still live where this file disagrees.

## (a) Cards: 13, stamped

The structure CSV was 9 Cards. This phase stamps **13**. No 14th. Skill, `jobs.json`, and `CARD_IDS` match.

Four compose jobs added because they were stretching an existing Card:

| Card | Container | Why it is a Card, not a Facet |
| --- | --- | --- |
| `compose_sign_in` | `forms_and_input` | Login / password / forgot-password is not “design a form” |
| `compose_search` | `navigation_and_wayfinding` | Placing search is not “orient in the place” |
| `compose_the_layout` | `layout_and_data_display` | Page scan / headings is not a table or chart |
| `write_the_interface` | `layout_and_data_display` | Page voice and link-destination text is the job |

Copy stays a Facet line on Forms / Actions / Feedback. `write_the_interface` is the picker when the compose job **is** the wording. It is not an 8th container.

Containers stay the locked seven. `content/` on disk is the rule `category` field (harvest taxonomy). It is not a container, not a Card, not a picker.

## (b) Path: nested, accepted

Architect lock was `catalog/rules/{id}.json`.

Accepted layout: `catalog/rules/{category}/{source}/{file}.json`

- Category folder = `category` on the rule (Actions, Forms, Content, …). Not a container.
- Source folder = citation house (Ant, NN/g, Polaris, …). Actions ≠ Ant.
- Filename drops the harvest prefix. `copy/polar/dont-duplicate-content.json` still has `"id": "polar.dont-duplicate-content"`.
- Loader walks `catalog/rules/**/*.json`. `id` is the key; filename is not.

## (c) 14 files off disk (309 → 295)

Not silent. Every id below is accounted for. Remaining 295 each have a home.

### 7 UNMAPPED — no honest Leaf (dropped)

No file. No waive-on-disk row. Gap stays on [UNS-89](https://linear.app/3dyonic/issue/UNS-89) if a Card should exist later.

| id | Why no home |
| --- | --- |
| `canada.functional-alt-140-decorative-empty` | Alt / decorative image — no working Leaf |
| `canada.tables-no-blank-cells` | Table cell completeness — no working Leaf |
| `nl.last-step-is-send-not-volgende` | Last-step send label — no honest Leaf on the multi-step Card |
| `nng.eas-framework` | Framework essay, not a compose Leaf |
| `nng.guest-checkout-prominent` | Guest checkout — ecommerce domain pack, out of v1 |
| `polar.be-consistent-no-synonyms` | Voice consistency — no working Leaf |
| `uswds.search-min-27-chars-persist-query` | Search-box geometry — no honest Leaf on `compose_search` |

### 7 same-claim folds — URLs on the survivor

Deleted files. Survivor `citation[]` holds every URL. Survivor rule text unchanged.

| Deleted | Survivor |
| --- | --- |
| `nl.dont-reject-valid-variants` | `forms.inputs.forgiving_format_autoformat` |
| `nl.no-forced-input-patterns-or-masks` | `forms.inputs.forgiving_format_autoformat` |
| `forms.inputs.allow_typos_abbreviations` | `forms.inputs.forgiving_format_autoformat` |
| `fluent.required-asterisk-or-one-instruction` | `forms.fields.distinguish_optional_required` |
| `suomi.default-required-optional-in-parentheses` | `forms.fields.distinguish_optional_required` |
| `nl.mark-optional-niet-verplicht-above-form` | `forms.fields.distinguish_optional_required` |
| `suomi.toggle-button-immediate-input-submit` | `ant.checkbox-vs-switch` |

Cutoff fights, date-type slices, and “preselect when possible” were **not** folded — those are adjacent claims and still have their own files.
