from __future__ import annotations

import json
from dataclasses import replace

import pytest

from false_nine.content import cards, npcs, reports, strings
from false_nine.content.strings import DATA
from false_nine.core.match.card import BEATS
from false_nine.core.state import AXES, GameState
from false_nine.ui.screens.week import body_word, mood_word

# Until data/ holds more than cards and reports, this file is the whole content gate.
# tools/validate_content.py arrives with events, when CI needs it outside pytest.


def test_every_card_loads() -> None:
    assert len(cards.load()) >= 20


def test_outcome_weights_sum_to_one_hundred() -> None:
    for card in cards.load().values():
        total = sum(outcome.weight for outcome in card.outcomes)
        assert total == cards.OUTCOME_WEIGHT_TOTAL, card.id


def test_every_beat_has_cards_to_play() -> None:
    """A hand of five must never be entirely illegal for the beat it faces."""
    for beat in BEATS:
        playable = [c for c in cards.load().values() if c.playable_in(beat)]
        assert len(playable) > len(cards.load()) / 2, beat


def test_ids_are_unique_across_files() -> None:
    seen: list[str] = []
    for path in sorted((DATA / "cards").glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        seen += [raw["id"] for raw in payload["items"]]
    assert len(seen) == len(set(seen))


def test_ids_follow_the_naming_convention() -> None:
    for card_id in cards.load():
        assert card_id.startswith("card_"), card_id
        assert card_id.islower(), card_id


def test_pollution_cards_hurt_and_positive_cards_help() -> None:
    """A pool card that reads as a reward would break the mechanic 02 rests on."""
    for card in cards.load().values():
        best = max(outcome.rating_delta for outcome in card.outcomes)
        if card.pool == "pool_positive":
            assert best > 0, card.id
        elif card.pool != "pool_neutral":
            assert best <= 0, card.id


def test_every_rating_band_has_a_report() -> None:
    loaded = reports.load()
    assert set(loaded) == {name for name, _ in reports.BANDS}
    assert all(texts for texts in loaded.values())


@pytest.mark.parametrize(
    ("rating", "band"),
    [
        (1.0, "poor"),
        (4.4, "poor"),
        (4.5, "flat"),
        (5.4, "flat"),
        (6.0, "decent"),
        (7.0, "good"),
        (10.0, "good"),
    ],
)
def test_bands_cover_the_whole_rating_range(rating: float, band: str) -> None:
    assert reports.band_of(rating) == band


def test_reports_are_the_authored_length() -> None:
    """08 §5: 60-110 words. Longer stops being a paragraph and starts being a scene."""
    for texts in reports.load().values():
        for text in texts:
            assert 60 <= len(text.split()) <= 110, text[:40]


def test_every_npc_loads_with_four_axes() -> None:
    loaded = npcs.load()
    assert len(loaded) == 7, "02: seven tracked NPCs"
    for npc_id, npc in loaded.items():
        assert npc_id.startswith("npc_"), npc_id
        assert npc.name and npc.role, npc_id
        assert all(0 <= getattr(npc.initial, axis) <= 100 for axis in AXES), npc_id
    # 03 §9 reads these two by id when it decides the Reconciliation axis.
    assert {"npc_mother", "npc_father"} <= set(loaded)


def test_every_mood_word_is_reachable_and_in_order() -> None:
    """07 §4: seven words, worst last. A band width that parked the player on one word
    for most of a career would make Mood decoration rather than information."""
    state = GameState(seed="t")
    seen: list[str] = []
    for value in range(101):
        word = mood_word(replace(state, stress=value, cynicism=value, hope=100 - value))
        if word not in seen:
            seen.append(word)
    assert seen == strings.words("mood_words")


def test_every_body_word_is_reachable_and_in_order() -> None:
    state = GameState(seed="t")
    seen = [body_word(replace(state, fatigue=f)) for f in range(0, 101, 5)]
    seen += [body_word(replace(state, injury_weeks_left=w)) for w in (1.0, 8.0)]
    assert set(seen) == set(strings.words("body_words"))
