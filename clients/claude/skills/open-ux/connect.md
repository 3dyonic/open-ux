# Connect

`pip install` the package, or hosted — same tools, same Cards. Package name: `open-ux`. Console script: `open-ux`.

```bash
pip install open-ux
python -m open_ux validate-catalog
python -m open_ux stdio
OPEN_UX_MODE=hosted python -m open_ux http
```

Same catalog. No invite. Telemetry off. Point MCP clients at local stdio (clients/claude/mcp.stdio.json in this repo).

- **Hosted** (shared live catalog): `https://open-ux.dev/mcp` + bearer `uxmcp_` (`OPEN_UX_API_KEY`). Request an invite at `/invite` (landing **Get a key**).

**LLM-local helper (optional):** `pip install open-ux` on the machine ships **`open-ux rank-pack`** — BM25 reorder of one pack page after **`Open-UX:pack`**. Plugin + key alone do not install it; one local pip install is enough (no server call for rank).
