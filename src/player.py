"""Player sprite with 8-directional movement, per-axis collision, and walk animation."""
from __future__ import annotations

from typing import Dict, List, Tuple

import pygame


FACINGS = ("down", "up", "left", "right")


class Player(pygame.sprite.Sprite):
    SIZE = 32
    DEFAULT_COLOR = (220, 60, 60)
    SPEED = 120.0          # pixels per second
    STEP_DISTANCE = 12.0   # pixels between walk-frame flips

    def __init__(
        self,
        position: Tuple[int, int] = (0, 0),
        color: Tuple[int, int, int] = DEFAULT_COLOR,
        speed: float = SPEED,
    ) -> None:
        super().__init__()
        self.color = color
        self.speed = speed
        self.facing: str = "down"
        self.frame_index: int = 0
        self.walk_distance: float = 0.0
        self.images: Dict[Tuple[str, int], pygame.Surface] = self._build_images()
        self.image = self.images[(self.facing, self.frame_index)]
        self.rect = self.image.get_rect(topleft=position)
        self.position = pygame.Vector2(self.rect.topleft)
        self.velocity = pygame.Vector2(0, 0)
        self.blockers: List[pygame.Rect] = []

    # --- image construction ---

    def _build_images(self) -> Dict[Tuple[str, int], pygame.Surface]:
        return {
            (facing, frame): self._make_frame(facing, frame)
            for facing in FACINGS
            for frame in (0, 1)
        }

    def _make_frame(self, facing: str, frame: int) -> pygame.Surface:
        s = pygame.Surface((self.SIZE, self.SIZE), pygame.SRCALPHA)
        s.fill(self.color)
        pygame.draw.rect(s, (0, 0, 0), s.get_rect(), 2)

        # Eyes (lifted from previous version, with a slight directional offset).
        cx = self.SIZE // 2
        eye_y = cx - 4
        offset = {"left": -3, "right": 3, "up": 0, "down": 0}[facing]
        if facing == "up":
            eye_y -= 2
        pygame.draw.circle(s, (255, 255, 255), (cx - 5 + offset, eye_y), 2)
        pygame.draw.circle(s, (255, 255, 255), (cx + 5 + offset, eye_y), 2)

        # Walk-frame "feet" — small dots near the bottom that swap each step.
        if frame == 0:
            pygame.draw.rect(s, (40, 20, 20), pygame.Rect(10, 30, 3, 2))
            pygame.draw.rect(s, (40, 20, 20), pygame.Rect(20, 30, 3, 2))
        else:
            pygame.draw.rect(s, (40, 20, 20), pygame.Rect(13, 30, 3, 2))
            pygame.draw.rect(s, (40, 20, 20), pygame.Rect(17, 30, 3, 2))
        return s

    def _refresh_image(self) -> None:
        self.image = self.images[(self.facing, self.frame_index)]

    # --- movement ---

    def set_direction(self, direction: Tuple[float, float]) -> None:
        v = pygame.Vector2(direction)
        if v.length_squared() == 0:
            self.velocity.update(0, 0)
        else:
            v.scale_to_length(self.speed)
            self.velocity.update(v)

    def _sync_position_from_rect(self) -> None:
        if self.rect.x != int(round(self.position.x)) or self.rect.y != int(round(self.position.y)):
            self.position.update(self.rect.x, self.rect.y)

    def _resolve_axis(self, axis: str) -> None:
        if not self.blockers:
            return
        hits = [b for b in self.blockers if self.rect.colliderect(b)]
        if not hits:
            return
        if axis == "x":
            if self.velocity.x > 0:
                self.rect.right = min(b.left for b in hits)
            elif self.velocity.x < 0:
                self.rect.left = max(b.right for b in hits)
            self.position.x = float(self.rect.x)
        else:
            if self.velocity.y > 0:
                self.rect.bottom = min(b.top for b in hits)
            elif self.velocity.y < 0:
                self.rect.top = max(b.bottom for b in hits)
            self.position.y = float(self.rect.y)

    def _update_facing(self) -> None:
        if self.velocity.length_squared() == 0:
            return
        if abs(self.velocity.x) >= abs(self.velocity.y):
            self.facing = "right" if self.velocity.x > 0 else "left"
        else:
            self.facing = "down" if self.velocity.y > 0 else "up"

    def _update_walk_frame(self, dt: float) -> None:
        if self.velocity.length_squared() == 0:
            self.walk_distance = 0.0
            self.frame_index = 0
            return
        self.walk_distance += self.velocity.length() * dt
        if self.walk_distance >= self.STEP_DISTANCE:
            self.walk_distance %= self.STEP_DISTANCE
            self.frame_index ^= 1

    def update(self, dt: float = 0.0) -> None:
        self._sync_position_from_rect()
        self._update_facing()

        self.position.x += self.velocity.x * dt
        self.rect.x = int(round(self.position.x))
        self._resolve_axis("x")

        self.position.y += self.velocity.y * dt
        self.rect.y = int(round(self.position.y))
        self._resolve_axis("y")

        self._update_walk_frame(dt)
        self._refresh_image()
