# Catalog

One shared cited catalog. **`catalog/rules/{id}.json` is the SoT** — one guideline object per file.

- `rules/` — 309 guideline files (filename = `id`)
- `jobs.json` — 7 containers, 9 Cards, 21 Facets, 15 Leaves. Pointers only; no rule bodies
- `index.json` — generated `{id,title,jobs,lane,container,card,facet,leaf?}` (no rule bodies)
- `schema.json` — one guideline object

Placement on every rule: `container`, `card`, `facet`, and `leaf` when that Facet has working leaves. Cluster-only Facets omit `leaf` and the id sits in that Facet’s `guideline_ids[]`.

Agent-facing fields (`overview`, `apply_when`, `not_when`, `agent_hint`, `description`) are on the rule or the row has `waive_reason`. Never in SKILL.md.

`lane` is a harvest prefix on the index only (UNS-88). It is not a placement key.

The loader walks `catalog/rules/*.json`. Soft size: ~50–100 KB. Hard ceiling: ~384 KB (`open_ux.catalog` enforces both).
