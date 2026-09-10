# Wire shapes

**Map** (`get_situation` facet):

```json
{
  "id": "wrong_control_for_the_choice",
  "title": "Wrong control for the choice",
  "leaves": [
    { "id": "choose_control_for_choice", "count": 20 }
  ],
  "guideline_ids": ["…"]
}
```

**Pack** (Card or Leaf pull — envelope + page):

**`overview`** is the short definition — what this cite *is*. Start there. Fast confidence. Not a grade.

```json
{
  "situation": {
    "card": "design_a_form",
    "when": ["…"],
    "reject": [{ "id": "handle_form_errors", "why": "…" }],
    "leaf": "choose_control_for_choice"
  },
  "cite_via": "get_guideline",
  "guidelines": [{
    "id": "",
    "name": "",
    "overview": "",
    "apply_when": "",
    "not_when": "",
    "rule": "",
    "hints": [],
    "component": [],
    "leaf": "",
    "card": "",
    "facet": ""
  }],
  "count": 10,
  "total": 13,
  "offset": 0,
  "host": "citations_only",
  "next_offset": 10
}
```

Envelope **`leaf`** only when `jobs=` is a Leaf id. Container pulls (`forms` / `actions` / `feedback`) omit **`situation`**; they still set **`cite_via`**.

Read envelope **`reject`**, then row fit (`apply_when` / `not_when`). **`get_guideline`** for the cited rule; **`get_component`** when **`component[]`** names the control — then back to the pack.

One Card is many sources. Related Cards are not a fork with a winner. `host` is `citations_only`. Do not write a score as if we graded.
