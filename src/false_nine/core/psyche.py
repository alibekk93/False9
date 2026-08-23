from __future__ import annotations

# 03 §4 starting values. They live here rather than as literals in state.py so the
# deck and the tests read them from the same place.
STRESS_START = 20.0
HOPE_START = 75.0
CYNICISM_START = 10.0
SELF_KNOWLEDGE_START = 5.0

HOPE_DRIFT_FROM_SEASON = 5
HOPE_DRIFT_PER_SEASON = -0.8

# [TUNE] 07 §4 names seven mood words but no mapping. `strain` spans 0-300; a band of
# 30 puts a fresh 16-year-old on "steady" and a wrecked one on "done".
MOOD_BAND = 30.0


def season_drift(season: int) -> float:
    """03 §4: hope leaks from season 5. Nothing else in the game falls on its own."""
    return HOPE_DRIFT_PER_SEASON if season >= HOPE_DRIFT_FROM_SEASON else 0.0


def strain(stress: float, hope: float, cynicism: float) -> float:
    """0-300, higher is worse. The one number behind the Mood word (07 §4). Never
    shown: the player gets the word, and the word is true."""
    return stress + cynicism + (100.0 - hope)
