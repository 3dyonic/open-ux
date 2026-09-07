---
description: Fetch cited UX criteria for a Card or guideline ids. Always scoped. No file. No pass/fail from the host.
---

`$ARGUMENTS` is a Card id, `jobs=<card_id>`, container alias, or `--guideline-ids`.

```
python3 skills/open-ux/scripts/audit.py $ARGUMENTS
```

No file. No pass/fail. Print the criteria pack. If empty, say so. Do not invent rules.
