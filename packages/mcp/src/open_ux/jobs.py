from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from open_ux.settings import Settings

DEFAULT_LIMIT = 10
MAX_LIMIT = 50

MISS_NOTE = "No rules match this need."

CARD_IDS = (
    "design_a_form",
    "handle_form_errors",
    "compose_sign_in",
    "design_actions_and_ctas",
    "protect_destructive_and_leave",
    "compose_feedback",
    "orient_in_the_place",
    "compose_search",
    "compose_a_data_display",
    "compose_the_layout",
    "write_the_interface",
    "choose_an_overlay",
    "build_a_multi_step_flow",
)

CONTAINER_IDS = (
    "forms_and_input",
    "actions_and_decisions",
    "feedback_and_status",
    "navigation_and_wayfinding",
    "layout_and_data_display",
    "overlays_and_content_structure",
    "multi_step_flows",
)

JOB_ALIASES = ("forms", "actions", "feedback")

LEAF_IDS = (
    "avoid_placeholder_as_label",
    "name_a_control",
    "choose_control_for_choice",
    "use_familiar_control",
    "group_related_inputs",
    "mark_requirements_up_front",
    "word_the_field_help",
    "explain_failure_next_to_cause",
    "recover_from_invalid_input",
    "show_the_password",
    "pick_primary_action",
    "word_the_action",
    "compose_the_command_surface",
    "show_action_state",
    "keep_hit_target_usable",
    "disable_or_confirm_destructive",
    "warn_before_leave",
    "announce_system_status",
    "write_empty_state",
    "tone_of_voice_for_failure",
    "wayfind_after_nav",
    "place_the_search_control",
    "chart_has_a_story",
    "map_is_not_the_only_channel",
    "keep_the_page_scannable",
    "name_the_link_by_destination",
    "write_to_you",
    "pick_modal_only_when_blocking",
    "disclose_instead_of_dump",
    "show_step_progress",
)

JobId = Literal[
    "design_a_form",
    "handle_form_errors",
    "compose_sign_in",
    "design_actions_and_ctas",
    "protect_destructive_and_leave",
    "compose_feedback",
    "orient_in_the_place",
    "compose_search",
    "compose_a_data_display",
    "compose_the_layout",
    "write_the_interface",
    "choose_an_overlay",
    "build_a_multi_step_flow",
    "forms_and_input",
    "actions_and_decisions",
    "feedback_and_status",
    "navigation_and_wayfinding",
    "layout_and_data_display",
    "overlays_and_content_structure",
    "multi_step_flows",
    "forms",
    "actions",
    "feedback",
]

JOB_FIELD_DESCRIPTION = (
    "One Situation Card or container: the compose job being solved. "
    "Prefer a Card over guideline_ids. Leaf ids are not needs. "
    "design_a_form — Signup, settings, or field labeling. "
    "handle_form_errors — Validation and inline form errors. "
    "compose_sign_in — Login, password, forgot-password. "
    "design_actions_and_ctas — Primary/secondary actions and hit targets. "
    "protect_destructive_and_leave — Delete, discard, unsaved leave. "
    "compose_feedback — Toast, empty, 404, loading, failure tone. "
    "orient_in_the_place — Nav, breadcrumbs, where you are. "
    "compose_search — Place and compose search. "
    "compose_a_data_display — Table, dashboard, chart vs grid. "
    "compose_the_layout — Page scan path. "
    "write_the_interface — Link text and page voice. "
    "choose_an_overlay — Modal, accordion, tooltip, side panel. "
    "build_a_multi_step_flow — Wizard, checkout sequence, steps, go back to an earlier answer. "
    "A container id browses every Card in that kind of work. "
    "forms / actions / feedback — legacy aliases for the first three containers."
)

AUDIT_TOOL_DESCRIPTION = (
    "Say the UX need as one Situation Card or container. "
    "Returns cited rule criteria. "
    "Does not take a file. Does not return pass or fail. "
    "Required: jobs or guideline_ids."
)


class JobTreeError(ValueError):
    """catalog/jobs.json failed shape or lock checks."""


@dataclass(frozen=True)
class Reject:
    id: str
    why: str


@dataclass(frozen=True)
class Leaf:
    id: str
    guideline_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class Facet:
    id: str
    title: str
    leaves: tuple[Leaf, ...] = ()
    guideline_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class Card:
    id: str
    title: str
    container: str
    overview: str
    when: tuple[str, ...]
    reject: tuple[Reject, ...]
    hints: tuple[str, ...]
    facets: tuple[Facet, ...]
    provisional: bool = False


@dataclass(frozen=True)
class Container:
    id: str
    title: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class JobTree:
    containers: tuple[Container, ...]
    cards: tuple[Card, ...]

    @property
    def empty(self) -> bool:
        return len(self.cards) == 0


def _jobs_path(catalog_path: Path) -> Path:
    if catalog_path.is_dir():
        return catalog_path / "jobs.json"
    return catalog_path.parent / "jobs.json"


