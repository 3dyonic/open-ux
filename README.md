# Open UX

![Open UX](docs/readme-hero.svg)

**Cited UX rules agents can compose with, review, and audit against.**

Open UX is a shared catalog of UX guidelines — every rule cites a real source — plus MCP tools so an agent can find criteria for the task at hand and check work it already has. You keep the UI; we return cited claims with links.

**Site:** [open-ux.dev](https://open-ux.dev) · **License:** [MIT](LICENSE)

## The big picture

Agents compose and review UI all the time. Without a catalog, they guess from memory — mixed advice, no URL, no way to show where a rule came from.

Open UX is the opposite: **cited rules you can pull into the thread**, grouped by the kind of work (forms, actions, errors, nav, …), with tools to fetch the right slice and open the full source when you need it.

**Ask** — what the user or agent is trying to do in this conversation: “build a signup form,” “review this delete dialog,” “fix the loading state.” The ask tells you which rules to pull and how narrow to pull.

**Claim** — one cited sentence a source actually says, stored as a single rule in the catalog (the `rule` field). Example: *“Hide passwords by default until the user chooses to show them.”* Each claim has a URL, when-it-fits text, and pass/fail criteria — not a whole design-system essay, not advice invented by the model.

```
  Your UI (already in the chat or repo)
           │
           ▼
  What part of the work is this?  ──►  routing table / tools
           │
           ▼
  Pull matching rules (pack)  ──►  rows: when it fits + the claim (one cited sentence)
           │
           ▼
  Open the cite (get_guideline)  ──►  full rule + URL
           │
           ▼
  Compose, review, or audit against the claim  ──►  does our UI match what GOV.UK / Polaris / … said?
```

**Pieces that fit together:**

| Piece | Role |
| --- | --- |
| **Catalog** | 204 rules from GOV.UK, Polaris, Ant, Fluent, and others — one claim per file, sources included. Browse at [open-ux.dev/catalog](https://open-ux.dev/catalog). |
| **Routing** | Rules are grouped by compose job (signup form, delete confirm, loading state, …) so a pull returns what fits the task, not the whole library. |
| **MCP server** | Hosted or local stdio — tools fetch catalog data into your agent session. |
| **Plugins** | Claude Code and Cursor skill + slash commands that teach the loop. |
| **Helpers** | Optional local CLI (`open-ux rank-pack`, …) after a pull — same pip install, runs on your machine. |

Compose and review use **the same path**: name the task, pull criteria, open cites, decide what applies. The host does not grade your UI — it hands you evidence.

## What you can do

**Compose** — start from what you're building, narrow to the task, pull cited rules.

| If you're working on… | Start here |
| --- | --- |
| Form fields, labels, grouping | Fields and labels (not validation yet) |
| Validation, inline errors | Errors on a form |
| Login, password | Sign-in |
| Buttons, primary action, toolbar | Actions and CTAs |
| Delete, discard, unsaved changes | Destructive confirm |
| Toast, loading, 404 | Feedback and status |
| Nav, breadcrumbs, search placement | Wayfinding |
| Tables, dashboards, charts | Data display |
| Modals, tooltips, progressive disclosure | Overlays |
| Checkout steps, wizard | Multi-step flow |

Not sure? `suggest_situations` returns the full map. Know the area but not the exact task? `list_situations` lists the jobs in that area. Know the task? `get_situation` then `pack`.

**How wide to pull:**

- **Whole task** — signup form, checkout CTA row, delete dialog → `pack` scoped to that job
- **One slice** — only primary vs secondary, only control choice, only password toggle → narrower `pack`
- **Known rule** — skip browse; `get_guideline` by id

The plugin skill has the routing table (when to use which job, what to open instead). Agents: [`clients/claude/skills/open-ux/cards.md`](clients/claude/skills/open-ux/cards.md).

**Review** — same flow: name the task on the screen, pull rules, read whether each cite fits (`apply_when`), open sources, audit against the claim.

**Browse** — all 204 rules at [open-ux.dev/catalog](https://open-ux.dev/catalog).

**Cite** — every pulled row links to a source you can paste in the thread.

## The loop

1. **Name the task** — what part of the UI is this? Use the table above or the skill routing table. Related tasks stay open — pick more than one pull if the ask spans them.
2. **Pull** — `Open-UX:pack` for that job (whole task or one slice). Ten rows per page; follow `next_offset`. Each row says when it fits and what the cited claim is.
3. **Open** — `get_guideline` for the full rule and URL. `get_component` when you need control-level detail (variants, keyboard, a11y).
4. **Apply** — use the claim on the work in hand. Optional: `open-ux rank-pack` to reorder one page locally.

Same catalog on hosted MCP or local stdio. Plugins add the skill and slash commands (`/pack`, `/get`, …).

## Catalog

204 cited rules, grouped into compose jobs and finer slices. One JSON file per rule in `catalog/rules/`. Tree in `catalog/jobs.json`. Authoring: [`catalog/README.md`](catalog/README.md).

## Get started

### Get a key (hosted catalog)

Hosted MCP uses a bearer token that starts with `uxmcp_`.

1. Go to [open-ux.dev/invite](https://open-ux.dev/invite) and request access (email).
2. When you receive an invite, open the link and **redeem** it — you get one API key.
3. Copy the key. **Claude Code:** paste when the plugin asks for `api_key`. **Cursor:** **Plugins → Configure** → `OPEN_UX_API_KEY`. **Other MCP clients:** `Authorization: Bearer uxmcp_…` on `https://open-ux.dev/mcp`.

No key? Skip hosted — use [self-host](#self-host) with local stdio (same tools, no auth).

### Hosted

1. Complete [Get a key](#get-a-key-hosted-catalog) above
2. Point your MCP client at `https://open-ux.dev/mcp` with that bearer token
3. Name the task (e.g. a signup form), `get_situation`, then `Open-UX:pack` — see the skill table for `jobs=` ids

### Self-host

```bash
pip install open-ux
python -m open_ux validate-catalog
python -m open_ux stdio
```

Local site + MCP:

```bash
OPEN_UX_MODE=hosted python -m open_ux http
# http://127.0.0.1:8080/catalog
```

Helpers on the same install: `open-ux helpers list` · [`helpers/README.md`](helpers/README.md)

### Claude Code and Cursor

The **plugin** is not the rule catalog. It adds three things to your editor agent:

1. **Skill** — when to pull UX rules and how to route (forms vs delete vs loading, …)
2. **Slash commands** — `/pack`, `/get`, … as shortcuts to the tools
3. **MCP connection** — how the agent reaches Open UX to fetch rules

Rules still come from the **server** — either hosted (`open-ux.dev`) or a local Python process you run yourself. For hosted, [get a key](#get-a-key-hosted-catalog) first.

**Claude Code** (terminal, from any folder):

```bash
claude plugin marketplace add 3dyonic/open-ux   # register this GitHub repo as a plugin source
claude plugin install open-ux@open-ux           # install the Open UX plugin from that source
```

Then enable the plugin in Claude Code and paste your `uxmcp_` key when it asks.

**Cursor** (this repository open as the workspace):

1. Enable the Open UX plugin (Cursor reads it from [`clients/claude`](clients/claude)).
2. **Plugins → Configure** → set **`OPEN_UX_API_KEY`** to your `uxmcp_…` token.

That key is sent as `Authorization: Bearer …` to `https://open-ux.dev/mcp` (see [`mcp.json`](clients/claude/mcp.json)).

**No key — local catalog instead:** `pip install open-ux`, run `python -m open_ux stdio`, and point MCP at [`mcp.stdio.json`](clients/claude/mcp.stdio.json). Same tools; catalog loads from this repo’s `catalog/` folder. Step-by-step: [`clients/claude/SETUP.md`](clients/claude/SETUP.md).

Plugins are not in the public marketplaces yet — install from this repo until listing ships.

### Contribute

```bash
pip install -e "packages/mcp[dev]"
python -m open_ux validate-catalog --strict-fit
python -m open_ux stdio
cd packages/mcp && python -m pytest
```

## Tools

`Open-UX:*` on the wire. Details: [`docs/TOOLS.md`](docs/TOOLS.md).

| Tool | Role |
| --- | --- |
| `suggest_situations` | Full map when the ask is vague |
| `list_situations` | List compose jobs; optional filter by area (forms, actions, feedback, …) |
| `get_situation` | One job — when to use it, what to open instead, how many rules per slice |
| **`pack`** | Cited criteria for a job, slice, or rule ids; page with `next_offset` |
| `get_guideline` | Full rule body and sources |
| `list_guidelines` / `search_guidelines` | Paged index |
| `list_components` / `get_component` | Control detail when a row points at a component |

## Repository

```
catalog/           rules, jobs tree, schema
packages/mcp/      MCP server — PyPI: open-ux
packages/web/      public site
helpers/           local CLI (rank-pack, wire debug)
clients/claude/    Claude Code + Cursor plugin
docs/              doc map, tools, contributing, privacy
```

## Hosted vs self-host

| | Hosted | Self-host |
| --- | --- | --- |
| Catalog | Shared live | Same wheel |
| Auth | `uxmcp_` key | None |
| Privacy | [open-ux.dev/privacy](https://open-ux.dev/privacy) | Telemetry off |

Sources: [open-ux.dev/sources](https://open-ux.dev/sources)

## Contributing

PRs welcome — cited catalog rules, server changes, docs, plugin pack. **Docs map:** [`docs/README.md`](docs/README.md). **Before a PR:** [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) (checklist + cite shape).

## License

[MIT](LICENSE)
