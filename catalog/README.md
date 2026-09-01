# Catalog

One shared cited catalog, split by lane:

- `actions.json` — 40 Actions/verbs guidelines (UNS-65 craft-pass)
- `forms.json` — 54 Forms guidelines (UNS-66 craft-pass; first three are the LIVE seed)
- `index.json` — all lanes, `{id,title,jobs,lane}` only (no rule bodies)
- `schema.json` — guideline document shape

The loader merges lane files. `lane` is index-only and is not stored on guideline objects.

Soft size: ~50–100 KB. Hard ceiling: ~256 KB (`open_ux.catalog` enforces both).
