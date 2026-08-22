from __future__ import annotations

import json
from functools import cache
from pathlib import Path

# ponytail: data/ is found relative to the source tree. Packaging (M9) moves it into the
# wheel and this becomes importlib.resources.
DATA = Path(__file__).resolve().parents[3] / "data"


@cache
def _ui() -> dict[str, str | list[str]]:
    payload = json.loads((DATA / "strings" / "ui.json").read_text(encoding="utf-8"))
    items: dict[str, str | list[str]] = payload["items"]
    return items


def text(key: str, **fields: object) -> str:
    value = _ui()[key]
    assert isinstance(value, str), key
    return value.format(**fields) if fields else value


def words(key: str) -> list[str]:
    value = _ui()[key]
    assert isinstance(value, list), key
    return value
