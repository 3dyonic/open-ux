# Open UX

![Open UX: catalog to audit flow](docs/readme-hero.svg)

**Cited UX rules agents audit against.**

Stop inventing UX rules from memory. Open UX is a shared, cited catalog agents list, fetch, and audit against. v1: Forms → field labels. Request an invite on the hosted service; self-host without our cloud. Telemetry improves the shared catalog — we never store your UI payloads.

## What it is

A curated, machine-readable store of UX guidelines plus tools so an agent can:

1. **Find** a Situation Card for the compose job
2. **Fetch** cited rule criteria for that Card
3. **Apply** those criteria (`rule` / `pass_when` / `fail_when`) to the work already in hand

The host does not take the file and does not return pass or fail. The client applies those criteria to the work it already has. There is no server-side LLM.

Use the hosted endpoint (request an invite, redeem for an API key) or self-host the same catalog and tools. Open source, MIT.

## What it isn’t

- A generative design copilot, redesign product, or “does this look good?” scorer
- Everyone shares the same guidelines. Creating an account only lets you use the service — it doesn’t give you a private rulebook.
- An accessibility or **WCAG compliance** checker — we do not claim WCAG conformance, contrast, or screen-reader names

## v1 scope

**Category:** Forms  
**Segment:** Field labels  
**Three cited rules:**

| id | Rule | Citation |
| --- | --- | --- |
| `forms.field_labels.visible_label` | Every input has a visible label. Placeholder text alone is not enough. | [Apple HIG — Text fields](https://developer.apple.com/design/human-interface-guidelines/text-fields), Material |
| `forms.field_labels.label_stays_visible` | The field label remains visible while the field has a value (floating or persistent — not replaced by the value alone). | [Material 3 — Text fields](https://m3.material.io/components/text-fields/guidelines) |
| `forms.field_labels.error_identifies_and_fixes` | Error text identifies the field and tells the user how to fix it. | [NN/g — Error-Message Guidelines](https://www.nngroup.com/articles/error-message-guidelines/) |

Those ids are the Designer LIVE seed (UNS-44), kept as the first three files under [`catalog/rules/`](catalog/rules/). The generated index is [`catalog/index.json`](catalog/index.json). The tree is [`catalog/jobs.json`](catalog/jobs.json).

**Out of v1:** other form segments, screenshots, search, suggest-fixes, bulk ingest, inventing look, a server LLM grader.

## Tools

| Tool | Input | Output |
| --- | --- | --- |
| `list_situations` | optional `container`, `limit`, `offset` | Paged Situation Cards (id, title, container) |
| `get_situation` | Card `id` | Card + facets + leaf / rule pointers. Fails on a Leaf id |
| `suggest_situations` | `task_text`, optional `surface` | Ranked Card ids from the allowlist. Fallback only |
| `list_guidelines` | `limit`, `offset` | Paged index: id, title, jobs, lane, placement |
| `search_guidelines` | `query` and/or `jobs` and/or `lane` | Same index shape |
| `get_guideline` | `id` | Full rule body |
| `audit` | `jobs` (one Card or container) or `guideline_ids`; optional `query`, `limit` | `{ guidelines: [{ id, title, rule, pass_when, fail_when }], count, total }` |

`jobs` is a Card id or container id (plus legacy `forms` / `actions` / `feedback` aliases). Leaf ids are not needs. Default `limit` 10, max 50. No `target`. No host `verdict`. If nothing matches: empty list + note. The tree lives in [`catalog/jobs.json`](catalog/jobs.json).

## Catalog

One file per rule in [`catalog/rules/`](catalog/rules/) (`{id}.json`). Generated index: [`catalog/index.json`](catalog/index.json). Schema: [`catalog/schema.json`](catalog/schema.json). Tree: [`catalog/jobs.json`](catalog/jobs.json). Never forked per tenant.

Soft size ~50–100 KB. Hard ceiling ~384 KB.

## Hosted vs self-host

| | Hosted HTTP | Self-host stdio |
| --- | --- | --- |
| Auth | Waitlist → redeem invite → bearer `uxmcp_`. Tools **401** without a key. | No auth |
| Limits | Soft ~60/min and ~1k/day per key | None |
| Telemetry | Callers (key_hash), tool mix, rule ids | Off |

See [docs/PRIVACY.md](docs/PRIVACY.md) and [docs/DEPLOY.md](docs/DEPLOY.md). Display name is **Open UX**. Do not put “MCP” in the H1 or marketplace title.

## Layout

```
packages/mcp     Python FastMCP server
catalog/         shared rules JSON + schema
clients/claude   thin Claude plugin / install craft (no duplicate rule bodies)
docs/            LANDING.md + readme-hero.svg (designer craft), PRIVACY.md, DEPLOY.md
packs/           honest imp.* / eor.e* notes for this scaffold
```

Package name: `@3dyonic/open-ux` (Claude plugin / npm scope). Python distribution: `open-ux`.

## Quick start

**Connect → key → list → one audit.** Thursday: URL + key in client settings. Plugin registry comes after that proof.

### Hosted

1. Request an invite on `/invite` (`POST /invite/request`). When approved, redeem the one-time `inv_…` token (`POST /invite/redeem`) → bearer API key (`uxmcp_…`).
2. Point your client at the hosted `/mcp` URL (deploy your own; no public URL in this repo yet).
3. Call `list_guidelines`, then `audit` with a `jobs` template (no file).

Hosted tools return 401 without a key. One shared catalog for every caller.

### Claude plugin

Thin install from [`clients/claude`](clients/claude). Connect → list rules → one audit. The plugin does not ship a second copy of the catalog.

### Self-host / run locally

Same tools from `packages/mcp` over stdio. No invite step. Same catalog as hosted.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e "packages/mcp[dev]"
python -m open_ux validate-catalog
python -m open_ux stdio          # self-host, no auth
OPEN_UX_MODE=hosted python -m open_ux http   # http://127.0.0.1:8080
```

Tests (no LLM):

```bash
cd packages/mcp && python -m pytest
```

## Privacy

On the hosted service:

- **Never stored:** file contents, prompts, or other UI / PII bodies
- **Telemetry:** callers, tool mix, rule ids

Self-host: your process, your logs. Telemetry off.

## Status

Early. v1 is the three Forms → field-labels rules above; the catalog file is still a stub until Designer UNS-44 lands. Merge of this scaffold is held for Architect review.

## License

[MIT](LICENSE)
