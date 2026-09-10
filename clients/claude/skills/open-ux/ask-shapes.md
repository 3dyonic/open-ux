# Ask shapes

User language → Card (optional Leaf) → **`get_component`** when **`component[]`** is stamped on the row or Card.

| Ask (how users say it) | Card / Leaf | Component context |
| --- | --- | --- |
| Delete modal — right red / danger button for destructive action | `protect_destructive_and_leave` / `disable_or_confirm_destructive` | `button` |
| Clicked away with unsaved edits — need a leave confirmation? | `protect_destructive_and_leave` / `warn_before_leave` | `button`, `modal` when control-specific |
| Row delete — popconfirm or full modal? | `protect_destructive_and_leave` (Leaf if map counts justify) | `popconfirm`, `modal`, `button` |
| Dialog title feels sorry / alarmist for delete | `protect_destructive_and_leave` | cite only |
| Cancel styled as a link on a form | `design_a_form` / `choose_control_for_choice` | `button`, `link` |
| Save gray, Continue blue — primary feels backwards | `design_actions_and_ctas` / `pick_primary_action` | `button` |
| After delete fails — is “Error” enough? | `compose_feedback` | — |
| Submit button tiny / hard to tap on mobile | `design_actions_and_ctas` | `button` |
| Review signup or settings labels (and fields) | `design_a_form` | — |
| Inline validation / error messages on a form | `handle_form_errors` | — |
| Spinner on the submit button while saving | `compose_feedback` | `button` when variant naming matters |

Map leaf counts first; narrow with **`jobs=<leaf_id>`** when the ask fits one bay. Labels **and** validation → two Cards, not one forced winner.
