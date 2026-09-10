# Contributing

PRs welcome. Prefer small PRs — one concern each: catalog rows, server behavior, docs, or plugin pack.

**See also:** [Documentation map](README.md) · [MCP tools](TOOLS.md) · [Agent skill](../clients/claude/skills/open-ux/SKILL.md) · [Catalog authoring](../catalog/README.md)

## Before you open a PR

From the repo root, after `pip install -e "packages/mcp[dev]"`:

| Command | What it checks |
| --- | --- |
| `python -m open_ux validate-catalog --strict-fit` | Catalog JSON vs schema; task-language `apply_when` on gate Leaves |
| `claude plugin validate . --strict` | Claude Code plugin + marketplace layout |
| `node scripts/validate-cursor-plugin.mjs --strict` | Cursor plugin manifest and required files |
| `cd packages/mcp && python -m pytest` | Python server, tools, catalog loader, plugin contracts |

Maintainer harvest scripts live in [`scripts/`](../scripts/) — not part of this checklist unless your PR touches them.

## Adding a cite

**One claim per file.** A claim is one cited sentence a source actually says — not model advice, not a whole design-system page.

Path:

```
catalog/rules/{category}/{source}/{file}.json
```

The `id` field is the key (e.g. `govuk.hide-password-by-default-show-toggle`). Folders are browse layout; placement lives on the JSON and in `jobs.json`.

### Minimal shape

Required unless `waive_reason` is set (published catalog does not waive):

```json
{
  "id": "govuk.example-claim",
  "title": "example claim slug",
  "name": "Short name — GOV.UK",
  "rule": "One cited sentence — the claim.",
  "citation": [{ "source": "GOV.UK Design System — …", "url": "https://…" }],
  "check": "deterministic",
  "pass_when": ["When the UI matches the claim."],
  "fail_when": ["When the UI violates the claim."],
  "severity": "major",
  "container": "forms_and_input",
  "card": "design_a_form",
  "facet": "field_has_no_lasting_name",
  "leaf": "name_a_control",
  "overview": "Short definition — what this cite is.",
  "apply_when": "Task language — when this claim fits the work in hand.",
  "not_when": "Closest wrong use — not a host fail, a fence.",
  "agent_hint": "Short how-to while composing.",
  "description": "Two to four sentences expanding the claim."
}
```

| Field | Contributor note |
| --- | --- |
| `rule` | The claim — one sentence you can cite in a thread |
| `citation` | Real URL(s). Extra URLs support the same claim, not new claims |
| `apply_when` / `not_when` | Task language, not vendor marketing (“On Ant surfaces…”) |
| `container`, `card`, `facet`, `leaf` | Where the cite sits in the compose tree — see [`catalog/README.md`](../catalog/README.md) |
| `pass_when` / `fail_when` | How to tell if the claim applies to a UI |

Cluster-only facets omit `leaf` and list the id on the facet’s `guideline_ids[]` in `jobs.json`.

### Register in the tree

Add the cite id to `catalog/jobs.json` — on a leaf’s `guideline_ids` or a facet’s cluster list. Regenerate index if your workflow requires it; `validate-catalog` loads from `rules/` directly.

Optional on the cite:

- **`component[]`** — closed ids (`button`, …) when the claim is about that control. See component section in [`catalog/README.md`](../catalog/README.md).
- **`hints[]`** — host-language extras the pack skim does not already say. Omit the key when empty; do not copy `agent_hint` or component keywords.

### Validate

```bash
python -m open_ux validate-catalog --strict-fit
```

Schema reference: [`catalog/schema.json`](../catalog/schema.json). Deeper authoring (pack row, hints pass, components): [`catalog/README.md`](../catalog/README.md).
