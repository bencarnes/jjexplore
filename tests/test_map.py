import os

import pygame
from pytmx import TiledMap

from src import config

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

TILESET_PNG = config.ASSETS_DIR / "tileset.png"
TILESET_TSX = config.ASSETS_DIR / "tileset.tsx"
MAP_PATH = config.MAPS_DIR / "overworld.tmx"


def test_tileset_assets_exist():
    assert TILESET_PNG.is_file()
    assert TILESET_TSX.is_file()


def test_tileset_dimensions():
    pygame.init()
    try:
        surf = pygame.image.load(str(TILESET_PNG))
        assert surf.get_width() == 128
        assert surf.get_height() == 64
    finally:
        pygame.quit()


def test_overworld_tmx_exists():
    assert MAP_PATH.is_file()


def test_overworld_loads_with_pytmx():
    tm = TiledMap(str(MAP_PATH))
    assert tm.width == 32
    assert tm.height == 24
    assert tm.tilewidth == 32
    assert tm.tileheight == 32


def test_overworld_has_ground_layer():
    tm = TiledMap(str(MAP_PATH))
    layer_names = [layer.name for layer in tm.visible_layers]
    assert "ground" in layer_names


def test_overworld_uses_external_tileset_with_eight_tiles():
    tm = TiledMap(str(MAP_PATH))
    assert len(tm.tilesets) == 1
    assert tm.tilesets[0].tilecount == 8


def test_overworld_uses_multiple_terrain_types():
    tm = TiledMap(str(MAP_PATH))
    ground = tm.get_layer_by_name("ground")
    distinct_gids = {gid for _x, _y, gid in ground.iter_data() if gid != 0}
    # forest + lake + canyon + fort + grass crossroads should give us 5+ distinct tile types.
    assert len(distinct_gids) >= 5
