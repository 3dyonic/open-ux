# Claude plugin (thin)

Display name: **Open UX**  
Subtitle: cited UX rules agents audit against / shared cited guidelines

Do not put “MCP” in the marketplace / plugin title or landing H1.

Connect: `pip install open-ux` then `python -m open_ux stdio` (no key; same catalog), or hosted `https://open-ux.dev/mcp` + `uxmcp_` bearer (`OPEN_UX_API_KEY`) for the shared live catalog. Contributors: clone the repo and `pip install -e "packages/mcp[dev]"`. Registry listing is after proof.

One skill package: `skills/open-ux`. Compose and review share the pull trigger. Map and cite are sections in that skill — not extra packages.

Commands: `/list` `/get` are `Open-UX:*` tools. `/audit` plus aliases `/forms` `/actions` `/feedback` pick a Card, then **must** run `skills/open-ux/scripts/audit.py`. Agent pointers: `agents/open-ux.md`.

Optional without a Claude session: repo-root `scripts/mcp_call.py` (`tools/list` / `tools/call`). Not a substitute for the required audit script.
