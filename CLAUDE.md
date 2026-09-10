# Open UX — Claude pointers

Same connect as [`AGENTS.md`](AGENTS.md). Skill and commands live in `clients/claude`. Do not duplicate the Card table.

## Connect

`pip install` the package, or hosted — same tools, same Cards. Package name: `open-ux`. Console script: `open-ux`.

```bash
pip install open-ux
python -m open_ux validate-catalog
python -m open_ux validate-catalog --strict-fit
python -m open_ux stdio
OPEN_UX_MODE=hosted python -m open_ux http
```

Same catalog. No invite. Telemetry off. Point MCP clients at local stdio.

- **Hosted** (shared live catalog): `https://open-ux.dev/mcp` + `Authorization: Bearer uxmcp_…` (`OPEN_UX_API_KEY`). Invite at `/invite`.

Contributors: clone the repo and `pip install -e "packages/mcp[dev]"`.

Install from this repo: `claude plugin marketplace add 3dyonic/open-ux` then `claude plugin install open-ux@open-ux`. Validate: `claude plugin validate . --strict` and `claude plugin validate ./clients/claude --strict`. Cursor: `node scripts/validate-cursor-plugin.mjs --strict`. CI runs both.

## Use

One skill: `open-ux`. Commands: `/list` `/get` `/pack`, aliases `/forms` `/actions` `/feedback` — short prompts that call `Open-UX:*` tools.

No `Open-UX:audit` — use **`Open-UX:pack`**. Tool reference: [`docs/TOOLS.md`](docs/TOOLS.md).

Scope `Open-UX:pack` (`jobs=` or `guideline_ids`). Surfaces (`home` / `cart` / `checkout`) are context, not ids. You decide which Cards to open. Component records: `Open-UX:list_components`, `Open-UX:get_component`. MCP tools fetch catalog data; optional LLM-local `open-ux rank-pack` after pack (`pip install open-ux`) ([`helpers/registry.json`](helpers/registry.json)). Contributor scripts: `scripts/` only.
