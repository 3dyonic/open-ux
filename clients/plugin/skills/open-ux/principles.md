# Principles

Read this when the ask does not map cleanly to [cards.md](cards.md), or before treating something as a new tool, command, or Card. It states the design rules the rest of the skill already follows, so an ambiguous case can be resolved the same way a maintainer would resolve it.

## Design intent

- **One skill, always on.** Everything else — [cards.md](cards.md), [ask-shapes.md](ask-shapes.md), [examples.md](examples.md), [tools.md](tools.md), this file — is a reference the skill points to, read only when a step needs it. Nothing else registers itself.
- **`jobs=` is the only lever.** Container, Card, or Leaf id — one parameter, three sizes. No parallel commands for a value that lever already accepts.
- **Catalog stays server-side.** The host fetches and returns cited rows; it never picks a Card, never ranks, never grades pass/fail. The decision is always yours.
- **Map, then pull.** Cheap id-and-count calls (`get_situation`, `list_*`) come before body calls (`pack`, `get_guideline`), so scope is chosen with the size of what's behind it already known.

Compose and review run the same tree. For review, read each row's `apply_when` before trusting it fits the screen you are auditing.

## Decision tree: you have a UI task

Start from **what the user said and what is on screen** — not from Card ids. Cards are how the catalog groups compose jobs; you **resolve** to them after the ask is understood.

```
What do you have?
│
├─ Direct /open-ux:open-ux, no task attached yet
│   └─ Open-UX:list_situations or suggest_situations → [bare-invoke.md](bare-invoke.md) verbatim reply
│
├─ User words + UI in front of you (usual case)
│   ├─ Ask matches a row in ask-shapes.md?
│   │   └─ Open-UX:get_situation(that Card) → scope pack → pull (below)
│   └─ Ask still fuzzy?
│       └─ Open-UX:suggest_situations(task_text) → compare when / reject → one or more Cards
│
├─ Kind of work clear, job not ("form stuff", "buttons", "errors on the page")
│   ├─ Open-UX:list_situations(container=forms|actions|feedback|…)
│   │   → compare when / reject → pick Card(s) → get_situation → pull (below)
│   └─ Broad audit across that kind, no single job yet
│       └─ Open-UX:pack(jobs=<container>) → loop pages → narrow to a Card when the ask sharpens
│
├─ Already have a guideline id
│   └─ Open-UX:get_guideline(id) → done, no pack needed
│
└─ Pull (after a Card or Leaf is named — not the starting point)
    Open-UX:get_situation(card_id)   → leaves:[{id,count}], component[]
        │
        ├─ Whole Card fits
        │   └─ Open-UX:pack(jobs=<card_id>) → read reject → skim rows
        └─ One bay fits
            └─ Open-UX:pack(jobs=<leaf_id>) → narrower rows, same reject

                │
                ▼
    Row worth acting on?
    Open-UX:get_guideline(row.id)
    Open-UX:get_component(row.component[])   → only if stamped
                │
                ▼
    next_offset? → pack again
    Ask spans another job? → next Card, same pull loop
```

User phrasing → [ask-shapes.md](ask-shapes.md) first. Card table and reject neighbors → [cards.md](cards.md). Scope sizes → [examples.md](examples.md).

## Decision order for an ambiguous ask

1. **Start with the ask:** user words and visible UI — not a Card id.
2. **Recognized phrasing:** [ask-shapes.md](ask-shapes.md) → `get_situation` on that Card.
3. **No area in mind:** `Open-UX:suggest_situations` — full map; compare `when` / `reject`; pick one or more Cards.
4. **Area known, job unclear:** `Open-UX:list_situations` scoped to the container; then pick Card(s).
5. **Broad pass, no job yet:** `Open-UX:pack` with a container alias; narrow when the ask sharpens.
6. **Card known, not mapped:** `Open-UX:get_situation` on the Card id before `pack`.
7. **Already have a `guideline_id`:** `Open-UX:get_guideline` — skip map and pack.
8. **Two Cards both plausible:** open both `get_situation` calls; compare `when` and `reject`; take more than one if the ask spans them. Do not force a single winner.

## Why `jobs=` is the only scoping parameter

`Open-UX:pack` takes one parameter, `jobs=`, at three sizes: a container alias (`forms`, `actions`, `feedback`, …), a Card id, or a Leaf id. The envelope grows with the size (`cite_via` only → `+ situation, reject` → `+ leaf`). A new kind of pull is a new value on `jobs=`, not a new tool and not a new command — this is why the catalog can grow from 13 Cards to more without the tool count changing.

A container alias such as `forms` is a `jobs=` value, nothing else. It is not a distinct operation and must never be re-implemented as its own registered command or skill — that duplicates what `cards.md` and this parameter already cover, and costs every future install a standing entry that never had its own behavior. If you are about to write a file whose whole content is "same as `pack`, but with `jobs=<one specific value>` pre-filled," that value belongs in `cards.md` or `examples.md`, not in its own file.

## Map before you pull

`Open-UX:get_situation` (ids and counts) precedes `Open-UX:pack` (bodies) for a reason: `leaves: [{ id, count }]` tells you roughly how much sits behind a scope before you choose how narrow to go. Do not guess a Leaf id and pack it blind when the Card has not been mapped yet.

## `reject` is not optional reading

`reject` travels inside the same `situation` envelope as the fit criteria, on every Card or Leaf pull. Skipping it is how an agent ends up applying `design_a_form` guidance to a login field that `compose_sign_in` already covers. Read it before skimming rows.

## Ranking stays off this surface

`pack`'s and `search_guidelines`'s `query` parameter is not authoritative here; the host does not rank or BM25-sort results. Reordering one already-fetched pack page is what the optional local `open-ux rank-pack` CLI is for (`pip install open-ux`), not something to reimplement inline.

## `component[]` is stamped, not enumerated

Open a component record only when a pack row or Card actually names it in `component[]`. `Open-UX:list_components` is a 38-entry browse index, opened by choice — never pulled in as background context for every pack.

## One hub, references on demand

`SKILL.md` is the only thing that loads every turn. Everything it links to — [cards.md](cards.md), [ask-shapes.md](ask-shapes.md), [shapes.md](shapes.md), [examples.md](examples.md), [guideline.md](guideline.md), [component.md](component.md), [tools.md](tools.md), [connect.md](connect.md), this file — is read only when the step at hand calls for it. The registered surface should equal the number of genuinely distinct entry points into this catalog. A capability that is really a new value on an existing parameter, or a new row in a reference file, does not get its own registration.
