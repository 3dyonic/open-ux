# Open UX

![Open UX](docs/readme-hero.svg)

**Cited UX rules agents can list, fetch, and audit against.**

Stop inventing UX guidance from memory. Open UX is a shared, open-source catalog of UX rules with citations, plus tools so an agent can find the right criteria and apply them to work it already has.

**Hosted:** [open-ux.dev](https://open-ux.dev) · **License:** [MIT](LICENSE)

## What it is

A curated, machine-readable store of UX guidelines and a small tool surface so an agent can:

1. **Browse situations** — pick a compose job (Situation Card) that matches the work
2. **Fetch criteria** — get cited rules for that job (`rule`, `pass_when`, `fail_when`)
3. **Apply locally** — the client judges the artifact; the host never takes the file and never returns pass/fail

There is no server-side LLM. One shared catalog for every caller — an account unlocks the hosted API; it does not give you a private rulebook.

## What it is not

* A generative design copilot or “does this look good?” scorer
* A WCAG / accessibility compliance checker (we do not claim conformance, contrast audits, or screen-reader naming)
* A closed corpus — the catalog and server are open source; you can self-host the same tools

## Features

* **Cited catalog** — one JSON file per rule, with sources you can follow
* **Public catalog site** — browse rules in the browser at [`/catalog`](https://open-ux.dev/catalog)
* **Agent tools** — list / search / get guidelines; suggest situations; audit by need (job or ids)
* **Hosted or self-host** — waitlist + API key on the hosted service, or stdio locally with no auth
* **Privacy-minded hosted mode** — we do not store UI payloads or prompts; see [Privacy](https://open-ux.dev/privacy)

## Quick start

### Hosted

1. Request access at [open-ux.dev/invite](https://open-ux.dev/invite)
2. After approval, redeem your invite for a bearer API key (`uxmcp_…`)
3. Point your MCP client at the hosted `/mcp` endpoint with that key
4. Call `list_guidelines` or `audit` with a job (no file upload)

Tools return **401** without a key.

### Self-host

```bash
pip install open-ux
python -m open_ux validate-catalog
python -m open_ux stdio
OPEN_UX_MODE=hosted python -m open_ux http
```

Browse the local site at `http://127.0.0.1:8080/catalog`. Point MCP clients at local stdio, or at hosted `/mcp` with a `uxmcp_` key.

### Contribute from this repo

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e "packages/mcp[dev]"
python -m open_ux validate-catalog
python -m open_ux stdio
```

### Tests

```bash
cd packages/mcp && python -m pytest
```

### Claude plugin

Pack in [`clients/claude`](clients/claude). It connects to the catalog; it does not ship a second copy of the rules. `.cursor` and `.claude` in this repo are mounts (symlinks) into that pack.

```bash
claude plugin marketplace add 3dyonic/open-ux
claude plugin install open-ux@open-ux
```

Enable, then paste a key from [open-ux.dev/invite](https://open-ux.dev/invite).

Cursor uses the same pack (`.cursor-plugin/` + `mcp.json`). Set `OPEN_UX_API_KEY` under Plugins → Configure. Submit: [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish).

## Agent tools

| Tool | Purpose |
| -- | -- |
| `list_situations` | Page Situation Cards (optional container filter) |
| `get_situation` | One Card plus facets / rule pointers |
| `suggest_situations` | Rank Cards from task text (allowlisted) |
| `list_guidelines` | Paged catalog index |
| `search_guidelines` | Filter index by query / jobs / lane |
| `get_guideline` | Full rule body by id |
| `audit` | Say the need (`jobs` Card/container or `guideline_ids`); get matching criteria |

`audit` accepts optional `query` and `limit` (default 10, max 50). It does **not** take a file target and does **not** return a host verdict. If nothing matches, you get an empty list and a note.

## Catalog layout

```
catalog/
  rules/{category}/{source}/   one JSON file per rule
  index.json                   generated index
  jobs.json                    Situation tree
  schema.json                  rule schema
  MANIFEST.md                  human map (no rule bodies)
```

Rules are never forked per tenant. Soft size budget ~50–100 KB; hard ceiling ~384 KB. Details: [`catalog/README.md`](catalog/README.md).

## Repository layout

```
packages/mcp      Python server (FastMCP)
catalog/          shared rules + schema
clients/claude    thin Claude plugin
docs/             privacy, assets
```

Python package: `open-ux` · npm / plugin scope: `@3dyonic/open-ux`

## Hosted vs self-host

|  | Hosted HTTP | Self-host (stdio) |
| -- | -- | -- |
| Auth | Waitlist → invite → bearer `uxmcp_` | None |
| Rate limits | Per-key and per-IP on `/mcp` | None |
| Telemetry | Aggregated usage (key hash, tools, rule ids) | Off |

Privacy on the hosted product: [open-ux.dev/privacy](https://open-ux.dev/privacy) (Eng constraints also in [`docs/PRIVACY.md`](docs/PRIVACY.md)).

## Contributing

Issues and pull requests are welcome. Keep the catalog cited — every rule should point at a real source. Prefer small, reviewable PRs: one concern per change (catalog rows, server behavior, or docs).

Before opening a PR:

```bash
python -m open_ux validate-catalog
cd packages/mcp && python -m pytest
```

## License

[MIT](LICENSE)
