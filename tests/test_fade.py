"""Fade-out / fade-in transition effect tests."""
import os

import pygame
import pytest

from src.game import Game

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")


@pytest.fixture(scope="module", autouse=True)
def _display():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


@pytest.fixture
def game(tmp_path):
    g = Game(width=200, height=200, save_path=tmp_path / "s.json", fade_duration_s=0.4)
    g.setup((200, 200))
    yield g
    g.teardown()


def test_fade_starts_idle(game):
    assert game.fade_alpha == 0
    assert game.fade_direction == 0
    assert game.pending_transition is None


def test_walking_into_transition_starts_fade_out(game):
    entrance = next(i for i in game.interactables if i.name == "fort2_entrance")
    game.player.rect.center = entrance.rect.center
    game._check_transitions()
    assert game.fade_direction == 1
    assert game.pending_transition is not None
    # Map hasn't actually switched yet — fade-out is just starting.
    assert game.map_path.name == "overworld.tmx"


def test_fade_out_then_in_completes_transition(game):
    entrance = next(i for i in game.interactables if i.name == "fort2_entrance")
    game.player.rect.center = entrance.rect.center
    game._check_transitions()

    # Drive update enough times to push fade to completion.
    for _ in range(30):
        game.update(0.05)
        if game.fade_direction == 0 and game.pending_transition is None:
            break

    assert game.map_path.name == "fort_interior.tmx"
    assert game.fade_direction == 0
    assert game.fade_alpha == 0
    assert game.pending_transition is None


def test_player_is_frozen_during_fade_out(game):
    entrance = next(i for i in game.interactables if i.name == "fort2_entrance")
    game.player.rect.center = entrance.rect.center
    game._check_transitions()
    # Set a velocity that should NOT move the player while fading out.
    game.player.set_direction((1, 0))
    starting_x = game.player.rect.x
    game.update(0.05)
    assert game.player.rect.x == starting_x


def test_fade_disabled_does_immediate_transition(tmp_path):
    g = Game(width=200, height=200, save_path=tmp_path / "s.json", fade_duration_s=0)
    g.setup((200, 200))
    try:
        entrance = next(i for i in g.interactables if i.name == "fort2_entrance")
        g.player.rect.center = entrance.rect.center
        g._check_transitions()
        assert g.map_path.name == "fort_interior.tmx"
        assert g.fade_direction == 0
        assert g.pending_transition is None
    finally:
        g.teardown()
