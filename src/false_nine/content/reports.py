from __future__ import annotations

import json
from functools import cache

from false_nine.content.cards import ContentError
from false_nine.content.strings import DATA
from false_nine.core.rng import Stream

# [TUNE] Rating band edges. The report describes his performance and never the team's
# result — 03 §5.4. Team results arrive with clubs at M4.
BANDS = (("poor", 4.5), ("flat", 5.5), ("decent", 7.0), ("good", 11.0))


def band_of(rating: float) -> str:
    return next(name for name, upper in BANDS if rating < upper)


@cache
def load() -> dict[str, tuple[str, ...]]:
    path = DATA / "events" / "match_reports" / "reports.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    by_band: dict[str, list[str]] = {name: [] for name, _ in BANDS}
    for raw in payload["items"]:
        if raw["band"] not in by_band:
            raise ContentError(f"{path.name}: {raw['id']} has unknown band")
        by_band[raw["band"]].append(raw["text"])

    empty = [name for name, texts in by_band.items() if not texts]
    if empty:
        raise ContentError(f"{path.name}: no reports for band(s) {empty}")
    return {name: tuple(texts) for name, texts in by_band.items()}


def for_rating(rating: float, stream: Stream) -> str:
    return stream.choice(load()[band_of(rating)])
