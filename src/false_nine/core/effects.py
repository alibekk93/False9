from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from false_nine.core.state import GameState


@dataclass(frozen=True)
class Change:
    """One ledger row. `reason` is a key into data/strings/ui.json, never prose.

    Deliberately narrower than the tagged union in 04: every effect the game can
    produce so far is "a named quantity moved from X to Y because Z". A card's
    outcome text is not a Change — MatchScreen reads it off the card itself."""

    field: str
    before: float
    after: float
    reason: str


def update(
    state: GameState, effects: list[Change], reason: str, **values: Any
) -> GameState:
    """Set fields, recording a ledger row for each one that actually moved."""
    for field, after in values.items():
        before: float = getattr(state, field)
        if before != after:
            effects.append(Change(field, before, after, reason))
    return replace(state, **values)
