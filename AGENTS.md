# Open UX — agent pointers

Connect and tools only. The routing table lives in [`clients/claude/skills/open-ux/SKILL.md`](clients/claude/skills/open-ux/SKILL.md). Do not copy it here.

## Connect

Hosted or download the package — same tools, same Cards.

- **Hosted** (shared live catalog): `https://open-ux.dev/mcp` with bearer `uxmcp_` (`OPEN_UX_API_KEY`). Invite at [open-ux.dev/invite](https://open-ux.dev/invite).
- **Package** (local): clone [github.com/3dyonic/open-ux](https://github.com/3dyonic/open-ux) (MIT), `pip install -e "packages/mcp[dev]"`, then `python -m open_ux stdio`. Same catalog. No invite. Telemetry off.

Plugin metadata: [`clients/claude/.claude-plugin/plugin.json`](clients/claude/.claude-plugin/plugin.json) + [`clients/claude/.mcp.json`](clients/claude/.mcp.json). One skill package: `open-ux`.

## Tools

Fully qualified: `Open-UX:list_situations`, `Open-UX:get_situation`, `Open-UX:suggest_situations`, `Open-UX:list_guidelines`, `Open-UX:search_guidelines`, `Open-UX:get_guideline`, `Open-UX:audit`.

Scope `audit` with `jobs=` (or `forms` / `actions` / `feedback`) or `guideline_ids`. The host returns cited criteria, not pass or fail.

A local helper `scripts/mcp_call.py` is available for humans and CI. The product is the hosted tools.

## One skill

`open-ux` is the only always-on skill. Compose and review share the pull trigger; map and cite are sections inside it. Claude agent file: [`clients/claude/agents/open-ux.md`](clients/claude/agents/open-ux.md).
