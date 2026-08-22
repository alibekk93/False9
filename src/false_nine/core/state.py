from __future__ import annotations

from dataclasses import dataclass, replace

from false_nine.core import calendar


@dataclass(frozen=True)
class GameState:
    """The single source of truth. Only `week_index` is stored; season, week, age and
    phase are derived, so they cannot drift out of sync with each other.

    Fields are flat rather than nested so `save.load` can rebuild the state with
    `GameState(**snapshot)`. Psyche (M3) and club (M4) will want their own dataclasses;
    `stress` sits here alone until then."""

    seed: str
    week_index: int = 1

    technique: float = 30.0
    physical: float = 30.0
    mental: float = 20.0

    fatigue: float = 0.0
    stress: float = 20.0

    money: int = 0
    debt: int = 0

    ap: int = 4

    injury_weeks_left: float = 0.0
    injury_history: int = 0

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
    def ability(self) -> float:
        return 0.4 * self.technique + 0.35 * self.physical + 0.25 * self.mental

    @property
    def is_injured(self) -> bool:
        return self.injury_weeks_left > 0

    @property
    def is_over(self) -> bool:
        return self.week_index > calendar.CAREER_WEEKS


def advance_week(state: GameState) -> GameState:
    return replace(state, week_index=state.week_index + 1)
