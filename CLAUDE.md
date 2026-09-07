# Open UX — Claude pointers

Same connect as [`AGENTS.md`](AGENTS.md). Skill and commands live in `clients/claude`. Do not duplicate the Card table.

## Connect

`pip install` the package, or hosted — same tools, same Cards.

- **Package** (local): `pip install open-ux`, then `python -m open_ux stdio` (console script: `open-ux`) or `OPEN_UX_MODE=hosted python -m open_ux http`. Same catalog. No invite. Telemetry off.
- **Hosted** (shared live catalog): `https://open-ux.dev/mcp` + `Authorization: Bearer uxmcp_…` (`OPEN_UX_API_KEY`). Invite at `/invite`.

Contributors: clone the repo and `pip install -e "packages/mcp[dev]"`.

## Use

One skill: `open-ux`. Commands: `/list` `/get` `/audit`, aliases `/forms` `/actions` `/feedback` — short prompts that call `Open-UX:*` tools.

Scope `Open-UX:audit` (`jobs=` or `guideline_ids`). Surfaces (`home` / `cart` / `checkout`) are context, not ids.
