# Open UX

![Open UX](docs/readme-hero.svg)

**Cited UX rules agents can list, fetch, and audit against.**

Stop inventing UX guidance from memory. Open UX is a shared, open-source catalog of UX rules with citations, plus tools so an agent can find the right criteria and apply them to work it already has.

**Hosted:** [open-ux.dev](https://open-ux.dev) · **License:** [MIT](LICENSE)

## What it is

A curated, machine-readable store of UX guidelines and a small tool surface so an agent can:

1. **Map a Card** — `get_situation` for when / reject, facets, and leaf `{ id, count }` bays
2. **Fetch criteria** — `pack` with `jobs=` (Card or Leaf); read envelope `situation.reject` and row fit (`overview`, `apply_when`, `not_when`)
3. **Deep read** — `get_guideline` for the cited rule; `get_component` for control context when `component[]` is stamped on the Card or row; loop `next_offset`
4. **Apply locally** — the client judges the artifact; the host never takes the file and never returns pass/fail

There is no server-side LLM. One shared catalog for every caller — an account unlocks the hosted API; it does not give you a private rulebook.

## What it is not

* A generative design copilot or “does this look good?” scorer
* A WCAG / accessibility compliance checker (we do not claim conformance, contrast audits, or screen-reader naming)
* A closed corpus — the catalog and server are open source; you can self-host the same tools

## Features

* **Cited catalog** — one JSON file per rule, with sources you can follow
* **Public catalog site** — browse rules in the browser at [`/catalog`](https://open-ux.dev/catalog)
* **Agent tools** — map Cards (`get_situation` with leaf counts); pack by need; list / search / get guidelines; component records (`get_component`)
* **Hosted or self-host** — waitlist + API key on the hosted service, or stdio locally with no auth
* **Privacy-minded hosted mode** — we do not store UI payloads or prompts; see [Privacy](https://open-ux.dev/privacy). How we cite rules: [Sources](https://open-ux.dev/sources)

## Quick start

### Hosted

1. Request access at [open-ux.dev/invite](https://open-ux.dev/invite)
2. After approval, redeem your invite for a bearer API key (`uxmcp_…`)
3. Point your MCP client at the hosted `/mcp` endpoint with that key
4. Call `list_guidelines` or `pack` with a job (no file upload)

Tools return **401** without a key.

### Self-host

```bash
pip install open-ux
python -m open_ux validate-catalog
python -m open_ux validate-catalog --strict-fit
python -m open_ux stdio
OPEN_UX_MODE=hosted python -m open_ux http
```

The wheel includes the catalog. A change to `catalog/` or the package source on `master` publishes a new PyPI patch so pip and hosted carry the same rules.

Browse the local site at `http://127.0.0.1:8080/catalog`. Point MCP clients at local stdio, or at hosted `/mcp` with a `uxmcp_` key.

### Contribute from this repo

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e "packages/mcp[dev]"
python -m open_ux validate-catalog
python -m open_ux validate-catalog --strict-fit
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

There is **no** `audit` tool — use **`pack`**. Full reference: [`docs/TOOLS.md`](docs/TOOLS.md).

- **`suggest_situations`** — `task_text` → full catalog map of all 13 Cards by container. Does not pick or rank.
- **`list_situations`** — Card index; optional `container` filter. Metadata only, no rule bodies.
- **`get_situation`** — One Card: when / reject, facets, `leaves: [{ id, count }]`. Leaf id fails. No rule text.
- **`pack`** — Cited rule criteria for `jobs` (Card, Leaf, or container) or `guideline_ids`. Page with `limit` / `offset` / `next_offset`. Host ignores `query` (use [`helpers/rank_pack.py`](helpers/registry.json) locally). No file, no pass/fail.
- **`get_guideline`** — One full rule body by id.
- **`list_guidelines`** / **`search_guidelines`** — Paged index; scope by jobs / lane. No bodies; host ignores `query` on search.
- **`list_components`** / **`get_component`** — Component index and record. `get_component`: section switches `include_vs`, `include_variants`, `include_accessibility`, `include_keyboard` (default on); opt-in `include_keywords`, `include_used_on`.

Card/Leaf **`pack`** pulls add envelope **`situation`** (`when`, `reject`; `leaf` when scoped) and **`cite_via: get_guideline`**. Rows are browse slices — open `get_guideline` or `get_component` for full records.

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
helpers/          optional agent helpers (registry.json)
scripts/          contributor catalog maintenance
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

Privacy on the hosted product: [open-ux.dev/privacy](https://open-ux.dev/privacy) (Eng constraints also in [`docs/PRIVACY.md`](docs/PRIVACY.md)). How we write and cite catalog rules, and how to ask us to change or remove one: [open-ux.dev/sources](https://open-ux.dev/sources).

## Contributing

Issues and pull requests are welcome. Keep the catalog cited — every rule should point at a real source. Prefer small, reviewable PRs: one concern per change (catalog rows, server behavior, or docs).

Before opening a PR:

```bash
python -m open_ux validate-catalog --strict-fit
claude plugin validate . --strict
node scripts/validate-cursor-plugin.mjs --strict
cd packages/mcp && python -m pytest
```

## License

[MIT](LICENSE)
