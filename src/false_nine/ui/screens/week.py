from __future__ import annotations

from dataclasses import dataclass

import pygame

from false_nine.content import bundle, strings
from false_nine.content import clubs as club_content
from false_nine.content import npcs as npc_content
from false_nine.core import psyche, relationships
from false_nine.core.actions import (
    TRAINABLE,
    Change,
    PlayerAction,
    StepResult,
    can_do,
    step,
)
from false_nine.core.rng import Rng
from false_nine.core.state import GameState
from false_nine.ui import text, theme
from false_nine.ui.app import App, Screen
from false_nine.ui.screens.event import EventScreen
from false_nine.ui.screens.ledger import LedgerScreen
from false_nine.ui.screens.match import MatchScreen
from false_nine.ui.screens.season import SeasonScreen

COL_STATUS = 64
COL_WEEK = 476
COL_PEOPLE = 888
TOP = 64
ROW = 32

ACTIONS = ("recover", "work", "socialise", "deal_with_it", "drift")
SUBMENU_ROOTS = ("train", "socialise")
DRIFT_DOT_WEEKS = 5  # one dot per this many weeks of silence, four dots maximum
MAX_DRIFT_DOTS = 4


@dataclass(frozen=True)
class Row:
    """The label is resolved here rather than kept as a key, because an NPC's name
    comes from `data/npcs` and every other label comes from `data/strings`."""

    label: str
    action: PlayerAction
    indent: int


