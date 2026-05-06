import math
import os

import pygame
import pytest

from src.player import Player

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")


@pytest.fixture(scope="module", autouse=True)
def _display():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


def test_initial_velocity_is_zero():
    p = Player()
    assert p.velocity == pygame.Vector2(0, 0)


def test_set_direction_sets_velocity_at_speed():
    p = Player(speed=100)
    p.set_direction((1, 0))
    assert p.velocity == pygame.Vector2(100, 0)


def test_set_direction_zero_zeroes_velocity():
    p = Player(speed=100)
    p.set_direction((1, 0))
    p.set_direction((0, 0))
    assert p.velocity == pygame.Vector2(0, 0)


def test_diagonal_is_normalized_to_speed():
    p = Player(speed=100)
    p.set_direction((1, 1))
    assert math.isclose(p.velocity.length(), 100, rel_tol=1e-6)


def test_negative_direction_moves_negative():
    p = Player(speed=80)
    p.set_direction((-1, 0))
    assert p.velocity.x < 0
    assert p.velocity.y == 0


def test_update_advances_position_by_velocity_times_dt():
    p = Player(position=(0, 0), speed=100)
    p.set_direction((1, 0))
    p.update(0.5)
    assert p.rect.x == 50  # 100 px/s * 0.5 s = 50
    assert p.rect.y == 0


def test_update_with_zero_velocity_does_not_move():
    p = Player(position=(40, 60))
    p.update(1.0)
    assert p.rect.topleft == (40, 60)


def test_subpixel_movement_accumulates_across_frames():
    p = Player(position=(0, 0), speed=10)  # 10 px/s
    p.set_direction((1, 0))
    for _ in range(10):
        p.update(0.05)  # 0.5 px per step → would be 0 every frame without accumulation
    assert p.rect.x == 5  # 10 px/s * 0.5 s total = 5


def test_external_rect_change_is_picked_up():
    p = Player(position=(0, 0), speed=100)
    p.rect.topleft = (200, 100)
    p.set_direction((1, 0))
    p.update(0.1)
    assert p.rect.x == 210  # 200 + 100*0.1
    assert p.rect.y == 100
