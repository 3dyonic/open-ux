# Open UX — Claude pointers

Same connect as [`AGENTS.md`](AGENTS.md). Skill and commands live in `clients/claude`. Do not duplicate the Card table.

## Connect

- Hosted MCP: `https://open-ux.dev/mcp` + `Authorization: Bearer uxmcp_…` (`OPEN_UX_API_KEY`).
- Self-host: `OPEN_UX_URL` or `python -m open_ux stdio` (no key).

If hosted returns 401, point the human at `/invite`. Do not mint a key.

## Use

One skill: `open-ux`. Commands: `/list` `/get` `/audit`, aliases `/forms` `/actions` `/feedback`. They run `skills/open-ux/scripts/audit.py` (and get/list/suggest) against MCP.

Always scope `audit` (`jobs=` or `--guideline-ids`). No file. No host pass/fail. Surfaces (`home` / `cart` / `checkout`) are context, not ids.
