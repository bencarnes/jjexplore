"""Save/load round-trip tests."""
import json
import os

import pygame
import pytest

from src.game import Game
from src.save import save_game, load_game

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")


@pytest.fixture(scope="module", autouse=True)
def _display():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


@pytest.fixture
def game(tmp_path):
    save_path = tmp_path / "save.json"
    g = Game(width=200, height=200, save_path=save_path, fade_duration_s=0)
    g.setup((g.width, g.height))
    yield g
    g.teardown()


def test_save_creates_json(game, tmp_path):
    save_path = save_game(game, tmp_path / "out.json")
    assert save_path.is_file()
    data = json.loads(save_path.read_text())
    assert data["version"] == 1
    assert data["map"] == "overworld.tmx"
    assert "player" in data
    assert "inventory" in data


def test_save_captures_inventory_and_position(game, tmp_path):
    game.inventory.add("gold", 7)
    game.inventory.add("apple", 1)
    game.player.rect.topleft = (123, 456)
    path = save_game(game, tmp_path / "out.json")
    data = json.loads(path.read_text())
    assert data["player"] == [123, 456]
    assert data["inventory"] == {"gold": 7, "apple": 1}


def test_save_captures_opened_chest(game, tmp_path):
    chest = next(i for i in game.interactables if i.kind == "chest")
    chest.state["opened"] = True
    path = save_game(game, tmp_path / "out.json")
    data = json.loads(path.read_text())
    assert chest.name in data["opened_chests"]


def test_save_captures_consumed_items(game, tmp_path):
    apple = next(i for i in game.interactables if i.name == "lonely_apple")
    game._despawn_item(apple)
    path = save_game(game, tmp_path / "out.json")
    data = json.loads(path.read_text())
    assert "lonely_apple" in data["consumed_items"]


def test_load_returns_false_when_missing(game, tmp_path):
    assert load_game(game, tmp_path / "nope.json") is False


def test_round_trip_restores_inventory(game, tmp_path):
    game.inventory.add("gold", 7)
    game.inventory.add("apple", 1)
    save_path = save_game(game, tmp_path / "save.json")
    # Mutate state
    game.inventory.add("gold", 100)
    game.inventory.add("trash", 50)
    load_game(game, save_path)
    assert game.inventory.count("gold") == 7
    assert game.inventory.count("apple") == 1
    assert "trash" not in game.inventory


def test_round_trip_restores_position(game, tmp_path):
    game.player.rect.topleft = (300, 200)
    save_path = save_game(game, tmp_path / "save.json")
    game.player.rect.topleft = (0, 0)
    load_game(game, save_path)
    assert game.player.rect.topleft == (300, 200)


def test_round_trip_restores_opened_chest(game, tmp_path):
    chest = next(i for i in game.interactables if i.kind == "chest")
    chest.state["opened"] = True
    save_path = save_game(game, tmp_path / "save.json")
    load_game(game, save_path)
    chest_after = next(i for i in game.interactables if i.kind == "chest")
    assert chest_after.state.get("opened") is True


def test_round_trip_keeps_consumed_items_consumed(game, tmp_path):
    apple = next(i for i in game.interactables if i.name == "lonely_apple")
    game._despawn_item(apple)
    save_path = save_game(game, tmp_path / "save.json")
    load_game(game, save_path)
    names = {i.name for i in game.interactables}
    assert "lonely_apple" not in names


def test_round_trip_across_maps(game, tmp_path):
    """Save while in fort_interior, then load and verify we land back inside."""
    entrance = next(i for i in game.interactables if i.name == "fort2_entrance")
    game.player.rect.center = entrance.rect.center
    game._check_transitions()
    assert game.map_path.name == "fort_interior.tmx"
    game.player.rect.topleft = (160, 96)
    save_path = save_game(game, tmp_path / "save.json")

    # Go back to overworld, then load.
    fort_exit = next(i for i in game.interactables if i.kind == "transition")
    game.player.rect.center = fort_exit.rect.center
    game._check_transitions()
    assert game.map_path.name == "overworld.tmx"

    load_game(game, save_path)
    assert game.map_path.name == "fort_interior.tmx"
    assert game.player.rect.topleft == (160, 96)


def test_save_raises_when_no_map_loaded(tmp_path):
    g = Game()  # no setup called
    with pytest.raises(RuntimeError):
        save_game(g, tmp_path / "x.json")
