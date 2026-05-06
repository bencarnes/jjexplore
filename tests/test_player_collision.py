"""Per-axis collision tests for Player."""
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


def test_no_blockers_means_no_collision():
    p = Player(position=(0, 0), speed=100)
    p.set_direction((1, 0))
    p.update(1.0)
    assert p.rect.x == 100


def test_walking_right_into_blocker_stops_at_left_edge():
    # Blocker at x=80, full player height. Player walks right at 100 px/s for 1s.
    blocker = pygame.Rect(80, 0, 32, Player.SIZE)
    p = Player(position=(0, 0), speed=100)
    p.blockers = [blocker]
    p.set_direction((1, 0))
    p.update(1.0)
    assert p.rect.right == blocker.left


def test_walking_left_into_blocker_stops_at_right_edge():
    blocker = pygame.Rect(0, 0, 50, Player.SIZE)
    p = Player(position=(150, 0), speed=100)
    p.blockers = [blocker]
    p.set_direction((-1, 0))
    p.update(1.0)
    assert p.rect.left == blocker.right


def test_walking_down_into_blocker_stops_at_top_edge():
    blocker = pygame.Rect(0, 80, Player.SIZE, 32)
    p = Player(position=(0, 0), speed=100)
    p.blockers = [blocker]
    p.set_direction((0, 1))
    p.update(1.0)
    assert p.rect.bottom == blocker.top


def test_walking_up_into_blocker_stops_at_bottom_edge():
    blocker = pygame.Rect(0, 0, Player.SIZE, 50)
    p = Player(position=(0, 150), speed=100)
    p.blockers = [blocker]
    p.set_direction((0, -1))
    p.update(1.0)
    assert p.rect.top == blocker.bottom


def test_diagonal_into_horizontal_wall_slides_vertically():
    """Tall vertical wall blocks rightward motion; vertical motion should still happen."""
    wall = pygame.Rect(80, -1000, 32, 4000)
    p = Player(position=(0, 0), speed=100)
    p.blockers = [wall]
    p.set_direction((1, 1))
    p.update(1.0)
    assert p.rect.right == wall.left  # x stopped
    assert p.rect.y > 0                 # y still moved


def test_diagonal_into_vertical_wall_slides_horizontally():
    """Long horizontal wall blocks downward motion; horizontal motion should still happen."""
    wall = pygame.Rect(-1000, 80, 4000, 32)
    p = Player(position=(0, 0), speed=100)
    p.blockers = [wall]
    p.set_direction((1, 1))
    p.update(1.0)
    assert p.rect.bottom == wall.top
    assert p.rect.x > 0


def test_unblocked_axis_unaffected_when_other_axis_blocks():
    blocker = pygame.Rect(80, 0, 32, Player.SIZE)
    p = Player(position=(0, 0), speed=100)
    p.blockers = [blocker]
    p.set_direction((1, 0))
    p.update(0.1)  # moves to x=10, no collision
    assert p.rect.x == 10
    assert p.rect.y == 0


def test_can_move_along_corridor_between_two_blockers():
    top_wall = pygame.Rect(-1000, -32, 4000, 32)
    bot_wall = pygame.Rect(-1000, 32, 4000, 32)
    p = Player(position=(0, 0), speed=100)
    p.blockers = [top_wall, bot_wall]
    p.set_direction((1, 0))
    p.update(0.5)
    assert p.rect.x == 50
    assert p.rect.y == 0
