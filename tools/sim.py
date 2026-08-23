from __future__ import annotations

import argparse
import statistics
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field

from false_nine.content import cards as card_content
from false_nine.core.actions import PlayerAction, can_do, step
from false_nine.core.calendar import CAREER_WEEKS
from false_nine.core.match.card import Card
from false_nine.core.resources import BASE_AP, FATIGUE_TRAIN
from false_nine.core.rng import Rng
from false_nine.core.state import GameState

BUDGET_MS = 400.0
AGE_26_WEEK = 101  # season 11 week 1, the first week he is 26
PERCENTILES = (1, 25, 50, 75, 99)

Policy = Callable[[GameState], PlayerAction]

TRAIN_THRESHOLD = 50.0
WORK_UNTIL = 30_000


def train_max(state: GameState) -> PlayerAction:
    """Train as hard as the body allows, ignore money entirely. The ceiling anchor:
    if this player lands in the 70s at 26, nobody reaches the 90s. See 03 §3.1."""
    if state.is_injured or state.fatigue + FATIGUE_TRAIN >= TRAIN_THRESHOLD:
        return PlayerAction("recover")
    weakest = min(("technique", "physical", "mental"), key=lambda s: getattr(state, s))
    return PlayerAction("train", weakest)


def balanced(state: GameState) -> PlayerAction:
    """Keeps the lights on, then trains. Closer to how the game is actually played."""
    if state.money < WORK_UNTIL:
        return PlayerAction("work")
    return train_max(state)


def broke(state: GameState) -> PlayerAction:
    """Always Work. The floor of the ability distribution."""
    return PlayerAction("work")


POLICIES: dict[str, Policy] = {
    "train_max": train_max,
    "balanced": balanced,
    "broke": broke,
}


@dataclass
class Career:
    """What one headless career is worth to the balance report."""

    ability_at_26: float = 0.0
    final: GameState = field(default_factory=lambda: GameState(seed=""))
    ratings: list[float] = field(default_factory=list)
    squeezed_weeks: int = 0  # weeks that opened below 4 AP — fatigue or stress bit


def best_card(state: GameState, cards: Mapping[str, Card]) -> str:
    """A policy's card pick: the best expected rating in hand that this beat allows.
    Ties break on id so the choice does not depend on hand order."""
    legal = [c for c in state.match_hand if cards[c].playable_in(state.beat_name)]
    return max(legal or list(state.match_hand), key=lambda c: (_expected(cards[c]), c))


def _expected(card: Card) -> float:
    return sum(o.weight * o.rating_delta for o in card.outcomes) / 100.0


def run_career(
    seed: str,
    policy: Policy,
    cards: Mapping[str, Card],
    until_week: int = CAREER_WEEKS + 1,
) -> Career:
    rng = Rng(seed)
    state = GameState(seed=seed)
    career = Career()

    while state.week_index < until_week:
        if state.week_index == AGE_26_WEEK and not career.ability_at_26:
            career.ability_at_26 = state.ability

        if state.in_match:
            action = PlayerAction("play_card", best_card(state, cards))
        elif state.match_pending:
            action = PlayerAction("start_match")
        elif state.ap > 0:
            action = policy(state)
        else:
            action = PlayerAction("end_week")

        if not can_do(state, action):
            action = PlayerAction("drift" if state.ap > 0 else "end_week")

        played, week = state.last_match_week, state.week_index
        state = step(state, action, rng, cards).state
        if state.last_match_week != played:
            career.ratings.append(state.last_match_rating)
        if state.week_index != week and state.ap < BASE_AP:
            career.squeezed_weeks += 1

    career.final = state
    return career


def percentiles(values: Sequence[float]) -> list[float]:
    if len(values) < 2:
        return [values[0] if values else 0.0] * len(PERCENTILES)
    cuts = statistics.quantiles(values, n=100, method="inclusive")
    return [cuts[p - 1] for p in PERCENTILES]


def report(careers: list[Career], strategy: str, elapsed_s: float) -> str:
    rows = {
        "ability at 26": [c.ability_at_26 for c in careers],
        "ability final": [c.final.ability for c in careers],
        "technique": [c.final.technique for c in careers],
        "physical": [c.final.physical for c in careers],
        "mental": [c.final.mental for c in careers],
        "form": [c.final.form for c in careers],
        "money": [float(c.final.money) for c in careers],
        "debt": [float(c.final.debt) for c in careers],
        "injuries": [float(c.final.injury_history) for c in careers],
        "matches played": [float(len(c.ratings)) for c in careers],
        "mean match rating": [
            statistics.fmean(c.ratings) if c.ratings else 0.0 for c in careers
        ],
        "weeks under 4 AP": [float(c.squeezed_weeks) for c in careers],
    }

    header = " | ".join(f"p{p}".rjust(9) for p in PERCENTILES)
    lines = [
        f"# balance - {strategy}, {len(careers)} careers, {elapsed_s:.1f}s",
        "",
        f"{'metric':<20} | {header}",
        f"{'-' * 20} | {'-' * len(header)}",
    ]
    for name, values in rows.items():
        cells = " | ".join(f"{v:9,.1f}" for v in percentiles(values))
        lines.append(f"{name:<20} | {cells}")
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="tools.sim")
    parser.add_argument("--careers", type=int, default=100)
    parser.add_argument("--strategy", choices=sorted(POLICIES), default="train_max")
    parser.add_argument("--seed-prefix", default="sim")
    parser.add_argument("--report", help="write the table here instead of stdout")
    args = parser.parse_args(argv)

    cards = card_content.load()
    policy = POLICIES[args.strategy]

    start = time.perf_counter()
    careers = [
        run_career(f"{args.seed_prefix}{i}", policy, cards) for i in range(args.careers)
    ]
    elapsed_s = time.perf_counter() - start

    table = report(careers, args.strategy, elapsed_s)
    if args.report:
        with open(args.report, "w", encoding="utf-8") as handle:
            handle.write(table)
    print(table, end="")

    per_career_ms = elapsed_s * 1000 / max(1, args.careers)
    print(f"\n{per_career_ms:.1f} ms per career (budget {BUDGET_MS:.0f} ms)")
    if per_career_ms > BUDGET_MS:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
