# Open UX — Claude pointers

Same connect as [`AGENTS.md`](AGENTS.md). Skill and commands live in `clients/claude`. Do not duplicate the Card table.

## Connect

- Hosted MCP: `https://open-ux.dev/mcp` + `Authorization: Bearer uxmcp_…` (`OPEN_UX_API_KEY`).
- Stdio: `python -m open_ux stdio` (no key).

If hosted returns 401, point the human at `/invite`. Do not mint a key.

## Use

One skill: `open-ux`. Commands: `/list` `/get` `/audit`, aliases `/forms` `/actions` `/feedback` (container aliases into that skill).

Always scope `Open-UX:audit` (`jobs=` or `guideline_ids`). No file. No host pass/fail. Surfaces (`home` / `cart` / `checkout`) are context, not ids.
