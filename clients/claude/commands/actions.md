---
description: Route into the open-ux skill for the actions container (CTAs, destructive, leave).
---

Same skill (`open-ux`). Container alias `actions` = `actions_and_decisions`.

Pick a Card from the skill routing table:

- Primary vs secondary, submit/continue label, toolbar, hit targets → `design_actions_and_ctas`
- Delete, discard, unsaved leave, confirm/undo → `protect_destructive_and_leave`

Then `Open-UX:get_situation` → `Open-UX:audit` with `jobs=<card_id>` (or `jobs=actions` if the user did not name a problem).

Field labels stay `design_a_form`. Page voice / link text → `write_the_interface`.

Do not load an `open-ux-actions` package. Do not send a file. Do not return pass or fail.
