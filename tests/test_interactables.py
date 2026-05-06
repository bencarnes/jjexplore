"""Tests for parsing the interact object layer + Game.interact behavior."""
import os

import pygame
import pytest

from src import config
from src.game import Game
from src.tilemap import Interactable, TileMap

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")


@pytest.fixture(scope="module", autouse=True)
def _display():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


@pytest.fixture(scope="module")
def tilemap():
    return TileMap(config.MAPS_DIR / "overworld.tmx")


def test_interactables_parsed_from_object_layer(tilemap):
    assert len(tilemap.interactables) == 10
    kinds = sorted(i.kind for i in tilemap.interactables)
    assert kinds == [
        "chest", "door", "item", "item",
        "npc", "npc", "sign", "sign", "sign", "transition",
    ]


def test_interactable_has_text_property(tilemap):
    chest = next(i for i in tilemap.interactables if i.kind == "chest")
    assert "gold" in chest.text.lower()


def test_interactable_rects_are_in_map_bounds(tilemap):
    map_rect = pygame.Rect(0, 0, tilemap.pixel_width, tilemap.pixel_height)
    for i in tilemap.interactables:
        assert map_rect.contains(i.rect)


# --- Game.interact behavior ---


@pytest.fixture
def game():
    g = Game(width=200, height=200)
    g.setup((g.width, g.height))
    yield g
    g.teardown()


def _place_player_on(game, item):
    game.player.rect.center = item.rect.center
    game.player.position.update(game.player.rect.x, game.player.rect.y)


def test_interact_with_no_nearby_object_does_nothing(game):
    # Spawn is at (16, 12); the welcome sign is at (15, 11) — close. Move player far away.
    game.player.rect.center = (0, 0)
    game.interact()
    assert game.current_message is None


def test_interact_with_sign_shows_text(game):
    sign = next(i for i in game.interactables if i.name == "welcome_sign")
    _place_player_on(game, sign)
    game.interact()
    assert game.current_message == sign.text


def test_interact_with_chest_marks_opened_and_shows_text(game):
    chest = next(i for i in game.interactables if i.kind == "chest")
    _place_player_on(game, chest)
    game.interact()
    assert chest.state.get("opened") is True
    assert game.current_message == chest.text


def test_second_interact_with_chest_says_empty(game):
    chest = next(i for i in game.interactables if i.kind == "chest")
    _place_player_on(game, chest)
    game.interact()             # opens
    game.interact()             # dismisses message
    game.interact()             # second open — empty
    assert game.current_message == "The chest is empty."


def test_interact_with_locked_door(game):
    door = next(i for i in game.interactables if i.kind == "door")
    _place_player_on(game, door)
    game.interact()
    assert "lock" in game.current_message.lower()


def test_interact_dismisses_active_message(game):
    sign = next(i for i in game.interactables if i.kind == "sign")
    _place_player_on(game, sign)
    game.interact()
    assert game.current_message is not None
    game.interact()
    assert game.current_message is None


def test_player_does_not_move_while_message_is_shown(game):
    sign = next(i for i in game.interactables if i.kind == "sign")
    _place_player_on(game, sign)
    game.interact()
    game.player.set_direction((1, 0))
    starting_x = game.player.rect.x
    game.update(1.0)
    assert game.player.rect.x == starting_x


def test_find_nearest_picks_closest_when_two_are_in_range(game):
    # Two synthetic interactables; player is right next to A.
    a = Interactable(name="a", kind="sign", rect=pygame.Rect(100, 100, 32, 32), text="A")
    b = Interactable(name="b", kind="sign", rect=pygame.Rect(180, 100, 32, 32), text="B")
    game.interactables = [a, b]
    game.player.rect.center = (110, 116)  # adjacent to A
    nearest = game.find_nearest_interactable()
    assert nearest is a
