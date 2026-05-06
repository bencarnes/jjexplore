"""Walk-cycle animation + facing direction tests."""
import os

import pygame
import pytest

from src.player import FACINGS, Player

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")


@pytest.fixture(scope="module", autouse=True)
def _display():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


def test_player_default_facing_is_down():
    assert Player().facing == "down"


def test_player_initial_frame_is_zero():
    assert Player().frame_index == 0


def test_player_has_a_frame_for_every_facing_and_step():
    p = Player()
    for facing in FACINGS:
        for frame in (0, 1):
            assert (facing, frame) in p.images
            assert p.images[(facing, frame)].get_size() == (Player.SIZE, Player.SIZE)


def test_facing_changes_with_horizontal_velocity():
    p = Player()
    p.set_direction((1, 0))
    p.update(0.01)
    assert p.facing == "right"
    p.set_direction((-1, 0))
    p.update(0.01)
    assert p.facing == "left"


def test_facing_changes_with_vertical_velocity():
    p = Player()
    p.set_direction((0, 1))
    p.update(0.01)
    assert p.facing == "down"
    p.set_direction((0, -1))
    p.update(0.01)
    assert p.facing == "up"


def test_diagonal_picks_dominant_axis_horizontal_when_x_larger():
    p = Player(speed=100)
    p.velocity.update(80, 30)
    p._update_facing()
    assert p.facing == "right"


def test_walk_frame_alternates_with_distance():
    p = Player(speed=100)
    p.set_direction((1, 0))
    initial = p.frame_index
    # Move enough to trigger a step (STEP_DISTANCE = 12 px @ 100 px/s = 0.12 s)
    p.update(0.13)
    assert p.frame_index != initial
    p.update(0.13)
    assert p.frame_index == initial


def test_stationary_player_resets_frame_to_zero():
    p = Player(speed=100)
    p.set_direction((1, 0))
    p.update(0.13)
    assert p.frame_index == 1
    p.set_direction((0, 0))
    p.update(0.05)
    assert p.frame_index == 0


def test_image_updates_when_facing_changes():
    p = Player()
    down_img = p.image
    p.set_direction((-1, 0))
    p.update(0.01)
    assert p.image is not down_img
    assert p.image is p.images[("left", p.frame_index)]
