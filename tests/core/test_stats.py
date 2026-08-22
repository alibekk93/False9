from __future__ import annotations

import statistics
from dataclasses import replace

import pytest

from false_nine.core import stats
from false_nine.core.actions import PlayerAction, step
from false_nine.core.rng import Rng
from false_nine.core.state import GameState
from tools.sim import run_career, train_max

RNG = Rng("t")
AGE_26_WEEK = 101  # season 11, the first week he is 26


@pytest.mark.parametrize(
    ("age", "expected"),
    [(16, 1.4), (19, 1.4), (20, 1.0), (24, 1.0), (25, 0.6), (28, 0.6), (29, 0.25)],
)
def test_age_factor_bands(age: int, expected: float) -> None:
    assert stats.age_factor(age) == expected


@pytest.mark.parametrize(
    ("fatigue", "expected"),
    [(0.0, 1.0), (49.9, 1.0), (50.0, 0.6), (74.9, 0.6), (75.0, 0.25)],
)
def test_fatigue_factor_bands(fatigue: float, expected: float) -> None:
    assert stats.fatigue_factor(fatigue) == expected


def test_gain_shrinks_as_the_stat_rises() -> None:
    gains = [stats.training_gain(s, age=20, fatigue=0.0) for s in (20, 50, 80, 95)]
    assert gains == sorted(gains, reverse=True)
    assert gains[-1] > 0  # diminishing, never zero — there is no wall, only a slope


def test_gain_never_goes_negative_above_100() -> None:
    """No ceiling exists, so the formula stays defined past 100 rather than clamping."""
    assert stats.training_gain(105.0, age=20, fatigue=0.0) == 0.0


def test_ability_is_the_weighted_mean() -> None:
    state = GameState(seed="t", technique=80.0, physical=60.0, mental=40.0)
    assert state.ability == pytest.approx(0.4 * 80 + 0.35 * 60 + 0.25 * 40)


@pytest.mark.parametrize(
    ("age", "expected"),
    [(26, (0.0, 0.0)), (28, (0.0, 1.2)), (29, (0.0, 1.2)), (30, (0.4, 1.2))],
)
def test_decay_starts_after_the_peak(age: int, expected: tuple[float, float]) -> None:
    assert stats.season_decay(age) == expected


def test_decay_applies_at_the_season_boundary() -> None:
    # week_index 150 is season 15 week 10; he is 30.
    before = replace(
        GameState(seed="t"), week_index=150, ap=0, technique=60.0, physical=60.0
    )
    after = step(before, PlayerAction("end_week"), RNG).state
    assert (after.technique, after.physical) == (59.6, 58.8)


def test_training_lifts_the_chosen_stat_only() -> None:
    before = GameState(seed="t")
    after = step(before, PlayerAction("train", "technique"), RNG).state
    assert after.technique > before.technique
    assert (after.physical, after.mental) == (before.physical, before.mental)
    assert after.fatigue == 12.0


def test_training_curve_shape() -> None:
    """The acceptance test for M1. A protagonist who trains as hard as the body allows
    and ignores money entirely is in the 70s at 26 — never the 90s — and no line of
    code clamps him there. See 03 §3.1."""
    finals = [
        run_career(f"curve{i}", train_max, until_week=AGE_26_WEEK).ability
        for i in range(40)
    ]
    assert 70.0 <= statistics.median(finals) < 80.0
    assert max(finals) < 85.0
    assert min(finals) > 55.0  # injury luck costs a few points, not a career


def test_no_stat_ceiling_exists_in_the_formula() -> None:
    """Feed the curve absurd training time. A clamp would park him on a round number;
    the curve walks him past 100 instead. The ceiling is the world, not the formula."""
    stat = 60.0
    for _ in range(500):
        stat += stats.training_gain(stat, age=18, fatigue=0.0)
    assert stat > 100.0
    assert stats.training_gain(99.9, age=18, fatigue=0.0) > 0.0
