from __future__ import annotations

from typing import Literal

DEFAULT_LIMIT = 10
MAX_LIMIT = 50

MISS_NOTE = "No rules match this need."

JOB_TEMPLATES = (
    "name_a_control",
    "avoid_placeholder_as_label",
    "keep_field_purpose_visible_while_filled",
    "recover_from_invalid_input",
    "explain_failure_next_to_cause",
    "choose_control_for_choice",
    "group_related_inputs",
    "announce_system_status",
    "wayfind_after_nav",
    "use_familiar_control",
    "write_empty_state",
    "tone_of_voice_for_failure",
    "pick_primary_action",
    "disable_or_confirm_destructive",
    "keep_hit_target_usable",
)

JOB_ALIASES = ("forms", "actions", "feedback")

JobId = Literal[
    "name_a_control",
    "avoid_placeholder_as_label",
    "keep_field_purpose_visible_while_filled",
    "recover_from_invalid_input",
    "explain_failure_next_to_cause",
    "choose_control_for_choice",
    "group_related_inputs",
    "announce_system_status",
    "wayfind_after_nav",
    "use_familiar_control",
    "write_empty_state",
    "tone_of_voice_for_failure",
    "pick_primary_action",
    "disable_or_confirm_destructive",
    "keep_hit_target_usable",
    "forms",
    "actions",
    "feedback",
]

# Until UNS-86 retags LIVE seeds, a template with no tagged rows
# falls back to its container alias so the call is not empty.
TEMPLATE_FALLBACK_ALIAS: dict[str, str] = {
    "name_a_control": "forms",
    "avoid_placeholder_as_label": "forms",
    "keep_field_purpose_visible_while_filled": "forms",
    "recover_from_invalid_input": "forms",
    "explain_failure_next_to_cause": "forms",
    "choose_control_for_choice": "forms",
    "group_related_inputs": "forms",
    "announce_system_status": "feedback",
    "wayfind_after_nav": "feedback",
    "use_familiar_control": "actions",
    "write_empty_state": "feedback",
    "tone_of_voice_for_failure": "feedback",
    "pick_primary_action": "actions",
    "disable_or_confirm_destructive": "actions",
    "keep_hit_target_usable": "actions",
}

JOB_FIELD_DESCRIPTION = (
    "One job template: the problem being solved and the UX being defined. "
    "Prefer this over guideline_ids. "
    "name_a_control — Naming a field / control. "
    "avoid_placeholder_as_label — Placeholder as the only name. "
    "keep_field_purpose_visible_while_filled — Label disappears while typing. "
    "recover_from_invalid_input — Recovering from bad input. "
    "explain_failure_next_to_cause — Error far from the cause. "
    "choose_control_for_choice — Picking among options. "
    "group_related_inputs — Related fields scattered. "
    "announce_system_status — Silent success / progress. "
    "wayfind_after_nav — Lost after navigation. "
    "use_familiar_control — A weird control for a common act. "
    "write_empty_state — Empty / no-results. "
    "tone_of_voice_for_failure — Failure copy that hurts. "
    "pick_primary_action — No clear next step. "
    "disable_or_confirm_destructive — Destroy is too easy. "
    "keep_hit_target_usable — Control is hard to hit. "
    "forms / actions / feedback — vague ask only; prefer a template."
)

AUDIT_TOOL_DESCRIPTION = (
    "Say the UX need as one jobs template. Returns cited rule criteria. "
    "Does not take a file. Does not return pass or fail. "
    "Required: jobs or guideline_ids."
)
