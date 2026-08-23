from __future__ import annotations

from false_nine.content import bundle
from false_nine.content import npcs as npc_content
from false_nine.core.actions import PlayerAction, step
from false_nine.core.rng import Rng
from false_nine.core.save import dump, load
from false_nine.core.state import GameState
from tools.sim import run_career, train_max

ACTIONS = [
    PlayerAction("train", "technique"),
    PlayerAction("work"),
    PlayerAction("train", "physical"),
    PlayerAction("recover"),
    PlayerAction("end_week"),
    PlayerAction("train", "mental"),
    PlayerAction("socialise", "npc_kostya"),
    PlayerAction("drift"),
    PlayerAction("end_week"),
]


def replay(seed: str, actions: list[PlayerAction]) -> GameState:
    """A week with a match will not end until it is played, so the fixed action list is
    interleaved with the picks the hand actually offers."""
    rng = Rng(seed)
    content = bundle.load()
    state = bundle.new_career(seed)
    for action in actions * 12:
        if state.match_pending:
            state = step(state, PlayerAction("start_match"), rng, content).state
            while state.in_match:
                pick = PlayerAction("play_card", sorted(state.match_hand)[0])
                state = step(state, pick, rng, content).state
        # A scene or a contract blocks the week the way a match does; answering the
        # first thing offered keeps the fixed action list fixed.
        while state.pending_events:
            scene = content.events[state.pending_events[0]]
            legal = min(c.id for c in scene.choices if c.is_open(state))
            state = step(
                state, PlayerAction("resolve_event", legal), rng, content
            ).state
        if state.offers:
            pick = PlayerAction("sign", sorted(state.offers)[0])
            state = step(state, pick, rng, content).state
        state = step(state, action, rng, content).state
    return state


def test_replay_reproduces_state() -> None:
    assert replay("8f2c", ACTIONS) == replay("8f2c", ACTIONS)


def test_different_seeds_diverge() -> None:
    """Otherwise the test above would pass on a game that ignores its RNG entirely."""
    assert replay("8f2c", ACTIONS) != replay("other", ACTIONS)


def test_the_replay_actually_played_matches() -> None:
    """Guards the guard: if matches stopped firing, the test above still passes."""
    assert replay("8f2c", ACTIONS).last_match_week > 0


def test_the_replay_actually_socialised() -> None:
    """Same guard for the action that took an argument in M3: an unreachable or
    misnamed NPC would make every Socialise in the list a silent no-op."""
    bond = replay("8f2c", ACTIONS).relationships["npc_kostya"]
    assert bond.closeness > npc_content.load()["npc_kostya"].initial.closeness


def test_a_full_career_is_reproducible() -> None:
    a = run_career("full", train_max, bundle.load())
    b = run_career("full", train_max, bundle.load())
    assert a.final == b.final
    assert a.ratings == b.ratings


def test_save_roundtrip_after_a_played_career() -> None:
    state = replay("8f2c", ACTIONS)
    assert state.week_index > 1
    assert load(dump(state)) == state
