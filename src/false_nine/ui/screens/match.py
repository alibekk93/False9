from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from false_nine.content import cards as card_content
from false_nine.content import reports, strings
from false_nine.core.actions import PlayerAction
from false_nine.core.match.card import Card
from false_nine.ui import text, theme
from false_nine.ui.app import App, Screen

if TYPE_CHECKING:
    from false_nine.ui.screens.week import WeekScreen

LEFT = 48
TOP = 64
ROW = 28
CARD_TOP = 500
CARD_WIDTH = 224
CARD_HEIGHT = 220
CARD_GAP = 16
CARD_PAD = 12
OUTCOME_TOP = 220
MEASURE = 1280 - 2 * theme.MARGIN

# 07: a minimum, never a deadline. Nothing on this screen is on a timer the player
# can lose to; holding Enter only ever moves it forward.
HOLD_MS = 1600


class MatchScreen(Screen):
    """Three beats of card play. The hand and every consequence live in GameState —
    this screen only chooses which card to send to `step`."""

    def __init__(self, app: App, week: WeekScreen) -> None:
        self.app = app
        self.week = week
        self.cards = card_content.load()
        self.selection = 0
        self.outcome: str | None = None
        self.resolved_at = 0
        self.report: str | None = None

    @property
    def hand(self) -> list[Card]:
        return [self.cards[card_id] for card_id in self.week.state.match_hand]

    # --- input -------------------------------------------------------------

    def handle(self, event: pygame.event.Event) -> bool:
        if event.type != pygame.KEYDOWN:
            return False
        if self.report is not None:
            return self._finish() if _is_confirm(event) else False
        if self.outcome is not None:
            return self._advance() if _is_confirm(event) else False

        if pygame.K_1 <= event.key <= pygame.K_5:
            self.selection = event.key - pygame.K_1
            self._confirm()
            return True
        if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
            step = 1 if event.key in (pygame.K_RIGHT, pygame.K_DOWN) else -1
            self.selection = (self.selection + step) % len(self.hand)
            return True
        if _is_confirm(event):
            self._confirm()
            return True
        return False

    def _confirm(self) -> None:
        if self.selection >= len(self.hand):
            return
        card = self.hand[self.selection]
        if not self._playable(card):
            return

        resolved = self.week.apply(PlayerAction("play_card", card.id))
        assert resolved.outcome is not None  # every played card resolves to one
        self.outcome = resolved.outcome.text
        self.resolved_at = pygame.time.get_ticks()
        self.selection = 0

    def _advance(self) -> bool:
        if pygame.time.get_ticks() - self.resolved_at < HOLD_MS:
            return True  # consumed, so Enter never skips a beat that has not held
        self.outcome = None
        if not self.week.state.in_match:
            state = self.week.state
            self.report = reports.for_rating(
                state.last_match_rating,
                self.week.rng.stream("report", state.week_index),
            )
        return True

    def _finish(self) -> bool:
        self.app.pop()
        return True

    def _playable(self, card: Card) -> bool:
        """A card out of its beat is shown and refused. If that would leave nothing to
        play, everything is legal — the hand must never be a dead end."""
        if card.playable_in(self.week.state.beat_name):
            return True
        return not any(c.playable_in(self.week.state.beat_name) for c in self.hand)

    # --- drawing -----------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(theme.bg_deep)
        if self.report is not None:
            self._draw_report(surface)
            return

        state = self.week.state
        text.draw(surface, strings.text("match_header"), (LEFT, TOP), "header")
        text.draw(
            surface,
            strings.text(
                "match_beat",
                beat=strings.text(f"beat_{state.beat_name}"),
                number=min(state.beat, 3),
            ),
            (LEFT, TOP + 40),
            "label",
            theme.text_muted,
        )

        if self.outcome is not None:
            text.draw_wrapped(
                surface, self.outcome, (LEFT, OUTCOME_TOP), MEASURE, "body"
            )
            if pygame.time.get_ticks() - self.resolved_at >= HOLD_MS:
                text.draw(
                    surface,
                    strings.text("match_continue"),
                    (LEFT, CARD_TOP + CARD_HEIGHT),
                    "label",
                    theme.text_dim,
                )
            return

        for index, card in enumerate(self.hand):
            self._draw_card(surface, index, card)
        text.draw(
            surface,
            strings.text("match_pick"),
            (LEFT, CARD_TOP + CARD_HEIGHT + 16),
            "label",
            theme.text_dim,
        )

    def _draw_card(self, surface: pygame.Surface, index: int, card: Card) -> None:
        rect = pygame.Rect(
            LEFT + index * (CARD_WIDTH + CARD_GAP), CARD_TOP, CARD_WIDTH, CARD_HEIGHT
        )
        playable = self._playable(card)
        pygame.draw.rect(surface, theme.bg_raised if playable else theme.bg_panel, rect)
        if index == self.selection:
            pygame.draw.rect(surface, theme.accent_cold, rect, width=2)

        x, inner = rect.x + CARD_PAD, CARD_WIDTH - 2 * CARD_PAD
        y = rect.y + CARD_PAD
        text.draw(surface, str(index + 1), (x, y), "label", theme.text_dim)
        y += ROW
        y = text.draw_wrapped(
            surface,
            card.title,
            (x, y),
            inner,
            "body",
            theme.text_primary if playable else theme.text_dim,
        )
        y += 8
        text.draw_wrapped(
            surface, card.flavour, (x, y), inner, "mono", theme.text_muted
        )
        if not playable:
            # 07: colour is never the only channel, so the reason is spelled out.
            text.draw(
                surface,
                strings.text("match_card_locked"),
                (x, rect.bottom - CARD_PAD - text.height("label")),
                "label",
                theme.text_dim,
            )

    def _draw_report(self, surface: pygame.Surface) -> None:
        assert self.report is not None
        rating = self.week.state.last_match_rating
        text.draw(surface, strings.text("match_afterwards"), (LEFT, TOP), "header")
        text.draw(
            surface,
            strings.text("match_rating"),
            (LEFT, TOP + 56),
            "mono",
            theme.text_muted,
        )
        text.draw(surface, f"{rating:.1f}", (LEFT + 300, TOP + 56), "mono", right=True)
        text.draw_wrapped(surface, self.report, (LEFT, TOP + 120), MEASURE, "body")
        text.draw(
            surface,
            strings.text("match_continue"),
            (LEFT, TOP + 600),
            "label",
            theme.text_dim,
        )


def _is_confirm(event: pygame.event.Event) -> bool:
    return event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
