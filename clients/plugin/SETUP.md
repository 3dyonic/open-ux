# Open UX: enable

Plugins are not in the public marketplaces yet; install from this GitHub repo.

## Get a key (hosted)

1. [open-ux.dev/invite](https://open-ux.dev/invite) and request access.
2. Redeem the invite → copy bearer token `uxmcp_…`.
3. Paste into plugin config (not mcp.json first):
   - **Claude Code:** when the plugin asks (`api_key`).
   - **Claude Desktop Chat:** Connect header **Name** `Authorization`, **Value** `Bearer uxmcp_…` (include Bearer).
   - **Cursor:** **Plugins → Configure** → `OPEN_UX_API_KEY` = `uxmcp_…`.

## Claude Code

```bash
claude plugin marketplace add 3dyonic/open-ux
claude plugin install open-ux@open-ux
```

Enable the plugin; paste `uxmcp_` into plugin `api_key` when prompted.

Desktop **Code** panel: local plugins only (no remote marketplace add). Use CLI Code, or enable a local plugin from a checkout and paste `api_key`, or use Cowork / Desktop Chat for marketplace-style install.

## Claude Desktop Chat

After Install → Connect `open-ux` → **No sign-in**. Request header **Name** `Authorization`, **Value** `Bearer uxmcp_…` (include the word Bearer and a space). Server URL `https://open-ux.dev/mcp`. Desktop often skips the plugin `api_key` prompt; a header named `api-key` fails.

## Cursor

Enable the Open UX plugin in this repository. **Plugins → Configure** → `OPEN_UX_API_KEY` = `uxmcp_…` (not mcp.json first).

## Use the plugin

1. Map the job with `Open-UX:get_situation` (leaf counts).
2. Pull criteria: `Open-UX:pack` with `jobs=<card_id>` or `jobs=<leaf_id>`.
3. Read envelope reject and row fit; `get_guideline`; `get_component` when `component[]` names the control.

## Advanced / other clients

Paste MCP config only here. Other clients: `Authorization: Bearer uxmcp_…` on `https://open-ux.dev/mcp`. This plugin’s [`.mcp.json`](.mcp.json) is `Authorization: Bearer ${user_config.api_key}` for that URL.

No key? End users: `pip install open-ux`. In this repo, contributors: `make install` (uv + lockfile; `make install-pip` if you do not have uv). Point MCP at [`mcp.stdio.json`](mcp.stdio.json); local `python -m open_ux stdio` (after `make install`, `uv run --directory packages/mcp python -m open_ux stdio`), same catalog. Hosted Cursor [`mcp.json`](mcp.json) updates on deploy.

Do not invent a key. Do not send a file.
