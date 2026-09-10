# Scripts (contributors)

Catalog and repo maintenance — **not** offered to agents. Agents use **`Open-UX:*` MCP tools** plus optional LLM-local [`helpers/rank_pack.py`](../helpers/rank_pack.py) ([`helpers/registry.json`](../helpers/registry.json) → `agent_helpers`).

| Script | Role |
| --- | --- |
| `apply_component_stamps.py` | Stamp Card/cite `component[]` from `component_stamps.json` |
| `component_stamps.json` | Stamp manifest (Card + cite → component ids) |
| `apply_cite_hints.py` | Apply cite `hints[]` from `cite_hints.json` |
| `cite_hints.json` | Cite hints manifest (host scan extras only) |
| `apply_stamped_catalog.py` | Apply stamped catalog generation |
| `apply_rule_names.py` | Rule name normalization |
| `split_rules.py` | Split bundled rule files |
| `fold_same_claim_rules.py` | Fold duplicate claims |
| `drop_apple_nng_primary.py` | Source cleanup |

Run from repo root after `pip install -e "packages/mcp[dev]"`.

## Plugin manifests (agents)

| Script | Role |
| --- | --- |
| `validate-cursor-plugin.mjs` | Cursor marketplace + `.cursor-plugin/plugin.json` (adapted from [cursor/plugin-template](https://github.com/cursor/plugin-template)); `--strict` fails on warnings |

Claude: `claude plugin validate . --strict` and `claude plugin validate ./clients/claude --strict`. Both run in CI (`.github/workflows/test.yml`).
