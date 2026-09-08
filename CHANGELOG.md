# Changelog

## Unreleased

- `audit` browse row includes `overview` and omits `pass_when` / `fail_when` (those stay on `get_guideline`).
- Skill pack: browse orientation on `SKILL.md`; full-record field guide in `guideline.md`.

## 0.2.2

OUX-32: `audit` pages at 10 with `offset` / `omitted` / `next_offset`. `query_fallback` when fail-open. `host: "citations_only"`.

## 0.2.0

Breaking: `suggest_situations` is a catalog map, not a ranked list.

- Response is `{containers: [{id, title, situations: [...]}], note}`. There is no top-level card list, `why`, score, or `attention`.
- Order is the catalog lock. `task_text` and `surface` do not reorder. The tool description no longer calls order a heuristic hint.
- BM25 still orders `search_guidelines` and `audit` `query` over guideline JSON, not Situation Cards.

Plugin pack **1.1.0**. PyPI tag **v0.2.0** (commit subject must include `BREAKING` so publish does not ship this as a 0.1.x patch).
