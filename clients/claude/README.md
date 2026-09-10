# Open UX

![Open UX](assets/hero.svg)

Cited UX rules agents audit against. Open Cards that fit, then get a criteria pack. You decide.

Homepage: [open-ux.dev](https://open-ux.dev)

Do not put “MCP” in the marketplace / plugin title or landing H1.

Logo (Cursor `logo` field): [assets/icon.svg](assets/icon.svg). Listing art: [assets/hero.svg](assets/hero.svg), [assets/offerings.svg](assets/offerings.svg).

## Install

Invite: [open-ux.dev/invite](https://open-ux.dev/invite) → `uxmcp_`. Then enable. See [SETUP.md](SETUP.md).

### Claude

```bash
claude plugin marketplace add 3dyonic/open-ux
claude plugin install open-ux@open-ux
```

Paste the key when prompted (`api_key`). Submit: [platform.claude.com/plugins/submit](https://platform.claude.com/plugins/submit). Validate: `claude plugin validate . --strict` (repo marketplace) or `claude plugin validate ./clients/claude --strict`.

### Cursor

Same pack (`.cursor-plugin/` + `mcp.json`). Set `OPEN_UX_API_KEY` under **Plugins → Configure**. Submit: [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish).

## Connect

`pip install` the package, or hosted — same tools, same Cards. Package name: `open-ux`. Console script: `open-ux`.

```bash
pip install open-ux
python -m open_ux validate-catalog
python -m open_ux stdio
OPEN_UX_MODE=hosted python -m open_ux http
```

No key; same catalog. Point MCP clients at local stdio, or hosted `https://open-ux.dev/mcp` + `uxmcp_` bearer (`OPEN_UX_API_KEY`) for the shared live catalog. Contributors: clone the repo and `pip install -e "packages/mcp[dev]"`.

## Offerings (one skill)

Compose, review, map, and cite are jobs in `skills/open-ux` — not extra packages.

- **Compose / review** — compare Cards that fit; `Open-UX:get_situation` (leaf `{ id, count }`), then `Open-UX:pack` with `jobs=`; read envelope reject and row fit; `get_guideline` or `get_component`; loop `next_offset`. You decide. No winner Card.
- **Map** — `Open-UX:suggest_situations` when the ask is a vague surface (catalog map). The catalog stays open after a pack.
- **Cite** — `Open-UX:search_guidelines` / `Open-UX:get_guideline`

Commands: `/list` `/get` `/pack`, plus aliases `/forms` `/actions` `/feedback`. Agent pointers: `agents/open-ux.md`.

Same wire without a session: `open-ux pack --jobs …`, `open-ux component button --include-used-on`. Agent helpers: [`helpers/registry.json`](../../helpers/registry.json) — `helpers/pack.py`, `helpers/rank_pack.py`, `helpers/get_component.py`, `helpers/mcp_call.py` (available, not required). Do not invent a ranker. Contributor scripts live in `scripts/` — not the skill path.
