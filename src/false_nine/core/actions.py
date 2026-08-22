from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from false_nine.core import calendar, resources, stats
from false_nine.core.rng import Rng
from false_nine.core.state import GameState, advance_week

TRAINABLE = ("technique", "physical", "mental")
FREE_ACTIONS = frozenset({"drift", "end_week"})


@dataclass(frozen=True)
class PlayerAction:
    """Matches the `action_log` shape in save.py, so a career replays from its log."""

    kind: str
    arg: str | None = None


@dataclass(frozen=True)
class Change:
    """One ledger row. `reason` is a key into data/strings/ui.json, never prose.

    Deliberately narrower than the tagged union in 04: every effect M1 can produce is
    "a named quantity moved from X to Y because Z". `CardResolved` and `EventFired`
    have genuinely different shapes and arrive with the systems that emit them."""

    field: str
    before: float
    after: float
    reason: str


@dataclass(frozen=True)
class StepResult:
    state: GameState
    effects: list[Change]


def can_do(state: GameState, action: PlayerAction) -> bool:
    if action.kind == "end_week":
        return state.ap == 0
    if state.ap <= 0:
        return False
    if action.kind == "train":
        return not state.is_injured and action.arg in TRAINABLE
    if action.kind == "deal_with_it":
        return state.debt > 0 and state.money > 0
    return action.kind in {"recover", "work", "socialise", "drift"}


def step(state: GameState, action: PlayerAction, rng: Rng) -> StepResult:
    if action.kind == "end_week":
        return end_week(state, rng) if can_do(state, action) else StepResult(state, [])
    if not can_do(state, action):
        return StepResult(state, [])

    effects: list[Change] = []
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

    state = _update(
        state,
        effects,
        "reason_week_passed",
        fatigue=resources.clamp01_100(state.fatigue + resources.FATIGUE_PASSIVE),
        injury_weeks_left=max(0.0, state.injury_weeks_left - 1.0),
    )
    state = _update(
        state,
        effects,
        "reason_living_cost",
        money=state.money - resources.living_cost(state.phase),
    )
    state = _update(
        state,
        effects,
        "reason_debt_interest",
        debt=resources.apply_interest(state.debt),
    )
    if state.money < 0:
        # Only the debt row is worth a ledger line. Showing money dip negative and come
        # back to zero would read as an accounting glitch rather than as a shortfall.
        state = _update(
            state, effects, "reason_overdrawn", debt=state.debt - state.money
        )
        state = replace(state, money=0)
    if state.week == calendar.WEEKS_PER_SEASON:
        technique_loss, physical_loss = stats.season_decay(state.age)
        state = _update(
            state,
            effects,
            "reason_season_end",
            technique=_floored(state.technique - technique_loss),
            physical=_floored(state.physical - physical_loss),
        )

    state = advance_week(state)
    return StepResult(replace(state, ap=resources.ap_for_week(state)), effects)


def _train(state: GameState, stat: str, rng: Rng, effects: list[Change]) -> GameState:
    gain = stats.training_gain(getattr(state, stat), state.age, state.fatigue)
    state = _update(
        state,
        effects,
        "reason_training",
        **{stat: getattr(state, stat) + gain},
        fatigue=resources.clamp01_100(state.fatigue + resources.FATIGUE_TRAIN),
    )

    stream = rng.stream("injury", state.week_index)
    risk = stats.p_injury(
        stats.INJURY_BASE_TRAIN, state.fatigue, state.age, state.injury_history
    )
    if stream.random() >= risk:
        return state

    injury = stats.roll_injury(stream)
    return _update(
        state,
        effects,
        f"reason_injury_{injury.severity}",
        injury_weeks_left=float(injury.weeks),
        injury_history=state.injury_history + 1,
        physical=_floored(state.physical - injury.physical_damage),
    )


def _recover(state: GameState, effects: list[Change]) -> GameState:
    return _update(
        state,
        effects,
        "reason_recover",
        fatigue=resources.clamp01_100(state.fatigue + resources.FATIGUE_RECOVER),
        stress=resources.clamp01_100(state.stress + resources.STRESS_RECOVER),
        injury_weeks_left=max(0.0, state.injury_weeks_left - 0.5),
    )


def _work(state: GameState, effects: list[Change]) -> GameState:
    return _update(
        state,
        effects,
        "reason_work",
        money=state.money + resources.SIDE_JOB_INCOME,
        fatigue=resources.clamp01_100(state.fatigue + resources.FATIGUE_WORK),
    )


def _socialise(state: GameState, effects: list[Change]) -> GameState:
    return _update(
        state,
        effects,
        "reason_socialise",
        stress=resources.clamp01_100(state.stress + resources.STRESS_SOCIALISE),
    )


def _deal_with_it(state: GameState, effects: list[Change]) -> GameState:
    paid = min(state.money, state.debt)
    return _update(
        state,
        effects,
        "reason_debt_payment",
        money=state.money - paid,
        debt=state.debt - paid,
    )


def _drift(state: GameState, effects: list[Change]) -> GameState:
    if state.debt > 0:
        state = _update(
            state,
            effects,
            "reason_drift",
            stress=resources.clamp01_100(
                state.stress + resources.STRESS_DRIFT_WITH_OBLIGATIONS
            ),
        )
    return replace(state, ap=0)


def _floored(stat: float) -> float:
    """Ability has a floor, not a ceiling. See stats.STAT_FLOOR."""
    return max(stats.STAT_FLOOR, stat)


def _update(
    state: GameState, effects: list[Change], reason: str, **values: Any
) -> GameState:
    """Set fields, recording a ledger row for each one that actually moved."""
    for field, after in values.items():
        before: float = getattr(state, field)
        if before != after:
            effects.append(Change(field, before, after, reason))
    return replace(state, **values)