def _leaf(raw: Any) -> Leaf:
    if isinstance(raw, str):
        return Leaf(id=raw)
    if not isinstance(raw, dict) or not raw.get("id"):
        raise JobTreeError("Each leaf needs an id.")
    gids = raw.get("guideline_ids") or []
    if not isinstance(gids, list) or not all(isinstance(g, str) for g in gids):
        raise JobTreeError(f"Leaf {raw.get('id')!r} guideline_ids must be strings.")
    return Leaf(id=str(raw["id"]), guideline_ids=tuple(gids))


def _facet(raw: Any) -> Facet:
    if not isinstance(raw, dict) or not raw.get("id"):
        raise JobTreeError("Each facet needs an id.")
    leaves = tuple(_leaf(item) for item in (raw.get("leaves") or []))
    gids = raw.get("guideline_ids") or []
    if not isinstance(gids, list) or not all(isinstance(g, str) for g in gids):
        raise JobTreeError(f"Facet {raw.get('id')!r} guideline_ids must be strings.")
    return Facet(
        id=str(raw["id"]),
        title=str(raw.get("title") or raw["id"]),
        leaves=leaves,
        guideline_ids=tuple(gids),
    )


def _reject(raw: Any) -> Reject:
    if not isinstance(raw, dict) or not raw.get("id"):
        raise JobTreeError("Each reject needs a Card id.")
    return Reject(id=str(raw["id"]), why=str(raw.get("why") or ""))


def _card(raw: Any) -> Card:
    if not isinstance(raw, dict) or not raw.get("id"):
        raise JobTreeError("Each card needs an id.")
    when = raw.get("when") or []
    hints = raw.get("hints") or []
    if not isinstance(when, list) or not isinstance(hints, list):
        raise JobTreeError(f"Card {raw.get('id')!r} when/hints must be lists.")
    return Card(
        id=str(raw["id"]),
        title=str(raw.get("title") or raw["id"]),
        container=str(raw.get("container") or ""),
        overview=str(raw.get("overview") or ""),
        when=tuple(str(item) for item in when),
        reject=tuple(_reject(item) for item in (raw.get("reject") or [])),
        hints=tuple(str(item) for item in hints),
        facets=tuple(_facet(item) for item in (raw.get("facets") or [])),
        provisional=bool(raw.get("provisional")),
    )


def _container(raw: Any) -> Container:
    if not isinstance(raw, dict) or not raw.get("id"):
        raise JobTreeError("Each container needs an id.")
    aliases = raw.get("aliases") or []
    if not isinstance(aliases, list):
        raise JobTreeError(f"Container {raw.get('id')!r} aliases must be a list.")
    return Container(
        id=str(raw["id"]),
        title=str(raw.get("title") or raw["id"]),
        aliases=tuple(str(item) for item in aliases),
    )


def parse_job_tree(data: dict[str, Any]) -> JobTree:
    containers = tuple(_container(item) for item in (data.get("containers") or []))
    cards = tuple(_card(item) for item in (data.get("cards") or []))
    container_ids = [c.id for c in containers]
    card_ids = [c.id for c in cards]
    if container_ids != list(CONTAINER_IDS):
        raise JobTreeError(
            "jobs.json containers must be the locked seven, in lock order."
        )
    if card_ids != list(CARD_IDS):
        raise JobTreeError("jobs.json cards must be the locked thirteen, in lock order.")
    known_containers = set(CONTAINER_IDS)
    for card in cards:
        if card.container not in known_containers:
            raise JobTreeError(
                f"Card {card.id!r} container {card.container!r} is not locked."
            )
        for reject in card.reject:
            if reject.id not in CARD_IDS:
                raise JobTreeError(
                    f"Card {card.id!r} reject {reject.id!r} is not a Card."
                )
        for facet in card.facets:
            for leaf in facet.leaves:
                if leaf.id not in LEAF_IDS:
                    raise JobTreeError(
                        f"Card {card.id!r} minted leaf {leaf.id!r}."
                    )
    leaf_homes = [leaf.id for card in cards for facet in card.facets for leaf in facet.leaves]
    if sorted(leaf_homes) != sorted(LEAF_IDS):
        raise JobTreeError("Every working leaf must sit on exactly one Card.")
    if len(leaf_homes) != len(set(leaf_homes)):
        raise JobTreeError("A Leaf cannot sit on two Cards.")
    return JobTree(
        containers=containers,
        cards=cards,
    )


def empty_job_tree() -> JobTree:
    return JobTree(containers=(), cards=())


