# Helpers

Canonical list: [`registry.json`](registry.json). **`pip install open-ux`** ships every entry as an **`open-ux`** CLI subcommand on the user's machine.

```bash
pip install open-ux
open-ux helpers list
```

## Agent helpers (LLM local)

Run **after** MCP tools return data.

| CLI | When |
| --- | --- |
| `open-ux rank-pack` | Reorder one pack page after `Open-UX:pack` (host does not rank) |

```bash
open-ux rank-pack --query "delete confirm" < pack.json
```

## Contributor wire (terminal / CI)

Not the agent skill path when MCP is connected.

| CLI | Wire |
| --- | --- |
| `open-ux pack` | `Open-UX:pack` |
| `open-ux component` | `Open-UX:get_component` |
| `open-ux tools list` / `open-ux tools call` | MCP debug |

Repo shims in this directory (`pack.py`, `rank_pack.py`, …) delegate to the same CLI for contributors who clone the repo.

Catalog maintenance: [`scripts/`](../scripts/): not offered to agents.
