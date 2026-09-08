# Open UX

![Open UX](assets/hero.svg)

Cited UX rules agents audit against. Pick a Situation Card, then get a criteria pack.

Homepage: [open-ux.dev](https://open-ux.dev)

Do not put “MCP” in the marketplace / plugin title or landing H1.

## Install

```bash
claude plugin marketplace add 3dyonic/open-ux
claude plugin install open-ux@open-ux
```

Then enable and paste your key. Invite: [open-ux.dev/invite](https://open-ux.dev/invite) → `uxmcp_`. See [SETUP.md](SETUP.md).

Cursor uses the same pack (`.cursor-plugin/` + `mcp.json`). Set `OPEN_UX_API_KEY` under **Plugins → Configure**. Submit: [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish).

Claude submit: [platform.claude.com/plugins/submit](https://platform.claude.com/plugins/submit). Validate: `claude plugin validate . --strict` (repo marketplace) or `claude plugin validate ./clients/claude --strict`.

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

- **Compose / review** — pick a Card, `Open-UX:get_situation`, then `Open-UX:audit` with `jobs=`
- **Map** — `Open-UX:suggest_situations` when the ask is a vague surface
- **Cite** — `Open-UX:search_guidelines` / `Open-UX:get_guideline`

Commands: `/list` `/get` `/audit`, plus aliases `/forms` `/actions` `/feedback`. Agent pointers: `agents/open-ux.md`.

Same wire without a session: `open-ux audit --jobs …`. Repo helper `scripts/mcp_call.py` (`tools/list` / `tools/call`) is available, not required. Not the skill path.
