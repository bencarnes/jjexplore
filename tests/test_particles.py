"""Particle sprite + pickup-burst tests."""
import os
import random

import pygame
import pytest

from src.game import Game
from src.particle import Particle, spawn_pickup_burst

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")


@pytest.fixture(scope="module", autouse=True)
def _display():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


def test_particle_dies_after_lifetime():
    group = pygame.sprite.Group()
    p = Particle(position=(100, 100), velocity=(0, 0), lifetime=0.1)
    group.add(p)
    p.update(0.5)  # well past lifetime
    assert p not in group


def test_particle_moves_over_time():
    p = Particle(position=(100, 100), velocity=(50, 0), lifetime=1.0, gravity=0)
    p.update(0.2)
    assert p.rect.centerx > 100


def test_particle_gravity_pulls_down():
    p = Particle(position=(100, 100), velocity=(0, 0), lifetime=1.0, gravity=200)
    p.update(0.5)
    assert p.rect.centery > 100


def test_spawn_pickup_burst_adds_particles_to_group():
    group = pygame.sprite.Group()
    rng = random.Random(0)
    spawn_pickup_burst(group, (50, 50), count=5, rng=rng)
    assert len(group) == 5


def test_pickup_burst_particles_expire_with_updates():
    group = pygame.sprite.Group()
    rng = random.Random(0)
    spawn_pickup_burst(group, (50, 50), count=3, rng=rng)
    for _ in range(20):
        group.update(0.05)
    assert len(group) == 0


# --- Game integration ---


@pytest.fixture
def game(tmp_path):
    g = Game(width=200, height=200, save_path=tmp_path / "s.json", fade_duration_s=0)
    g.setup((200, 200))
    yield g
    g.teardown()


def test_picking_up_item_spawns_particles(game):
    apple = next(i for i in game.interactables if i.kind == "item")
    game.player.rect.center = apple.rect.center
    pre_count = len(game.group)
    game.interact()
    # Pickup despawns the item sprite, adds N particles. Net gain: count-1 sprites.
    assert len(game.group) > pre_count - 1


def test_opening_chest_spawns_particles(game):
    chest = next(i for i in game.interactables if i.kind == "chest")
    game.player.rect.center = chest.rect.center
    pre_count = len(game.group)
    game.interact()
    assert len(game.group) > pre_count
