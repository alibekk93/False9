from __future__ import annotations

import json
from functools import cache
from typing import Any

from false_nine.content import npcs as npc_content
from false_nine.content.cards import ContentError, check_keys
from false_nine.content.strings import DATA
from false_nine.core.events import apply, expr
from false_nine.core.events.event import MAX_CHOICES, MIN_CHOICES, Choice, Event
from false_nine.core.state import GameState

# 05 §1 authors more than M4 reads: `pools`, `weight`, `repeatable` and `cooldown_weeks`
# only mean something once events are selected rather than fired by id, which is M5.
# They are accepted and ignored so the corpus can be written once.
EVENT_KEYS = frozenset(
    {
        "id",
        "pools",
        "tags",
        "weight",
        "repeatable",
        "cooldown_weeks",
        "requires",
        "scene",
        "choices",
        "notes",
    }
)
SCENE_KEYS = frozenset({"location", "time_of_day", "body"})
CHOICE_KEYS = frozenset({"id", "text", "requires", "effects", "outcome_text"})

EVENT_DIRS = ("opportunity_fail", "club", "opportunity_success")


@cache
def load() -> dict[str, Event]:
    probe = _probe()
    npcs = frozenset(npc_content.load())
    events: dict[str, Event] = {}
    for folder in EVENT_DIRS:
        for path in sorted((DATA / "events" / folder).glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            for raw in payload["items"]:
                event = _event(raw, path.name, probe, npcs)
                if event.id in events:
                    raise ContentError(f"{path.name}: duplicate event id {event.id}")
                events[event.id] = event
    if not events:
        raise ContentError(f"no events found under {DATA / 'events'}")
    return events


def _probe() -> GameState:
    """A real state to resolve authored paths against. The bonds are what make a
    `relationships.npc_x.trust` path checkable at all — the ids live in `data/` and no
    dataclass field names them. 05 §5: a typo is a startup error, not a silent False."""
    return GameState(seed="probe", relationships=npc_content.starting_bonds())


def _event(
    raw: dict[str, Any], where: str, probe: GameState, npcs: frozenset[str]
) -> Event:
    event_id = raw.get("id", "<no id>")
    where = f"{where}: {event_id}"
    check_keys(raw, EVENT_KEYS, where)
    if not str(event_id).startswith("ev_"):
        raise ContentError(f"{where} does not start with ev_")

    if "requires" in raw:
        expr.validate(raw["requires"], probe, where)

    scene = raw["scene"]
    check_keys(scene, SCENE_KEYS, f"{where}: scene")
    body = tuple(scene["body"])
    if not body:
        raise ContentError(f"{where}: scene has no body")

    choices = tuple(_choice(c, where, probe, npcs) for c in raw["choices"])
    if not MIN_CHOICES <= len(choices) <= MAX_CHOICES:
        raise ContentError(f"{where}: {len(choices)} choices, not 2-4 (05 §1)")
    ids = {choice.id for choice in choices}
    if len(ids) != len(choices):
        raise ContentError(f"{where}: duplicate choice ids")
    # A scene every choice gates out is a scene nobody can leave. 05 §1 greys the
    # closed ones, which only works while one of them is open.
    if all(choice.requires is not None for choice in choices):
        raise ContentError(f"{where}: every choice is gated, so none can be taken")

    return Event(
        id=raw["id"],
        body=body,
        choices=choices,
        location=scene.get("location", ""),
        time_of_day=scene.get("time_of_day", ""),
    )


def _choice(
    raw: dict[str, Any], where: str, probe: GameState, npcs: frozenset[str]
) -> Choice:
    choice_id = raw.get("id", "<no id>")
    where = f"{where}/{choice_id}"
    check_keys(raw, CHOICE_KEYS, where)
    # 05 §1: a choice without consequence text feels broken even when the mechanical
    # effect is real, so it is required rather than defaulted.
    if not raw.get("outcome_text"):
        raise ContentError(f"{where}: outcome_text is required")

    requires = raw.get("requires")
    if requires is not None:
        expr.validate(requires, probe, where)

    return Choice(
        id=raw["id"],
        text=raw["text"],
        outcome_text=raw["outcome_text"],
        effects=apply.validate(raw.get("effects", []), npcs, where),
        requires=requires,
    )
