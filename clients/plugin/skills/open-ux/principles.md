# Principles

Read this when the ask does not map cleanly to [cards.md](cards.md), or before treating something as a new tool, command, or Card. It states the design rules the rest of the skill already follows, so an ambiguous case can be resolved the same way a maintainer would resolve it.

## Decision order for an ambiguous ask

1. **No area in mind:** `Open-UX:suggest_situations` — the full map, no Card picked for you.
2. **Area known, Card unclear:** `Open-UX:list_situations` scoped to the container.
3. **Card known, not mapped:** `Open-UX:get_situation` on the Card id.
4. **Already have a `guideline_id`:** skip straight to `Open-UX:get_guideline`; no map or pack needed.
5. **Two Cards both plausible:** open both `get_situation` calls; compare `when` and `reject`; take more than one Card if the ask genuinely spans them. Do not force a single winner.

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

`SKILL.md` is the only thing that loads every turn. Everything it links to — `cards.md`, `ask-shapes.md`, `shapes.md`, `examples.md`, `guideline.md`, `component.md`, `tools.md`, `connect.md`, this file — is read only when the step at hand calls for it. The registered surface (skills, commands, agents) should equal the number of genuinely distinct entry points into this catalog. A capability that is really a new value for an existing parameter, or a new row in a reference file, does not get its own registration.
