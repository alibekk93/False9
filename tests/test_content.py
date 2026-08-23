from __future__ import annotations

import json
from dataclasses import replace

import pytest

from false_nine.content import (
    cards,
    clubs,
    events,
    npcs,
    opportunities,
    reports,
    strings,
)
from false_nine.content.strings import DATA
from false_nine.core.club import CONTRACT_SEASONS
from false_nine.core.match.card import BEATS
from false_nine.core.opportunity import TOP_TIER
from false_nine.core.state import AXES, GameState
from false_nine.ui.screens.week import body_word, mood_word

# This file is the whole content gate. Each loader validates its own file as it reads
# it and raises with the file and the id; what is asserted here is the cross-file
# integrity no single loader can see, plus the counts the spec puts a number on.
# tools/validate_content.py arrives when CI needs the same checks outside pytest.

# 03 §7.3, and the reason it is a hard number: a player who fails six chances must
# fail them six different ways.
MIN_FAILURE_SCENES = 12


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


def raw_items(schema: str, *parts: str) -> list[dict]:
    """Read straight from the JSON rather than through a loader, so a loader that
    silently drops or dedupes something cannot hide it from these assertions.
    `data/events/` also holds the match reports, which are not scenes."""
    found: list[dict] = []
    for path in sorted(DATA.joinpath(*parts).rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload["schema"] == schema:
            found += payload["items"]
    return found


# --- clubs ------------------------------------------------------------------


def test_every_club_loads_and_covers_the_ladder() -> None:
    loaded = clubs.load()
    assert len(loaded) >= 10, "05 §4 wants ten before M5 authors more"
    tiers = {club.tier for club in loaded.values()}
    assert tiers == set(range(TOP_TIER, 6)), f"tiers present: {sorted(tiers)}"


def test_exactly_one_club_is_the_one_he_starts_at() -> None:
    home = clubs.starting_club()
    assert clubs.HOME_TRAIT in home.traits
    assert home.tier == 5, "02: the academy years are the bottom of the ladder"


def test_club_ids_are_unique_and_prefixed() -> None:
    ids = [item["id"] for item in raw_items("club", "clubs")]
    assert len(ids) == len(set(ids))
    for club_id in ids:
        assert club_id.startswith("club_") and club_id.islower(), club_id


def test_every_tier_has_a_contract_length() -> None:
    for club in clubs.load().values():
        assert club.tier in CONTRACT_SEASONS, club.id


def test_wages_rise_with_the_ladder() -> None:
    """Not a rule in 03, but if a tier-4 club outbid a tier-2 one the whole point of
    converting an opportunity would quietly go away."""
    by_tier = {tier: [] for tier in range(TOP_TIER, 6)}
    for club in clubs.load().values():
        by_tier[club.tier].append(club.wage_offer)
    for tier in range(TOP_TIER, 5):
        assert max(by_tier[tier + 1]) < min(by_tier[tier]), tier


# --- opportunities ----------------------------------------------------------


def test_the_schedule_is_the_one_the_spec_names() -> None:
    """03 §7.5: six, roughly seasons 3, 5, 7, 9, 11, 13, and nothing after 13."""
    seasons = sorted(opp.season for opp in opportunities.load().values())
    assert seasons == [3, 5, 7, 9, 11, 13]


def test_every_world_condition_has_a_named_failure() -> None:
    """03 §7.3 is a hard rule: `ev_opportunity_fail` must never fire generic text."""
    authored = events.load()
    for opp in opportunities.load().values():
        for condition in opp.world_conditions:
            assert condition.fail_event in authored, f"{opp.id}/{condition.id}"
        assert opp.success_event in authored, opp.id
        assert opp.fail_event_player in authored, opp.id


def test_a_player_condition_failure_is_never_shared_between_chances() -> None:
    """Each chance fires at most once a career, so a scene only it can reach can never
    repeat. This is what makes the uniqueness rule structural rather than lucky."""
    scenes = [opp.fail_event_player for opp in opportunities.load().values()]
    assert len(scenes) == len(set(scenes))


def test_there_are_enough_failure_scenes_to_go_round() -> None:
    scenes = {
        condition.fail_event
        for opp in opportunities.load().values()
        for condition in opp.world_conditions
    }
    assert len(scenes) >= MIN_FAILURE_SCENES, sorted(scenes)


def test_no_two_chances_share_a_world_failure_scene() -> None:
    """Stronger than 03 §7.3 asks for, and it is what makes
    `test_failure_scenes_unique_per_career` pass by construction rather than by luck."""
    seen: dict[str, str] = {}
    for opp in opportunities.load().values():
        for condition in opp.world_conditions:
            assert condition.fail_event not in seen, (
                f"{condition.fail_event} is used by {seen.get(condition.fail_event)} "
                f"and {opp.id}"
            )
            seen[condition.fail_event] = opp.id


def test_reveal_weeks_are_spread_across_the_window() -> None:
    """03 §7.2: he finds out during the arc. Two conditions revealing in the same week
    would make one of them a scene nobody ever sees."""
    for opp in opportunities.load().values():
        weeks = [c.reveal_week for c in opp.world_conditions]
        assert len(weeks) == len(set(weeks)), opp.id
        assert min(weeks) >= opp.window_weeks[0], opp.id
        assert max(weeks) <= opp.window_weeks[1], opp.id


def test_a_prepared_player_converts_between_eight_and_fifteen_percent() -> None:
    """03 §7.2 puts a number on it, and the number is the design. If the product of
    the world conditions drifted up, the ceiling would stop being a ceiling."""
    for opp in opportunities.load().values():
        chance = 1.0
        for condition in opp.world_conditions:
            chance *= condition.p
        assert 0.08 <= chance <= 0.15, f"{opp.id}: {chance:.3f}"


# --- events -----------------------------------------------------------------


def test_every_event_loads() -> None:
    assert len(events.load()) >= 25


def test_event_ids_are_unique_and_prefixed() -> None:
    ids = [item["id"] for item in raw_items("event", "events")]
    assert len(ids) == len(set(ids))
    for event_id in ids:
        assert event_id.startswith("ev_") and event_id.islower(), event_id


def test_every_choice_says_what_happened() -> None:
    """05 §1: a choice without consequence text feels broken even when the mechanical
    effect is real."""
    for item in raw_items("event", "events"):
        for choice in item["choices"]:
            assert choice.get("outcome_text", "").strip(), (
                f"{item['id']}/{choice['id']}"
            )


def test_scenes_are_the_authored_length() -> None:
    """08 §5: an event scene body is 2-5 sentences and a choice is twelve words."""
    for event in events.load().values():
        assert 2 <= len(event.body) <= 5, event.id
        for choice in event.choices:
            assert len(choice.text.split()) <= 12, f"{event.id}/{choice.id}"


def test_the_club_folding_scene_exists_because_the_code_queues_it_by_name() -> None:
    from false_nine.core.club import FOLD_EVENT

    assert FOLD_EVENT in events.load()
