from __future__ import annotations

from dataclasses import replace
from typing import Any

from false_nine.core import relationships, stats
from false_nine.core.effects import Change, update
from false_nine.core.events.event import Effect
from false_nine.core.resources import clamp01_100
from false_nine.core.state import AXES, GameState

# 05 §2 lists twelve effect types. These are the ones M4's authored scenes use;
# `injury`, `unlock_pool` and `queue_event` have no caller until M7 and M5, and an
# effect the validator cannot exercise is worse than none. Unknown types raise at
# load time, so a scene authored against a type that does not exist yet fails on
# startup rather than on the week it fires.
EFFECT_TYPES = frozenset(
    {"stat", "psyche", "money", "debt", "fatigue", "relationship", "flag", "club"}
)
PSYCHE_KEYS = frozenset({"stress", "hope", "cynicism", "self_knowledge"})
STAT_KEYS = frozenset({"technique", "physical", "mental"})
CLUB_KEYS = frozenset({"solvency"})


def apply(
    state: GameState, effects: list[Change], reason: str, items: tuple[Effect, ...]
) -> GameState:
    for item in items:
        state = _one(state, effects, reason, item)
    return state


def _one(
    state: GameState, effects: list[Change], reason: str, item: Effect
) -> GameState:
    kind = item["type"]
    if kind == "psyche":
        key = item["key"]
        moved = clamp01_100(_current(state, key) + float(item["delta"]))
        return update(state, effects, reason, **{key: moved})
    if kind == "stat":
        key = item["key"]
        # Ability has a floor and no ceiling. See stats.STAT_FLOOR and 03 §7.1.
        moved = max(stats.STAT_FLOOR, _current(state, key) + float(item["delta"]))
        return update(state, effects, reason, **{key: moved})
    if kind == "fatigue":
        moved = clamp01_100(state.fatigue + float(item["delta"]))
        return update(state, effects, reason, fatigue=moved)
    if kind == "money":
        return update(state, effects, reason, money=state.money + int(item["delta"]))
    if kind == "debt":
        owed = max(0, state.debt + int(item["delta"]))
        return update(state, effects, reason, debt=owed)
    if kind == "relationship":
        return relationships.adjust(
            state, effects, item["npc"], item["key"], float(item["delta"]), reason
        )
    if kind == "club":
        return update(
            state,
            effects,
            reason,
            club_solvency=clamp01_100(_club_value(state, item)),
        )
    return _flag(state, item)


def _current(state: GameState, key: str) -> float:
    value: float = getattr(state, key)
    return value


def _club_value(state: GameState, item: Effect) -> float:
    if "set" in item:
        return float(item["set"])
    return state.club_solvency + float(item["delta"])


def _flag(state: GameState, item: Effect) -> GameState:
    """A flag is not a quantity, so it gets no ledger row. Stored sorted so two
    careers that set the same flags in a different order still compare equal."""
    if "set" in item:
        return replace(state, flags=tuple(sorted({*state.flags, item["set"]})))
    return replace(state, flags=tuple(f for f in state.flags if f != item["clear"]))


def validate(items: Any, npcs: frozenset[str], where: str) -> tuple[Effect, ...]:
    if not isinstance(items, list):
        raise ValueError(f"{where}: effects must be a list")
    for item in items:
        _validate_one(item, npcs, where)
    return tuple(items)


def _validate_one(item: Any, npcs: frozenset[str], where: str) -> None:
    if not isinstance(item, dict) or "type" not in item:
        raise ValueError(f"{where}: effect needs a type, got {item!r}")
    kind = item["type"]
    if kind not in EFFECT_TYPES:
        raise ValueError(f"{where}: effect type {kind!r} is not supported yet")

    if kind == "flag":
        if len(item) != 2 or not ({"set", "clear"} & set(item)):
            raise ValueError(f"{where}: flag takes exactly one of set/clear")
        return
    if kind == "club":
        if item.get("key") not in CLUB_KEYS:
            raise ValueError(f"{where}: club key {item.get('key')!r} is not writable")
        if ("set" in item) == ("delta" in item):
            raise ValueError(f"{where}: club takes exactly one of set/delta")
        return

    if "delta" not in item:
        raise ValueError(f"{where}: {kind} needs a delta")
    if kind == "psyche" and item.get("key") not in PSYCHE_KEYS:
        raise ValueError(f"{where}: unknown psyche key {item.get('key')!r}")
    if kind == "stat" and item.get("key") not in STAT_KEYS:
        raise ValueError(f"{where}: unknown stat key {item.get('key')!r}")
    if kind == "relationship":
        if item.get("npc") not in npcs:
            raise ValueError(f"{where}: unknown npc {item.get('npc')!r}")
        if item.get("key") not in AXES:
            raise ValueError(f"{where}: unknown axis {item.get('key')!r}")
