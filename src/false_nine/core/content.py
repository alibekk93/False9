from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from false_nine.core.club import Club
from false_nine.core.events.event import Event
from false_nine.core.match.card import Card
from false_nine.core.opportunity import Opportunity


@dataclass(frozen=True)
class Content:
    """Everything `data/` holds, in the one shape `step` takes.

    Core cannot read files, so authored content arrives as an argument. It arrives as
    one bundle rather than four mappings because M4 alone needs all four, and a module
    level registry would put mutable global state inside a function the whole test
    suite treats as pure."""

    cards: Mapping[str, Card] = field(default_factory=dict)
    clubs: Mapping[str, Club] = field(default_factory=dict)
    opportunities: Mapping[str, Opportunity] = field(default_factory=dict)
    events: Mapping[str, Event] = field(default_factory=dict)
