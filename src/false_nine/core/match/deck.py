from __future__ import annotations

from collections.abc import Mapping

from false_nine.core.match.card import Card
from false_nine.core.rng import Stream
from false_nine.core.state import HAND_SIZE, GameState

DECK_SIZE = 20
POSITIVE_SLOTS_AT_FULL_QUALITY = 10
QUALITY_FLOOR = 0.05
QUALITY_CEILING = 0.95
POOL_THRESHOLD = 35.0  # [TUNE] 03 §5.3


def quality(
    ability: float,
    form: float,
    fatigue: float,
    stress: float,
    cynicism: float,
    hope: float,
) -> float:
    """03 §5.3. Deck quality is what the week did, not what a dice roll decided."""
    raw = (
        0.30
        + 0.45 * (ability / 100)
        + 0.20 * (form / 100)
        - 0.20 * (fatigue / 100)
        - 0.25 * (stress / 100)
        - 0.15 * (cynicism / 100)
        + 0.10 * (hope / 100)
    )
    return max(QUALITY_FLOOR, min(QUALITY_CEILING, raw))


def pool_drivers(state: GameState) -> dict[str, float]:
    """03 §5.3. A pool with no authored cards is skipped by `_draw_noise`, so a driver
    may lead the field here and still contribute nothing — `pool_hurt` never fires at
    all, because §1 keeps him out of the squad while injured."""
    return {
        "pool_anxious": state.stress,
        "pool_bitter": state.cynicism,
        "pool_flat": 100.0 - state.hope,
        "pool_tired": state.fatigue,
        "pool_hurt": 100.0 if state.is_injured else 0.0,
    }


def by_pool(cards: Mapping[str, Card]) -> dict[str, list[str]]:
    """Card ids grouped by pool, sorted, so deck construction does not depend on the
    order `data/` happened to load in."""
    grouped: dict[str, list[str]] = {}
    for card_id in sorted(cards):
        grouped.setdefault(cards[card_id].pool, []).append(card_id)
    return grouped


def build(state: GameState, cards: Mapping[str, Card], stream: Stream) -> list[str]:
    """20 slots. Duplicates are expected — the slot counts are the probabilities."""
    grouped = by_pool(cards)
    positive_slots = round(
        POSITIVE_SLOTS_AT_FULL_QUALITY
        * quality(
            state.ability,
            state.form,
            state.fatigue,
            state.stress,
            state.cynicism,
            state.hope,
        )
    )

    deck = _draw_positive(state, cards, grouped, positive_slots, stream)
    deck += _draw_noise(state, grouped, DECK_SIZE - positive_slots, stream)
    return deck


def deal(deck: list[str], cards: Mapping[str, Card], stream: Stream) -> tuple[str, ...]:
    """Five distinct cards. The deck carries duplicates so that a heavily polluted deck
    is genuinely more likely to serve pollution; the hand dedupes so the player is
    never shown the same moment twice in one row."""
    hand: list[str] = []
    for card_id in stream.sample(deck, len(deck)):
        if card_id not in hand:
            hand.append(card_id)
        if len(hand) == HAND_SIZE:
            return tuple(hand)

    # Only reachable if the whole deck is fewer than five distinct cards.
    spare = [card_id for card_id in sorted(cards) if card_id not in hand]
    hand += stream.sample(spare, min(HAND_SIZE - len(hand), len(spare)))
    return tuple(hand)


def _draw_positive(
    state: GameState,
    cards: Mapping[str, Card],
    grouped: dict[str, list[str]],
    slots: int,
    stream: Stream,
) -> list[str]:
    """Weighted by the stat each card reads from, so what he is good at is what the
    match tends to offer him."""
    ids = grouped.get("pool_positive", [])
    if not ids or slots <= 0:
        return []
    weights = [getattr(state, str(cards[i].weight_source)) for i in ids]
    return stream.choices(ids, weights=weights, k=slots)


def _draw_noise(
    state: GameState, grouped: dict[str, list[str]], slots: int, stream: Stream
) -> list[str]:
    driven = {
        pool: value
        for pool, value in pool_drivers(state).items()
        if value >= POOL_THRESHOLD and grouped.get(pool)
    }
    if not driven:
        neutral = grouped.get("pool_neutral", [])
        return stream.choices(neutral, k=slots) if neutral and slots > 0 else []

    pools = sorted(driven)
    weights = [driven[pool] for pool in pools]
    return [
        stream.choice(grouped[stream.choices(pools, weights=weights, k=1)[0]])
        for _ in range(max(0, slots))
    ]
