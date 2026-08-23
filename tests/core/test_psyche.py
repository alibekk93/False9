from __future__ import annotations

from dataclasses import replace

from false_nine.content import cards as card_content
from false_nine.core import psyche
from false_nine.core.actions import PlayerAction, end_week, step
from false_nine.core.content import Content
from false_nine.core.rng import Rng
from false_nine.core.state import Bond, GameState

PSYCHE_FIELDS = ("stress", "hope", "cynicism", "self_knowledge")
EXTREMES = (0.0, 100.0)
TRAIN = PlayerAction("train", "technique")

# (week_index, technique, fatigue) — young and fresh, mid-career, old and wrecked.
CASES = ((1, 30.0, 0.0), (61, 55.0, 40.0), (141, 72.0, 85.0))


def test_hope_leaks_from_season_five() -> None:
    assert psyche.season_drift(4) == 0.0
    assert psyche.season_drift(5) == psyche.HOPE_DRIFT_PER_SEASON

    def hope_after(week_index: int) -> float:
        state = GameState(seed="t", week_index=week_index, ap=0)
        return end_week(state, Rng("t"), Content()).state.hope

    assert hope_after(40) == psyche.HOPE_START  # season 4 ends, nothing leaks
    assert hope_after(45) == psyche.HOPE_START  # mid-season, nothing leaks
    assert hope_after(50) == psyche.HOPE_START + psyche.HOPE_DRIFT_PER_SEASON


def test_psyche_does_not_touch_stats() -> None:
    """03 §4, the separation the whole design rests on. Ability moves in exactly two
    places — a Train action and the season-end decay — so both are swept here against
    every psyche value at both extremes. The emergent version of this claim, over a
    whole career with matches in it, is `tests/test_balance.py`."""
    for week_index, technique, fatigue in CASES:
        base = GameState(
            seed="t", week_index=week_index, technique=technique, fatigue=fatigue
        )
        trained = step(base, TRAIN, Rng("t"), Content()).state.technique
        decayed = end_week(
            replace(base, week_index=week_index + 9, ap=0), Rng("t"), Content()
        )

        for name in PSYCHE_FIELDS:
            for value in EXTREMES:
                skewed = replace(base, **{name: value})
                assert (
                    step(skewed, TRAIN, Rng("t"), Content()).state.technique == trained
                ), f"{name}={value} changed what training is worth"

                aged = end_week(
                    replace(skewed, week_index=week_index + 9, ap=0),
                    Rng("t"),
                    Content(),
                )
                assert aged.state.technique == decayed.state.technique, name
                assert aged.state.physical == decayed.state.physical, name


def test_psyche_does_reach_the_deck() -> None:
    """The other half: if psyche touched nothing at all the test above would pass on
    a game where the four values were dead weight."""
    from false_nine.core.match import deck

    calm = GameState(seed="t", stress=5.0, cynicism=5.0, hope=95.0)
    wrecked = replace(calm, stress=95.0, cynicism=95.0, hope=5.0)
    stream = Rng("t").stream("deck", 1)
    cards = card_content.load()

    assert deck.build(wrecked, cards, stream) != deck.build(calm, cards, stream)
    assert deck.pool_drivers(wrecked)["pool_bitter"] > deck.POOL_THRESHOLD
    assert deck.pool_drivers(wrecked)["pool_flat"] > deck.POOL_THRESHOLD


def test_relationships_do_not_affect_match() -> None:
    """03 §8: relationships gate the ending and nothing else mechanical. Two players
    with the same body and opposite lives play the identical match."""
    cards = card_content.load()
    loved = GameState(
        seed="t",
        week_index=2,
        relationships={"npc_a": Bond(90.0, 90.0, 90.0, 90.0, last_contact_week=2)},
    )
    alone = replace(loved, relationships={"npc_a": Bond(1.0, 1.0, 1.0, 1.0)})

    played = [_play_a_match(state, cards) for state in (loved, alone)]
    assert played[0].last_match_rating == played[1].last_match_rating
    assert [replace(s, relationships={}) for s in played] == [
        replace(played[0], relationships={})
    ] * 2


def _play_a_match(state: GameState, cards: dict[str, object]) -> GameState:
    rng = Rng(state.seed)
    state = step(state, PlayerAction("start_match"), rng, Content(cards=cards)).state
    assert state.in_match, "the fixture stopped landing on a match week"
    while state.in_match:
        pick = PlayerAction("play_card", sorted(state.match_hand)[0])
        state = step(state, pick, rng, Content(cards=cards)).state
    return state
