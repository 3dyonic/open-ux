---
description: Route into the open-ux skill for the feedback container (toast, empty, 404, hard error).
---

Same skill (`open-ux`). Container alias `feedback` = `feedback_and_status`.

The Card is `compose_feedback` (toast after save, loading, empty, 404, hard error, failure tone).

Then `Open-UX:get_situation` → `Open-UX:audit` with `jobs=compose_feedback` (or `jobs=feedback` if the user did not name a problem).

Inline field errors → `handle_form_errors`. Wizard progress → `build_a_multi_step_flow`.

Do not load an `open-ux-feedback` package. Do not send a file. Do not return pass or fail.
