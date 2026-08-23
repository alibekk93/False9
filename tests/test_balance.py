from __future__ import annotations

import statistics

from false_nine.content import bundle
from tools.sim import (
    AGE_26_WEEK,
    Career,
    Policy,
    broke,
    careerist,
    quiet,
    run_career,
    social,
)

CAREERS = 20
UNTIL = AGE_26_WEEK + 1  # stop at 26, where 09 pins the ability distribution

# What "statistically indistinguishable" and "visibly different" are worth in numbers.
ABILITY_TOLERANCE = 1.0
POLLUTED_HAND = 0.30
CLEAN_HAND = 0.05

# 09 M4. The full-career runs are slower than the M3 pair, so this is the count the
# suite carries; the 1000-career figures live in `balance.md` and are quoted in the
# commit. Measured at 300 careers, `careerist` sits at 0.64.
FULL_CAREERS = 40
CONVERSION_BAND = (0.3, 1.5)
# 03 §7.4's ladder is three rungs — tier 5 to the tier-2 ceiling — so three is what an
# honest probability model can produce. See the note in 09 M4.
MAX_CONVERSIONS = 3


def careers(policy: Policy) -> list[Career]:
    content = bundle.load()
    return [
        run_career(f"m3-{i}", policy, content, until_week=UNTIL) for i in range(CAREERS)
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


def full_careers(policy: Policy) -> list[Career]:
    content = bundle.load()
    return [run_career(f"m4-{i}", policy, content) for i in range(FULL_CAREERS)]


def test_the_world_converts_about_one_chance_in_a_career() -> None:
    """09 M4's acceptance, measured against 03 §7.2's "well-prepared player" — which
    is what `careerist` is, and `train_max` is not: he never speaks to his agent, so
    three of the six chances gate him out before the world gets a say."""
    converted = [c.converted for c in full_careers(careerist)]
    mean = statistics.fmean(converted)
    low, high = CONVERSION_BAND
    assert low <= mean <= high, f"mean conversions {mean:.2f}"
    assert max(converted) <= MAX_CONVERSIONS, converted


def test_preparation_is_what_separates_them() -> None:
    """The other half, and 03 §7.2's claim that player conditions genuinely matter. A
    player who never trains is not unlucky — he is ineligible, every time."""
    assert sum(c.converted for c in full_careers(broke)) == 0


def test_failure_scenes_unique_per_career() -> None:
    """09 M4, and 03 §7.3: a player who fails six chances must fail them six different
    ways. If this ever fails the fix is another authored scene, never code that hides
    the repeat."""
    for career in full_careers(careerist):
        scenes = career.failure_scenes
        assert len(set(scenes)) == len(scenes), scenes


def test_every_chance_is_offered_before_the_ceiling_is_reached() -> None:
    """03 §7.5 promises six. Guards the guard on the test above: if the tier gate were
    wrong, most careers would see one chance, fail it uniquely, and pass."""
    seen = [len(c.failure_scenes) + c.converted for c in full_careers(careerist)]
    assert statistics.median(seen) == 6, seen
