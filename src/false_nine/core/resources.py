from __future__ import annotations

from false_nine.core.state import GameState

BASE_AP = 4
AP_FLOOR = 2
AP_CEILING = 5
PHASE3_BONUS_SEASON = 13

FATIGUE_TRAIN = 12.0
FATIGUE_WORK = 8.0
FATIGUE_MATCH = 6.0
FATIGUE_RECOVER = -25.0
FATIGUE_PASSIVE = -8.0

STRESS_RECOVER = -6.0
STRESS_SOCIALISE = -8.0
STRESS_DRIFT_WITH_OBLIGATIONS = 5.0

SIDE_JOB_INCOME = 6_000
LIVING_COST = {1: 4_000, 2: 12_000, 3: 18_000}
DEBT_INTEREST = 0.03


def clamp01_100(value: float) -> float:
    """Fatigue and stress are bounded at both ends. Ability is not — see stats.py."""
    return max(0.0, min(100.0, value))


def ap_for_week(state: GameState) -> int:
    ap = BASE_AP
    if state.fatigue > 70:
        ap -= 1
    if state.stress > 80:
        ap -= 1
    if state.season >= PHASE3_BONUS_SEASON:
        ap += 1
    return max(AP_FLOOR, min(AP_CEILING, ap))


def living_cost(phase: int) -> int:
    return LIVING_COST[phase]


def apply_interest(debt: int) -> int:
    return round(debt * (1 + DEBT_INTEREST))
