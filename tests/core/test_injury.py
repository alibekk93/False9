from __future__ import annotations

import collections
from dataclasses import replace

import pytest

from false_nine.core import stats
from false_nine.core.actions import PlayerAction, can_do, step
from false_nine.core.rng import Rng
from false_nine.core.state import GameState


def state(**kwargs: object) -> GameState:
    return replace(GameState(seed="t"), **kwargs)


def test_risk_composes_the_three_multipliers() -> None:
    base = stats.p_injury(0.02, fatigue=0.0, age=20, injury_history=0)
    assert base == pytest.approx(0.02)
    assert stats.p_injury(0.02, 81.0, 20, 0) == pytest.approx(0.02 * 1.8)
    assert stats.p_injury(0.02, 0.0, 26, 0) == pytest.approx(0.02 * 1.3)
    assert stats.p_injury(0.02, 0.0, 30, 0) == pytest.approx(0.02 * 1.7)
    assert stats.p_injury(0.02, 0.0, 20, 4) == pytest.approx(0.02 * 1.08)


def test_risk_is_not_multiplied_at_exactly_eighty() -> None:
    assert stats.p_injury(0.02, 80.0, 20, 0) == pytest.approx(0.02)


def test_severity_split_matches_the_spec() -> None:
    rng = Rng("severity")
    rolls = [stats.roll_injury(rng.stream("injury", i)) for i in range(4000)]
    counts = collections.Counter(injury.severity for injury in rolls)
    assert counts["minor"] / 4000 == pytest.approx(0.60, abs=0.03)
    assert counts["moderate"] / 4000 == pytest.approx(0.30, abs=0.03)
    assert counts["severe"] / 4000 == pytest.approx(0.10, abs=0.03)

    by_severity = {injury.severity: injury for injury in rolls}
    assert by_severity["minor"].physical_damage == 0.0
    assert by_severity["moderate"].physical_damage == 2.0
    assert by_severity["severe"].physical_damage == 6.0
    for injury in rolls:
        span = {"minor": (1, 2), "moderate": (3, 8), "severe": (12, 30)}
        assert span[injury.severity][0] <= injury.weeks <= span[injury.severity][1]


def test_injury_blocks_training_but_not_recovery() -> None:
    hurt = state(injury_weeks_left=3.0)
    assert not can_do(hurt, PlayerAction("train", "technique"))
    assert can_do(hurt, PlayerAction("recover"))
    assert step(hurt, PlayerAction("train", "technique"), Rng("t")).state == hurt


def test_recovery_speeds_healing_and_the_week_does_the_rest() -> None:
    healing = step(
        state(injury_weeks_left=4.0), PlayerAction("recover"), Rng("t")
    ).state
    assert healing.injury_weeks_left == 3.5

    passed = step(
        state(ap=0, injury_weeks_left=1.0), PlayerAction("end_week"), Rng("t")
    )
    assert passed.state.injury_weeks_left == 0.0
    assert not passed.state.is_injured


def test_injury_costs_physical_permanently() -> None:
    """The only irreversible stat loss in the game, and it is visible in the ledger."""
    rng = Rng("hurt")
    current = state(fatigue=95.0, physical=60.0)
    for _ in range(400):
        result = step(current, PlayerAction("train", "physical"), rng)
        damage = [
            e for e in result.effects if e.field == "physical" and e.after < e.before
        ]
        if damage:
            assert damage[0].before - damage[0].after in (2.0, 6.0)
            assert damage[0].reason in {
                "reason_injury_moderate",
                "reason_injury_severe",
            }
            return
        current = replace(result.state, ap=4, injury_weeks_left=0.0, fatigue=95.0)
    raise AssertionError("no injury in 400 high-fatigue training sessions")
