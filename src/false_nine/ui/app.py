from __future__ import annotations

import pygame

from false_nine.ui import theme


class Screen:
    def handle(self, event: pygame.event.Event) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        pass


class BlankScreen(Screen):
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(theme.bg_deep)


class App:
    def __init__(self) -> None:
        self.screens: list[Screen] = []
        self.running = False

    def push(self, screen: Screen) -> None:
        self.screens.append(screen)

    def pop(self) -> None:
        self.screens.pop()
        if not self.screens:
            self.running = False

    def run(self) -> None:
        pygame.init()
        pygame.display.set_caption("False Nine")
        window = pygame.display.set_mode(theme.LOGICAL_SIZE, pygame.RESIZABLE)
        logical = pygame.Surface(theme.LOGICAL_SIZE)
        clock = pygame.time.Clock()

        if not self.screens:
            self.push(BlankScreen())
        self.running = True

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.pop()
                elif self.screens:
                    self.screens[-1].handle(event)

            if self.screens:
                self.screens[-1].draw(logical)
            self._present(window, logical)
            clock.tick(60)

        pygame.quit()

    @staticmethod
    def _present(window: pygame.Surface, logical: pygame.Surface) -> None:
        """Integer-scale the logical surface into the window, centred, letterboxed."""
        win_w, win_h = window.get_size()
        log_w, log_h = logical.get_size()
        # ponytail: integer scale floors at 1x, so a display under 1280x800 crops rather
        # than letterboxes. Fractional smoothscale fallback if a real user hits it.
        scale = max(1, min(win_w // log_w, win_h // log_h))
        scaled = pygame.transform.scale_by(logical, scale)
        window.fill(theme.bg_deep)
        window.blit(scaled, scaled.get_rect(center=(win_w // 2, win_h // 2)))
        pygame.display.flip()
