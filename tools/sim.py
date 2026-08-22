from __future__ import annotations

import time

from false_nine.core.calendar import CAREER_WEEKS
from false_nine.core.state import GameState, advance_week

BUDGET_MS = 400.0


def run_career(seed: str) -> GameState:
    state = GameState(seed=seed)
    while not state.is_over:
        state = advance_week(state)
    return state


def main() -> None:
    start = time.perf_counter()
    state = run_career("m0")
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert state.week_index == CAREER_WEEKS + 1, state.week_index
    print(f"{CAREER_WEEKS} weeks in {elapsed_ms:.1f} ms (budget {BUDGET_MS:.0f} ms)")
    if elapsed_ms > BUDGET_MS:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
