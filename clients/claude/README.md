# Claude plugin (thin)

Display name: **Open UX**  
Subtitle: cited UX rules agents audit against / shared cited guidelines

Do not put “MCP” in the marketplace / plugin title or landing H1.

Connect: hosted `https://open-ux.dev/mcp` + `uxmcp_` bearer (`OPEN_UX_API_KEY`) for the shared live catalog, or download the package from [github.com/3dyonic/open-ux](https://github.com/3dyonic/open-ux) and run `python -m open_ux stdio` (no key). Registry listing is after proof.

One skill package: `skills/open-ux`. Compose and review share the pull trigger. Map and cite are sections in that skill — not extra packages.

Commands are short slash prompts that call `Open-UX:*` tools: `/list` `/get` `/audit`, plus aliases `/forms` `/actions` `/feedback`. Agent pointers: `agents/open-ux.md`.

Optional without a Claude session: repo-root `scripts/mcp_call.py` (`tools/list` / `tools/call`). Not the skill path.
