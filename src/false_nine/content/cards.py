from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

from false_nine.content.strings import DATA
from false_nine.core.match.card import BEATS, POOLS, WEIGHT_SOURCES, Card, Outcome

CARD_KEYS = frozenset(
    {
        "id",
        "title",
        "pool",
        "beat_tags",
        "weight_source",
        "flavour",
        "outcomes",
        "effects",
    }
)
OUTCOME_KEYS = frozenset(
    {"weight", "rating_delta", "momentum", "fatigue", "injury_roll", "text"}
)
OUTCOME_WEIGHT_TOTAL = 100


class ContentError(ValueError):
    """Raised at load time with the file and the id, never at week 94. See 04."""


@cache
def load() -> dict[str, Card]:
    cards: dict[str, Card] = {}
    for path in sorted((DATA / "cards").glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for raw in payload["items"]:
            card = _card(raw, path)
            if card.id in cards:
                raise ContentError(f"{path.name}: duplicate card id {card.id}")
            cards[card.id] = card
    if not cards:
        raise ContentError(f"no cards found under {DATA / 'cards'}")
    return cards


def _card(raw: dict[str, Any], path: Path) -> Card:
    where = f"{path.name}: {raw.get('id', '<no id>')}"
    check_keys(raw, CARD_KEYS, where)

    pool = raw["pool"]
    if pool not in POOLS:
        raise ContentError(f"{where}: unknown pool {pool!r}")

    source = raw["weight_source"]
    # A positive card is drawn because of a stat; a pollution card is drawn because of
    # the week he has had. Neither may borrow the other's reason.
    if (source is not None) != (pool == "pool_positive"):
        raise ContentError(f"{where}: weight_source {source!r} does not fit {pool}")
    if source is not None and source not in WEIGHT_SOURCES:
        raise ContentError(f"{where}: unknown weight_source {source!r}")

    beats = tuple(raw["beat_tags"])
    if not beats or any(beat not in BEATS for beat in beats):
        raise ContentError(f"{where}: bad beat_tags {beats}")

    outcomes = tuple(_outcome(o, where) for o in raw["outcomes"])
    total = sum(o.weight for o in outcomes)
    if total != OUTCOME_WEIGHT_TOTAL:
        raise ContentError(f"{where}: outcome weights sum to {total}, not 100")

    return Card(
        id=raw["id"],
        title=raw["title"],
        pool=pool,
        beat_tags=beats,
        flavour=raw["flavour"],
        outcomes=outcomes,
        weight_source=source,
        effects=tuple(raw.get("effects", ())),
    )


def _outcome(raw: dict[str, Any], where: str) -> Outcome:
    check_keys(raw, OUTCOME_KEYS, where)
    return Outcome(
        weight=raw["weight"],
        rating_delta=float(raw["rating_delta"]),
        momentum=raw["momentum"],
        text=raw["text"],
        fatigue=float(raw.get("fatigue", 0.0)),
        injury_roll=float(raw.get("injury_roll", 0.0)),
    )


def check_keys(raw: dict[str, Any], allowed: frozenset[str], where: str) -> None:
    """05: unknown keys are an error, not a warning."""
    unknown = set(raw) - allowed
    if unknown:
        raise ContentError(f"{where}: unknown keys {sorted(unknown)}")
