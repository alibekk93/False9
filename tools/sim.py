from __future__ import annotations

import time
from collections.abc import Callable

from false_nine.core.actions import PlayerAction, can_do, step
from false_nine.core.calendar import CAREER_WEEKS
from false_nine.core.resources import FATIGUE_TRAIN
from false_nine.core.rng import Rng
from false_nine.core.state import GameState

BUDGET_MS = 400.0

Policy = Callable[[GameState], PlayerAction]

# The full balance harness (N careers, distributions, strategies, reports) is M2's job.
# This is the one policy M1 needs: the calibration anchor for stats.BASE_GAIN.
TRAIN_THRESHOLD = 50.0


def train_max(state: GameState) -> PlayerAction:
    """Train as hard as the body allows, ignore money entirely. The ceiling anchor:
    if this player lands in the 70s at 26, nobody reaches the 90s. See 03 §3.1."""
    if state.is_injured or state.fatigue + FATIGUE_TRAIN >= TRAIN_THRESHOLD:
        return PlayerAction("recover")
    weakest = min(("technique", "physical", "mental"), key=lambda s: getattr(state, s))
    return PlayerAction("train", weakest)


def run_career(
    seed: str, policy: Policy, until_week: int = CAREER_WEEKS + 1
) -> GameState:
    rng = Rng(seed)
    state = GameState(seed=seed)
    while state.week_index < until_week:
        action = policy(state) if state.ap > 0 else PlayerAction("end_week")
        if not can_do(state, action):
            action = PlayerAction("drift" if state.ap > 0 else "end_week")
        state = step(state, action, rng).state
    return state


def main() -> None:
    start = time.perf_counter()
    state = run_career("m1", train_max)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert state.week_index == CAREER_WEEKS + 1, state.week_index
    print(f"{CAREER_WEEKS} weeks in {elapsed_ms:.1f} ms (budget {BUDGET_MS:.0f} ms)")
    print(
        f"final: tech {state.technique:.1f} phys {state.physical:.1f} "
        f"ment {state.mental:.1f} ability {state.ability:.1f} "
        f"injuries {state.injury_history}"
    )
    if elapsed_ms > BUDGET_MS:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