class WeekScreen(Screen):
    def __init__(self, app: App, state: GameState) -> None:
        self.app = app
        self.state = state
        self.rng = Rng(state.seed)
        self.content = bundle.load()
        self.cards = self.content.cards
        self.npcs = npc_content.load()
        self.clubs = club_content.load()
        self.week_effects: list[Change] = []
        self.selection = 0
        self.expanded: str | None = None

    # --- input -------------------------------------------------------------

    def handle(self, event: pygame.event.Event) -> bool:
        if event.type != pygame.KEYDOWN:
            return False
        rows = self._rows()
        if event.key in (pygame.K_DOWN, pygame.K_UP):
            direction = 1 if event.key == pygame.K_DOWN else -1
            self.selection = (self.selection + direction) % len(rows)
            return True
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self._confirm(rows[self.selection])
            return True
        if event.key == pygame.K_ESCAPE and self.expanded:
            self.expanded = None
            self.selection = 0
            return True
        return False

    def _confirm(self, row: Row) -> None:
        if row.action.kind in SUBMENU_ROOTS and row.action.arg is None:
            opening = self.expanded != row.action.kind
            self.expanded = row.action.kind if opening else None
            # Land on the first child, so a choice is Enter-Enter and repeats on Enter.
            self.selection += 1 if opening else 0
            return
        if not can_do(self.state, row.action):
            return

        week = self.state.week_index
        self.apply(row.action)
        if row.action.kind == "start_match":
            self.app.push(MatchScreen(self.app, self))
            return
        if row.action.kind == "drift":
            # Drift ends the week, but not before a match he is still due to play.
            self.apply(PlayerAction("end_week"))
        # Whether the week turned over, not whether it was asked to: Drift with a
        # match outstanding leaves him at 0 AP with the match still to play.
        if self.state.week_index != week:
            self._end_week()
        self.selection = min(self.selection, len(self._rows()) - 1)

    def apply(self, action: PlayerAction) -> StepResult:
        """MatchScreen, EventScreen and SeasonScreen call this too, so every change
        reaches one ledger."""
        result = step(self.state, action, self.rng, self.content)
        self.state = result.state
        self.week_effects.extend(result.effects)
        return result

    def _end_week(self) -> None:
        """Pushed in reverse: the ledger lands on top and each pop uncovers the next
        thing the week produced, so he reads what changed before he answers for it."""
        self.expanded = None
        self.selection = 0
        if self.state.is_over:
            self.app.pop()
            return
        if self.state.week == 1:
            self.app.push(SeasonScreen(self.app, self))
        for event_id in reversed(self.state.pending_events):
            self.app.push(EventScreen(self.app, self, self.content.events[event_id]))
        self.app.push(LedgerScreen(self.app, self.week_effects))
        self.week_effects = []

    # --- layout ------------------------------------------------------------

    def _rows(self) -> list[Row]:
        rows = [Row(strings.text("act_train"), PlayerAction("train"), 0)]
        if self.expanded == "train":
            rows += [
                Row(strings.text(f"arg_{stat}"), PlayerAction("train", stat), 1)
                for stat in TRAINABLE
            ]
        for kind in ACTIONS:
            rows.append(Row(strings.text(f"act_{kind}"), PlayerAction(kind), 0))
            if kind == "socialise" and self.expanded == "socialise":
                rows += [
                    Row(self.npcs[npc].name, PlayerAction("socialise", npc), 1)
                    for npc in self.npcs
                    if npc in self.state.relationships
                ]
        if self.state.match_pending:
            rows.append(
                Row(strings.text("act_start_match"), PlayerAction("start_match"), 0)
            )
        rows.append(Row(strings.text("act_end_week"), PlayerAction("end_week"), 0))
        return rows

    def _available(self, row: Row) -> bool:
        """A submenu root is available when any of its children is."""
        if row.action.arg is not None or row.action.kind not in SUBMENU_ROOTS:
            return can_do(self.state, row.action)
        args = (
            TRAINABLE if row.action.kind == "train" else tuple(self.state.relationships)
        )
        return any(can_do(self.state, PlayerAction(row.action.kind, a)) for a in args)

    # --- drawing -----------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(theme.bg_deep)
        self._draw_status(surface)
        self._draw_actions(surface)
        self._draw_people(surface)

    def _draw_status(self, surface: pygame.Surface) -> None:
        state = self.state
        y = TOP
        text.draw(
            surface,
            strings.text("week_header", season=state.season, week=state.week),
            (COL_STATUS, y),
            "header",
        )
        y += ROW + 8
        text.draw(
            surface,
            strings.text("age", age=state.age),
            (COL_STATUS, y),
            "mono",
            theme.text_muted,
        )

        y += ROW + 16
        text.draw(
            surface,
            strings.text("col_status"),
            (COL_STATUS, y),
            "label",
            theme.text_dim,
        )
        y += ROW
        for field in TRAINABLE:
            self._field(surface, y, f"label_{field}", f"{getattr(state, field):.1f}")
            y += ROW

        y += 16
        # 07: form is exact, like every other number. Only the body and mood are words.
        self._field(surface, y, "label_form", f"{state.form:.1f}")
        y += ROW + 16
        self._field(surface, y, "label_body", body_word(state))
        y += ROW
        self._field(surface, y, "label_mood", mood_word(state))
        y += ROW + 16
        club = self.clubs.get(state.club_id)
        self._field(
            surface,
            y,
            "label_club",
            club.name if club else strings.text("label_no_club"),
            theme.text_primary if club else theme.text_dim,
        )
        y += ROW
        if state.contract_wage:
            self._field(surface, y, "label_contract_wage", f"{state.contract_wage:,}")
            y += ROW

        y += 16
        self._field(surface, y, "label_money", f"{state.money:,}")
        y += ROW
        if state.debt:
            self._field(surface, y, "label_debt", f"{state.debt:,}", theme.neg)
            y += ROW
        if state.is_owed_wages:
            self._field(surface, y, "label_arrears", f"{state.arrears:,}", theme.neg)
            y += ROW
        if state.is_injured:
            weeks = strings.text(
                "weeks_suffix", weeks=int(state.injury_weeks_left + 0.5)
            )
            self._field(surface, y, "label_injury_weeks_left", weeks, theme.neg)

    def _field(
        self,
        surface: pygame.Surface,
        y: int,
        label_key: str,
        value: str,
        colour: str = theme.text_primary,
    ) -> None:
        text.draw(
            surface, strings.text(label_key), (COL_STATUS, y), "mono", theme.text_muted
        )
        text.draw(surface, value, (COL_STATUS + 300, y), "mono", colour, right=True)

    def _draw_actions(self, surface: pygame.Surface) -> None:
        y = TOP
        text.draw(
            surface,
            strings.text("col_this_week"),
            (COL_WEEK, y),
            "label",
            theme.text_dim,
        )
        y += ROW + 16

        text.draw(
            surface,
            strings.text("label_action_points"),
            (COL_WEEK, y),
            "label",
            theme.text_muted,
        )
        y += ROW
        dots = "  ".join("○" * self.state.ap) or "·"
        text.draw(surface, dots, (COL_WEEK, y), "body", theme.accent_cold)
        y += ROW + 16

        for index, row in enumerate(self._rows()):
            available = self._available(row)
            colour = theme.text_primary if available else theme.text_dim
            x = COL_WEEK + 24 * row.indent
            if index == self.selection:
                ring = pygame.Rect(x - 8, y - 4, 300 - 24 * row.indent, ROW)
                pygame.draw.rect(surface, theme.accent_cold, ring, width=2)
            text.draw(surface, row.label, (x, y), "body", colour)
            y += ROW

    def _draw_people(self, surface: pygame.Surface) -> None:
        """07: the dots are how long it has been. Nobody is warned they are drifting
        until the name goes dim, which is roughly how it happens."""
        y = TOP
        text.draw(
            surface,
            strings.text("col_people"),
            (COL_PEOPLE, y),
            "label",
            theme.text_dim,
        )
        y += ROW + 16
        for npc_id, npc in self.npcs.items():
            bond = self.state.relationships.get(npc_id)
            if bond is None:
                continue
            week = self.state.week_index
            drifted = relationships.is_drifted(bond, week)
            colour = theme.text_dim if drifted else theme.text_muted
            since = relationships.weeks_since_contact(bond, week)
            mark = (
                strings.text("people_drifted")
                if drifted
                else "·" * min(MAX_DRIFT_DOTS, max(0, since) // DRIFT_DOT_WEEKS)
            )
            text.draw(surface, npc.name, (COL_PEOPLE, y), "mono", colour)
            text.draw(surface, mark, (COL_PEOPLE + 300, y), "mono", colour, right=True)
            y += ROW


def body_word(state: GameState) -> str:
    """07 §4: the body is a word, never a number. Withholding precision, not lying."""
    words = strings.words("body_words")
    if state.injury_weeks_left >= 8:
        return words[6]
    if state.is_injured:
        return words[5]
    return words[min(4, int(state.fatigue // 20))]


def mood_word(state: GameState) -> str:
    """07 §4: three psyche values collapse to one of seven words. The player must not
    be able to read a number back out, so the bands are wide on purpose."""
    words = strings.words("mood_words")
    strain = psyche.strain(state.stress, state.hope, state.cynicism)
    return words[min(len(words) - 1, int(strain // psyche.MOOD_BAND))]
