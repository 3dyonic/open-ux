# Open UX: enable

## Get a key (hosted)

1. [open-ux.dev/invite](https://open-ux.dev/invite) and request access.
2. Redeem the invite → copy bearer token `uxmcp_…`.
3. **Claude Code:** paste when the plugin asks (`api_key`). **Cursor:** **Plugins → Configure** → `OPEN_UX_API_KEY`.

## Use the plugin

1. Map the job with `Open-UX:get_situation` (leaf counts).
2. Pull criteria: `Open-UX:pack` with `jobs=<card_id>` or `jobs=<leaf_id>`.
3. Read envelope reject and row fit; `get_guideline`; `get_component` when `component[]` names the control.

No key? `pip install open-ux` (or `pip install -e "packages/mcp[dev]"` in this repo) and point MCP at [`mcp.stdio.json`](mcp.stdio.json); local `python -m open_ux stdio`, same catalog. Hosted [`mcp.json`](mcp.json) updates on deploy.

Do not invent a key. Do not send a file.
