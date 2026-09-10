# Glossary

Open UX vocabulary for **any MCP agent** using `Open-UX:*` tools. Same terms in Claude Code, Cursor, or any other client; the editor plugin skill links here too.

Coarse → fine. **`jobs=`** on **`pack`** names the pull.

**Map:** Two maps, do not mix them.
- **Situation map:** 13 compose **Cards**. Tools: **`suggest_situations`**, **`list_situations`**, **`get_situation`**, [cards.md](../clients/plugin/skills/open-ux/cards.md). Answers *which job am I doing?*
- **Catalog map:** 204 **cites** by **category** (disk layout) and **source** (govuk, ant, …). [`catalog/MANIFEST.md`](../catalog/MANIFEST.md), **`list_guidelines`**, **`search_guidelines`**. Answers *what exists in the library?*

**Container:** Kind of work in jobs.json (7). Groups Cards. **`jobs=forms`**, **`jobs=actions`**, **`jobs=feedback`** (aliases) pack every cite in that kind: broad browse, no **`situation`** envelope. Not the same as rule **category** on disk.

**Card:** Situation Card (13). One compose job: `design_a_form`, `protect_destructive_and_leave`, … **`when`**, **`reject`**, facets, optional **`component[]`**. **`jobs=<card_id>`** → pack with **`situation`** envelope. **`home` / `cart` / `checkout`** are surface context for ranking, not Cards.

**Facet:** Topic slice on the Card map from **`get_situation`**. Lists **Leaves** (with counts) or cite pointers. Not a **`jobs=`** value: scope with Card or Leaf.

**Leaf:** Narrow bay on a Card. Finest **`jobs=`** before one cite: `choose_control_for_choice`, `disable_or_confirm_destructive`, … **`jobs=<leaf_id>`** → pack; envelope includes the scoped leaf id. Map counts first.

**Cite:** One sourced UX claim. One file in catalog/rules (204). Full record: **`get_guideline`**. **`pack`** returns a browse **row** per cite: not the full file.

**Pack:** The offer. A **page** of cite rows for **`jobs=`** or **`guideline_ids`**. Skim on the row; **`get_guideline`** for depth. **`next_offset`** to continue. Host does not rank; does not pass or fail.

**Component:** Named control in `catalog/components/` (`button`, …). **Not** a Card or cite. **`component[]`** on Card and cite joins control context. **`get_component`:** variants, a11y, keyboard; usually after **`get_guideline`** on the same row.
