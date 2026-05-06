import os

import pygame
import pytest

from src.player import Player

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")


@pytest.fixture(scope="module", autouse=True)
def _pygame_init():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


def test_player_default_position():
    p = Player()
    assert p.rect.topleft == (0, 0)
    assert p.rect.size == (Player.SIZE, Player.SIZE)


def test_player_custom_position():
    p = Player(position=(64, 96))
    assert p.rect.topleft == (64, 96)


def test_player_image_has_player_color():
    p = Player(color=(123, 45, 67))
    # Center pixel should be the body color (corners are border).
    color = p.image.get_at((Player.SIZE // 2, Player.SIZE - 4))[:3]
    assert color == (123, 45, 67)


def test_player_with_no_velocity_does_not_move():
    p = Player(position=(50, 50))
    p.update(0.016)
    assert p.rect.topleft == (50, 50)
