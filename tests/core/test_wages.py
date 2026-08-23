from __future__ import annotations

import random
from dataclasses import replace

from false_nine.core import club
from false_nine.core.actions import PlayerAction, step
from false_nine.core.content import Content
from false_nine.core.effects import Change
from false_nine.core.rng import Rng
from false_nine.core.state import GameState

RNG = Rng("t")

ZARYA = club.Club(
    id="club_test_zarya",
    name="Zarya",
    tier=4,
    strength=38.0,
    facilities=0.6,
    solvency=40.0,
    town=club.Town(name="Test", population=60_000, remoteness=0.7),
    wage_offer=45_000,
)
UPTOWN = replace(ZARYA, id="club_test_uptown", tier=3, solvency=70.0, wage_offer=95_000)
CLUBS = {ZARYA.id: ZARYA, UPTOWN.id: UPTOWN}
CONTENT = Content(clubs=CLUBS)


def employed(**overrides: object) -> GameState:
    base = GameState(
        seed="t",
        tier=4,
        club_id=ZARYA.id,
        club_solvency=ZARYA.solvency,
        contract_wage=ZARYA.wage_offer,
        contract_seasons_left=1,
    )
    return replace(base, **overrides)


def paid(state: GameState, roll: float) -> tuple[int, int]:
    """One payday against a stream pinned to a known roll, so the three-way split in
    03 §6.2 is checked at its boundaries rather than sampled."""
    stream = random.Random()
    stream.random = lambda: roll  # type: ignore[method-assign]
    after = club.payday(state, stream, [])
    return after.money, after.arrears


def test_payday_pays_in_full_below_the_solvency_line() -> None:
    assert paid(employed(club_solvency=40.0), 0.39) == (45_000, 0)


def test_payday_pays_half_in_the_middle_band() -> None:
    """03 §6.2 names three outcomes and one probability. The rest is two draws of the
    same solvency, so at 40 the half-pay band runs from 0.40 to 0.64."""
    assert paid(employed(club_solvency=40.0), 0.55) == (22_500, 22_500)
    assert paid(employed(club_solvency=40.0), 0.65) == (0, 45_000)


def test_payday_pays_nothing_in_the_top_band() -> None:
    assert paid(employed(club_solvency=40.0), 0.85) == (0, 45_000)


def test_a_solvent_club_always_pays_and_a_broke_one_never_does() -> None:
    for roll in (0.0, 0.5, 0.999):
        assert paid(employed(club_solvency=100.0), roll) == (45_000, 0)
        assert paid(employed(club_solvency=0.0), roll) == (0, 45_000)


def test_an_unpaid_wage_costs_stress_and_cynicism() -> None:
    stream = random.Random()
    stream.random = lambda: 0.99  # type: ignore[method-assign]
    before = employed(stress=20.0, cynicism=10.0)
    after = club.payday(before, stream, [])
    assert after.stress == before.stress + club.UNPAID_STRESS
    assert after.cynicism == before.cynicism + club.UNPAID_CYNICISM


def test_no_contract_means_no_payday_at_all() -> None:
    idle = employed(club_id="", contract_wage=0)
    assert paid(idle, 0.0) == (0, 0)


def test_arrears_accumulate_across_paydays() -> None:
    stream = random.Random()
    stream.random = lambda: 0.99  # type: ignore[method-assign]
    state = employed()
    for _ in range(3):
        state = club.payday(state, stream, [])
    assert state.arrears == 3 * 45_000


def test_solvency_drifts_only_in_the_lower_tiers() -> None:
    lower = club.drift_solvency(employed(), CLUBS)
    assert lower.club_solvency == 40.0 + club.SOLVENCY_DRIFT[4]

    higher = employed(club_id=UPTOWN.id, tier=3)
    assert club.drift_solvency(higher, CLUBS).club_solvency == higher.club_solvency


def test_a_folded_club_takes_the_arrears_with_it() -> None:
    """03 §6.2: written off is not paid off. The money is gone and he is unattached."""
    dying = employed(club_solvency=club.FOLD_SOLVENCY - 1, arrears=80_000)
    assert club.has_folded(dying)
    gone = club.fold(dying, [])
    assert gone.arrears == 0
    assert gone.money == dying.money  # nobody paid it
    assert not gone.is_employed
    assert gone.contract_seasons_left == 0


def test_offers_come_from_his_own_tier_only() -> None:
    for seed in range(20):
        offers = club.offers(employed(), CLUBS, random.Random(seed))
        assert offers == (ZARYA.id,), offers


def test_offers_are_deterministic_for_a_given_stream() -> None:
    state = employed(tier=3)
    a = club.offers(state, CLUBS, random.Random(1))
    b = club.offers(state, CLUBS, random.Random(1))
    assert a == b


def test_signing_takes_the_club_terms_and_clears_the_offers() -> None:
    state = employed(tier=3, offers=(UPTOWN.id,))
    signed = club.sign(state, UPTOWN, [])
    assert signed.club_id == UPTOWN.id
    assert signed.contract_wage == UPTOWN.wage_offer
    assert signed.contract_seasons_left == club.CONTRACT_SEASONS[UPTOWN.tier]
    assert signed.offers == ()


def test_re_signing_keeps_the_solvency_he_has_watched_slide() -> None:
    """A new club starts from its own books. Staying put does not reset them, which is
    the only way a club he has been at for years can fold under him."""
    worn = employed(club_solvency=18.0, offers=(ZARYA.id,))
    assert club.sign(worn, ZARYA, []).club_solvency == 18.0
    assert club.sign(worn, UPTOWN, []).club_solvency == UPTOWN.solvency


def test_the_week_cannot_end_while_a_contract_is_unsigned() -> None:
    """An offer blocks the week the way an unplayed match does — 09 M4 puts the
    decision on SeasonScreen, and the week is not over until it is made."""
    waiting = employed(ap=0, offers=(ZARYA.id,))
    assert (
        not step(waiting, PlayerAction("end_week"), RNG, CONTENT).state.week_index > 1
    )

    signed = step(waiting, PlayerAction("sign", ZARYA.id), RNG, CONTENT).state
    assert signed.offers == ()
    assert step(signed, PlayerAction("end_week"), RNG, CONTENT).state.week_index == 2


def test_wages_reach_the_ledger_with_a_reason() -> None:
    effects: list[Change] = []
    stream = random.Random()
    stream.random = lambda: 0.0  # type: ignore[method-assign]
    club.payday(employed(), stream, effects)
    assert [c.reason for c in effects] == ["reason_wages"]


def test_facilities_fall_back_when_he_has_no_club() -> None:
    assert club.facilities(employed(), CLUBS) == ZARYA.facilities
    assert club.facilities(employed(club_id=""), CLUBS) == club.UNEMPLOYED_FACILITIES
