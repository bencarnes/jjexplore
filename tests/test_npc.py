"""NPC sprite + multi-page dialog tests."""
import os

import pygame
import pytest

from src.game import Game
from src.npc import NPC

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


# --- NPC sprite ---


def test_npc_sprite_has_correct_size():
    npc = NPC(position=(0, 0))
    assert npc.rect.size == (NPC.SIZE, NPC.SIZE)


def test_npc_carries_name():
    npc = NPC(position=(10, 20), name="guide")
    assert npc.name == "guide"
    assert npc.rect.topleft == (10, 20)


def test_npc_update_does_not_move():
    npc = NPC(position=(50, 50))
    npc.update(1.0)
    assert npc.rect.topleft == (50, 50)


# --- Game integration ---


def test_npcs_spawn_for_each_npc_interactable(game):
    npc_items = [i for i in game.interactables if i.kind == "npc"]
    assert len(game.npcs) == len(npc_items)
    assert len(game.npcs) >= 1


def test_npcs_added_to_sprite_group(game):
    for npc in game.npcs:
        assert npc in game.group.sprites()


def test_npc_rects_added_to_player_blockers(game):
    for npc in game.npcs:
        assert npc.rect in game.player.blockers


def test_player_cannot_walk_through_npc(game):
    npc = game.npcs[0]
    # Place player one tile to the left of the NPC and try to walk into it.
    game.player.rect.topleft = (npc.rect.left - game.player.rect.width, npc.rect.top)
    game.player.position.update(game.player.rect.x, game.player.rect.y)
    game.player.set_direction((1, 0))
    game.player.update(0.1)  # short step: would overlap NPC; collision should stop it
    assert game.player.rect.right <= npc.rect.left


# --- Multi-page dialog ---


def test_talking_to_npc_shows_first_page(game):
    npc_item = next(i for i in game.interactables if i.kind == "npc")
    _place_player_on(game, npc_item)
    game.interact()
    expected = npc_item.text.split("|")[0].strip()
    assert game.current_message == expected


def test_pressing_interact_advances_to_next_page(game):
    npc_item = next(
        i for i in game.interactables
        if i.kind == "npc" and "|" in i.text
    )
    _place_player_on(game, npc_item)
    game.interact()
    page1 = game.current_message
    game.interact()
    page2 = game.current_message
    assert page1 != page2


def test_pressing_interact_after_last_page_clears_dialog(game):
    npc_item = next(i for i in game.interactables if i.kind == "npc")
    _place_player_on(game, npc_item)
    pages = [p.strip() for p in npc_item.text.split("|") if p.strip()]
    game.interact()  # page 1
    for _ in range(len(pages)):
        game.interact()  # advance past last
    assert game.current_message is None


def test_signs_use_single_page_dialog(game):
    sign_item = next(i for i in game.interactables if i.kind == "sign")
    _place_player_on(game, sign_item)
    game.interact()
    assert game.current_message == sign_item.text
    game.interact()
    assert game.current_message is None
