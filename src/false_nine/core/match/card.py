from __future__ import annotations

from dataclasses import dataclass, field

# 05 §3. `pool_bitter` and `pool_flat` hold no cards yet. Their drivers went live at
# M3 and M4 finally moves them — failed chances and unpaid wages take cynicism to 100
# in a career that keeps nobody close — so the eight per pool M5 authors now have
# something to answer. `deck._draw_noise` skips an empty pool, so until then the
# drivers can lead the field and still contribute nothing.
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
