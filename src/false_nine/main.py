from __future__ import annotations

from uuid import uuid4

from false_nine.content import bundle
from false_nine.ui.app import App
from false_nine.ui.screens.week import WeekScreen


def main() -> None:
    # No title or new-career screen yet: 09 puts the shell at M8, and a career that
    # starts on launch is the fastest way to look at the week.
    app = App()
    state = bundle.new_career(uuid4().hex[:8])
    app.push(WeekScreen(app, state))
    app.run()
