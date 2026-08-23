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


@cache
def wrap(content: str, role: str, width: int) -> tuple[str, ...]:
    """Greedy word wrap. Cached alongside `render`, since the paragraphs it wraps —
    card flavour, the match report — are redrawn every frame they are on screen."""
    measure = font(role)
    lines: list[str] = []
    line = ""
    for word in content.split():
        candidate = f"{line} {word}" if line else word
        if line and measure.size(candidate)[0] > width:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    return tuple(lines)


def draw_wrapped(
    surface: pygame.Surface,
    content: str,
    pos: tuple[int, int],
    width: int,
    role: str = "body",
    colour: str = theme.text_primary,
) -> int:
    """Returns the y the caller should carry on from."""
    y = pos[1]
    for line in wrap(content, role, width):
        draw(surface, line, (pos[0], y), role, colour)
        y += height(role)
    return y
