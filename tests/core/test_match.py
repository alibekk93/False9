from __future__ import annotations

from dataclasses import replace

import pytest

from false_nine.core import resources
from false_nine.core.actions import PlayerAction, can_do, step
from false_nine.core.match import play
from false_nine.core.match.card import Card, Outcome
from false_nine.core.rng import Rng
from false_nine.core.state import HAND_SIZE, GameState

MATCH_WEEK = 2  # 03 §1: weeks 2, 3, 5, 6, 8, 9, 10


def _card(card_id: str, rating: float, momentum: int = 0) -> Card:
    return Card(
        id=card_id,
        title=card_id,
        pool="pool_neutral",
        beat_tags=("early", "middle", "late"),
        flavour="x",
        outcomes=(Outcome(100, rating, momentum, "y"),),
    )


CARDS = {c.id: c for c in (_card(f"card_{i}", 0.5) for i in range(8))}
CARDS["card_swing"] = _card("card_swing", 1.0, 1)

FILLER = ("card_0", "card_1", "card_2", "card_3", "card_4")


def fresh(**overrides: object) -> GameState:
    return replace(GameState(seed="t", week_index=MATCH_WEEK, ap=0), **overrides)


def dealt(*first: str) -> GameState:
    """A hand with known cards at the front, so a pick is not left to the deal."""
    rest = [c for c in FILLER if c not in first]
    return fresh(match_hand=(*first, *rest[: HAND_SIZE - len(first)]))


def start(state: GameState, rng: Rng) -> GameState:
    return step(state, PlayerAction("start_match"), rng, CARDS).state


def play_out(state: GameState, rng: Rng, picks: list[str] | None = None) -> GameState:
    for _ in range(3):
        card_id = picks.pop(0) if picks else state.match_hand[0]
        state = step(state, PlayerAction("play_card", card_id), rng, CARDS).state
    return state


def test_a_match_week_owes_a_match() -> None:
    assert fresh().match_pending
    assert not fresh(week_index=1).match_pending
    assert not fresh(injury_weeks_left=3.0).match_pending


def test_the_week_cannot_end_with_a_match_unplayed() -> None:
    state = fresh()
    assert not can_do(state, PlayerAction("end_week"))
    assert can_do(fresh(week_index=1), PlayerAction("end_week"))


def test_playing_the_match_unblocks_the_week() -> None:
    rng = Rng("t")
    state = play_out(start(fresh(), rng), rng)
    assert not state.match_pending
    assert can_do(state, PlayerAction("end_week"))


def test_a_hand_is_dealt_and_shrinks_one_card_per_beat() -> None:
    rng = Rng("t")
    state = start(fresh(), rng)
    assert len(state.match_hand) == HAND_SIZE
    for expected_beat in (1, 2, 3):
        assert state.beat == expected_beat
        state = step(
            state, PlayerAction("play_card", state.match_hand[0]), rng, CARDS
        ).state
    assert state.match_hand == ()  # the two discards go with the finished match


def test_a_match_cannot_be_started_twice_in_one_week() -> None:
    rng = Rng("t")
    state = play_out(start(fresh(), rng), rng)
    assert not can_do(state, PlayerAction("start_match"))


def test_a_card_not_in_hand_is_refused() -> None:
    rng = Rng("t")
    state = start(fresh(), rng)
    outside = next(c for c in CARDS if c not in state.match_hand)
    assert not can_do(state, PlayerAction("play_card", outside))


def test_rating_is_five_plus_what_he_did() -> None:
    rng = Rng("t")
    state = start(fresh(), rng)
    hand = list(state.match_hand)
    state = play_out(state, rng, hand[:3])
    expected = play.BASE_RATING + sum(
        CARDS[c].outcomes[0].rating_delta for c in hand[:3]
    )
    assert state.last_match_rating == pytest.approx(expected)


def test_momentum_carries_into_the_beats_that_follow() -> None:
    """03 §5.1: an outcome modifies the next beat's context, not just the total."""
    swung = play_out(dealt("card_swing"), Rng("t"), ["card_swing", "card_1", "card_2"])
    flat = play_out(dealt(), Rng("t"), ["card_0", "card_1", "card_2"])
    lead = swung.last_match_rating - flat.last_match_rating
    # card_swing beats card_0 by 0.5 outright; its momentum is worth more on top.
    assert lead > 0.5


def test_rating_stays_inside_one_to_ten() -> None:
    """Three cards cannot reach either bound, so the clamp is checked where it lives."""
    for performance in (-99.0, 99.0):
        finished = play.finish(fresh(match_performance=performance), Rng("t"), [])
        assert play.RATING_FLOOR <= finished.last_match_rating <= play.RATING_CEILING


def test_form_follows_the_rolling_average() -> None:
    rng = Rng("t")
    before = fresh(form=50.0)
    after = play_out(start(before, rng), rng)
    expected = (
        play.FORM_INERTIA * before.form
        + (1 - play.FORM_INERTIA) * after.last_match_rating * 10
    )
    assert after.form == pytest.approx(expected)


def test_the_match_costs_fatigue_once() -> None:
    rng = Rng("t")
    after = play_out(start(fresh(fatigue=10.0), rng), rng)
    assert after.fatigue == pytest.approx(10.0 + resources.FATIGUE_MATCH)


def test_the_match_costs_no_action_points() -> None:
    rng = Rng("t")
    before = fresh(ap=3)
    assert play_out(start(before, rng), rng).ap == 3


def test_the_ledger_records_the_match() -> None:
    rng = Rng("t")
    state = start(fresh(), rng)
    effects = []
    for _ in range(3):
        result = step(state, PlayerAction("play_card", state.match_hand[0]), rng, CARDS)
        state, _ = result.state, effects.extend(result.effects)
    assert {change.field for change in effects} >= {"form", "fatigue"}
    assert all(change.reason.startswith("reason_") for change in effects)
