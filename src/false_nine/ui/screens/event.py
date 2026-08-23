from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from false_nine.content import strings
from false_nine.core.actions import PlayerAction
from false_nine.core.events.event import Choice, Event
from false_nine.ui import text, theme
from false_nine.ui.app import App, Screen

if TYPE_CHECKING:
    from false_nine.ui.screens.week import WeekScreen

LEFT = 64
TOP = 64
ROW = 32
WRAP = 720
PARAGRAPH_GAP = 12


class EventScreen(Screen):
    """One authored scene and its two to four choices. Gated choices are drawn, dim,
    with the reason beside them — 05 §1: seeing what you can't do is part of the
    design, so this screen never hides a row it will not let you take."""

    def __init__(self, app: App, week: WeekScreen, event: Event) -> None:
        self.app = app
        self.week = week
        self.event = event
        self.selection = 0
        self.outcome: str | None = None

    def handle(self, event: pygame.event.Event) -> bool:
        if event.type != pygame.KEYDOWN:
            return False
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self._confirm()
            return True
        if event.key in (pygame.K_DOWN, pygame.K_UP) and self.outcome is None:
            step = 1 if event.key == pygame.K_DOWN else -1
            self.selection = (self.selection + step) % len(self.event.choices)
            return True
        # Esc would pop the scene without answering it. The week is waiting on this.
        return event.key == pygame.K_ESCAPE

    def _confirm(self) -> None:
        if self.outcome is not None:
            self.app.pop()
            return
        choice = self.event.choices[self.selection]
        if not choice.is_open(self.week.state):
            return
        self.week.apply(PlayerAction("resolve_event", choice.id))
        self.outcome = choice.outcome_text

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(theme.bg_deep)
        y = TOP
        for line in self.event.body:
            y = text.draw_wrapped(surface, line, (LEFT, y), WRAP) + PARAGRAPH_GAP
        y += ROW

        if self.outcome is not None:
            y = text.draw_wrapped(
                surface, self.outcome, (LEFT, y), WRAP, colour=theme.text_muted
            )
            text.draw(
                surface,
                strings.text("event_continue"),
                (LEFT, TOP + 640),
                "label",
                theme.text_dim,
            )
            return

        for index, choice in enumerate(self.event.choices):
            self._choice(surface, y, choice, index == self.selection)
            y += ROW

    def _choice(
        self, surface: pygame.Surface, y: int, choice: Choice, selected: bool
    ) -> None:
        open_to_him = choice.is_open(self.week.state)
        colour = theme.text_primary if open_to_him else theme.text_dim
        if selected:
            ring = pygame.Rect(LEFT - 8, y - 4, WRAP + 16, ROW)
            pygame.draw.rect(surface, theme.accent_cold, ring, width=2)
        text.draw(surface, choice.text, (LEFT, y), "body", colour)
        if not open_to_him:
            text.draw(
                surface,
                strings.text("event_locked"),
                (LEFT + WRAP, y),
                "mono",
                theme.text_dim,
                right=True,
            )
