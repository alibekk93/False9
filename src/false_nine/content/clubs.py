from __future__ import annotations

import json
from functools import cache
from typing import Any

from false_nine.content.cards import ContentError, check_keys
from false_nine.content.strings import DATA
from false_nine.core.club import Club, Town
from false_nine.core.opportunity import TOP_TIER

CLUB_KEYS = frozenset(
    {
        "id",
        "name",
        "tier",
        "strength",
        "facilities",
        "solvency",
        "town",
        "wage_offer",
        "traits",
    }
)
TOWN_KEYS = frozenset({"name", "population", "remoteness"})

# 03 §6.1 has five tiers; nothing above TOP_TIER is reachable (§7.4), so nothing above
# it is authored. A tier-1 club in `data/` would be a place the game promises and
# cannot deliver.
BOTTOM_TIER = 5
FACILITY_RANGE = (0.5, 1.2)

# The club he is at when the game opens. Marked in `data/` rather than named here, so
# the one id core has no way to know still does not live in code.
HOME_TRAIT = "home"


@cache
def load() -> dict[str, Club]:
    clubs: dict[str, Club] = {}
    for path in sorted((DATA / "clubs").glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for raw in payload["items"]:
            club = _club(raw, path.name)
            if club.id in clubs:
                raise ContentError(f"{path.name}: duplicate club id {club.id}")
            clubs[club.id] = club
    if not clubs:
        raise ContentError(f"no clubs found under {DATA / 'clubs'}")
    _check_ladder(clubs)
    return clubs


def starting_club() -> Club:
    """What a career opens at. Core cannot read `data/`, so the caller that builds the
    first GameState passes the terms in, the way `npcs.starting_bonds` does."""
    home = [club for club in load().values() if HOME_TRAIT in club.traits]
    if len(home) != 1:
        raise ContentError(f"expected one {HOME_TRAIT!r} club, found {len(home)}")
    return home[0]


def _club(raw: dict[str, Any], where: str) -> Club:
    club_id = raw.get("id", "<no id>")
    where = f"{where}: {club_id}"
    check_keys(raw, CLUB_KEYS, where)
    if not str(club_id).startswith("club_"):
        raise ContentError(f"{where} does not start with club_")

    tier = raw["tier"]
    if not TOP_TIER <= tier <= BOTTOM_TIER:
        raise ContentError(f"{where}: tier {tier} is outside {TOP_TIER}-{BOTTOM_TIER}")

    facilities = float(raw["facilities"])
    if not FACILITY_RANGE[0] <= facilities <= FACILITY_RANGE[1]:
        raise ContentError(
            f"{where}: facilities {facilities} is outside 03 §3.1's range"
        )

    solvency = float(raw["solvency"])
    if not 0.0 <= solvency <= 100.0:
        raise ContentError(f"{where}: solvency {solvency} is outside 0-100")

    if int(raw["wage_offer"]) < 0:
        raise ContentError(f"{where}: wage_offer is negative")

    town = raw["town"]
    check_keys(town, TOWN_KEYS, f"{where}: town")

    return Club(
        id=raw["id"],
        name=raw["name"],
        tier=tier,
        strength=float(raw["strength"]),
        facilities=facilities,
        solvency=solvency,
        town=Town(
            name=town["name"],
            population=int(town["population"]),
            remoteness=float(town["remoteness"]),
        ),
        wage_offer=int(raw["wage_offer"]),
        traits=tuple(raw.get("traits", ())),
    )


def _check_ladder(clubs: dict[str, Club]) -> None:
    """Every rung he can be offered has to have somewhere on it. A tier with no clubs
    is a season unemployed that no rule intended."""
    for tier in range(TOP_TIER, BOTTOM_TIER + 1):
        if not any(club.tier == tier for club in clubs.values()):
            raise ContentError(f"no clubs at tier {tier}")
