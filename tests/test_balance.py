from __future__ import annotations

import statistics

from false_nine.content import cards as card_content
from tools.sim import AGE_26_WEEK, Career, Policy, quiet, run_career, social

CAREERS = 20
UNTIL = AGE_26_WEEK + 1  # stop at 26, where 09 pins the ability distribution

# What "statistically indistinguishable" and "visibly different" are worth in numbers.
ABILITY_TOLERANCE = 1.0
POLLUTED_HAND = 0.30
CLEAN_HAND = 0.05


def careers(policy: Policy) -> list[Career]:
    cards = card_content.load()
    return [
        run_career(f"m3-{i}", policy, cards, until_week=UNTIL) for i in range(CAREERS)
    ]


def test_socialising_changes_the_hand_and_not_the_player() -> None:
    """09 M3's acceptance, and the design's central claim. `quiet` and `social` train
    identically by construction — same fatigue cap, same weeks — and differ only in
    what they do with the AP left over. If Socialise made him a better footballer
    rather than a better-off one, the ability medians would separate here."""
    lonely, sociable = careers(quiet), careers(social)

    def median(group: list[Career], value: str) -> float:
        return statistics.median(getattr(c, value) for c in group)

    ability_gap = abs(
        median(lonely, "ability_at_26") - median(sociable, "ability_at_26")
    )
    assert ability_gap < ABILITY_TOLERANCE, f"psyche moved ability by {ability_gap:.2f}"

    assert median(lonely, "pollution_rate") > POLLUTED_HAND
    assert median(sociable, "pollution_rate") < CLEAN_HAND

    # Guards the guard: if either policy stopped training, both medians would sit at
    # the starting ability and the comparison above would pass on nothing.
    assert (
        min(median(lonely, "ability_at_26"), median(sociable, "ability_at_26")) > 25.0
    )
