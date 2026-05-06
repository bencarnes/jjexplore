import os

import pygame
import pytest

from src import config
from src.tilemap import TileMap

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

MAP_PATH = config.MAPS_DIR / "overworld.tmx"

# Reference tiles known to be of a given terrain (per scripts/make_overworld_map.py).
SPAWN_TILE = (16, 12)        # grass crossroads (player spawn)
LAKE_CENTER_TILE = (24, 6)   # center of lake
FORT1_WALL_TILE = (18, 14)   # top-left wall of fort 1
CANYON_STONE_TILE = (4, 13)  # canyon wall
TREELESS_GRASS_TILE = (16, 11)  # one row above spawn, also grass


@pytest.fixture(scope="module")
def display():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


@pytest.fixture(scope="module")
def tilemap(display):
    return TileMap(MAP_PATH)


def test_dimensions(tilemap):
    assert tilemap.width_tiles == 32
    assert tilemap.height_tiles == 24
    assert tilemap.tile_width == 32
    assert tilemap.tile_height == 32


def test_pixel_dimensions(tilemap):
    assert tilemap.pixel_width == 1024
    assert tilemap.pixel_height == 768


def test_in_bounds(tilemap):
    assert tilemap.in_bounds(0, 0)
    assert tilemap.in_bounds(31, 23)
    assert not tilemap.in_bounds(-1, 0)
    assert not tilemap.in_bounds(32, 0)
    assert not tilemap.in_bounds(0, 24)


def test_spawn_tile_is_grass(tilemap):
    grass_gid = tilemap.gid_at(*SPAWN_TILE)
    assert grass_gid != 0
    # Adjacent center tiles should also be grass.
    assert tilemap.gid_at(*TREELESS_GRASS_TILE) == grass_gid


def test_distinct_terrains_have_distinct_gids(tilemap):
    grass = tilemap.gid_at(*SPAWN_TILE)
    water = tilemap.gid_at(*LAKE_CENTER_TILE)
    wall = tilemap.gid_at(*FORT1_WALL_TILE)
    stone = tilemap.gid_at(*CANYON_STONE_TILE)
    assert len({grass, water, wall, stone}) == 4


def test_gid_at_out_of_bounds_raises(tilemap):
    with pytest.raises(IndexError):
        tilemap.gid_at(99, 99)


def test_blocked_rects_are_nonempty_and_grid_aligned(tilemap):
    rects = tilemap.blocked_rects
    tw, th = tilemap.tile_width, tilemap.tile_height
    assert len(rects) > 50  # dozens of trees + lake + canyon walls + fort walls
    for rect in rects:
        assert rect.width == tw
        assert rect.height == th
        assert rect.x % tw == 0
        assert rect.y % th == 0


def test_known_water_tile_is_blocked(tilemap):
    x, y = LAKE_CENTER_TILE
    rect = pygame.Rect(x * tilemap.tile_width, y * tilemap.tile_height,
                       tilemap.tile_width, tilemap.tile_height)
    assert rect in tilemap.blocked_rects


def test_known_wall_tile_is_blocked(tilemap):
    x, y = FORT1_WALL_TILE
    rect = pygame.Rect(x * tilemap.tile_width, y * tilemap.tile_height,
                       tilemap.tile_width, tilemap.tile_height)
    assert rect in tilemap.blocked_rects


def test_known_stone_tile_is_blocked(tilemap):
    x, y = CANYON_STONE_TILE
    rect = pygame.Rect(x * tilemap.tile_width, y * tilemap.tile_height,
                       tilemap.tile_width, tilemap.tile_height)
    assert rect in tilemap.blocked_rects


def test_spawn_tile_is_not_blocked(tilemap):
    x, y = SPAWN_TILE
    rect = pygame.Rect(x * tilemap.tile_width, y * tilemap.tile_height,
                       tilemap.tile_width, tilemap.tile_height)
    assert rect not in tilemap.blocked_rects


def test_render_draws_pixels(tilemap):
    surface = pygame.Surface((tilemap.pixel_width, tilemap.pixel_height))
    surface.fill((0, 0, 0))
    tilemap.render(surface)
    # Top-left tile (0, 0) is grass — green-dominant.
    r, g, b, _ = surface.get_at((4, 4))
    assert (r, g, b) != (0, 0, 0)
    assert g > r and g > b


def test_render_with_offset_shifts_content(tilemap):
    base = pygame.Surface((tilemap.pixel_width, tilemap.pixel_height))
    base.fill((0, 0, 0))
    tilemap.render(base)

    shifted = pygame.Surface((tilemap.pixel_width, tilemap.pixel_height))
    shifted.fill((0, 0, 0))
    tilemap.render(shifted, offset=(32, 0))

    assert shifted.get_at((4, 4))[:3] == base.get_at((36, 4))[:3]
