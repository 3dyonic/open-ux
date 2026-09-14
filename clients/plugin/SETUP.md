# Open UX: enable

Plugins are not in the public marketplaces yet; install from this GitHub repo. Marketplace submit is paused until Cowork and Desktop Chat smoke paths exist.

## Get a key (hosted)

1. [open-ux.dev/invite](https://open-ux.dev/invite) and request access.
2. Redeem the invite → copy bearer token `uxmcp_…`.
3. Paste into plugin config (not mcp.json first):
   - **Claude Code:** when the plugin asks (`api_key`).
   - **Cursor:** **Plugins → Configure** → `OPEN_UX_API_KEY`.

## Claude Code

```bash
claude plugin marketplace add 3dyonic/open-ux
claude plugin install open-ux@open-ux
```

Enable the plugin; paste `uxmcp_` into plugin `api_key` when prompted.

Desktop **Code** panel: local plugins only — it cannot add a remote GitHub marketplace. Use the CLI path above, or enable a local plugin from a repo checkout and paste `api_key`.

## Cursor

Enable the Open UX plugin in this repository. **Plugins → Configure** → `OPEN_UX_API_KEY`.

## Use the plugin

1. Map the job with `Open-UX:get_situation` (leaf counts).
2. Pull criteria: `Open-UX:pack` with `jobs=<card_id>` or `jobs=<leaf_id>`.
3. Read envelope reject and row fit; `get_guideline`; `get_component` when `component[]` names the control.

## Advanced / other clients

Paste MCP config only here. Other clients: `Authorization: Bearer uxmcp_…` on `https://open-ux.dev/mcp`. This plugin’s [`.mcp.json`](.mcp.json) is `Authorization: Bearer ${user_config.api_key}` for that URL.

No key? `pip install open-ux` (or `pip install -e "packages/mcp[dev]"` in this repo) and point MCP at [`mcp.stdio.json`](mcp.stdio.json); local `python -m open_ux stdio`, same catalog. Hosted Cursor [`mcp.json`](mcp.json) updates on deploy.

Do not invent a key. Do not send a file.
