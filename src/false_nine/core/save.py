from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict
from typing import Any

from false_nine.core.state import Bond, GameState

# 2: M3 added the psyche fields and `relationships`. An M2 save has no bonds to
# rebuild, so it fails on the version check rather than on a KeyError three lines
# later. Migration proper is M9.
SAVE_VERSION = 2


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
    # JSON has neither tuples nor dataclasses, so a saved hand comes back as a list
    # and a saved bond as a plain dict; both would compare unequal to the state they
    # were written from.
    return GameState(
        **{
            **snapshot,
            "match_hand": tuple(snapshot["match_hand"]),
            "relationships": {
                npc: Bond(**axes) for npc, axes in snapshot["relationships"].items()
            },
        }
    )
