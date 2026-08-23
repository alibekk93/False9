from __future__ import annotations

from functools import cache

from false_nine.content import cards, clubs, events, npcs, opportunities
from false_nine.core.calendar import PHASE_1_SEASONS
from false_nine.core.content import Content
from false_nine.core.state import GameState


@cache
def load() -> Content:
    """Everything `step` needs, loaded once. Every loader validates as it goes and
    raises with the file and the id, so a bad `data/` fails here and not at week 94."""
    return Content(
        cards=cards.load(),
        clubs=clubs.load(),
        opportunities=opportunities.load(),
        events=events.load(),
    )


def new_career(seed: str) -> GameState:
    """Core cannot read `data/`, so the terms he starts on are assembled here. He opens
    at the club down the road on a deal that runs exactly as long as 02's academy
    years, which is what makes the end of season 3 a placement and not a formality."""
    home = clubs.starting_club()
    return GameState(
        seed=seed,
        relationships=npcs.starting_bonds(),
        tier=home.tier,
        club_id=home.id,
        club_solvency=home.solvency,
        contract_wage=home.wage_offer,
        contract_seasons_left=PHASE_1_SEASONS,
    )
