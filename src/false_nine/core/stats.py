from __future__ import annotations

from dataclasses import dataclass

from false_nine.core.rng import Stream

# Calibrated against tools.sim.train_max — the player who trains as hard as the fatigue
# system permits and ignores money entirely. He reaches a median ability of 75 at 26 and
# never passes 79 across 200 seeds: good, not elite. The spec's first guess of 1.6 put
# that same player in the high 90s. See 03 §3.1.
BASE_GAIN = 0.85
DIMINISHING_EXPONENT = 0.7

# Ability has a floor and deliberately NO ceiling. The career ceiling is enforced by the
# opportunity system (03 §7), never by a stat cap. Do not add an upper bound here.
STAT_FLOOR = 1.0

TECHNIQUE_DECAY_AGE = 29
TECHNIQUE_DECAY = 0.4
PHYSICAL_DECAY_AGE = 27
PHYSICAL_DECAY = 1.2

INJURY_BASE_TRAIN = 0.02
INJURY_BASE_MATCH = 0.04


@dataclass(frozen=True)
class Injury:
    severity: str
    weeks: int
    physical_damage: float


def age_factor(age: int) -> float:
    if age <= 19:
        return 1.4
    if age <= 24:
        return 1.0
    if age <= 28:
        return 0.6
    return 0.25


def fatigue_factor(fatigue: float) -> float:
    if fatigue < 50:
        return 1.0
    if fatigue < 75:
        return 0.6
    return 0.25


def training_gain(
    stat: float, age: int, fatigue: float, facilities: float = 1.0
) -> float:
    # max() guards the fractional power against a stat above 100 producing a complex
    # number. It is a domain guard on the *gain*, not a bound on the stat.
    headroom: float = max(0.0, 1.0 - stat / 100.0) ** DIMINISHING_EXPONENT
    return BASE_GAIN * age_factor(age) * fatigue_factor(fatigue) * facilities * headroom


def season_decay(age: int) -> tuple[float, float]:
    """Technique and physical loss for one season ended at `age`."""
    technique = TECHNIQUE_DECAY if age > TECHNIQUE_DECAY_AGE else 0.0
    physical = PHYSICAL_DECAY if age > PHYSICAL_DECAY_AGE else 0.0
    return technique, physical


def p_injury(base: float, fatigue: float, age: int, injury_history: int) -> float:
    fatigue_mult = 1.8 if fatigue > 80 else 1.0
    if age <= 25:
        age_mult = 1.0
    elif age <= 29:
        age_mult = 1.3
    else:
        age_mult = 1.7
    return base * fatigue_mult * age_mult * (1 + 0.02 * injury_history)


def roll_injury(stream: Stream) -> Injury:
    roll = stream.random()
    if roll < 0.60:
        return Injury("minor", stream.randint(1, 2), 0.0)
    if roll < 0.90:
        return Injury("moderate", stream.randint(3, 8), 2.0)
    return Injury("severe", stream.randint(12, 30), 6.0)
