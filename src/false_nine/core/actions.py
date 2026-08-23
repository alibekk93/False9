from __future__ import annotations

from dataclasses import dataclass, replace

from false_nine.core import (
    calendar,
    club,
    opportunity,
    psyche,
    relationships,
    resources,
    stats,
)
from false_nine.core.content import Content
from false_nine.core.effects import Change, update
from false_nine.core.events import apply as event_effects
from false_nine.core.match import play
from false_nine.core.match.card import Outcome
from false_nine.core.rng import Rng
from false_nine.core.state import GameState, advance_week

TRAINABLE = ("technique", "physical", "mental")
# A match costs no AP: 03 §2.1 lists six actions and playing is not one of them.
# Neither does answering a scene or signing a contract; those are the week happening
# to him, not something he spends the week on.
FREE_ACTIONS = frozenset(
    {"drift", "end_week", "start_match", "play_card", "resolve_event", "sign"}
)
BEATS_PER_MATCH = 3


@dataclass(frozen=True)
class PlayerAction:
    """Matches the `action_log` shape in save.py, so a career replays from its log."""

    kind: str
    arg: str | None = None


@dataclass(frozen=True)
class StepResult:
    state: GameState
    effects: list[Change]
    # The outcome a played card resolved to, so the screen shows the roll that
    # happened rather than one of its own. None for every other action.
    outcome: Outcome | None = None


def can_do(state: GameState, action: PlayerAction) -> bool:
    if action.kind == "end_week":
        # A match he is due to play blocks the week from ending, the way it would, and
        # so do a scene he has not answered and a contract he has not signed.
        return (
            state.ap == 0
            and not state.match_pending
            and not state.pending_events
            and not state.offers
        )
    if action.kind == "start_match":
        return state.match_pending and not state.in_match
    if action.kind == "play_card":
        return state.in_match and action.arg in state.match_hand
    if action.kind == "resolve_event":
        # Which choices are open needs the authored `requires`, which lives in
        # `data/`; `step` checks that and no-ops on a choice that is not.
        return bool(state.pending_events)
    if action.kind == "sign":
        return action.arg in state.offers
    if state.ap <= 0:
        return False
    if action.kind == "train":
        return not state.is_injured and action.arg in TRAINABLE
    if action.kind == "deal_with_it":
        return state.debt > 0 and state.money > 0
    if action.kind == "socialise":
        # 03 §2.1 makes it a choice of NPC, and §8 puts a drifted one out of reach.
        return action.arg is not None and relationships.is_reachable(state, action.arg)
    return action.kind in {"recover", "work", "drift"}


def step(
    state: GameState, action: PlayerAction, rng: Rng, content: Content
) -> StepResult:
    if action.kind == "end_week":
        if not can_do(state, action):
            return StepResult(state, [])
        return end_week(state, rng, content)
    if not can_do(state, action):
        return StepResult(state, [])

    effects: list[Change] = []
    if action.kind == "start_match":
        return StepResult(play.start(state, content.cards, rng), effects)
    if action.kind == "play_card":
        assert action.arg is not None  # can_do checked membership in the hand
        state, outcome = play.play_card(state, content.cards, action.arg, rng, effects)
        if state.beat > BEATS_PER_MATCH:
            state = play.finish(
                state, rng, effects, club.strength(state, content.clubs)
            )
        return StepResult(state, effects, outcome)
    if action.kind == "resolve_event":
        assert action.arg is not None
        return StepResult(_resolve_event(state, action.arg, content, effects), effects)
    if action.kind == "sign":
        assert action.arg is not None  # can_do checked membership in the offers
        return StepResult(club.sign(state, content.clubs[action.arg], effects), effects)

    if action.kind == "train":
        assert action.arg is not None  # can_do checked membership in TRAINABLE
        state = _train(
            state, action.arg, rng, effects, club.facilities(state, content.clubs)
        )
    elif action.kind == "recover":
        state = _recover(state, effects)
    elif action.kind == "work":
        state = _work(state, effects)
    elif action.kind == "socialise":
        assert action.arg is not None  # can_do checked reachability
        state = _socialise(state, action.arg, effects)
    elif action.kind == "deal_with_it":
        state = _deal_with_it(state, effects)
    elif action.kind == "drift":
        state = _drift(state, effects)

    spent = 0 if action.kind in FREE_ACTIONS else 1
    return StepResult(replace(state, ap=state.ap - spent), effects)


