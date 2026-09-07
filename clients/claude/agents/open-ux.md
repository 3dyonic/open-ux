---
name: open-ux
description: Pointers for the Open UX skill and hosted tools. Use when composing or reviewing UI against cited UX rules.
---

# Open UX agent

Pointers only. One skill: `open-ux` (`clients/claude/skills/open-ux/SKILL.md`). No `/critique`. No catalog bodies.

## Connect

- Hosted: `https://open-ux.dev/mcp` + bearer `uxmcp_` (`OPEN_UX_API_KEY`). Invite: hosted `/invite`.
- Self-host: `OPEN_UX_URL` or `python -m open_ux stdio` (no key).

## Scripts

| Job | Run |
| --- | --- |
| compose / review | `skills/open-ux/scripts/audit.py --jobs=<card_id>` |
| map | `skills/open-ux/scripts/suggest.py "task text"` |
| cite | `skills/open-ux/scripts/get.py <guideline_id>` |
| index | `skills/open-ux/scripts/list.py` |

Always scope `audit` (`jobs=` or `--guideline-ids`). Never a file. No pass or fail from the host. Surfaces are context, not ids. Leaf ids are not needs.

Slash commands `/list` `/get` `/audit` plus aliases `/forms` `/actions` `/feedback` run those scripts.
