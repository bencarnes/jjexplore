"""NPC sprite. Stationary for now; behavior can grow over time."""
from __future__ import annotations

from typing import Tuple

import pygame


class NPC(pygame.sprite.Sprite):
    SIZE = 32
    DEFAULT_COLOR = (80, 130, 220)

    def __init__(
        self,
        position: Tuple[int, int] = (0, 0),
        color: Tuple[int, int, int] = DEFAULT_COLOR,
        name: str = "",
    ) -> None:
        super().__init__()
        self.name = name
        self.image = pygame.Surface((self.SIZE, self.SIZE), pygame.SRCALPHA)
        self.image.fill(color)
        pygame.draw.rect(self.image, (0, 0, 0), self.image.get_rect(), 2)
        pygame.draw.circle(self.image, (255, 255, 255), (self.SIZE // 2 - 5, self.SIZE // 2 - 4), 2)
        pygame.draw.circle(self.image, (255, 255, 255), (self.SIZE // 2 + 5, self.SIZE // 2 - 4), 2)
        self.rect = self.image.get_rect(topleft=position)

    def update(self, dt: float = 0.0) -> None:
        """Stationary."""
