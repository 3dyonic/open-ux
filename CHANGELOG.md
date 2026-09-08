# Changelog

## Unreleased

OUX-32: `audit` lazy-loads pages of 10.

- `offset` plus `omitted` / `next_offset` / `omitted_hint` until the in-scope shelf is empty. `limit` max 50 is one page, not a shelf ceiling.
- `query_fallback: true` when fail-open (OUX-21).
- Always `host: "citations_only"`. Cited criteria help you decide; the decision is yours.

## 0.2.0

Breaking: `suggest_situations` is a catalog map, not a ranked list.

- Response is `{containers: [{id, title, situations: [...]}], note}`. There is no top-level card list, `why`, score, or `attention`.
- Order is the catalog lock. `task_text` and `surface` do not reorder. The tool description no longer calls order a heuristic hint.
- BM25 still orders `search_guidelines` and `audit` `query` over guideline JSON, not Situation Cards.

Plugin pack **1.1.0**. PyPI tag **v0.2.0** (commit subject must include `BREAKING` so publish does not ship this as a 0.1.x patch).
