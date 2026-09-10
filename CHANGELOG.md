# Changelog

## Unreleased

- Docs: root README lists Claude Code and Cursor plugins as equal paths; both are in marketplace submission and not yet published. Catalog size (204 / 13 / 28) and `packages/web` in the repo layout.
- Search appearance: PNG favicon (`/icon.png`), canonical / Open Graph tags, WebSite + Organization JSON-LD, breadcrumbs on catalog pages. Sitemap adds `/invite`, `lastmod` from real file dates, and the homepage image entry. `noindex` on health and invite utility pages.

- Helpers: **`pip install open-ux`** ships all helper tools as **`open-ux`** subcommands (`open-ux helpers list`; agent helper **`open-ux rank-pack`**). Registry bundled in wheel. MCP fetches catalog data; helpers run on the user's machine ([`helpers/README.md`](helpers/README.md)). No MCP helper resources; pip is the execution path.
- Docs: components as context helper for Cards and jobs; ask-shapes table and Leaf-scoping examples in skill; `component.md` link and CLI aliases in [`docs/TOOLS.md`](docs/TOOLS.md); `widget` → `component` in tool docstrings; [`clients/plugin/mcp.stdio.json`](clients/plugin/mcp.stdio.json) for local MCP wire (`pack`, `get_component`).
- Skill: hub + references `open-ux` package; hub [`SKILL.md`](clients/plugin/skills/open-ux/SKILL.md) + glossary, ask-shapes, examples, shapes, cards, tools, connect, guideline, component references (progressive disclosure).
- Docs: [`docs/TOOLS.md`](docs/TOOLS.md): canonical tool blurbs; no `audit` tool (use `pack`); sweep `packs/imp.json`, README, AGENTS, plugin README; ops `DEPLOY.md`.
- Docs: root README tool table and pack loop; `catalog/README.md` file count (204); plugin SETUP/README; `docs/PRIVACY.md` `pack`; agent Tools list includes components; `packs/eor.json` claims use `pack` not `audit`.
- CI and contributor checks: `claude plugin validate` (marketplace + plugin, `--strict`) and `node scripts/validate-cursor-plugin.mjs --strict`. Slash command frontmatter adds `name`.
- **BREAKING:** `Open-UX:get_situation` facet `leaves` is `{id, count}` (stocked cite count per Leaf), not a string list.
- Pack Card/Leaf pulls add envelope `situation` (`when`, `reject`; `leaf` when scoped) and `cite_via: get_guideline`.
- Skill: documented loop: map leaf counts → pack (envelope reject, row fit) → `get_guideline` or `get_component` by question type; Leaf routing examples (control choice vs primary loudness; spinner → `compose_feedback`).
- `validate_apply_when_fit` on gate Leaves; `validate-catalog` reports violations (exit 0), `--strict-fit` exits 1. CI uses `--strict-fit`.
- Slash commands `/get` and `/pack` aligned with the loop; `packages/mcp/README.md` documents `pack` and `--strict-fit`.
- Vite owns the cookie banner, `open_ux_gtm_consent`, and Google Tag Manager after Accept. Python only returns the container id at `/api/site`.
- OUX-37: `/health` and `/health.json`: `ok` is computed (catalog loaded, no recorded 5xx). Payload adds `error`, `title`, and `body`. HTTP stays 200.
- OUX-37: Public 404 and 500 pages are prerendered into the SPA shell. Missing catalog ids and unknown paths return 404. Unhandled errors return the 500 page.
- OUX-37: Vite writes public HTML at build. Python serves the files and status codes; it does not write page markup.
- **BREAKING:** `Open-UX:audit` → `Open-UX:pack`. Module `open_ux.audit` → `open_ux.pack`. CLI `open-ux pack`. Slash command `/pack`. Host does not BM25-rank on request; optional `helpers/rank_pack.py`.
- **BREAKING:** Leaf ids are valid `jobs=` values (`pick_primary_action`, etc.). MCP `pack` jobs enum includes all 28 Leaves.
- Pack row adds `apply_when`, `not_when`, `leaf`, `card`, `hints`, `component`. Component matching dimension: `catalog/components.json` + 38 records; `load_components()`; Card and cite `component[]` stamps (131 cites, 13 Cards). Cite `hints[]` on 52 cites where host scan benefits; pack omits `hints` when the cite omits it; do not bridge `agent_hint` → `hints` (see `catalog/README.md`).
- `Open-UX:list_components` / `Open-UX:get_component`: component index and record with section switches; optional `used_on` reverse index. CLI `open-ux components` / `open-ux component`. Helper `helpers/get_component.py`.
- **Lock:** `component[]` is a join id on the Card and the cite only. Facet, Leaf, and container do not stamp it. Component `keywords` stay on the component record; do not copy into `jobs.json` or echo onto every pack row. Pack `component[]` is ids only (no variant axes). Cite `hints[]` are host extras not already on the row; omit the key when empty; do not ship `[]` or copy `agent_hint` / component `keywords`.
- Pack envelope: `count`, `total`, `offset`, optional `next_offset`, `host`: no echoed `limit` (page size is input only).
- Agent helpers moved to `helpers/` with `helpers/registry.json`. Contributor scripts stay in `scripts/`.
- Skill: no winner Card; compare Cards; Python helpers `helpers/pack.py` and `helpers/rank_pack.py` (available, not required: do not invent a ranker).
- Dropped empty Leaves `show_action_state` and `write_empty_state`. Spinner / loading on the control routes to `compose_feedback`. Empty-collection is not a named bay until a cite exists.
- Skill pack: browse orientation on `SKILL.md`; full-record field guide in `guideline.md`.

## 0.2.2

OUX-32: `audit` pages at 10 with `offset` / `omitted` / `next_offset`. `query_fallback` when fail-open. `host: "citations_only"`.

## 0.2.0

Breaking: `suggest_situations` is a catalog map, not a ranked list.

- Response is `{containers: [{id, title, situations: [...]}], note}`. There is no top-level card list, `why`, score, or `attention`.
- Order is the catalog lock. `task_text` and `surface` do not reorder. The tool description no longer calls order a heuristic hint.
- BM25 still orders `search_guidelines` and `audit` `query` over guideline JSON, not Situation Cards.

Plugin pack **1.1.0**. PyPI tag **v0.2.0** (commit subject must include `BREAKING` so publish does not ship this as a 0.1.x patch).
