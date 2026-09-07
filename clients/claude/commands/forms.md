---
description: Route into the open-ux skill for the forms container (fields, labels, validation, sign-in).
---

Same skill (`open-ux`). Container alias `forms` = `forms_and_input`.

Pick a Card from the skill routing table:

- Field labels, controls, grouping, required → `design_a_form`
- Validation / inline errors → `handle_form_errors`
- Login / password → `compose_sign_in`

Then `Open-UX:get_situation` → `Open-UX:audit` with `jobs=<card_id>` (or `jobs=forms` if the user did not name a problem).

Wizard / steps → `build_a_multi_step_flow`. CTA wording → `design_actions_and_ctas`. Field labels stay `design_a_form`.

Do not load an `open-ux-forms` package. Do not send a file. Do not return pass or fail.
