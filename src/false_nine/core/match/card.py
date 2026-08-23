from __future__ import annotations

from dataclasses import dataclass, field

# 05 §3. `pool_bitter` and `pool_flat` are driven by real state since M3 but hold no
# cards yet: nothing raises cynicism or drops hope far enough until M4's failed
# opportunities, and M5 authors eight per pool. `deck._draw_noise` skips an empty
# pool, so the drivers can lead the field and still contribute nothing.
POOLS = frozenset(
    {
        "pool_positive",
        "pool_neutral",
        "pool_anxious",
        "pool_bitter",
        "pool_flat",
        "pool_tired",
        "pool_hurt",
    }
)
WEIGHT_SOURCES = frozenset({"technique", "physical", "mental"})
BEATS = ("early", "middle", "late")


@dataclass(frozen=True)
class Outcome:
    weight: int
    rating_delta: float
    momentum: int
    text: str
    fatigue: float = 0.0
    injury_roll: float = 0.0


@dataclass(frozen=True)
class Card:
    id: str
    title: str
    pool: str
    beat_tags: tuple[str, ...]
    flavour: str
    outcomes: tuple[Outcome, ...]
    weight_source: str | None = None
    effects: tuple[dict[str, object], ...] = field(default=())

    def playable_in(self, beat: str) -> bool:
        return beat in self.beat_tags
