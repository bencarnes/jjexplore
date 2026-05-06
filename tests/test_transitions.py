"""Map transitions: walking onto a transition tile loads a new map."""
import os

import pygame
import pytest

from src import config
from src.game import Game
from src.tilemap import TileMap

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")


@pytest.fixture(scope="module", autouse=True)
def _display():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


@pytest.fixture
def game():
    g = Game(width=200, height=200, fade_duration_s=0)
    g.setup((g.width, g.height))
    yield g
    g.teardown()


def test_overworld_has_fort_entrance_transition(game):
    entrance = next(
        (i for i in game.interactables if i.kind == "transition" and i.name == "fort2_entrance"),
        None,
    )
    assert entrance is not None
    assert entrance.properties.get("target_map") == "fort_interior.tmx"


def test_fort_interior_map_exists_and_has_exit_transition():
    tm = TileMap(config.MAPS_DIR / "fort_interior.tmx")
    exits = [i for i in tm.interactables if i.kind == "transition"]
    assert len(exits) == 1
    assert exits[0].properties.get("target_map") == "overworld.tmx"


def test_walking_onto_transition_loads_new_map(game):
    entrance = next(i for i in game.interactables if i.name == "fort2_entrance")
    game.player.rect.center = entrance.rect.center
    game.player.position.update(game.player.rect.x, game.player.rect.y)
    game._check_transitions()
    assert game.map_path.name == "fort_interior.tmx"


def test_player_respawns_at_target_tile_after_transition(game):
    entrance = next(i for i in game.interactables if i.name == "fort2_entrance")
    target_tx = int(entrance.properties["target_tx"])
    target_ty = int(entrance.properties["target_ty"])
    game.player.rect.center = entrance.rect.center
    game._check_transitions()
    expected_x = target_tx * game.tilemap.tile_width + game.tilemap.tile_width // 2
    expected_y = target_ty * game.tilemap.tile_height + game.tilemap.tile_height // 2
    assert game.player.rect.center == (expected_x, expected_y)


def test_inventory_persists_across_transition(game):
    game.inventory.add("gold", 7)
    entrance = next(i for i in game.interactables if i.name == "fort2_entrance")
    game.player.rect.center = entrance.rect.center
    game._check_transitions()
    assert game.inventory.count("gold") == 7


def test_transition_replaces_interactables_with_new_map_set(game):
    pre_count = len(game.interactables)
    entrance = next(i for i in game.interactables if i.name == "fort2_entrance")
    game.player.rect.center = entrance.rect.center
    game._check_transitions()
    # Fort interior has fewer interactables than overworld.
    assert len(game.interactables) != pre_count
    kinds = sorted(i.kind for i in game.interactables)
    assert kinds == ["chest", "npc", "transition"]


def test_round_trip_overworld_to_fort_and_back(game):
    # Enter the fort.
    entrance = next(i for i in game.interactables if i.name == "fort2_entrance")
    game.player.rect.center = entrance.rect.center
    game._check_transitions()
    assert game.map_path.name == "fort_interior.tmx"

    # Walk onto fort exit.
    fort_exit = next(i for i in game.interactables if i.kind == "transition")
    game.player.rect.center = fort_exit.rect.center
    game._check_transitions()
    assert game.map_path.name == "overworld.tmx"


def test_dialog_clears_on_transition(game):
    game.dialog_pages = ["leftover message"]
    entrance = next(i for i in game.interactables if i.name == "fort2_entrance")
    game.player.rect.center = entrance.rect.center
    game._check_transitions()
    assert game.current_message is None


def test_transition_target_tile_is_not_on_a_transition(game):
    """Spawning on a transition would cause an immediate re-trigger loop."""
    entrance = next(i for i in game.interactables if i.name == "fort2_entrance")
    game.player.rect.center = entrance.rect.center
    game._check_transitions()
    # Now in fort_interior. Player position should NOT overlap any transition.
    for it in game.interactables:
        if it.kind == "transition":
            assert not game.player.rect.colliderect(it.rect)
