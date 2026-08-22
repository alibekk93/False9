from __future__ import annotations

from functools import cache

import pygame

from false_nine.ui import theme

# ponytail: system fonts, not the IBM Plex in 06 — assets/fonts/ does not exist yet.
# Swap the two family lists for Font(path, size) when it does; nothing else changes.
SANS = "segoeui,dejavusans,arial"
MONO = "consolas,dejavusansmono,couriernew,monospace"

ROLES = {
    "body": (SANS, 18, False),
    "mono": (MONO, 16, False),
    "header": (SANS, 28, True),
    "label": (SANS, 12, False),
}


@cache
def font(role: str) -> pygame.font.Font:
    family, size, bold = ROLES[role]
    return pygame.font.SysFont(family, size, bold=bold)


@cache
def render(content: str, role: str, colour: str) -> pygame.Surface:
    """Text rendering is the hot path (04); surfaces are cached, never re-rendered."""
    return font(role).render(content, True, colour)


def draw(
    surface: pygame.Surface,
    content: str,
    pos: tuple[int, int],
    role: str = "body",
    colour: str = theme.text_primary,
    right: bool = False,
) -> None:
    rendered = render(content, role, colour)
    x = pos[0] - rendered.get_width() if right else pos[0]
    surface.blit(rendered, (x, pos[1]))


def height(role: str) -> int:
    return font(role).get_linesize()
