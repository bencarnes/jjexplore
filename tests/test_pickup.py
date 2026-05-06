"""Game-level tests: picking up items, opening loot chests, sprite removal."""
import os

import pygame
import pytest

from src.game import Game
from src.item import Item

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")


@pytest.fixture(scope="module", autouse=True)
def _display():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


@pytest.fixture
def game():
    g = Game(width=200, height=200)
    g.setup((g.width, g.height))
    yield g
    g.teardown()


def _place_player_on(game, item):
    game.player.rect.center = item.rect.center
    game.player.position.update(game.player.rect.x, game.player.rect.y)


def test_inventory_starts_empty(game):
    assert len(game.inventory) == 0


def test_item_sprites_spawned_for_item_kind(game):
    item_items = [i for i in game.interactables if i.kind == "item"]
    assert len(game.item_sprites) == len(item_items)
    for sprite in game.item_sprites.values():
        assert isinstance(sprite, Item)
        assert sprite in game.group.sprites()


def test_picking_up_item_adds_to_inventory(game):
    apple = next(i for i in game.interactables if i.name == "lonely_apple")
    _place_player_on(game, apple)
    game.interact()
    assert game.inventory.count("apple") == 1


def test_picking_up_item_removes_it_from_world(game):
    apple = next(i for i in game.interactables if i.name == "lonely_apple")
    sprite = game.item_sprites["lonely_apple"]
    _place_player_on(game, apple)
    game.interact()
    assert apple not in game.interactables
    assert "lonely_apple" not in game.item_sprites
    assert sprite not in game.group.sprites()


def test_picking_up_shows_message(game):
    apple = next(i for i in game.interactables if i.name == "lonely_apple")
    _place_player_on(game, apple)
    game.interact()
    assert game.current_message is not None
    assert "apple" in game.current_message.lower()


def test_opening_chest_adds_loot_to_inventory(game):
    chest = next(i for i in game.interactables if i.kind == "chest")
    _place_player_on(game, chest)
    game.interact()
    assert game.inventory.count("gold") == 5


def test_opening_chest_only_adds_loot_once(game):
    chest = next(i for i in game.interactables if i.kind == "chest")
    _place_player_on(game, chest)
    game.interact()       # opens, adds gold
    game.interact()       # dismisses message
    game.interact()       # second open — empty
    game.interact()       # dismiss
    assert game.inventory.count("gold") == 5


def test_picking_up_two_different_items(game):
    apple = next(i for i in game.interactables if i.name == "lonely_apple")
    potion = next(i for i in game.interactables if i.name == "shore_potion")

    _place_player_on(game, apple)
    game.interact()
    game.interact()  # dismiss

    _place_player_on(game, potion)
    game.interact()
    game.interact()  # dismiss

    assert "apple" in game.inventory
    assert "potion" in game.inventory
    assert game.inventory.total() == 2
