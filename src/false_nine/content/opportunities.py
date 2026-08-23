from __future__ import annotations

import json
from functools import cache
from typing import Any

from false_nine.content import events as event_content
from false_nine.content import npcs as npc_content
from false_nine.content.cards import ContentError, check_keys
from false_nine.content.strings import DATA
from false_nine.core.calendar import WEEKS_PER_SEASON
from false_nine.core.events import expr
from false_nine.core.opportunity import Opportunity, WorldCondition
from false_nine.core.state import GameState

OPPORTUNITY_KEYS = frozenset(
    {
        "id",
        "season",
        "window_weeks",
        "player_conditions",
        "world_conditions",
        "success_event",
        "fail_event_player",
        "notes",
    }
)
CONDITION_KEYS = frozenset({"id", "p", "reveal_week", "fail_event"})

# 03 §7.2: four to six world conditions, each individually plausible at 55-75%. The
# product is what makes a well-prepared player's chance 8-15%, so the count and the
# band are the rule and not a suggestion — a fifth condition at 0.9 would quietly
# undo the whole system.
CONDITION_COUNT = (4, 6)
CONDITION_P = (0.55, 0.75)


@cache
def load() -> dict[str, Opportunity]:
    probe = GameState(seed="probe", relationships=npc_content.starting_bonds())
    events = event_content.load()
    opportunities: dict[str, Opportunity] = {}
    for path in sorted((DATA / "opportunities").glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for raw in payload["items"]:
            opp = _opportunity(raw, path.name, probe, frozenset(events))
            if opp.id in opportunities:
                raise ContentError(f"{path.name}: duplicate opportunity id {opp.id}")
            opportunities[opp.id] = opp
    if not opportunities:
        raise ContentError(f"no opportunities found under {DATA / 'opportunities'}")
    _check_schedule(opportunities)
    return opportunities


def _opportunity(
    raw: dict[str, Any], where: str, probe: GameState, events: frozenset[str]
) -> Opportunity:
    opp_id = raw.get("id", "<no id>")
    where = f"{where}: {opp_id}"
    check_keys(raw, OPPORTUNITY_KEYS, where)
    if not str(opp_id).startswith("opp_"):
        raise ContentError(f"{where} does not start with opp_")

    window = tuple(raw["window_weeks"])
    if len(window) != 2 or not 1 <= window[0] < window[1] <= WEEKS_PER_SEASON:
        raise ContentError(f"{where}: window_weeks {window} is not a week range")

    conditions = tuple(
        _condition(c, where, window, events) for c in raw["world_conditions"]
    )
    if not CONDITION_COUNT[0] <= len(conditions) <= CONDITION_COUNT[1]:
        raise ContentError(f"{where}: {len(conditions)} world conditions, not 4-6")
    if len({c.id for c in conditions}) != len(conditions):
        raise ContentError(f"{where}: duplicate world condition ids")

    for condition in raw["player_conditions"]:
        expr.validate(condition, probe, where)

    for key in ("success_event", "fail_event_player"):
        if raw[key] not in events:
            raise ContentError(f"{where}: {key} {raw[key]!r} is not authored")

    return Opportunity(
        id=raw["id"],
        season=int(raw["season"]),
        window_weeks=(window[0], window[1]),
        player_conditions=tuple(raw["player_conditions"]),
        world_conditions=conditions,
        success_event=raw["success_event"],
        fail_event_player=raw["fail_event_player"],
    )


def _condition(
    raw: dict[str, Any], where: str, window: tuple[int, ...], events: frozenset[str]
) -> WorldCondition:
    where = f"{where}/{raw.get('id', '<no id>')}"
    check_keys(raw, CONDITION_KEYS, where)

    p = float(raw["p"])
    if not CONDITION_P[0] <= p <= CONDITION_P[1]:
        raise ContentError(f"{where}: p {p} is outside 03 §7.2's 0.55-0.75")

    reveal = int(raw["reveal_week"])
    if not window[0] <= reveal <= window[1]:
        raise ContentError(f"{where}: reveal_week {reveal} is outside the window")

    # 03 §7.3 is a hard rule: no world condition may fail into generic text.
    if raw["fail_event"] not in events:
        raise ContentError(f"{where}: fail_event {raw['fail_event']!r} is not authored")

    return WorldCondition(
        id=raw["id"], p=p, reveal_week=reveal, fail_event=raw["fail_event"]
    )


def _check_schedule(opportunities: dict[str, Opportunity]) -> None:
    """One arc per season at most: `opportunity.due` takes the first it finds, and two
    in a season would silently mean one of them never happens."""
    seasons = [opp.season for opp in opportunities.values()]
    if len(set(seasons)) != len(seasons):
        raise ContentError(f"two opportunities share a season: {sorted(seasons)}")
