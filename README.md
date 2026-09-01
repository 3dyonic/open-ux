# Open UX

<!-- Designer-owned: docs/readme-hero.svg — catalog → tools → pass/fail. Do not invent brand art; file may arrive in a follow-up commit. -->
![Catalog → tools → pass/fail](docs/readme-hero.svg)

**Stop inventing UX rules from memory.**

UX rules live in PDFs, blog posts, and chat. Agents invent them or misquote them. Open UX is a shared, cited catalog those agents can list, fetch, and audit against. One catalog. Hybrid checks. Not a vibes tool.

Product landing (designer-owned): [docs/LANDING.md](docs/LANDING.md).

## What it is

A small, machine-readable store of UX guidelines plus tools so an agent can:

1. **List** the current rules
2. **Fetch** a full cited rule
3. **Audit** a UI snippet and get structured `pass` / `fail` / `incomplete` with rule ids

Audits are **hybrid**. Where a rule is checkable and the input is parseable HTML or JSX, the **server** grades it deterministically. Where it isn’t, the server returns `incomplete` plus the rule text (`pass_when` / `fail_when`) so the **client LLM** can finish. There is no server-side LLM.

Use the hosted endpoint (register with email, get an API key) or self-host the same catalog and tools. Open source, MIT.

## What it isn’t

- A generative design copilot, redesign product, or “does this look good?” scorer
- A full design system, token set, or house visual language
- Per-tenant catalogs — one shared catalog; auth is who may call, not whose rules
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

**Out of v1:** other form segments, screenshots, search, suggest-fixes, bulk ingest, inventing look, a server LLM grader.

## Tools

| Tool | Input | Output |
| --- | --- | --- |
| `list_guidelines` | Optional `category`, `segment` | Thin index: id, title, category, segment, severity |
| `get_guideline` | `id` | Full rule: text, citation, check method, examples |
| `audit` | `{ target: { type: "html" \| "jsx" \| "description", content }, guideline_ids? }` | `{ results: [{ guideline_id, verdict, reasons }], summary }` |

Verdicts are `pass`, `fail`, or `incomplete`. Default audit scope is the Forms → field-labels seed if `guideline_ids` is omitted.

## Intended layout

```text
catalog/          # rules JSON — one shared catalog
packages/mcp/     # Python FastMCP server
clients/claude/   # thin plugin (pointers only; do not duplicate rule bodies)
docs/
  LANDING.md      # designer — product landing copy
  readme-hero.svg # designer — catalog → tools → pass/fail
```

Display name is **Open UX**. Do not put “MCP” in the H1 or marketplace title.

## Quick start

The server, catalog files, and plugin are not in this repo yet. Placeholders:

### Hosted

1. Register with email → bearer API key (`uxmcp_…`).
2. Point your client at the hosted URL *(TBD)*.
3. Call `list_guidelines`, then `audit` a snippet.

Hosted tools return 401 without a key. One shared catalog for every caller.

### Claude plugin

Thin install from `clients/claude` *(TBD)*. Connect → list rules → one audit. The plugin does not ship a second copy of the catalog.

### Self-host

Same tools from `packages/mcp` over stdio. No register step. Same catalog as hosted.

```text
# TBD — run the FastMCP server from packages/mcp
```

## Privacy

On the hosted service:

- **Never stored:** `audit.content`, prompts, or other UI / PII bodies
- **Telemetry:** callers, tool mix, verdicts, rule ids (and target type / size as needed)

Self-host: your process, your logs.

## Status

Early. This public repo is the home for the catalog, server, and thin client. v1 is the three Forms → field-labels rules above. Expect the tree and hosted URL to land as they ship.

## License

[MIT](LICENSE)
