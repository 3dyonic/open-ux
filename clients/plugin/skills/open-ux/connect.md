# Connect

`pip install` the package, or hosted; same tools, same Cards. Package name: `open-ux`. Console script: `open-ux`.

```bash
pip install open-ux
python -m open_ux validate-catalog
python -m open_ux stdio
OPEN_UX_MODE=hosted python -m open_ux http
```

Same catalog. No invite. Telemetry off. Point MCP clients at local stdio (clients/plugin/mcp.stdio.json in this repo).

- **Hosted** (shared live catalog): `https://open-ux.dev/mcp` + bearer `uxmcp_` (`OPEN_UX_API_KEY`). Request an invite at `/invite` (landing **Get a key**).

**Helpers (pip):** `pip install open-ux` on the machine ships all helper tools as **`open-ux`** subcommands: list with **`open-ux helpers list`**. See [`helpers/README.md`](../../../../helpers/README.md). Agent helper: **`open-ux rank-pack`** after **`Open-UX:pack`**. Plugin + key alone do not install them; one local pip install is enough (rank uses local BM25, not your server).
