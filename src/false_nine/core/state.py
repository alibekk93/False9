from __future__ import annotations

from dataclasses import dataclass, replace

from false_nine.core import calendar


@dataclass(frozen=True)
class GameState:
    """The single source of truth. Only `week_index` is stored; the rest is derived,
    so season, week, age, and phase cannot drift out of sync with each other."""

    seed: str
    week_index: int = 1

    @property
    def season(self) -> int:
        return calendar.season_of(self.week_index)

    @property
    def week(self) -> int:
        return calendar.week_of(self.week_index)

    @property
    def age(self) -> int:
        return calendar.age_of(self.week_index)

    @property
    def phase(self) -> int:
        return calendar.phase_of(self.week_index)

    @property
    def is_over(self) -> bool:
        return self.week_index > calendar.CAREER_WEEKS


def advance_week(state: GameState) -> GameState:
    return replace(state, week_index=state.week_index + 1)
