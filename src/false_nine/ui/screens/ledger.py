from __future__ import annotations

import pygame

from false_nine.content import npcs as npc_content
from false_nine.content import strings
from false_nine.core.actions import Change
from false_nine.ui import text, theme
from false_nine.ui.app import App, Screen

LEFT = 64
TOP = 64
ROW = 28
REVEAL_MS = 90  # 06: watching the damage arrive one line at a time is the feeling
MINUS = "−"  # U+2212, so a loss reads the same in the value and the delta columns

MONEY_FIELDS = frozenset({"money", "debt", "arrears", "contract_wage"})
# 07 §4: shown as a direction, never a number.
PSYCHE_FIELDS = frozenset({"stress", "hope", "cynicism", "self_knowledge"})
WHOLE_FIELDS = frozenset(
    {"injury_weeks_left", "injury_history", "contract_seasons_left", "tier"}
)
LOWER_IS_BETTER = frozenset(
    {
        "debt",
        "arrears",
        "fatigue",
        "stress",
        "cynicism",
        "dependence",
        "injury_weeks_left",
        "injury_history",
        # A smaller number is a higher division. The one row on this screen where
        # down is up, which is why it is named here rather than inferred.
        "tier",
    }
)


class LedgerScreen(Screen):
    def __init__(self, app: App, effects: list[Change]) -> None:
        self.app = app
        self.rows = collapse(effects)
        self.opened = pygame.time.get_ticks()
        self.revealed = 0

    def handle(self, event: pygame.event.Event) -> bool:
        if event.type != pygame.KEYDOWN:
            return False
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            if self.revealed < len(self.rows):
                # No timed input anywhere (07): this reveals the rest, never skips them.
                self.opened -= REVEAL_MS * len(self.rows)
            else:
                self.app.pop()
            return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(theme.bg_deep)
        elapsed = pygame.time.get_ticks() - self.opened
        self.revealed = min(len(self.rows), elapsed // REVEAL_MS)

        text.draw(surface, strings.text("ledger_header"), (LEFT, TOP), "header")
        y = TOP + 56
        if not self.rows:
            text.draw(
                surface,
                strings.text("ledger_quiet"),
                (LEFT, y),
                "body",
                theme.text_muted,
            )
        for change in self.rows[: self.revealed]:
            self._row(surface, y, change)
            y += ROW

        if self.revealed == len(self.rows):
            text.draw(
                surface,
                strings.text("ledger_continue"),
                (LEFT, TOP + 640),
                "label",
                theme.text_dim,
            )

    def _row(self, surface: pygame.Surface, y: int, change: Change) -> None:
        npc, _, field = change.field.rpartition(".")
        delta = change.after - change.before
        improved = (delta < 0) if field in LOWER_IS_BETTER else (delta > 0)
        colour = theme.pos if improved else theme.neg

        text.draw(surface, label(change.field), (LEFT, y), "mono", theme.text_muted)
        # 07: the sign carries the meaning, so colour is never the only channel.
        sign = "+" if delta > 0 else MINUS
        if npc:
            # 07's mockup shows the movement but not the value: how far a friendship
            # has left to give is not a thing anyone knows about their own.
            text.draw(
                surface,
                f"{sign}{number(field, abs(delta))}",
                (LEFT + 600, y),
                "mono",
                colour,
                right=True,
            )
        elif field in PSYCHE_FIELDS:
            # 07 §4: psyche is never a number. The direction is all the player gets.
            text.draw(surface, sign, (LEFT + 600, y), "mono", colour, right=True)
        else:
            before = number(field, change.before)
            arrow = f"{before} → {number(field, change.after)}"
            text.draw(
                surface, arrow, (LEFT + 460, y), "mono", theme.text_primary, right=True
            )
            text.draw(
                surface,
                f"{sign}{number(field, abs(delta))}",
                (LEFT + 600, y),
                "mono",
                colour,
                right=True,
            )
        text.draw(
            surface,
            strings.text(change.reason),
            (LEFT + 640, y),
            "mono",
            theme.text_muted,
        )


def label(field: str) -> str:
    """A relationship row is `npc_id.axis`; everything else is a plain field name."""
    npc, _, axis = field.rpartition(".")
    if not npc:
        return strings.text(f"label_{field}")
    return f"{npc_content.load()[npc].name} {strings.text(f'label_{axis}')}"


def number(field: str, value: float) -> str:
    if field in MONEY_FIELDS:
        rendered = f"{round(value):,}"
    elif field in WHOLE_FIELDS:
        rendered = f"{round(value)}"
    else:
        rendered = f"{value:.1f}"
    return rendered.replace("-", MINUS)


def collapse(effects: list[Change]) -> list[Change]:
    """One row per field per reason. Four training sessions are one line, not four.
    Rows that net out to no change are dropped — 07: unchanged omitted."""
    merged: dict[tuple[str, str], Change] = {}
    for change in effects:
        key = (change.field, change.reason)
        first = merged.get(key)
        merged[key] = Change(
            change.field,
            first.before if first else change.before,
            change.after,
            change.reason,
        )
    return [c for c in merged.values() if c.before != c.after]
