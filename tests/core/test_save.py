from __future__ import annotations

import json

import pytest

from false_nine.core.save import SAVE_VERSION, dump, load
from false_nine.core.state import GameState


def test_roundtrip() -> None:
    state = GameState(seed="8f2c", week_index=94)
    assert load(dump(state)) == state


def test_roundtrip_survives_json() -> None:
    state = GameState(seed="8f2c", week_index=94)
    assert load(json.loads(json.dumps(dump(state)))) == state


def test_action_log_is_carried() -> None:
    payload = dump(
        GameState(seed="s"), [{"week": 1, "action": "train", "arg": "technique"}]
    )
    assert payload["action_log"] == [{"week": 1, "action": "train", "arg": "technique"}]


def test_unknown_version_is_rejected() -> None:
    payload = dump(GameState(seed="s"))
    payload["version"] = SAVE_VERSION + 1
    with pytest.raises(ValueError, match="version"):
        load(payload)


def test_mismatched_seed_is_rejected() -> None:
    payload = dump(GameState(seed="s"))
    payload["seed"] = "tampered"
    with pytest.raises(ValueError, match="seed"):
        load(payload)
