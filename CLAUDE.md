# Open UX: Claude pointers

Same connect as [`AGENTS.md`](AGENTS.md). Skill and commands live in `clients/plugin`. Do not duplicate the Card table.

## Connect

`pip install` the package, or hosted; same tools, same Cards. Package name: `open-ux`. Console script: `open-ux`.

```bash
pip install open-ux
python -m open_ux validate-catalog
python -m open_ux validate-catalog --strict-fit
python -m open_ux stdio
OPEN_UX_MODE=hosted python -m open_ux http
```

Same catalog. No invite. Telemetry off. Point MCP clients at local stdio.

- **Hosted** (shared live catalog): `https://open-ux.dev/mcp` + `Authorization: Bearer uxmcp_…` (`OPEN_UX_API_KEY`). Invite at `/invite`.

Contributors: clone the repo and `pip install -e "packages/mcp[dev]"`. Before PR: [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md).

Plugins are not in the public marketplaces yet. Install from this repo: `claude plugin marketplace add 3dyonic/open-ux` then `claude plugin install open-ux@open-ux`. Validate: `claude plugin validate . --strict`. Cursor: `node scripts/validate-cursor-plugin.mjs --strict`.

## Use

One skill: `open-ux`, invoked automatically when the ask matches its description, or directly via `/open-ux:open-ux`. No separate commands: the skill routes straight to `Open-UX:*` tools.

Tool reference: [`docs/TOOLS.md`](docs/TOOLS.md). Criteria pull: **`Open-UX:pack`**.

Scope `Open-UX:pack` (`jobs=<card_id>`, `jobs=<leaf_id>`, container alias, or `guideline_ids`). Surfaces (`home` / `cart` / `checkout`) are context, not ids. Prefer a Card; use a Leaf when the ask is one bay. Component records: `Open-UX:list_components`, `Open-UX:get_component`. MCP tools fetch catalog data; optional LLM local `open-ux rank-pack` after pack (`pip install open-ux`); see [`helpers/README.md`](helpers/README.md). Maintainer scripts: [`scripts/`](scripts/) only.
