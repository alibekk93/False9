from __future__ import annotations

from dataclasses import replace

import pytest

from false_nine.content import cards
from false_nine.core import resources
from false_nine.core.actions import PlayerAction, step
from false_nine.core.rng import Rng
from false_nine.core.state import GameState
from tools.sim import run_career, train_max

RNG = Rng("t")


def state(**kwargs: object) -> GameState:
    return replace(GameState(seed="t"), **kwargs)


# (fatigue, stress, week_index, expected ap)
AP_CASES = [
    (0.0, 0.0, 1, 4),
    (71.0, 0.0, 1, 3),
    (70.0, 0.0, 1, 4),  # strictly greater, per 03 §2.1
    (0.0, 81.0, 1, 3),
    (0.0, 80.0, 1, 4),
    (71.0, 81.0, 1, 2),
    (0.0, 0.0, 121, 5),  # season 13
    (71.0, 81.0, 121, 3),
    (100.0, 100.0, 111, 2),  # season 12: no bonus, floor holds
]


@pytest.mark.parametrize(("fatigue", "stress", "week_index", "expected"), AP_CASES)
def test_ap_modifiers(
    fatigue: float, stress: float, week_index: int, expected: int
) -> None:
    assert (
        resources.ap_for_week(
            state(fatigue=fatigue, stress=stress, week_index=week_index)
        )
        == expected
    )


def test_living_cost_by_phase() -> None:
    assert (resources.living_cost(1), resources.living_cost(2)) == (4_000, 12_000)
    assert resources.living_cost(3) == 18_000


def test_debt_interest_compounds_at_three_percent() -> None:
    assert resources.apply_interest(100_000) == 103_000
    assert resources.apply_interest(0) == 0
    assert isinstance(resources.apply_interest(41_000), int)


def test_fatigue_clamps_at_both_ends() -> None:
    assert resources.clamp01_100(-10.0) == 0.0
    assert resources.clamp01_100(140.0) == 100.0


def test_work_pays_and_tires() -> None:
    after = step(state(), PlayerAction("work"), RNG, {}).state
    assert after.money == 6_000
    assert after.fatigue == 8.0
    assert after.ap == 3


def test_recover_sheds_fatigue_and_stress() -> None:
    after = step(
        state(fatigue=40.0, stress=30.0), PlayerAction("recover"), RNG, {}
    ).state
    assert (after.fatigue, after.stress) == (15.0, 24.0)


def test_socialise_only_touches_stress() -> None:
    before = state(stress=30.0)
    after = step(before, PlayerAction("socialise"), RNG, {}).state
    assert after.stress == 22.0
    assert (after.technique, after.fatigue, after.money) == (
        before.technique,
        before.fatigue,
        before.money,
    )


def test_deal_with_it_pays_what_it_can() -> None:
    after = step(state(money=5_000, debt=12_000), PlayerAction("deal_with_it"), RNG, {})
    assert (after.state.money, after.state.debt) == (0, 7_000)

    clears = step(
        state(money=20_000, debt=12_000), PlayerAction("deal_with_it"), RNG, {}
    )
    assert (clears.state.money, clears.state.debt) == (8_000, 0)


def test_deal_with_it_is_unavailable_without_debt() -> None:
    before = state(money=5_000)
    assert step(before, PlayerAction("deal_with_it"), RNG, {}).state == before


def test_drift_ends_the_week_and_stresses_only_when_owed() -> None:
    calm = step(state(stress=30.0), PlayerAction("drift"), RNG, {}).state
    assert (calm.ap, calm.stress) == (0, 30.0)

    owing = step(state(stress=30.0, debt=1_000), PlayerAction("drift"), RNG, {}).state
    assert (owing.ap, owing.stress) == (0, 35.0)


def test_week_end_charges_living_cost_and_converts_overdraft_to_debt() -> None:
    after = step(state(ap=0, money=1_000), PlayerAction("end_week"), RNG, {}).state
    assert after.money == 0
    assert after.debt == 3_000  # 4_000 living cost in phase 1, 1_000 covered
    assert after.week_index == 2


def test_week_end_charges_interest_before_new_debt_lands() -> None:
    after = step(
        state(ap=0, money=0, debt=100_000), PlayerAction("end_week"), RNG, {}
    ).state
    assert after.debt == 103_000 + 4_000


def test_week_end_refreshes_ap_and_sheds_passive_fatigue() -> None:
    after = step(state(ap=0, fatigue=30.0), PlayerAction("end_week"), RNG, {}).state
    assert (after.fatigue, after.ap) == (22.0, 4)


def test_end_week_needs_ap_spent_first() -> None:
    before = state(ap=2)
    assert step(before, PlayerAction("end_week"), RNG, {}).state == before


def test_money_and_debt_stay_integral_across_a_career() -> None:
    """Matches are in the loop now, so this runs through the harness rather than a
    hand-rolled loop that would stall on the first unplayed match."""
    for seed in range(4):
        final = run_career(f"ints{seed}", train_max, cards.load(), until_week=41).final
        assert isinstance(final.money, int) and isinstance(final.debt, int)
        assert final.debt >= 0 and final.money >= 0
