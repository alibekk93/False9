from __future__ import annotations

from uuid import uuid4

from false_nine.content import npcs as npc_content
from false_nine.core.state import GameState
from false_nine.ui.app import App
from false_nine.ui.screens.week import WeekScreen


def main() -> None:
    # No title or new-career screen yet (M4): a career starts on launch.
    app = App()
    seed = uuid4().hex[:8]
    state = GameState(seed=seed, relationships=npc_content.starting_bonds())
    app.push(WeekScreen(app, state))
    app.run()
