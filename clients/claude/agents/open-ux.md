---
name: open-ux
description: Pointers for the Open UX skill and hosted tools. Use when composing or reviewing UI against cited UX rules.
---

# Open UX agent

Pointers only. One skill: `open-ux` (`clients/claude/skills/open-ux/SKILL.md`). No `/critique`. No catalog bodies.

## Connect

- Hosted: `https://open-ux.dev/mcp` + bearer `uxmcp_` (`OPEN_UX_API_KEY`). Invite: hosted `/invite`.
- Self-host: `python -m open_ux stdio` (no key).

## Four offerings

| Job | Tools |
| --- | --- |
| compose (default) | Pick a Card → `Open-UX:get_situation` → `Open-UX:audit` `jobs=<card_id>` |
| review | Same Cards and `audit`. Host (you) judges. No file to the server. |
| map | `Open-UX:suggest_situations` when the ask is a surface. Fallback inside the skill. |
| cite | `Open-UX:search_guidelines` / `Open-UX:get_guideline` |

## Tools

`Open-UX:list_situations`, `Open-UX:get_situation`, `Open-UX:suggest_situations`, `Open-UX:list_guidelines`, `Open-UX:search_guidelines`, `Open-UX:get_guideline`, `Open-UX:audit`.

Scope `audit` (`jobs=` or `guideline_ids`). No file. No pass or fail from the host. Surfaces are context, not ids. Leaf ids are not needs.

Slash commands `/list` `/get` `/audit` plus aliases `/forms` `/actions` `/feedback` route into this same skill.
