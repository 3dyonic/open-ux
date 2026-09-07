---
description: Audit the feedback container (toast, empty, 404, hard error) via the open-ux skill.
---

Same skill (`open-ux`). Default Card: `compose_feedback`. `$ARGUMENTS` may be `feedback`.

```
python3 skills/open-ux/scripts/audit.py --jobs ${ARGUMENTS:-compose_feedback}
```

No file. No pass/fail. Do not load an `open-ux-feedback` package.
