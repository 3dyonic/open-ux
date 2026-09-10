# Open UX: agent pointers

Connect and tools only. The routing table lives in [`clients/plugin/skills/open-ux/SKILL.md`](clients/plugin/skills/open-ux/SKILL.md). Do not copy it here.

## Connect

`pip install` the package, or hosted; same tools, same Cards. Package name: `open-ux`. Console script: `open-ux`.

```bash
pip install open-ux
python -m open_ux validate-catalog
python -m open_ux validate-catalog --strict-fit
python -m open_ux stdio
OPEN_UX_MODE=hosted python -m open_ux http
```

Same catalog. No invite. Telemetry off. Point MCP clients at local stdio ([`clients/plugin/mcp.stdio.json`](clients/plugin/mcp.stdio.json) in this repo).

- **Hosted** (shared live catalog): `https://open-ux.dev/mcp` with bearer `uxmcp_` (`OPEN_UX_API_KEY`). Invite at [open-ux.dev/invite](https://open-ux.dev/invite).

Contributors: clone the repo and `pip install -e "packages/mcp[dev]"`. Before PR: see [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md).

The authored plugin pack is [`clients/plugin/`](clients/plugin/). `.cursor` and `.claude` are mounts (symlinks), not a second copy. Claude Code and Cursor plugins are **submitted, not yet published**. Until listed: `claude plugin marketplace add 3dyonic/open-ux` then `claude plugin install open-ux@open-ux`; Cursor uses the same pack from this repo (`.cursor-plugin/` + `mcp.json`). Site: [open-ux.dev](https://open-ux.dev).

## Tools

Reference: [`docs/TOOLS.md`](docs/TOOLS.md). Vocabulary: [`docs/glossary.md`](docs/glossary.md). Criteria pull: **`Open-UX:pack`** (`jobs=` or `guideline_ids`).

Fully qualified: `Open-UX:list_situations`, `Open-UX:get_situation`, `Open-UX:suggest_situations`, `Open-UX:list_guidelines`, `Open-UX:search_guidelines`, `Open-UX:get_guideline`, `Open-UX:pack`, `Open-UX:list_components`, `Open-UX:get_component`.

Scope `pack` with `jobs=<card_id>`, `jobs=<leaf_id>`, container alias, or `guideline_ids`. The host returns cited criteria, not pass or fail. `/list` `/get` `/pack` stay on tools.

Agents use **`Open-UX:*` MCP tools**; the host fetches catalog data. **`pip install open-ux`** ships helper tools as **`open-ux`** subcommands (`open-ux helpers list`); agent helper: **`open-ux rank-pack`** after pack. See [`helpers/README.md`](helpers/README.md). Do not substitute CLI pack for MCP in agent sessions. Contributor logic stays in `scripts/`; not offered to agents.

## One skill

`open-ux` is the only always on skill: hub [`SKILL.md`](clients/plugin/skills/open-ux/SKILL.md) plus read on demand references ([`docs/glossary.md`](docs/glossary.md), ask-shapes, examples, cards, …). Compose and review share the pull trigger. Claude agent file: [`clients/plugin/agents/open-ux.md`](clients/plugin/agents/open-ux.md).
