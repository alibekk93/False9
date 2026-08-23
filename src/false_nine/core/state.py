from __future__ import annotations

from dataclasses import dataclass, field, replace

from false_nine.core import calendar, psyche
from false_nine.core.match.card import BEATS

HAND_SIZE = 5

# 03 §8. Order is the order they are written to the ledger and drawn in the People
# column, so it lives with the dataclass rather than in either consumer.
AXES = ("trust", "respect", "dependence", "closeness")


@dataclass(frozen=True)
class Bond:
    """One NPC's four axes plus the week he last made contact. The rules that move
    these live in `relationships.py`; this is only the record."""

    trust: float = 50.0
    respect: float = 50.0
    dependence: float = 20.0
    closeness: float = 50.0
    last_contact_week: int = 0


@dataclass(frozen=True)
class GameState:
    """The single source of truth. Only `week_index` is stored; season, week, age and
    phase are derived, so they cannot drift out of sync with each other.

    Fields are flat rather than nested so `save.load` can rebuild the state with
    `GameState(**snapshot)`. `relationships` is the one exception — it is keyed by an
    id that only `data/` knows, so it cannot be flattened — and `save.load` rebuilds
    its `Bond`s by hand."""

    seed: str
    week_index: int = 1

    technique: float = 30.0
    physical: float = 30.0
    mental: float = 20.0

    fatigue: float = 0.0
    form: float = 50.0

    # 03 §4. Four values, never shown as numbers, never touching ability.
    stress: float = psyche.STRESS_START
    hope: float = psyche.HOPE_START
    cynicism: float = psyche.CYNICISM_START
    self_knowledge: float = psyche.SELF_KNOWLEDGE_START

    # Seeded from data/npcs at career start; empty in a bare state, which is what the
    # core tests want. See content/npcs.starting_bonds.
    relationships: dict[str, Bond] = field(default_factory=dict)

    money: int = 0
    debt: int = 0

    # 03 §6. The club's fixed attributes stay in `data/`; what moves lives here.
    # `tier` is his level and not the club's — it moves only when an opportunity is
    # converted, never as a function of ability. That is 03 §7.1 in one field.
    tier: int = 5
    club_id: str = ""
    club_solvency: float = 0.0
    contract_wage: int = 0
    contract_seasons_left: int = 0
    arrears: int = 0
    offers: tuple[str, ...] = ()

    # 03 §7. The arc in progress, its conditions already rolled, and what he has
    # already been told. `failure_scenes_seen` spans the career, not the arc.
    opportunity_id: str = ""
    opportunity_failed: tuple[str, ...] = ()
    opportunity_revealed: tuple[str, ...] = ()
    opportunities_converted: int = 0
    failure_scenes_seen: tuple[str, ...] = ()

    # Scenes he owes the game before the week can end, and 05 §2's string flags.
    pending_events: tuple[str, ...] = ()
    flags: tuple[str, ...] = ()

    ap: int = 4

    injury_weeks_left: float = 0.0
    injury_history: int = 0

    # The match in progress. `match_hand` empty means there is none; it shrinks by one
    # card per beat, so the beat number is derived from it rather than stored.
    match_hand: tuple[str, ...] = ()
    momentum: int = 0
    match_performance: float = 0.0
    last_match_week: int = 0
    last_match_rating: float = 0.0
    # 03 §5.4: −1, 0 or 1. Shown, never celebrated, and it feeds nothing.
    last_team_result: int = 0

    @property
    def season(self) -> int:
        return calendar.season_of(self.week_index)

    @property
    def week(self) -> int:
        return calendar.week_of(self.week_index)

    @property
    def age(self) -> int:
        return calendar.age_of(self.week_index)

    @property
    def phase(self) -> int:
        return calendar.phase_of(self.week_index)

    @property
    def ability(self) -> float:
        return 0.4 * self.technique + 0.35 * self.physical + 0.25 * self.mental

    @property
    def is_injured(self) -> bool:
        return self.injury_weeks_left > 0

    @property
    def in_match(self) -> bool:
        return bool(self.match_hand)

    @property
    def beat(self) -> int:
        """1, 2 or 3. The hand loses a card per beat, so its size carries the count."""
        return HAND_SIZE + 1 - len(self.match_hand)

    @property
    def beat_name(self) -> str:
        return BEATS[min(self.beat, len(BEATS)) - 1]

    @property
    def match_pending(self) -> bool:
        """A match he is due to play and has not. 03 §1: no match while injured."""
        return (
            calendar.is_match_week(self.week_index)
            and not self.is_injured
            and self.last_match_week != self.week_index
        )

    @property
    def is_employed(self) -> bool:
        return bool(self.club_id)

    @property
    def is_owed_wages(self) -> bool:
        return self.arrears > 0

    @property
    def is_over(self) -> bool:
        return self.week_index > calendar.CAREER_WEEKS


def advance_week(state: GameState) -> GameState:
    return replace(state, week_index=state.week_index + 1)
