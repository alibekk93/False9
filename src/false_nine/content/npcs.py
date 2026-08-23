from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache
from typing import Any

from false_nine.content.cards import ContentError
from false_nine.content.strings import DATA
from false_nine.core.state import AXES, Bond

NPC_KEYS = frozenset({"id", "name", "role", "initial"})


@dataclass(frozen=True)
class Npc:
    """05 §4. `arc_events` is in the authored schema but nothing loads events yet, so
    it is not read here — a reference the validator cannot check is worse than none."""

    id: str
    name: str
    role: str
    initial: Bond


@cache
def load() -> dict[str, Npc]:
    npcs: dict[str, Npc] = {}
    for path in sorted((DATA / "npcs").glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for raw in payload["items"]:
            npc = _npc(raw, path.name)
            if npc.id in npcs:
                raise ContentError(f"{path.name}: duplicate npc id {npc.id}")
            npcs[npc.id] = npc
    if not npcs:
        raise ContentError(f"no npcs found under {DATA / 'npcs'}")
    return npcs


def starting_bonds() -> dict[str, Bond]:
    """What a career opens with. Core cannot read `data/`, so the caller that builds
    the first GameState passes this in."""
    return {npc.id: npc.initial for npc in load().values()}


def _npc(raw: dict[str, Any], where: str) -> Npc:
    npc_id = raw.get("id", "<no id>")
    unknown = set(raw) - NPC_KEYS
    if unknown:
        raise ContentError(f"{where}: {npc_id}: unknown keys {sorted(unknown)}")
    if not str(npc_id).startswith("npc_"):
        raise ContentError(f"{where}: {npc_id} does not start with npc_")

    initial = raw["initial"]
    if set(initial) != set(AXES):
        raise ContentError(f"{where}: {npc_id}: axes are {sorted(initial)}, not {AXES}")
    if not all(0 <= value <= 100 for value in initial.values()):
        raise ContentError(f"{where}: {npc_id}: an axis is outside 0-100")

    return Npc(
        id=raw["id"],
        name=raw["name"],
        role=raw["role"],
        initial=Bond(**{axis: float(initial[axis]) for axis in AXES}),
    )
