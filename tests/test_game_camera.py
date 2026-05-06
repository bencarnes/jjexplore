"""Camera + pyscroll integration tests for Game.setup/update."""
import os

import pygame
import pytest

from src.game import Game
from src.player import Player

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")


@pytest.fixture(scope="module", autouse=True)
def _display():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


@pytest.fixture
def game():
    # Small viewport so camera has room to scroll within the 320x256 map.
    g = Game(width=100, height=100)
    g.setup((g.width, g.height))
    yield g
    g.teardown()


def test_setup_creates_tilemap_player_group(game):
    assert game.tilemap is not None
    assert game.player is not None
    assert game.group is not None
    assert game.map_layer is not None


def test_setup_assigns_blockers_to_player(game):
    assert game.player.blockers
    for rect in game.tilemap.blocked_rects:
        assert rect in game.player.blockers


def test_player_spawned_at_expected_tile(game):
    expected_x = Game.PLAYER_SPAWN_TILE[0] * game.tilemap.tile_width + game.tilemap.tile_width // 2
    expected_y = Game.PLAYER_SPAWN_TILE[1] * game.tilemap.tile_height + game.tilemap.tile_height // 2
    assert game.player.rect.center == (expected_x, expected_y)


def test_player_is_in_sprite_group(game):
    assert game.player in game.group.sprites()


def test_camera_centers_on_player_after_update(game):
    game.player.rect.center = (160, 128)  # middle of the 320x256 map
    game.update(0.0)
    view = game.map_layer.view_rect
    assert view.center == (160, 128)


def test_camera_follows_when_player_moves(game):
    game.player.rect.center = (120, 120)
    game.update(0.0)
    first = game.map_layer.view_rect.center

    game.player.rect.center = (200, 130)
    game.update(0.0)
    second = game.map_layer.view_rect.center

    assert second != first
    assert second == (200, 130)


def test_clamp_player_to_map_left_edge(game):
    game.player.rect.topleft = (-50, 100)
    game.clamp_player_to_map()
    assert game.player.rect.x == 0


def test_clamp_player_to_map_right_edge(game):
    game.player.rect.topleft = (10_000, 100)
    game.clamp_player_to_map()
    max_x = game.tilemap.pixel_width - game.player.rect.width
    assert game.player.rect.x == max_x


def test_clamp_player_to_map_bottom_edge(game):
    game.player.rect.topleft = (100, 10_000)
    game.clamp_player_to_map()
    max_y = game.tilemap.pixel_height - game.player.rect.height
    assert game.player.rect.y == max_y


def test_update_is_safe_before_setup():
    g = Game()
    g.update(0.016)  # no group yet — must not raise


def test_render_is_safe_with_no_screen(game):
    # Game.setup ran, but no display screen attached.
    assert game.screen is None
    game.render()  # must not raise
