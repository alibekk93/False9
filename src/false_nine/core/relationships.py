from __future__ import annotations

from dataclasses import replace

from false_nine.core.effects import Change
from false_nine.core.resources import clamp01_100
from false_nine.core.state import AXES, Bond, GameState

CLOSENESS_SOCIALISE = 6.0
TRUST_SOCIALISE = 2.0

NEGLECT_WEEKS = 8
NEGLECT_CLOSENESS = -5.0
DRIFT_WEEKS = 20


def weeks_since_contact(bond: Bond, week_index: int) -> int:
    return week_index - bond.last_contact_week


def is_drifted(bond: Bond, week_index: int) -> bool:
    """03 §8. Drifted is not a stored flag — it is what silence looks like after long
    enough. Restoring one takes a repair event (M5), not another evening out."""
    return weeks_since_contact(bond, week_index) >= DRIFT_WEEKS


def is_reachable(state: GameState, npc: str) -> bool:
    bond = state.relationships.get(npc)
    return bond is not None and not is_drifted(bond, state.week_index)


def socialise(state: GameState, npc: str, effects: list[Change]) -> GameState:
    bond = state.relationships[npc]
    return _write(
        state,
        effects,
        npc,
        bond,
        replace(
            bond,
            closeness=clamp01_100(bond.closeness + CLOSENESS_SOCIALISE),
            trust=clamp01_100(bond.trust + TRUST_SOCIALISE),
            last_contact_week=state.week_index,
        ),
        "reason_socialise",
    )


def decay(state: GameState, effects: list[Change]) -> GameState:
    """03 §8. Fires once per eight weeks of silence, not once a week — eight weeks is
    the unit the spec names, and charging it weekly would empty a bond in under four
    months, which no friendship does."""
    for npc in sorted(state.relationships):
        bond = state.relationships[npc]
        since = weeks_since_contact(bond, state.week_index)
        if since > 0 and since % NEGLECT_WEEKS == 0:
            state = _write(
                state,
                effects,
                npc,
                bond,
                replace(
                    bond, closeness=clamp01_100(bond.closeness + NEGLECT_CLOSENESS)
                ),
                "reason_neglect",
            )
    return state


def _write(
    state: GameState,
    effects: list[Change],
    npc: str,
    before: Bond,
    after: Bond,
    reason: str,
) -> GameState:
    """Ledger rows are `npc_id.axis`, so one field name carries both halves and the
    screen splits it back apart. `last_contact_week` is bookkeeping, not a row."""
    for axis in AXES:
        old, new = getattr(before, axis), getattr(after, axis)
        if old != new:
            effects.append(Change(f"{npc}.{axis}", old, new, reason))
    return replace(state, relationships={**state.relationships, npc: after})
