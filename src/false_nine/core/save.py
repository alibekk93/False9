from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict
from typing import Any

from false_nine.core.state import GameState

SAVE_VERSION = 1


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
    return GameState(**snapshot)
