from __future__ import annotations

from dataclasses import dataclass

import pygame

from false_nine.content import strings
from false_nine.core.actions import TRAINABLE, Change, PlayerAction, can_do, step
from false_nine.core.rng import Rng
from false_nine.core.state import GameState
from false_nine.ui import text, theme
from false_nine.ui.app import App, Screen
from false_nine.ui.screens.ledger import LedgerScreen

COL_STATUS = 64
COL_WEEK = 476
TOP = 64
ROW = 32

ACTIONS = ("recover", "work", "socialise", "deal_with_it", "drift")


@dataclass(frozen=True)
class Row:
    label_key: str
    action: PlayerAction
    indent: int


class WeekScreen(Screen):
    def __init__(self, app: App, state: GameState) -> None:
        self.app = app
        self.state = state
        self.rng = Rng(state.seed)
        self.week_effects: list[Change] = []
        self.selection = 0
        self.expanded = False

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
            self.expanded = False
            self.selection = 0
            return True
        return False

    def _confirm(self, row: Row) -> None:
        if row.action.kind == "train" and row.action.arg is None:
            self.expanded = not self.expanded
            # Land on the first stat, so training is Enter-Enter and repeats on Enter.
            self.selection = 1 if self.expanded else 0
            return
        if not can_do(self.state, row.action):
            return

        self._apply(row.action)
        if row.action.kind == "drift":
            self._apply(PlayerAction("end_week"))
        if row.action.kind in ("drift", "end_week"):
            self._end_week()
        self.selection = min(self.selection, len(self._rows()) - 1)

    def _apply(self, action: PlayerAction) -> None:
        result = step(self.state, action, self.rng)
        self.state = result.state
        self.week_effects.extend(result.effects)

    def _end_week(self) -> None:
        self.expanded = False
        self.selection = 0
        if self.state.is_over:
            self.app.pop()
            return
        self.app.push(LedgerScreen(self.app, self.week_effects))
        self.week_effects = []

    # --- layout ------------------------------------------------------------

    def _rows(self) -> list[Row]:
        rows = [Row("act_train", PlayerAction("train"), 0)]
        if self.expanded:
            rows += [
                Row(f"arg_{stat}", PlayerAction("train", stat), 1) for stat in TRAINABLE
            ]
        rows += [Row(f"act_{kind}", PlayerAction(kind), 0) for kind in ACTIONS]
        rows.append(Row("act_end_week", PlayerAction("end_week"), 0))
        return rows

    def _available(self, row: Row) -> bool:
        if row.action.kind == "train" and row.action.arg is None:
            return can_do(self.state, PlayerAction("train", TRAINABLE[0]))
        return can_do(self.state, row.action)

    # --- drawing -----------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(theme.bg_deep)
        self._draw_status(surface)
        self._draw_actions(surface)

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
        self._field(surface, y, "label_body", body_word(state))
        y += ROW + 16
        self._field(surface, y, "label_money", f"{state.money:,}")
        y += ROW
        if state.debt:
            self._field(surface, y, "label_debt", f"{state.debt:,}", theme.neg)
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
            text.draw(surface, strings.text(row.label_key), (x, y), "body", colour)
            y += ROW


def body_word(state: GameState) -> str:
    """07 §4: the body is a word, never a number. Withholding precision, not lying."""
    words = strings.words("body_words")
    if state.injury_weeks_left >= 8:
        return words[6]
    if state.is_injured:
        return words[5]
    return words[min(4, int(state.fatigue // 20))]
