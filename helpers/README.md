# Helpers

Canonical list: [`registry.json`](registry.json).

## Agent helpers (LLM-local, ships with pip)

Run **after** MCP tools return data. **`pip install open-ux`** installs **`open-ux rank-pack`** on the user's machine. Plugin + hosted MCP alone do not — agents need that one local pip install for optional reorder.

| CLI | When |
| --- | --- |
| `open-ux rank-pack` | Reorder one pack page after `Open-UX:pack` (host does not rank) |

```bash
pip install open-ux
open-ux rank-pack --query "delete confirm" < pack.json
```

Repo shim: `python3 helpers/rank_pack.py` (same wire). Do not invent a pack fetcher or BM25 ranker. Do not substitute helpers for `Open-UX:*` tools.

## Contributor wire (terminal / CI)

Same wire as MCP — not the agent skill path. See `contributor_wire` in [`registry.json`](registry.json).

Catalog maintenance scripts live in [`scripts/`](../scripts/) — not offered to agents.
