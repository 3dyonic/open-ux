# Helpers (for agents)

Optional Python helpers agents may run locally. **Available, not required** — `Open-UX:*` MCP tools stay first-class. Do not invent a pack fetcher or BM25 ranker.

Canonical list: [`registry.json`](registry.json).

| Helper | When |
| --- | --- |
| `pack.py` | Same wire as `Open-UX:pack` without MCP |
| `rank_pack.py` | Reorder one pack page after `Open-UX:pack` (host does not rank) |
| `get_component.py` | Same wire as `Open-UX:get_component` without MCP |
| `mcp_call.py` | `tools/list` and `tools/call` without a Claude session |

From repo root (after `pip install open-ux` or editable install):

```bash
python3 helpers/pack.py --jobs design_a_form
python3 helpers/rank_pack.py --query "delete confirm" < pack.json
python3 helpers/get_component.py button --include-used-on
python3 helpers/mcp_call.py list
```

Contributor catalog scripts live in [`scripts/`](../scripts/) — not offered to agents.
