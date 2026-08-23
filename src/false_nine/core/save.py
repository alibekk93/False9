from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict
from typing import Any

from false_nine.core.state import Bond, GameState

# 2: M3 added the psyche fields and `relationships`. An M2 save has no bonds to
# rebuild, so it fails on the version check rather than on a KeyError three lines
# later. Migration proper is M9.
# 3: M4 added the club, the contract and the opportunity arc.
SAVE_VERSION = 3

# JSON has no tuples. Anything stored as one comes back a list and would compare
# unequal to the state it was written from, so it is named here rather than rebuilt by
# hand one line at a time — a field added to GameState and forgotten here is a
# roundtrip failure, and the list is the thing that gets read when it happens.
TUPLE_FIELDS = frozenset(
    {
        "match_hand",
        "offers",
        "opportunity_failed",
        "opportunity_revealed",
        "failure_scenes_seen",
        "pending_events",
        "flags",
    }
)


def dump(state: GameState, action_log: Iterable[dict[str, Any]] = ()) -> dict[str, Any]:
    """Serialise to a plain dict. Writing it to disk belongs outside core, as does
    `created_at` — reading a clock is I/O."""
    return {
        "version": SAVE_VERSION,
        "seed": state.seed,
        "state": asdict(state),
        "action_log": list(action_log),
    }


def load(payload: dict[str, Any]) -> GameState:
    version = payload.get("version")
    if version != SAVE_VERSION:
        raise ValueError(f"unsupported save version: {version!r}")
    snapshot = payload["state"]
    if payload.get("seed") != snapshot.get("seed"):
        raise ValueError("save seed does not match its state")
    # JSON has neither tuples nor dataclasses, so a saved bond comes back as a plain
    # dict and every tuple as a list.
    return GameState(
        **{
            **snapshot,
            **{name: tuple(snapshot[name]) for name in TUPLE_FIELDS},
            "relationships": {
                npc: Bond(**axes) for npc, axes in snapshot["relationships"].items()
            },
        }
    )
