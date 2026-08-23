from __future__ import annotations

WEEKS_PER_SEASON = 10
SEASONS = 16
CAREER_WEEKS = SEASONS * WEEKS_PER_SEASON

MATCH_WEEKS = frozenset({2, 3, 5, 6, 8, 9, 10})

# 03 §1 phase boundaries. Phase 1 is also how long his first contract runs: 02 ends the
# academy years with a placement, so the deal he starts on expires exactly there.
PHASE_1_SEASONS = 3
PHASE_2_SEASONS = 10


def season_of(week_index: int) -> int:
    return (week_index - 1) // WEEKS_PER_SEASON + 1


def week_of(week_index: int) -> int:
    return (week_index - 1) % WEEKS_PER_SEASON + 1


def age_of(week_index: int) -> int:
    """Age during the season. He turns 32 in the off-season after season 16."""
    return 15 + season_of(week_index)


def phase_of(week_index: int) -> int:
    season = season_of(week_index)
    if season <= PHASE_1_SEASONS:
        return 1
    if season <= PHASE_2_SEASONS:
        return 2
    return 3


def is_match_week(week_index: int) -> bool:
    return week_of(week_index) in MATCH_WEEKS
