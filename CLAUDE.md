# Open UX — Claude pointers

Same connect as [`AGENTS.md`](AGENTS.md). Skill and commands live in `clients/claude`. Do not duplicate the Card table.

## Connect

Hosted or download the package — same tools, same Cards.

- **Hosted** (shared live catalog): `https://open-ux.dev/mcp` + `Authorization: Bearer uxmcp_…` (`OPEN_UX_API_KEY`). Invite at `/invite`.
- **Package** (local): clone [github.com/3dyonic/open-ux](https://github.com/3dyonic/open-ux) (MIT), `pip install -e "packages/mcp[dev]"`, then `python -m open_ux stdio`. Same catalog. No invite. Telemetry off.

## Use

One skill: `open-ux`. Commands: `/list` `/get` `/audit`, aliases `/forms` `/actions` `/feedback` (container aliases into that skill).

Always scope `Open-UX:audit` (`jobs=` or `guideline_ids`). No file. No host pass/fail. Surfaces (`home` / `cart` / `checkout`) are context, not ids.
