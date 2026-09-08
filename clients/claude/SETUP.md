# Open UX — enable

1. Request a key at [open-ux.dev/invite](https://open-ux.dev/invite).
2. Redeem the invite. You get a bearer token that starts with `uxmcp_`.
3. Enable this plugin. Claude: paste that key (`api_key`). Cursor: **Plugins → Configure**, set `OPEN_UX_API_KEY`.
4. Call `Open-UX:audit` with `jobs=<card_id>`. That pack is a stratified sample of the Card; `query` is optional. The host returns criteria, not pass or fail.

No key? `pip install open-ux` and point an MCP client at local `python -m open_ux stdio` — same catalog, no invite.

Do not invent a key. Do not send a file.
