from __future__ import annotations

from false_nine.core.actions import PlayerAction, step
from false_nine.core.rng import Rng
from false_nine.core.save import dump, load
from false_nine.core.state import GameState

ACTIONS = [
    PlayerAction("train", "technique"),
    PlayerAction("work"),
    PlayerAction("train", "physical"),
    PlayerAction("recover"),
    PlayerAction("end_week"),
    PlayerAction("train", "mental"),
    PlayerAction("socialise"),
    PlayerAction("drift"),
    PlayerAction("end_week"),
]


def replay(seed: str, actions: list[PlayerAction]) -> GameState:
    rng = Rng(seed)
    state = GameState(seed=seed)
    for action in actions * 12:
        state = step(state, action, rng).state
    return state


def test_replay_reproduces_state() -> None:
    assert replay("8f2c", ACTIONS) == replay("8f2c", ACTIONS)


def test_different_seeds_diverge() -> None:
    """Otherwise the test above would pass on a game that ignores its RNG entirely."""
    assert replay("8f2c", ACTIONS) != replay("other", ACTIONS)


def test_save_roundtrip_after_a_played_career() -> None:
    state = replay("8f2c", ACTIONS)
    assert state.week_index > 1
    assert load(dump(state)) == state
