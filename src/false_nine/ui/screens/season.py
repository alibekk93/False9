from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from false_nine.content import clubs as club_content
from false_nine.content import strings
from false_nine.core.actions import PlayerAction
from false_nine.core.club import CONTRACT_SEASONS, Club
from false_nine.ui import text, theme
from false_nine.ui.app import App, Screen

if TYPE_CHECKING:
    from false_nine.ui.screens.week import WeekScreen

LEFT = 64
COL_TERMS = 480
TOP = 64
ROW = 32


class SeasonScreen(Screen):
    """The end of a season: what he was paid, what he is still owed, and who will have
    him. Every term is exact — hard rule 3 — including the solvency, which is the one
    number that says whether the wage is a wage or a plan."""

    def __init__(self, app: App, week: WeekScreen) -> None:
        self.app = app
        self.week = week
        self.clubs = club_content.load()
        self.selection = 0
        # The season that just finished, not the one the rollover has already started.
        self.season = max(1, week.state.season - 1)

    def handle(self, event: pygame.event.Event) -> bool:
        if event.type != pygame.KEYDOWN:
            return False
        offers = self.week.state.offers
        if event.key in (pygame.K_DOWN, pygame.K_UP) and offers:
            step = 1 if event.key == pygame.K_DOWN else -1
            self.selection = (self.selection + step) % len(offers)
            return True
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            if offers:
                self.week.apply(PlayerAction("sign", offers[self.selection]))
                self.selection = 0
            else:
                self.app.pop()
            return True
        # Nothing here is optional while there is a contract to sign.
        return event.key == pygame.K_ESCAPE

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(theme.bg_deep)
        state = self.week.state
        text.draw(
            surface,
            strings.text("season_header", season=self.season),
            (LEFT, TOP),
            "header",
        )

        y = TOP + 72
        text.draw(
            surface, strings.text("season_wages"), (LEFT, y), "label", theme.text_dim
        )
        y += ROW
        club = self.clubs.get(state.club_id)
        self._line(
            surface,
            y,
            strings.text("label_club"),
            club.name if club else strings.text("label_no_club"),
        )
        y += ROW
        self._line(surface, y, strings.text("season_arrears"), f"{state.arrears:,}")
        y += ROW + 24

        text.draw(
            surface, strings.text("season_contract"), (LEFT, y), "label", theme.text_dim
        )
        y += ROW
        if state.contract_seasons_left > 0 and club is not None:
            self._line(
                surface,
                y,
                club.name,
                strings.text("seasons_suffix", seasons=state.contract_seasons_left),
            )
            y += ROW + 24
        else:
            text.draw(
                surface,
                strings.text("season_contract_expired"),
                (LEFT, y),
                "body",
                theme.text_muted,
            )
            y += ROW + 24
            y = self._draw_offers(surface, y, state.offers)

        text.draw(
            surface,
            strings.text("season_continue"),
            (LEFT, TOP + 640),
            "label",
            theme.text_dim,
        )

    def _draw_offers(
        self, surface: pygame.Surface, y: int, offers: tuple[str, ...]
    ) -> int:
        text.draw(
            surface, strings.text("season_offers"), (LEFT, y), "label", theme.text_dim
        )
        y += ROW
        if not offers:
            text.draw(
                surface,
                strings.text("season_no_offers"),
                (LEFT, y),
                "body",
                theme.text_muted,
            )
            return y + ROW
        for index, club_id in enumerate(offers):
            if index == self.selection:
                ring = pygame.Rect(LEFT - 8, y - 4, 1088, ROW)
                pygame.draw.rect(surface, theme.accent_cold, ring, width=2)
            self._offer(surface, y, self.clubs[club_id])
            y += ROW
        return y

    def _offer(self, surface: pygame.Surface, y: int, club: Club) -> None:
        text.draw(surface, club.name, (LEFT, y), "body")
        terms = strings.text(
            "season_offer_terms",
            wage=f"{club.wage_offer:,}",
            seasons=strings.text("seasons_suffix", seasons=CONTRACT_SEASONS[club.tier]),
            solvency=f"{club.solvency:.0f}",
        )
        text.draw(surface, terms, (COL_TERMS, y), "mono", theme.text_muted)

    def _line(self, surface: pygame.Surface, y: int, label: str, value: str) -> None:
        text.draw(surface, label, (LEFT, y), "mono", theme.text_muted)
        text.draw(
            surface, value, (LEFT + 360, y), "mono", theme.text_primary, right=True
        )