def end_week(state: GameState, rng: Rng, content: Content) -> StepResult:
    effects: list[Change] = []

    state = update(
        state,
        effects,
        "reason_week_passed",
        fatigue=resources.clamp01_100(state.fatigue + resources.FATIGUE_PASSIVE),
        injury_weeks_left=max(0.0, state.injury_weeks_left - 1.0),
    )
    if state.week in club.PAYDAY_WEEKS:
        state = club.payday(state, rng.stream("wages", state.week_index), effects)
    state = update(
        state,
        effects,
        "reason_living_cost",
        money=state.money - resources.living_cost(state.phase),
    )
    state = update(
        state,
        effects,
        "reason_debt_interest",
        debt=resources.apply_interest(state.debt),
    )
    if state.money < 0:
        # Only the debt row is worth a ledger line. Showing money dip negative and come
        # back to zero would read as an accounting glitch rather than as a shortfall.
        state = update(
            state, effects, "reason_overdrawn", debt=state.debt - state.money
        )
        state = replace(state, money=0)
    state = relationships.decay(state, effects)
    state = _opportunity(state, rng, content, effects)
    state = club.drift_solvency(state, content.clubs)
    if club.has_folded(state):
        state = _queue(club.fold(state, effects), club.FOLD_EVENT, content)

    if state.week == calendar.WEEKS_PER_SEASON:
        technique_loss, physical_loss = stats.season_decay(state.age)
        state = update(
            state,
            effects,
            "reason_season_end",
            technique=_floored(state.technique - technique_loss),
            physical=_floored(state.physical - physical_loss),
            hope=resources.clamp01_100(state.hope + psyche.season_drift(state.season)),
            cynicism=resources.clamp01_100(
                state.cynicism
                + (
                    relationships.CYNICISM_WARMTH_SEASON
                    if relationships.is_warm(state)
                    else 0.0
                )
            ),
        )
        state = club.season_end(state, rng.stream("wages", state.week_index), effects)
        if (
            state.contract_seasons_left == 0
            and state.week_index < calendar.CAREER_WEEKS
        ):
            offers = club.offers(
                state, content.clubs, rng.stream("offers", state.week_index)
            )
            state = replace(state, offers=offers)

    state = advance_week(state)
    return StepResult(replace(state, ap=resources.ap_for_week(state)), effects)


def _opportunity(
    state: GameState, rng: Rng, content: Content, effects: list[Change]
) -> GameState:
    """03 §7. One arc at a time: it opens on its window's first week, tells him what
    has gone wrong as each condition reaches its reveal week, and settles at the end
    of the window if it is still alive by then."""
    arc = content.opportunities.get(state.opportunity_id)
    if arc is None:
        arc = opportunity.due(state, content.opportunities)
        if arc is None:
            return state
        state = opportunity.activate(state, arc, rng)

    state = opportunity.reveal(state, arc, effects)
    if state.opportunity_id == arc.id and state.week >= arc.window_weeks[1]:
        state = opportunity.resolve(state, arc, effects)
    return state


def _resolve_event(
    state: GameState, choice_id: str, content: Content, effects: list[Change]
) -> GameState:
    event = content.events[state.pending_events[0]]
    chosen = next((c for c in event.choices if c.id == choice_id), None)
    if chosen is None or not chosen.is_open(state):
        return state
    state = replace(state, pending_events=state.pending_events[1:])
    return event_effects.apply(state, effects, "reason_event", chosen.effects)


def _queue(state: GameState, event_id: str, content: Content) -> GameState:
    """A scene with nothing authored behind it is skipped rather than crashing the
    week. The content test is what says it is missing."""
    if event_id not in content.events:
        return state
    return replace(state, pending_events=(*state.pending_events, event_id))


def _floored(stat: float) -> float:
    """Ability has a floor, not a ceiling. See stats.STAT_FLOOR."""
    return max(stats.STAT_FLOOR, stat)


def _train(
    state: GameState, stat: str, rng: Rng, effects: list[Change], facilities: float
) -> GameState:
    gain = stats.training_gain(
        getattr(state, stat), state.age, state.fatigue, facilities
    )
    state = update(
        state,
        effects,
        "reason_training",
        **{stat: getattr(state, stat) + gain},
        fatigue=resources.clamp01_100(state.fatigue + resources.FATIGUE_TRAIN),
    )
    return stats.maybe_injure(
        state,
        stats.p_injury(
            stats.INJURY_BASE_TRAIN, state.fatigue, state.age, state.injury_history
        ),
        rng.stream("injury", state.week_index),
        effects,
    )


def _recover(state: GameState, effects: list[Change]) -> GameState:
    return update(
        state,
        effects,
        "reason_recover",
        fatigue=resources.clamp01_100(state.fatigue + resources.FATIGUE_RECOVER),
        stress=resources.clamp01_100(state.stress + resources.STRESS_RECOVER),
        injury_weeks_left=max(0.0, state.injury_weeks_left - 0.5),
    )


def _work(state: GameState, effects: list[Change]) -> GameState:
    return update(
        state,
        effects,
        "reason_work",
        money=state.money + resources.SIDE_JOB_INCOME,
        fatigue=resources.clamp01_100(state.fatigue + resources.FATIGUE_WORK),
    )


def _socialise(state: GameState, npc: str, effects: list[Change]) -> GameState:
    state = update(
        state,
        effects,
        "reason_socialise",
        stress=resources.clamp01_100(state.stress + resources.STRESS_SOCIALISE),
    )
    return relationships.socialise(state, npc, effects)


def _deal_with_it(state: GameState, effects: list[Change]) -> GameState:
    paid = min(state.money, state.debt)
    return update(
        state,
        effects,
        "reason_debt_payment",
        money=state.money - paid,
        debt=state.debt - paid,
    )


def _drift(state: GameState, effects: list[Change]) -> GameState:
    if state.debt > 0:
        state = update(
            state,
            effects,
            "reason_drift",
            stress=resources.clamp01_100(
                state.stress + resources.STRESS_DRIFT_WITH_OBLIGATIONS
            ),
        )
    return replace(state, ap=0)
