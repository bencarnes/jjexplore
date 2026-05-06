"""Particle sprites for short-lived visual effects (e.g., pickup sparkles)."""
from __future__ import annotations

import math
import random
from typing import Tuple

import pygame


class Particle(pygame.sprite.Sprite):
    def __init__(
        self,
        position: Tuple[float, float],
        velocity: Tuple[float, float],
        lifetime: float = 0.5,
        color: Tuple[int, int, int] = (255, 220, 60),
        size: int = 3,
        gravity: float = 220.0,
    ) -> None:
        super().__init__()
        self.position = pygame.Vector2(position)
        self.velocity = pygame.Vector2(velocity)
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.color = color
        self.size = size
        self.gravity = gravity
        self.image = self._render()
        self.rect = self.image.get_rect(center=(int(self.position.x), int(self.position.y)))

    def _render(self) -> pygame.Surface:
        surf = pygame.Surface((self.size * 2 + 1, self.size * 2 + 1), pygame.SRCALPHA)
        alpha = max(0, min(255, int(255 * (self.lifetime / self.max_lifetime))))
        # `*self.color` unpacks the (r, g, b) tuple, then we append alpha to make (r, g, b, a).
        pygame.draw.circle(surf, (*self.color, alpha), (self.size, self.size), self.size)
        return surf

    def update(self, dt: float = 0.0) -> None:
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()
            return
        self.velocity.y += self.gravity * dt
        self.position += self.velocity * dt
        self.rect.center = (int(self.position.x), int(self.position.y))
        self.image = self._render()


def spawn_pickup_burst(
    group: pygame.sprite.Group,
    position: Tuple[float, float],
    count: int = 8,
    color: Tuple[int, int, int] = (255, 220, 60),
    rng: random.Random = None,
) -> list:
    """Add a small burst of upward-arcing particles to `group`. Returns the spawned particles."""
    rng = rng or random
    spawned = []
    for _ in range(count):
        angle = rng.uniform(0, math.tau)
        speed = rng.uniform(40, 90)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed - 30
        p = Particle(position, (vx, vy), lifetime=0.5, color=color)
        group.add(p)
        spawned.append(p)
    return spawned
