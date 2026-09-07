# Open UX — agent pointers

Connect and tools only. The routing table lives in [`clients/claude/skills/open-ux/SKILL.md`](clients/claude/skills/open-ux/SKILL.md). Do not copy it here.

## Connect

- **Hosted:** `https://open-ux.dev/mcp` with bearer `uxmcp_` (`OPEN_UX_API_KEY`). Request a key at [open-ux.dev/invite](https://open-ux.dev/invite). Do not invent a key.
- **Self-host:** `python -m open_ux stdio` from this repo (no key).

Plugin metadata: [`clients/claude/.claude-plugin/plugin.json`](clients/claude/.claude-plugin/plugin.json) + [`clients/claude/.mcp.json`](clients/claude/.mcp.json). One skill package: `open-ux`.

## Tools

Fully qualified: `Open-UX:list_situations`, `Open-UX:get_situation`, `Open-UX:suggest_situations`, `Open-UX:list_guidelines`, `Open-UX:search_guidelines`, `Open-UX:get_guideline`, `Open-UX:audit`.

Always scope `audit` with `jobs=<card_id>` (or `forms` / `actions` / `feedback`) or `guideline_ids`. Never a file. The host returns cited criteria, not pass or fail.

## One skill, four offerings

`open-ux` is the only always-on skill. Compose (default), review, map, and cite are jobs inside it — not extra packages. Claude agent file: [`clients/claude/agents/open-ux.md`](clients/claude/agents/open-ux.md).
