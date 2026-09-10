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

Paste the key when prompted (`api_key`). Submit: [platform.claude.com/plugins/submit](https://platform.claude.com/plugins/submit). Validate: `claude plugin validate . --strict` (repo marketplace) or `claude plugin validate ./clients/claude --strict`. Cursor: `node scripts/validate-cursor-plugin.mjs --strict` from repo root. CI runs both.

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

## Tools

No **`Open-UX:audit`** — use **`Open-UX:pack`**. See [`docs/TOOLS.md`](../../docs/TOOLS.md).

- **`suggest_situations`** — `task_text` → full 13-Card map by container. Does not pick or rank.
- **`list_situations`** — Card index; optional `container`. Metadata only.
- **`get_situation`** — One Card (when / reject / leaf counts). Leaf id fails.
- **`pack`** — Cited criteria for `jobs` or `guideline_ids`; page with `next_offset`. No file, no pass/fail.
- **`get_guideline`** — One full rule body by id.
- **`list_components`** / **`get_component`** — Component index and record. Context helper when `component[]` is on the Card or pack row.

## Offerings (one skill)

Compose, review, map, and cite are jobs in `skills/open-ux` — not extra packages.

- **Compose / review** — compare Cards that fit; `Open-UX:get_situation` (leaf `{ id, count }`), then `Open-UX:pack` with `jobs=`; read envelope reject and row fit; `get_guideline`; `get_component` for control context when `component[]` fits; loop `next_offset`. You decide. No winner Card.
- **Map** — `Open-UX:suggest_situations` when the ask is a vague surface (catalog map). The catalog stays open after a pack.
- **Cite** — `Open-UX:search_guidelines` / `Open-UX:get_guideline`

Commands: `/list` `/get` `/pack`, plus aliases `/forms` `/actions` `/feedback`. Agent pointers: `agents/open-ux.md`.

Agents use **`Open-UX:*` MCP tools** — host fetches catalog data. Optional LLM-local: **`open-ux rank-pack`** after pack (`pip install open-ux`) ([`helpers/registry.json`](../../helpers/registry.json)). Contributor CLI/wire: `contributor_wire` in registry. Contributor scripts live in `scripts/` — not the skill path.
