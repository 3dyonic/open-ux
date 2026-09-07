---
description: Audit the actions container (CTAs, destructive, leave) via the open-ux skill.
---

Same skill (`open-ux`). Default Card: `design_actions_and_ctas`. `$ARGUMENTS` may be `protect_destructive_and_leave` or `actions`.

```
python3 skills/open-ux/scripts/audit.py --jobs ${ARGUMENTS:-design_actions_and_ctas}
```

No file. No pass/fail. Do not load an `open-ux-actions` package.
