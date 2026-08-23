from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace

from false_nine.core import calendar, resources, stats
from false_nine.core.effects import Change, update
from false_nine.core.match import play
from false_nine.core.match.card import Card, Outcome
from false_nine.core.rng import Rng
from false_nine.core.state import GameState, advance_week

TRAINABLE = ("technique", "physical", "mental")
# A match costs no AP: 03 §2.1 lists six actions and playing is not one of them.
FREE_ACTIONS = frozenset({"drift", "end_week", "start_match", "play_card"})
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
        # A match he is due to play blocks the week from ending, the way it would.
        return state.ap == 0 and not state.match_pending
    if action.kind == "start_match":
        return state.match_pending and not state.in_match
    if action.kind == "play_card":
        return state.in_match and action.arg in state.match_hand
    if state.ap <= 0:
        return False
    if action.kind == "train":
        return not state.is_injured and action.arg in TRAINABLE
    if action.kind == "deal_with_it":
        return state.debt > 0 and state.money > 0
    return action.kind in {"recover", "work", "socialise", "drift"}


def step(
    state: GameState, action: PlayerAction, rng: Rng, cards: Mapping[str, Card]
) -> StepResult:
    if action.kind == "end_week":
        return end_week(state, rng) if can_do(state, action) else StepResult(state, [])
    if not can_do(state, action):
        return StepResult(state, [])

    effects: list[Change] = []
    if action.kind == "start_match":
        return StepResult(play.start(state, cards, rng), effects)
    if action.kind == "play_card":
        assert action.arg is not None  # can_do checked membership in the hand
        state, outcome = play.play_card(state, cards, action.arg, rng, effects)
        if state.beat > BEATS_PER_MATCH:
            state = play.finish(state, rng, effects)
        return StepResult(state, effects, outcome)

    if action.kind == "train":
        assert action.arg is not None  # can_do checked membership in TRAINABLE
        state = _train(state, action.arg, rng, effects)
    elif action.kind == "recover":
        state = _recover(state, effects)
    elif action.kind == "work":
        state = _work(state, effects)
    elif action.kind == "socialise":
        state = _socialise(state, effects)
    elif action.kind == "deal_with_it":
        state = _deal_with_it(state, effects)
    elif action.kind == "drift":
        state = _drift(state, effects)

    spent = 0 if action.kind in FREE_ACTIONS else 1
    return StepResult(replace(state, ap=state.ap - spent), effects)


def end_week(state: GameState, rng: Rng) -> StepResult:
    effects: list[Change] = []

    state = update(
        state,
        effects,
        "reason_week_passed",
        fatigue=resources.clamp01_100(state.fatigue + resources.FATIGUE_PASSIVE),
        injury_weeks_left=max(0.0, state.injury_weeks_left - 1.0),
    )
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
    if state.week == calendar.WEEKS_PER_SEASON:
        technique_loss, physical_loss = stats.season_decay(state.age)
        state = update(
            state,
            effects,
            "reason_season_end",
            technique=_floored(state.technique - technique_loss),
            physical=_floored(state.physical - physical_loss),
        )

    state = advance_week(state)
    return StepResult(replace(state, ap=resources.ap_for_week(state)), effects)


def _floored(stat: float) -> float:
    """Ability has a floor, not a ceiling. See stats.STAT_FLOOR."""
    return max(stats.STAT_FLOOR, stat)


def _train(state: GameState, stat: str, rng: Rng, effects: list[Change]) -> GameState:
    gain = stats.training_gain(getattr(state, stat), state.age, state.fatigue)
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


def _socialise(state: GameState, effects: list[Change]) -> GameState:
    return update(
        state,
        effects,
        "reason_socialise",
        stress=resources.clamp01_100(state.stress + resources.STRESS_SOCIALISE),
    )


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
