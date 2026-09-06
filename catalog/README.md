# Catalog

One shared cited catalog. **`catalog/rules/{category}/{source}/{id}.json` is the SoT** — one guideline object per file.

- `rules/` — 295 guideline files, grouped **category first, then source**. Filename = `id`. Actions is a category; Ant is a source. Seven leftovers with no honest Leaf were dropped. Same-claim rows fold onto one survivor. `citation` is always an array of one or many `{source, url}`.
- `jobs.json` — 7 containers, 13 Cards, Facet → Leaf map. Pointers only; no rule bodies
- `index.json` — generated `{id,title,name,jobs,lane,container,card,facet,leaf?}` (no rule bodies). `name` is the human-friendly label.
- `manifest.json` / `MANIFEST.md` — generated category → source map for skill reference. No rule bodies. Agents load this, then fetch one id.
- `schema.json` — one guideline object

Placement on every rule: `container`, `card`, `facet`, and `leaf` when that Facet has working leaves. Cluster-only Facets omit `leaf` and the id sits in that Facet’s `guideline_ids[]`.

Agent-facing fields (`overview`, `apply_when`, `not_when`, `agent_hint`, `description`) are on the rule or the row has `waive_reason`. Never in SKILL.md.

`lane` is a harvest prefix on the index only (UNS-88). It is not a placement key. It is not a folder.

The loader walks `catalog/rules/**/*.json`. Soft size: ~256 KB. Hard ceiling: ~768 KB (`open_ux.catalog` enforces both). Agent-facing copy on every rule is why the catalog is larger than the old waived pack.
