"""Item sprite shown in the world. Picked up via interaction."""
from __future__ import annotations

from typing import Tuple

import pygame


class Item(pygame.sprite.Sprite):
    SIZE = 16
    DEFAULT_COLOR = (240, 200, 60)

    def __init__(
        self,
        position: Tuple[int, int] = (0, 0),
        name: str = "",
        color: Tuple[int, int, int] = DEFAULT_COLOR,
    ) -> None:
        super().__init__()
        self.name = name
        self.image = pygame.Surface((self.SIZE, self.SIZE), pygame.SRCALPHA)
        radius = self.SIZE // 2 - 1
        center = (self.SIZE // 2, self.SIZE // 2)
        pygame.draw.circle(self.image, color, center, radius)
        pygame.draw.circle(self.image, (40, 30, 0), center, radius, 1)
        self.rect = self.image.get_rect(topleft=position)

    def update(self, dt: float = 0.0) -> None:
        """Stationary."""
