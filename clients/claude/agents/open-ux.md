---
name: open-ux
description: Pointers for the Open UX skill and hosted tools. Use when composing or reviewing UI against cited UX rules.
---

# Open UX agent

Pointers only. One skill: `open-ux` (`clients/claude/skills/open-ux/SKILL.md`). No `/critique`. No catalog bodies.

## Connect

`pip install` the package, or hosted — same tools, same Cards. Package name: `open-ux`. Console script: `open-ux`.

```bash
pip install open-ux
python -m open_ux validate-catalog
python -m open_ux stdio
OPEN_UX_MODE=hosted python -m open_ux http
```

Same catalog. No invite. Telemetry off. Point MCP clients at local stdio.

- **Hosted** (shared live catalog): `https://open-ux.dev/mcp` with bearer `uxmcp_` (`OPEN_UX_API_KEY`). Invite at [open-ux.dev/invite](https://open-ux.dev/invite).

## Path

| Job | Tools |
| --- | --- |
| compose / review | Pick a Card → `Open-UX:get_situation` → `Open-UX:audit` `jobs=<card_id>` |
| map | `Open-UX:suggest_situations` when the ask is a surface. Fallback inside the skill. |
| cite | `Open-UX:search_guidelines` / `Open-UX:get_guideline` |

## Tools

`Open-UX:list_situations`, `Open-UX:get_situation`, `Open-UX:suggest_situations`, `Open-UX:list_guidelines`, `Open-UX:search_guidelines`, `Open-UX:get_guideline`, `Open-UX:audit`.

Scope `audit` (`jobs=` or `guideline_ids`). Surfaces are context, not ids. Leaf ids are not needs.

Slash commands `/list` `/get` `/audit` plus aliases `/forms` `/actions` `/feedback` route into this same skill.
