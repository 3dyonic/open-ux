# Open UX — agent pointers

Connect and tools only. The routing table lives in [`clients/claude/skills/open-ux/SKILL.md`](clients/claude/skills/open-ux/SKILL.md). Do not copy it here.

## Connect

`pip install` the package, or hosted — same tools, same Cards.

- **Package** (local): `pip install open-ux`, then `python -m open_ux stdio` (console script: `open-ux`). Same catalog. No invite. Telemetry off.
- **Hosted** (shared live catalog): `https://open-ux.dev/mcp` with bearer `uxmcp_` (`OPEN_UX_API_KEY`). Invite at [open-ux.dev/invite](https://open-ux.dev/invite).

Contributors: clone the repo and `pip install -e "packages/mcp[dev]"`.

Plugin metadata: [`clients/claude/.claude-plugin/plugin.json`](clients/claude/.claude-plugin/plugin.json) + [`clients/claude/.mcp.json`](clients/claude/.mcp.json). One skill package: `open-ux`.

## Path

Compose/review **must** run `clients/claude/skills/open-ux/scripts/audit.py` (`jobs=` / `guideline_ids` only). list/get/map/cite are MCP tools, not scripts. The host returns cited criteria, not pass or fail.

Fully qualified tools: `Open-UX:list_situations`, `Open-UX:get_situation`, `Open-UX:suggest_situations`, `Open-UX:list_guidelines`, `Open-UX:search_guidelines`, `Open-UX:get_guideline`, `Open-UX:audit`.

A local helper `scripts/mcp_call.py` is available for humans and CI. Optional.

## One skill

`open-ux` is the only always-on skill. Compose and review share the pull trigger; map and cite are sections inside it. Claude agent file: [`clients/claude/agents/open-ux.md`](clients/claude/agents/open-ux.md).
