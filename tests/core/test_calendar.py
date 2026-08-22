from __future__ import annotations

import pytest

from false_nine.core.calendar import CAREER_WEEKS, is_match_week
from false_nine.core.state import GameState, advance_week

# week_index -> (season, week, age, phase)
BOUNDARIES = [
    (1, 1, 1, 16, 1),
    (10, 1, 10, 16, 1),
    (11, 2, 1, 17, 1),
    (30, 3, 10, 18, 1),
    (31, 4, 1, 19, 2),
    (100, 10, 10, 25, 2),
    (101, 11, 1, 26, 3),
    (160, 16, 10, 31, 3),
]


@pytest.mark.parametrize(("week_index", "season", "week", "age", "phase"), BOUNDARIES)
def test_calendar_boundaries(
    week_index: int, season: int, week: int, age: int, phase: int
) -> None:
    state = GameState(seed="t", week_index=week_index)
    assert (state.season, state.week, state.age, state.phase) == (
        season,
        week,
        age,
        phase,
    )


def test_match_weeks() -> None:
    played = [w for w in range(1, 11) if is_match_week(w)]
    assert played == [2, 3, 5, 6, 8, 9, 10]
    assert is_match_week(12) and not is_match_week(11)


def test_career_advances_to_the_end() -> None:
    state = GameState(seed="t")
    weeks = 0
    while not state.is_over:
        state = advance_week(state)
        weeks += 1
    assert weeks == CAREER_WEEKS
    assert state.week_index == CAREER_WEEKS + 1


def test_advance_does_not_mutate() -> None:
    state = GameState(seed="t")
    assert advance_week(state).week_index == 2
    assert state.week_index == 1
