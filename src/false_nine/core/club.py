from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace

from false_nine.core.effects import Change, update
from false_nine.core.resources import clamp01_100
from false_nine.core.rng import Stream
from false_nine.core.state import GameState

# 03 §6.2. `wage_offer` is what one payday pays, not a month or a season: the calendar
# has ten weeks and two paydays, and a per-payday figure is the only one both of those
# can be read against. A tier-4 club therefore pays 90,000 a season against Phase 2's
# 120,000 of living cost, which is why side work does not stop mattering.
PAYDAY_WEEKS = frozenset({5, 10})
PARTIAL_SHARE = 0.5

# [TUNE] §6.2 says solvency drifts down for tier 4-5 and gives no rate. Over a ten-week
# season these take a tier-5 club from 35 to 27, so folding is a thing that happens to a
# club he has been at for years rather than one he just signed for.
SOLVENCY_DRIFT = {4: -0.5, 5: -0.8}
FOLD_SOLVENCY = 10.0

ARREARS_LUMP_P = 0.30
UNPAID_STRESS = 8.0
UNPAID_CYNICISM = 4.0

# 03 §6.2 names this event; the id is a reference, not prose, so it belongs beside the
# rule that queues it rather than in a screen.
FOLD_EVENT = "ev_club_folds"

# [TUNE] §6.3 says 1-3 seasons and does not say what decides it. Tier does: the further
# down he is, the less anyone will commit to. Nothing here is a roll he cannot see.
CONTRACT_SEASONS = {2: 3, 3: 2, 4: 1, 5: 1}
OFFER_MIN = 1
OFFER_MAX = 3

# Training alone is the bottom of §3.1's facility range, not zero. He still trains.
UNEMPLOYED_FACILITIES = 0.5
# A club-less week still has a game in it somewhere, against nobody in particular.
UNATTACHED_STRENGTH = 30.0


@dataclass(frozen=True)
class Town:
    name: str
    population: int
    remoteness: float


@dataclass(frozen=True)
class Club:
    """05 §4. Everything here is fixed for the life of the career; what moves — his
    club's solvency, his wage, what he is owed — lives on GameState."""

    id: str
    name: str
    tier: int
    strength: float
    facilities: float
    solvency: float
    town: Town
    wage_offer: int
    traits: tuple[str, ...] = ()


def facilities(state: GameState, clubs: Mapping[str, Club]) -> float:
    club = clubs.get(state.club_id)
    return club.facilities if club is not None else UNEMPLOYED_FACILITIES


def strength(state: GameState, clubs: Mapping[str, Club]) -> float:
    club = clubs.get(state.club_id)
    return club.strength if club is not None else UNATTACHED_STRENGTH


def payday(state: GameState, stream: Stream, effects: list[Change]) -> GameState:
    """03 §6.2. `p_paid_in_full = solvency/100`; the spec names three outcomes and only
    that one probability.

    The remainder is split as two draws of the same solvency rather than evenly: the
    money has to exist, and then somebody has to find some of it. So `full = s`,
    `partial = (1-s)·s`, `nothing = (1-s)²`. An even split would have a club at
    solvency zero paying half a wage half the time, which is not what a club at
    solvency zero does — see 08 §8 on squads playing months without pay.
    """
    wage = state.contract_wage
    if wage <= 0:
        return state

    full = state.club_solvency / 100.0
    roll = stream.random()
    if roll < full:
        paid = wage
    elif roll < full + (1.0 - full) * full:
        paid = round(wage * PARTIAL_SHARE)
    else:
        paid = 0

    if paid:
        state = update(state, effects, "reason_wages", money=state.money + paid)
    if paid < wage:
        state = update(
            state,
            effects,
            "reason_wages_unpaid",
            arrears=state.arrears + (wage - paid),
            stress=clamp01_100(state.stress + UNPAID_STRESS),
            cynicism=clamp01_100(state.cynicism + UNPAID_CYNICISM),
        )
    return state


def drift_solvency(state: GameState, clubs: Mapping[str, Club]) -> GameState:
    """No ledger row: a club running out of money is not something that happens to him,
    and he learns it the way anybody does, on a payday that does not arrive."""
    club = clubs.get(state.club_id)
    drift = SOLVENCY_DRIFT.get(club.tier, 0.0) if club is not None else 0.0
    if not drift:
        return state
    return replace(state, club_solvency=clamp01_100(state.club_solvency + drift))


def has_folded(state: GameState) -> bool:
    return bool(state.club_id) and state.club_solvency < FOLD_SOLVENCY


def fold(state: GameState, effects: list[Change]) -> GameState:
    """03 §6.2: the contract ends mid-season and the arrears go with it. Written off is
    not paid off — the money is simply gone, and no line item says who has it."""
    state = update(state, effects, "reason_club_folded", arrears=0, contract_wage=0)
    return replace(
        state, club_id="", club_solvency=0.0, contract_seasons_left=0, offers=()
    )


def season_end(state: GameState, stream: Stream, effects: list[Change]) -> GameState:
    if state.arrears > 0 and stream.random() < ARREARS_LUMP_P:
        state = update(
            state,
            effects,
            "reason_arrears_paid",
            money=state.money + state.arrears,
            arrears=0,
        )
    if state.contract_seasons_left > 0:
        state = update(
            state,
            effects,
            "reason_season_end",
            contract_seasons_left=state.contract_seasons_left - 1,
        )
    return state


def offers(
    state: GameState, clubs: Mapping[str, Club], stream: Stream
) -> tuple[str, ...]:
    """1-3 clubs at the tier he has, sorted so the list does not depend on sample order.
    Nothing here reads ability: what tier will have him is 03 §7's business, not his."""
    eligible = sorted(club.id for club in clubs.values() if club.tier == state.tier)
    if not eligible:
        return ()
    count = min(len(eligible), stream.randint(OFFER_MIN, OFFER_MAX))
    return tuple(sorted(stream.sample(eligible, count)))


def sign(state: GameState, club: Club, effects: list[Change]) -> GameState:
    """Re-signing where he already is keeps the solvency he has watched slide, rather
    than handing the club a fresh set of books. Staying put is how a club folds under
    him; a new club starts from its own number because it is a different club."""
    solvency = state.club_solvency if club.id == state.club_id else club.solvency
    state = update(
        state,
        effects,
        "reason_signed",
        contract_wage=club.wage_offer,
        contract_seasons_left=CONTRACT_SEASONS[club.tier],
    )
    return replace(state, club_id=club.id, club_solvency=solvency, offers=())
