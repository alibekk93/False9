from __future__ import annotations

from dataclasses import replace

from false_nine.core import relationships
from false_nine.core.actions import PlayerAction, can_do, end_week, step
from false_nine.core.content import Content
from false_nine.core.effects import Change
from false_nine.core.rng import Rng
from false_nine.core.state import Bond, GameState

RNG = Rng("t")
NPC = "npc_x"


def state(bond: Bond | None = None, **kwargs: object) -> GameState:
    return replace(GameState(seed="t", relationships={NPC: bond or Bond()}), **kwargs)


def weeks(start: GameState, count: int) -> tuple[GameState, list[Change]]:
    """Turn the week over `count` times without spending any AP on the way."""
    effects: list[Change] = []
    for _ in range(count):
        result = end_week(replace(start, ap=0), RNG, Content())
        effects.extend(result.effects)
        start = result.state
    return start, effects


def test_socialise_moves_closeness_trust_and_stress() -> None:
    before = state(Bond(trust=40.0, closeness=50.0), stress=30.0, week_index=7)
    after = step(before, PlayerAction("socialise", NPC), RNG, Content()).state
    bond = after.relationships[NPC]

    assert (bond.closeness, bond.trust) == (56.0, 42.0)
    assert after.stress == 22.0
    assert bond.last_contact_week == 7
    # 03 §8: respect and dependence are not things an evening out buys.
    assert (bond.respect, bond.dependence) == (50.0, 20.0)


def test_socialise_clamps_at_the_top() -> None:
    after = step(
        state(Bond(trust=99.0, closeness=97.0)), PlayerAction("socialise", NPC), RNG, {}
    ).state
    bond = after.relationships[NPC]
    assert (bond.closeness, bond.trust) == (100.0, 100.0)


def test_an_unknown_npc_is_not_a_silent_no_op() -> None:
    assert not can_do(state(), PlayerAction("socialise", "npc_nobody"))
    assert not can_do(state(), PlayerAction("socialise"))


def test_neglect_bites_on_the_eighth_week_not_before() -> None:
    seven, _ = weeks(state(Bond(closeness=50.0)), 7)
    assert seven.relationships[NPC].closeness == 50.0

    eight, effects = weeks(state(Bond(closeness=50.0)), 8)
    assert eight.relationships[NPC].closeness == 45.0
    assert any(c.field == f"{NPC}.closeness" for c in effects), "no ledger row"


def test_neglect_repeats_every_eight_weeks_not_every_week() -> None:
    """03 §8 names eight weeks as the unit. Charged weekly a bond would be empty in
    under four months, which is not what not calling your mother does."""
    after, _ = weeks(state(Bond(closeness=80.0)), 17)
    assert after.relationships[NPC].closeness == 70.0


def test_contact_resets_the_clock() -> None:
    quiet, _ = weeks(state(Bond(closeness=50.0)), 7)
    seen = step(quiet, PlayerAction("socialise", NPC), RNG, Content()).state
    after, _ = weeks(seen, 7)
    assert after.relationships[NPC].closeness == 56.0  # +6 socialise, no decay


def test_twenty_weeks_of_silence_puts_him_out_of_reach() -> None:
    """03 §8: drifted is not a flag, it is what silence looks like. Only a repair
    event brings one back, and there are none until M5."""
    bond = Bond()
    assert not relationships.is_drifted(bond, 19)
    assert relationships.is_drifted(bond, 20)

    after, _ = weeks(state(), 20)
    assert not can_do(after, PlayerAction("socialise", NPC))


def test_bonds_survive_a_save_round_trip() -> None:
    from false_nine.core.save import dump, load

    played = step(
        state(week_index=4), PlayerAction("socialise", NPC), RNG, Content()
    ).state
    assert load(dump(played)) == played
