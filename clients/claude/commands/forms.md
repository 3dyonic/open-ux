---
description: Audit the forms container (fields, labels, validation, sign-in) via the open-ux skill.
---

Same skill (`open-ux`). Default Card: `design_a_form`. `$ARGUMENTS` may be `handle_form_errors`, `compose_sign_in`, or `forms`.

```
python3 skills/open-ux/scripts/audit.py --jobs ${ARGUMENTS:-design_a_form}
```

No file. No pass/fail. Do not load an `open-ux-forms` package.
