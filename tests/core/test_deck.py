from __future__ import annotations

from collections import Counter
from dataclasses import replace

from false_nine.core.match import deck
from false_nine.core.match.card import Card, Outcome
from false_nine.core.rng import Rng
from false_nine.core.state import HAND_SIZE, GameState


def _card(card_id: str, pool: str, source: str | None = None) -> Card:
    return Card(
        id=card_id,
        title=card_id,
        pool=pool,
        beat_tags=("early", "middle", "late"),
        flavour="x",
        outcomes=(Outcome(100, 0.0, 0, "y"),),
        weight_source=source,
    )


CARDS = {
    c.id: c
    for c in (
        _card("card_t", "pool_positive", "technique"),
        _card("card_p", "pool_positive", "physical"),
        _card("card_m", "pool_positive", "mental"),
        _card("card_n1", "pool_neutral"),
        _card("card_n2", "pool_neutral"),
        _card("card_anx", "pool_anxious"),
        _card("card_tired", "pool_tired"),
    )
}
STREAM = Rng("deck-test").stream("deck", 1)


def test_quality_clamps_at_both_ends() -> None:
    assert deck.quality(0.0, 0.0, 100.0, 100.0, 100.0, 0.0) == deck.QUALITY_FLOOR
    assert deck.quality(100.0, 100.0, 0.0, 0.0, 0.0, 100.0) == deck.QUALITY_CEILING


def test_quality_moves_the_way_the_spec_says() -> None:
    base = deck.quality(50.0, 50.0, 20.0, 20.0, 10.0, 75.0)
    assert deck.quality(70.0, 50.0, 20.0, 20.0, 10.0, 75.0) > base  # ability helps
    assert deck.quality(50.0, 70.0, 20.0, 20.0, 10.0, 75.0) > base  # form helps
    assert deck.quality(50.0, 50.0, 60.0, 20.0, 10.0, 75.0) < base  # fatigue hurts
    assert deck.quality(50.0, 50.0, 20.0, 60.0, 10.0, 75.0) < base  # stress hurts
    assert deck.quality(50.0, 50.0, 20.0, 20.0, 50.0, 75.0) < base  # cynicism hurts
    assert deck.quality(50.0, 50.0, 20.0, 20.0, 10.0, 40.0) < base  # hope helps


def test_deck_is_twenty_cards_split_by_quality() -> None:
    state = GameState(seed="t")
    built = deck.build(state, CARDS, STREAM)
    expected = round(
        deck.POSITIVE_SLOTS_AT_FULL_QUALITY
        * deck.quality(
            state.ability,
            state.form,
            state.fatigue,
            state.stress,
            state.cynicism,
            state.hope,
        )
    )
    positives = sum(1 for c in built if CARDS[c].pool == "pool_positive")
    assert len(built) == deck.DECK_SIZE
    assert positives == expected


def test_noise_is_neutral_until_a_pool_is_driven() -> None:
    state = GameState(seed="t", stress=10.0, fatigue=10.0)
    pools = {CARDS[c].pool for c in deck.build(state, CARDS, STREAM)}
    assert pools <= {"pool_positive", "pool_neutral"}


def test_a_driven_pool_takes_over_the_noise() -> None:
    """03 §5.3: a bad week shows up in the hand, never in a stat."""
    state = replace(GameState(seed="t"), stress=90.0)
    pools = Counter(CARDS[c].pool for c in deck.build(state, CARDS, STREAM))
    assert pools["pool_anxious"] > 0
    assert pools["pool_neutral"] == 0


def test_the_stronger_stat_is_drawn_more_often() -> None:
    state = replace(GameState(seed="t"), technique=90.0, physical=5.0, mental=5.0)
    drawn = Counter(
        card_id
        for seed in range(40)
        for card_id in deck.build(state, CARDS, Rng(str(seed)).stream("deck", 1))
    )
    assert drawn["card_t"] > drawn["card_p"] + drawn["card_m"]


def test_a_hand_is_five_distinct_cards() -> None:
    state = GameState(seed="t")
    for seed in range(20):
        stream = Rng(f"hand{seed}").stream("deck", 1)
        hand = deck.deal(deck.build(state, CARDS, stream), CARDS, stream)
        assert len(hand) == HAND_SIZE
        assert len(set(hand)) == HAND_SIZE


def test_a_hand_survives_a_deck_of_one_card() -> None:
    """Content is thin at M2 and must not be able to deal a short hand."""
    stream = Rng("thin").stream("deck", 1)
    hand = deck.deal(["card_n1"] * deck.DECK_SIZE, CARDS, stream)
    assert len(hand) == HAND_SIZE
    assert len(set(hand)) == HAND_SIZE
