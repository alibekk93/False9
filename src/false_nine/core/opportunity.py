from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace

from false_nine.core.effects import Change, update
from false_nine.core.events import expr
from false_nine.core.resources import clamp01_100
from false_nine.core.rng import Rng
from false_nine.core.state import GameState

# 03 §7.4: the top of the achievable world is a mid-table second-tier club. Nothing
# aims above it, so a player already there is offered nothing further — not because a
# counter says he has had enough, but because there is no step up left to be offered.
# This, and the fact that `tier` moves nowhere else, is the whole of §7.1's enforcement.
TOP_TIER = 2

# [TUNE] §4 says hope falls and cynicism rises when a chance fails, and gives no values.
# These are what feed pool_flat and pool_bitter, so a career of near misses shows up in
# the hand rather than in the stats. Success is worth more hope than failure costs, and
# less cynicism than failure adds: he is easier to disappoint than to convince.
HOPE_ON_FAIL = -8.0
CYNICISM_ON_FAIL = 6.0
HOPE_ON_SUCCESS = 12.0
CYNICISM_ON_SUCCESS = -4.0


@dataclass(frozen=True)
class WorldCondition:
    """One thing that has to go his way and that he has no hand in. `reveal_week` is
    what makes the failure ordinary rather than cruel (03 §7.2): it resolves early and
    he is told during the arc, not at the end."""

    id: str
    p: float
    reveal_week: int
    fail_event: str


@dataclass(frozen=True)
class Opportunity:
    id: str
    season: int
    window_weeks: tuple[int, int]
    player_conditions: tuple[expr.Expr, ...]
    world_conditions: tuple[WorldCondition, ...]
    success_event: str
    fail_event_player: str


def due(
    state: GameState, opportunities: Mapping[str, Opportunity]
) -> Opportunity | None:
    """The arc that opens this week, if one does. 03 §7.5 fixes the schedule; the tier
    check is §7.4's ceiling and the only gate."""
    if state.tier <= TOP_TIER or state.opportunity_id:
        return None
    for opp in sorted(opportunities.values(), key=lambda o: o.id):
        if opp.season == state.season and opp.window_weeks[0] == state.week:
            return opp
    return None


def activate(state: GameState, opp: Opportunity, rng: Rng) -> GameState:
    """03 §7.2: every world condition is rolled here, at the top of the arc, because
    this is the week they become fictionally true. None of them is rerolled, and none
    of them waits until the end — the dice are thrown before he has done anything, and
    what he does afterwards cannot change them. That is the honest version."""
    stream = rng.stream("opportunity", opp.id)
    failed = tuple(c.id for c in opp.world_conditions if stream.random() >= c.p)
    return replace(
        state, opportunity_id=opp.id, opportunity_failed=failed, opportunity_revealed=()
    )


def reveal(state: GameState, opp: Opportunity, effects: list[Change]) -> GameState:
    """Each condition tells him in its own week.

    ponytail: the first failure he hears about ends the arc, which caps a career at six
    scenes out of the twelve-plus authored and keeps them unique for free. If M6 says
    the arcs end too abruptly, fire every revealed failure and dedupe across the career.
    """
    for condition in opp.world_conditions:
        if condition.reveal_week != state.week:
            continue
        if condition.id in state.opportunity_revealed:
            continue
        state = replace(
            state, opportunity_revealed=(*state.opportunity_revealed, condition.id)
        )
        if condition.id in state.opportunity_failed:
            return _fail(state, effects, _scene(state, opp))
    return state


def resolve(state: GameState, opp: Opportunity, effects: list[Change]) -> GameState:
    """The end of the window. A world condition that failed without ever reaching a
    reveal week still fails the arc — it just does so without a scene of its own."""
    if state.opportunity_failed:
        return _fail(state, effects, _scene(state, opp))
    if all(expr.evaluate(cond, state) for cond in opp.player_conditions):
        return _succeed(state, opp, effects)
    # He was not ready. 03 §7.3 holds here too: this failure gets a name of its own,
    # authored per opportunity, so it can never repeat inside one career.
    return _fail(state, effects, opp.fail_event_player)


def _scene(state: GameState, opp: Opportunity) -> str:
    """The earliest-revealed failure whose scene he has not already lived through.

    If every one of them has been told, the last is told again and
    `test_failure_scenes_unique_per_career` says so. That is a content shortage and the
    fix is another authored scene — never a line of code that hides the repeat.
    """
    failed = [
        c
        for c in sorted(opp.world_conditions, key=lambda c: (c.reveal_week, c.id))
        if c.id in state.opportunity_failed
    ]
    for condition in failed:
        if condition.fail_event not in state.failure_scenes_seen:
            return condition.fail_event
    return failed[-1].fail_event


def _fail(state: GameState, effects: list[Change], scene: str) -> GameState:
    state = update(
        state,
        effects,
        "reason_opportunity_failed",
        hope=clamp01_100(state.hope + HOPE_ON_FAIL),
        cynicism=clamp01_100(state.cynicism + CYNICISM_ON_FAIL),
    )
    return replace(
        state,
        opportunity_id="",
        opportunity_failed=(),
        opportunity_revealed=(),
        failure_scenes_seen=(*state.failure_scenes_seen, scene),
        pending_events=(*state.pending_events, scene),
    )


def _succeed(state: GameState, opp: Opportunity, effects: list[Change]) -> GameState:
    """03 §7.4: one tier at most, to a club that is itself precarious. The move is not
    instant — the contract ends and the window at the end of the season does the rest,
    which is how it happens."""
    state = update(
        state,
        effects,
        "reason_opportunity_taken",
        tier=state.tier - 1,
        hope=clamp01_100(state.hope + HOPE_ON_SUCCESS),
        cynicism=clamp01_100(state.cynicism + CYNICISM_ON_SUCCESS),
        contract_seasons_left=0,
    )
    return replace(
        state,
        opportunity_id="",
        opportunity_failed=(),
        opportunity_revealed=(),
        opportunities_converted=state.opportunities_converted + 1,
        pending_events=(*state.pending_events, opp.success_event),
    )
