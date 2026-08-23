from __future__ import annotations

from dataclasses import replace

from false_nine.core import opportunity
from false_nine.core.opportunity import Opportunity, WorldCondition
from false_nine.core.rng import Rng
from false_nine.core.state import GameState

SEASON = 5
OPENS, CLOSES = 3, 8


def condition(name: str, p: float, week: int) -> WorldCondition:
    return WorldCondition(id=name, p=p, reveal_week=week, fail_event=f"ev_{name}")


ARC = Opportunity(
    id="opp_test",
    season=SEASON,
    window_weeks=(OPENS, CLOSES),
    player_conditions=({"path": "ability", "op": ">=", "value": 40},),
    world_conditions=(
        condition("early", 0.6, 4),
        condition("middle", 0.6, 6),
        condition("late", 0.6, 7),
        condition("last", 0.6, 8),
    ),
    success_event="ev_signed",
    fail_event_player="ev_not_ready",
)
ARCS = {ARC.id: ARC}


def at(week: int, **overrides: object) -> GameState:
    """Season 5 of a career, at a chosen week inside it."""
    base = GameState(seed="t", week_index=(SEASON - 1) * 10 + week, tier=4)
    return replace(base, **overrides)


def test_an_arc_opens_on_the_first_week_of_its_window() -> None:
    assert opportunity.due(at(OPENS), ARCS) is ARC
    assert opportunity.due(at(OPENS + 1), ARCS) is None
    assert opportunity.due(at(OPENS, week_index=OPENS), ARCS) is None  # wrong season


def test_nothing_is_offered_at_the_top_of_the_world() -> None:
    """03 §7.4: converting moves him one tier and nothing aims above the second. At
    the ceiling there is no step up to be offered — which is the whole of §7.1's
    enforcement, and there is no counter of conversions anywhere in it."""
    assert opportunity.due(at(OPENS, tier=opportunity.TOP_TIER), ARCS) is None
    assert opportunity.due(at(OPENS, tier=opportunity.TOP_TIER + 1), ARCS) is ARC


def test_one_arc_at_a_time() -> None:
    assert opportunity.due(at(OPENS, opportunity_id="opp_other"), ARCS) is None


def test_world_conditions_are_rolled_at_activation_and_never_again() -> None:
    """03 §7.2. The dice are thrown before he has done anything, and nothing he does
    afterwards rerolls them — the failure is a thing he can find out, not a surprise."""
    opened = opportunity.activate(at(OPENS), ARC, Rng("t"))
    assert opened.opportunity_id == ARC.id
    assert opened.opportunity_revealed == ()

    again = opportunity.activate(at(OPENS), ARC, Rng("t"))
    assert again.opportunity_failed == opened.opportunity_failed

    # And the roll does not depend on how good he is.
    strong = opportunity.activate(at(OPENS, technique=99.0), ARC, Rng("t"))
    assert strong.opportunity_failed == opened.opportunity_failed


def test_a_certain_arc_never_fails_and_an_impossible_one_always_does() -> None:
    certain = replace(
        ARC, world_conditions=tuple(replace(c, p=1.0) for c in ARC.world_conditions)
    )
    doomed = replace(
        ARC, world_conditions=tuple(replace(c, p=0.0) for c in ARC.world_conditions)
    )
    for seed in range(20):
        rng = Rng(f"s{seed}")
        assert opportunity.activate(at(OPENS), certain, rng).opportunity_failed == ()
        assert len(opportunity.activate(at(OPENS), doomed, rng).opportunity_failed) == 4


def test_a_revealed_failure_ends_the_arc_and_queues_its_scene() -> None:
    live = at(4, opportunity_id=ARC.id, opportunity_failed=("early",))
    told = opportunity.reveal(live, ARC, [])
    assert told.pending_events == ("ev_early",)
    assert told.failure_scenes_seen == ("ev_early",)
    assert told.opportunity_id == ""  # the arc is over


def test_a_condition_that_held_reveals_without_a_scene() -> None:
    live = at(4, opportunity_id=ARC.id, opportunity_failed=("late",))
    quiet = opportunity.reveal(live, ARC, [])
    assert quiet.pending_events == ()
    assert quiet.opportunity_revealed == ("early",)
    assert quiet.opportunity_id == ARC.id


def test_the_scene_is_the_earliest_failure_he_has_not_already_lived() -> None:
    """03 §7.3: a player who fails six chances must fail them six different ways."""
    live = at(
        CLOSES,
        opportunity_id=ARC.id,
        opportunity_failed=("early", "middle"),
        failure_scenes_seen=("ev_early",),
    )
    assert opportunity.resolve(live, ARC, []).pending_events == ("ev_middle",)


def test_meeting_every_condition_converts_exactly_one_tier() -> None:
    ready = at(
        CLOSES, opportunity_id=ARC.id, technique=99.0, physical=99.0, mental=99.0
    )
    won = opportunity.resolve(ready, ARC, [])
    assert won.tier == ready.tier - 1
    assert won.opportunities_converted == 1
    assert won.pending_events == ("ev_signed",)
    # The move waits for the window at the end of the season, the way it would.
    assert won.contract_seasons_left == 0


def test_the_world_holding_is_not_enough_on_its_own() -> None:
    """03 §7.2: the player's inputs genuinely matter. With every world condition met
    and him short of the bar, this is still a failure — with a scene of its own."""
    short = at(CLOSES, opportunity_id=ARC.id, technique=1.0, physical=1.0, mental=1.0)
    lost = opportunity.resolve(short, ARC, [])
    assert lost.tier == short.tier
    assert lost.opportunities_converted == 0
    assert lost.pending_events == ("ev_not_ready",)


def test_a_failed_world_condition_beats_a_perfect_player() -> None:
    perfect = at(
        CLOSES,
        opportunity_id=ARC.id,
        opportunity_failed=("late",),
        technique=99.0,
        physical=99.0,
        mental=99.0,
    )
    assert opportunity.resolve(perfect, ARC, []).opportunities_converted == 0


def test_failure_costs_hope_and_success_pays_it_back() -> None:
    live = at(CLOSES, opportunity_id=ARC.id, opportunity_failed=("early",))
    lost = opportunity.resolve(live, ARC, [])
    assert lost.hope < live.hope
    assert lost.cynicism > live.cynicism

    ready = at(
        CLOSES, opportunity_id=ARC.id, technique=99.0, physical=99.0, mental=99.0
    )
    won = opportunity.resolve(ready, ARC, [])
    assert won.hope > ready.hope
    assert won.cynicism < ready.cynicism


def test_nothing_in_the_module_reads_a_conversion_count() -> None:
    """03 §7.1: the ceiling is the ladder running out, never a counter saying enough.
    `opportunities_converted` exists for the balance report and for nothing else."""
    for converted in range(6):
        state = at(OPENS, opportunities_converted=converted)
        assert opportunity.due(state, ARCS) is ARC
