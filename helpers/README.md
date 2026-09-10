# Helpers

Canonical list: [`registry.json`](registry.json).

## Agent helpers (LLM-local)

Run **after** MCP tools return data. The host fetches catalog data; helpers do what the host does not.

| Helper | When |
| --- | --- |
| `rank_pack.py` | Reorder one pack page after `Open-UX:pack` (host does not rank) |

```bash
python3 helpers/rank_pack.py --query "delete confirm" < pack.json
```

Do not invent a pack fetcher or BM25 ranker. Do not substitute helpers for `Open-UX:*` tools.

## Contributor wire (terminal / CI)

Same wire as MCP — for humans and automation without a plugin session. **Not** the agent skill path.

| Script | CLI |
| --- | --- |
| `pack.py` | `open-ux pack --jobs …` |
| `get_component.py` | `open-ux component button --include-used-on` |
| `mcp_call.py` | `open-ux tools list` |

Catalog maintenance scripts live in [`scripts/`](../scripts/) — not offered to agents.
