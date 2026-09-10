# Open UX

![Open UX](docs/readme-hero.svg)

**Cited UX rules for the UI work you already have.**

You're building a form, reviewing a delete dialog, or fixing a loading state. Open UX gives you cited criteria from real design systems, with links you can share, so you and your agent can compose and review from evidence instead of guesswork.

> **Vision:** A community maintained catalog of UX criteria, every rule cited to a published source, validated for fit, and open to contribution, so teams work from evidence, not guesswork.

Open UX is a shared catalog plus tools that fetch the right slice for your task. You keep the UI; we return cited claims with links. You decide what applies.

**Site:** [open-ux.dev](https://open-ux.dev) · **License:** [MIT](LICENSE)

## Overview

You compose and review UI constantly. When advice has no source, it is hard to trust and hard to explain to teammates or stakeholders.

Open UX gives you two things: a **catalog of cited UX criteria** (one claim per rule, every entry links to a published source) and **tools** that fetch what fits the task at hand. You pull criteria into the thread, open the source when you need depth, and apply what makes sense for the people using the product.

**Task:** The work in scope for this session: build a signup form, review a delete dialog, fix a loading state. The task determines which catalog job to pull and how narrow the pull should be.

**Cited rule:** One sentence a source actually states, stored as a single catalog entry (`rule` field). Example: *“Hide passwords by default until the user chooses to show them.”* Each entry includes a source URL, text for when it applies, and fit criteria; not a full design system dump; not model generated advice.

```
 UI under review (in chat or repo)
 │
 ▼
 Identify the task ──► routing table / MCP tools
 │
 ▼
 Pull matching criteria (pack) ──► rows: fit + cited claim
 │
 ▼
 Open the source (get_guideline) ──► full rule + URL
 │
 ▼
 Compose, review, or audit ──► does the UI serve the people using it, and match what the source says?
```

| Component | Purpose |
| --- | --- |
| **Catalog** | 204 rules from GOV.UK, Polaris, Ant Design, Fluent, and others, one claim per file, sources included. Browse at [open-ux.dev/catalog](https://open-ux.dev/catalog). |
| **Routing** | Rules grouped by compose job (forms, actions, errors, navigation, …) so a pull returns task relevant criteria, not the whole library. |
| **MCP server** | Hosted or local stdio; loads catalog data into your editor session. |
| **Plugins** | Claude Code and Cursor skill plus slash commands that walk you through the loop. |
| **Helpers** | Optional local CLI (`open-ux rank-pack`, …) after a pull; same pip install, runs on your machine. |

Compose and review use the same loop: name the task, pull criteria, open cites, decide what applies. Nothing here grades your UI or returns pass or fail; you stay in charge of the decision.

## Who this is for

| You are… | Start here |
| --- | --- |
| Building or fixing UI in an agent session | [The loop](#the-loop) and the task table below |
| Reviewing a screen, flow, or PR | Same loop; read `apply_when` on each row before opening the source |
| Adding or correcting a rule | [`catalog/README.md`](catalog/README.md) and [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) |
| Wiring MCP or the plugin | [Get started](#get-started) |

## What you can do

**Compose:** start from what you're building, narrow to the task, pull cited rules.

| If you're working on… | Start here |
| --- | --- |
| Form fields, labels, grouping | Fields and labels (not validation yet) |
| Validation, inline errors | Errors on a form |
| Login, password | Sign in |
| Buttons, primary action, toolbar | Actions and CTAs |
| Delete, discard, unsaved changes | Destructive confirm |
| Toast, loading, 404 | Feedback and status |
| Nav, breadcrumbs, search placement | Wayfinding |
| Tables, dashboards, charts | Data display |
| Modals, tooltips, progressive disclosure | Overlays |
| Checkout steps, wizard | Multi step flow |

Not sure? `suggest_situations` returns the full map. Know the area but not the exact task? `list_situations` lists the jobs in that area. Know the task? `get_situation` then `pack`.

**How wide to pull:**

- **Whole task:** signup form, checkout CTA row, delete dialog → `pack` scoped to that job
- **One slice:** only primary vs secondary, only control choice, only password toggle → narrower `pack`
- **Known rule:** skip browse; `get_guideline` by id

The plugin skill has the routing table (when to use which job, what to open instead). Agents: [`clients/plugin/skills/open-ux/cards.md`](clients/plugin/skills/open-ux/cards.md).

**Review:** same flow: name the task on the screen, pull rules, read whether each cite fits (`apply_when`), open sources, audit against the claim.

**Browse:** all 204 rules at [open-ux.dev/catalog](https://open-ux.dev/catalog).

**Cite:** every pulled row links to a source you can paste in the thread.

## The loop

1. **Name the task:** what part of the UI is this? Use the table above or the skill routing table. Related tasks stay open; pick more than one pull if the ask spans them.
2. **Pull:** `Open-UX:pack` for that job (whole task or one slice). Ten rows per page; follow `next_offset`. Each row says when it fits and what the cited claim is.
3. **Open:** `get_guideline` for the full rule and URL. `get_component` when you need control level detail (variants, keyboard, a11y).
4. **Apply:** use the claim on the work in hand. Optional: `open-ux rank-pack` to reorder one page locally.

Same catalog on hosted MCP or local stdio. Plugins add the skill and slash commands (`/pack`, `/get`, …).

## Catalog

204 cited rules, grouped into compose jobs and finer slices. One JSON file per rule in `catalog/rules/`. Tree in `catalog/jobs.json`. Authoring: [`catalog/README.md`](catalog/README.md).

## Get started

### Get a key (hosted catalog)

Hosted MCP uses a bearer token that starts with `uxmcp_`.

1. Go to [open-ux.dev/invite](https://open-ux.dev/invite) and request access (email).
2. When you receive an invite, open the link and **redeem** it and you get one API key.
3. Copy the key. **Claude Code:** paste when the plugin asks for `api_key`. **Cursor:** **Plugins → Configure** → `OPEN_UX_API_KEY`. **Other MCP clients:** `Authorization: Bearer uxmcp_…` on `https://open-ux.dev/mcp`.

No key? Skip hosted and use [self-host](#self-host) with local stdio (same tools, no auth).

### Hosted

1. Complete [Get a key](#get-a-key-hosted-catalog) above
2. Point your MCP client at `https://open-ux.dev/mcp` with that bearer token
3. Name the task (e.g. a signup form), `get_situation`, then `Open-UX:pack`. See the skill table for `jobs=` ids

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

1. **Skill:** when to pull UX rules and how to route (forms vs delete vs loading, …)
2. **Slash commands:** `/pack`, `/get`, … as shortcuts to the tools
3. **MCP connection:** how the agent reaches Open UX to fetch rules

Rules still come from the **server:** either hosted (`open-ux.dev`) or a local Python process you run yourself. For hosted, [get a key](#get-a-key-hosted-catalog) first.

**Claude Code** (terminal, from any folder):

```bash
claude plugin marketplace add 3dyonic/open-ux # register this GitHub repo as a plugin source
claude plugin install open-ux@open-ux # install the Open UX plugin from that source
```

Then enable the plugin in Claude Code and paste your `uxmcp_` key when it asks.

**Cursor** (this repository open as the workspace):

1. Enable the Open UX plugin (Cursor reads it from [`clients/plugin`](clients/plugin)).
2. **Plugins → Configure** → set **`OPEN_UX_API_KEY`** to your `uxmcp_…` token.

That key is sent as `Authorization: Bearer …` to `https://open-ux.dev/mcp` (see [`mcp.json`](clients/plugin/mcp.json)).

**No key? Local catalog instead:** `pip install open-ux`, run `python -m open_ux stdio`, and point MCP at [`mcp.stdio.json`](clients/plugin/mcp.stdio.json). Same tools; catalog loads from this repo’s `catalog/` folder. Step by step: [`clients/plugin/SETUP.md`](clients/plugin/SETUP.md).

Plugins are not in the public marketplaces yet. Install from this repo until listing ships.

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
| `get_situation` | One job: when to use it, what to open instead, how many rules per slice |
| **`pack`** | Cited criteria for a job, slice, or rule ids; page with `next_offset` |
| `get_guideline` | Full rule body and sources |
| `list_guidelines` / `search_guidelines` | Paged index |
| `list_components` / `get_component` | Control detail when a row points at a component |

## Repository

```
catalog/           rules, jobs tree, schema
packages/mcp/      MCP server (PyPI: open-ux)
packages/web/      public site
helpers/           local CLI (rank-pack, wire debug)
clients/plugin/    Claude Code + Cursor plugin
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

PRs welcome: cited catalog rules, server changes, docs, plugin pack. **Docs map:** [`docs/README.md`](docs/README.md). **Before a PR:** [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) (checklist + cite shape).

## License

[MIT](LICENSE)
