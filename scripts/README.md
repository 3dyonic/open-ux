# Scripts (contributors)

Catalog and repo maintenance — **not** offered to agents. Agents use [`helpers/`](../helpers/) instead ([`helpers/registry.json`](../helpers/registry.json)).

| Script | Role |
| --- | --- |
| `apply_component_stamps.py` | Stamp Card/cite `component[]` from `component_stamps.json` |
| `component_stamps.json` | Stamp manifest (Card + cite → widget ids) |
| `apply_cite_hints.py` | Apply cite `hints[]` from `cite_hints.json` |
| `cite_hints.json` | Cite hints manifest (host scan extras only) |
| `apply_stamped_catalog.py` | Apply stamped catalog generation |
| `apply_rule_names.py` | Rule name normalization |
| `split_rules.py` | Split bundled rule files |
| `fold_same_claim_rules.py` | Fold duplicate claims |
| `drop_apple_nng_primary.py` | Source cleanup |

Run from repo root after `pip install -e "packages/mcp[dev]"`.
