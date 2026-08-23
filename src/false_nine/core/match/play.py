from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from false_nine.core import resources, stats
from false_nine.core.effects import Change, update
from false_nine.core.match import deck
from false_nine.core.match.card import Card, Outcome
from false_nine.core.rng import Rng, Stream
from false_nine.core.state import GameState

BASE_RATING = 5.0
RATING_FLOOR = 1.0
RATING_CEILING = 10.0
MOMENTUM_LIMIT = 1
# [TUNE] What a beat of momentum is worth to the beats that follow it. 03 §5.4 adds a
# "momentum_bonus" to performance; carrying it into each later beat is the same sum,
# and it makes momentum modify the next beat's context as §5.1 requires.
MOMENTUM_WEIGHT = 0.3

FORM_INERTIA = 0.7  # 03 §3.2


def start(state: GameState, cards: Mapping[str, Card], rng: Rng) -> GameState:
    stream = rng.stream("deck", state.week_index)
    built = deck.build(state, cards, stream)
    return replace(
        state,
        match_hand=deck.deal(built, cards, stream),
        momentum=0,
        match_performance=0.0,
    )


def play_card(
    state: GameState,
    cards: Mapping[str, Card],
    card_id: str,
    rng: Rng,
    effects: list[Change],
) -> tuple[GameState, Outcome]:
    """Returns the outcome that fired as well as the state, because the screen must
    show the text belonging to the roll that actually happened. Re-rolling it for
    display would be the game lying about a result the player has already lived."""
    card = cards[card_id]
    stream = rng.stream("match_outcome", (state.week_index, state.beat))
    outcome = pick_outcome(card, stream)

    state = replace(
        state,
        match_hand=tuple(c for c in state.match_hand if c != card_id),
        match_performance=state.match_performance
        + outcome.rating_delta
        + MOMENTUM_WEIGHT * state.momentum,
        momentum=max(
            -MOMENTUM_LIMIT, min(MOMENTUM_LIMIT, state.momentum + outcome.momentum)
        ),
    )
    if outcome.fatigue:
        state = update(
            state,
            effects,
            "reason_match",
            fatigue=resources.clamp01_100(state.fatigue + outcome.fatigue),
        )
    if outcome.injury_roll:
        state = stats.maybe_injure(
            state, outcome.injury_roll, rng.stream("injury", state.week_index), effects
        )
    return state, outcome


def pick_outcome(card: Card, stream: Stream) -> Outcome:
    """Weights sum to 100 — content validation guarantees it, so the last outcome is
    the fallback for a float that lands exactly on the boundary."""
    roll = stream.uniform(0.0, 100.0)
    running = 0.0
    for outcome in card.outcomes:
        running += outcome.weight
        if roll < running:
            return outcome
    return card.outcomes[-1]


def finish(state: GameState, rng: Rng, effects: list[Change]) -> GameState:
    rating = max(
        RATING_FLOOR, min(RATING_CEILING, BASE_RATING + state.match_performance)
    )
    state = update(
        state,
        effects,
        "reason_match",
        form=resources.clamp01_100(
            FORM_INERTIA * state.form + (1 - FORM_INERTIA) * rating * 10
        ),
        fatigue=resources.clamp01_100(state.fatigue + resources.FATIGUE_MATCH),
    )
    state = stats.maybe_injure(
        state,
        stats.p_injury(
            stats.INJURY_BASE_MATCH, state.fatigue, state.age, state.injury_history
        ),
        rng.stream("injury", state.week_index),
        effects,
    )
    return replace(
        state,
        match_hand=(),
        momentum=0,
        match_performance=0.0,
        last_match_week=state.week_index,
        last_match_rating=rating,
    )
