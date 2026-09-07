# Claude plugin (thin)

Display name: **Open UX**  
Subtitle: cited UX rules agents audit against / shared cited guidelines

Do not put “MCP” in the marketplace / plugin title or landing H1.

Connect: hosted `https://open-ux.dev/mcp` + `uxmcp_` bearer (`OPEN_UX_API_KEY`), or stdio. Registry listing is after proof.

One skill package: `skills/open-ux`. Offerings compose / review / map / cite live in that skill — not `open-ux-forms` / `open-ux-actions` / `open-ux-feedback`.

Commands: `/list` `/get` `/audit` plus aliases `/forms` `/actions` `/feedback` (container aliases). Agent pointers: `agents/open-ux.md`.

Skill and commands tell the LLM why to call Open UX and what it gets. A local helper `scripts/audit.py` is available for humans and CI.