@lru_cache(maxsize=8)
def _load_job_tree(path: str) -> JobTree:
    jobs_file = Path(path)
    if not jobs_file.is_file():
        return empty_job_tree()
    data = json.loads(jobs_file.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise JobTreeError("catalog/jobs.json must be an object.")
    return parse_job_tree(data)


def load_job_tree(settings: Settings | None = None) -> JobTree:
    settings = settings or Settings.load()
    return _load_job_tree(str(_jobs_path(settings.catalog_path)))


def card_by_id(tree: JobTree, card_id: str) -> Card | None:
    for card in tree.cards:
        if card.id == card_id:
            return card
    return None


def container_by_id_or_alias(tree: JobTree, value: str) -> Container | None:
    for container in tree.containers:
        if container.id == value or value in container.aliases:
            return container
    return None


def leaves_for_card(card: Card) -> tuple[str, ...]:
    out: list[str] = []
    seen: set[str] = set()
    for facet in card.facets:
        for leaf in facet.leaves:
            if leaf.id not in seen:
                seen.add(leaf.id)
                out.append(leaf.id)
    return tuple(out)


def pointers_for_card(card: Card) -> tuple[str, ...]:
    """Cluster and leaf guideline_id pointers. Not rule bodies."""
    out: list[str] = []
    seen: set[str] = set()
    for facet in card.facets:
        for gid in facet.guideline_ids:
            if gid not in seen:
                seen.add(gid)
                out.append(gid)
        for leaf in facet.leaves:
            for gid in leaf.guideline_ids:
                if gid not in seen:
                    seen.add(gid)
                    out.append(gid)
    return tuple(out)


@dataclass(frozen=True)
class NeedScope:
    """How a need reaches rules: leaf tags and/or explicit guideline pointers."""

    tags: tuple[str, ...] = ()
    guideline_ids: tuple[str, ...] = ()

    @property
    def empty(self) -> bool:
        return not self.tags and not self.guideline_ids


def _alias_for_container(tree: JobTree, container_id: str) -> str | None:
    container = container_by_id_or_alias(tree, container_id)
    if container is None:
        return None
    return container.aliases[0] if container.aliases else None


def expand_need(need: str, tree: JobTree | None = None) -> list[str]:
    """Tags to match on guideline placement. Leaf ids expand to nothing."""
    job = (need or "").strip()
    if not job:
        return []
    tree = tree or load_job_tree()
    container = container_by_id_or_alias(tree, job)
    if container is not None:
        leaves: list[str] = []
        seen: set[str] = set()
        for card in tree.cards:
            if card.container != container.id:
                continue
            for leaf_id in leaves_for_card(card):
                if leaf_id not in seen:
                    seen.add(leaf_id)
                    leaves.append(leaf_id)
        if leaves:
            return leaves
        alias = _alias_for_container(tree, container.id)
        return [alias] if alias else []
    card = card_by_id(tree, job)
    if card is not None:
        leaves = list(leaves_for_card(card))
        if leaves:
            return leaves
        alias = _alias_for_container(tree, card.container)
        return [alias] if alias else []
    return []


def resolve_need(need: str, tree: JobTree | None = None) -> NeedScope:
    """Card/container → leaf tags plus cluster pointers. Leaf ids are empty."""
    job = (need or "").strip()
    if not job:
        return NeedScope()
    tree = tree or load_job_tree()
    container = container_by_id_or_alias(tree, job)
    if container is not None:
        tags: list[str] = []
        ids: list[str] = []
        tag_seen: set[str] = set()
        id_seen: set[str] = set()
        for card in tree.cards:
            if card.container != container.id:
                continue
            for leaf_id in leaves_for_card(card):
                if leaf_id not in tag_seen:
                    tag_seen.add(leaf_id)
                    tags.append(leaf_id)
            for gid in pointers_for_card(card):
                if gid not in id_seen:
                    id_seen.add(gid)
                    ids.append(gid)
        if tags or ids:
            return NeedScope(tags=tuple(tags), guideline_ids=tuple(ids))
        alias = _alias_for_container(tree, container.id)
        return NeedScope(tags=(alias,) if alias else ())
    card = card_by_id(tree, job)
    if card is not None:
        tags = list(leaves_for_card(card))
        ids = list(pointers_for_card(card))
        if tags or ids:
            return NeedScope(tags=tuple(tags), guideline_ids=tuple(ids))
        alias = _alias_for_container(tree, card.container)
        return NeedScope(tags=(alias,) if alias else ())
    return NeedScope()


def resolve_need_scope(
    jobs: str | list[str] | None,
    tree: JobTree | None = None,
) -> NeedScope | None:
    """None = no filter. Empty scope = provided need that matches nothing."""
    if jobs is None:
        return None
    raw = [jobs] if isinstance(jobs, str) else list(jobs)
    raw = [item.strip() for item in raw if item and str(item).strip()]
    if not raw:
        return None
    tree = tree or load_job_tree()
    tags: list[str] = []
    ids: list[str] = []
    tag_seen: set[str] = set()
    id_seen: set[str] = set()
    for item in raw:
        scope = resolve_need(item, tree)
        for tag in scope.tags:
            if tag not in tag_seen:
                tag_seen.add(tag)
                tags.append(tag)
        for gid in scope.guideline_ids:
            if gid not in id_seen:
                id_seen.add(gid)
                ids.append(gid)
    return NeedScope(tags=tuple(tags), guideline_ids=tuple(ids))


def resolve_job_tags(
    jobs: str | list[str] | None,
    tree: JobTree | None = None,
) -> list[str] | None:
    """None = no filter. [] = provided need that matches nothing."""
    scope = resolve_need_scope(jobs, tree)
    if scope is None:
        return None
    return list(scope.tags)
