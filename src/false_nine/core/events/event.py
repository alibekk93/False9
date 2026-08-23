from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from false_nine.core.events import expr

# 05 §1. Choices are 2-4 because the UI does not scroll.
MIN_CHOICES = 2
MAX_CHOICES = 4

Effect = Mapping[str, Any]


@dataclass(frozen=True)
class Choice:
    """`requires` gates the choice but never hides it — 05 §1: a gated choice is shown
    greyed with its reason, because seeing what you can't do is part of the design."""

    id: str
    text: str
    outcome_text: str
    effects: tuple[Effect, ...] = ()
    requires: expr.Expr | None = None

    def is_open(self, state: object) -> bool:
        return self.requires is None or expr.evaluate(self.requires, state)


@dataclass(frozen=True)
class Event:
    """M4 fires events by id only. Pools, weights, cooldowns and `repeatable` are in
    the authored schema and are not read here: nothing selects an event at random
    until M5, and a field the validator cannot exercise is worse than none."""

    id: str
    body: tuple[str, ...]
    choices: tuple[Choice, ...]
    location: str = ""
    time_of_day: str = ""
