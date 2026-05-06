"""Title screen / pause menu state machine tests."""
import os

import pygame
import pytest

from src.game import (
    Game,
    STATE_PAUSED,
    STATE_PLAYING,
    STATE_TITLE,
)

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")


@pytest.fixture(scope="module", autouse=True)
def _display():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


def keydown(key):
    return pygame.event.Event(pygame.KEYDOWN, {"key": key})


def test_game_starts_at_title():
    assert Game().state == STATE_TITLE


def test_title_menu_options():
    labels = [label for label, _ in Game().menu_options]
    assert labels == ["New Game", "Load Game", "Quit"]


def test_arrow_keys_move_menu_index():
    g = Game()
    assert g.menu_index == 0
    g.handle_event(keydown(pygame.K_DOWN))
    assert g.menu_index == 1
    g.handle_event(keydown(pygame.K_DOWN))
    assert g.menu_index == 2
    g.handle_event(keydown(pygame.K_DOWN))
    assert g.menu_index == 0  # wraps
    g.handle_event(keydown(pygame.K_UP))
    assert g.menu_index == 2  # wraps the other way


def test_w_and_s_keys_navigate_menu():
    g = Game()
    g.handle_event(keydown(pygame.K_s))
    assert g.menu_index == 1
    g.handle_event(keydown(pygame.K_w))
    assert g.menu_index == 0


def test_enter_on_quit_stops_game():
    g = Game()
    g.menu_index = 2  # Quit
    g.handle_event(keydown(pygame.K_RETURN))
    assert g.running is False


def test_enter_on_new_game_transitions_to_playing(tmp_path):
    g = Game(width=200, height=200, save_path=tmp_path / "save.json")
    g.menu_index = 0  # New Game
    g.handle_event(keydown(pygame.K_RETURN))
    assert g.state == STATE_PLAYING
    assert g.tilemap is not None
    g.teardown()


def test_setup_directly_skips_title(tmp_path):
    g = Game(width=200, height=200, save_path=tmp_path / "save.json")
    g.setup((200, 200))
    assert g.state == STATE_PLAYING
    g.teardown()


def test_pressing_escape_during_play_opens_pause(tmp_path):
    g = Game(width=200, height=200, save_path=tmp_path / "save.json")
    g.setup((200, 200))
    g.handle_event(keydown(pygame.K_ESCAPE))
    assert g.state == STATE_PAUSED
    labels = [label for label, _ in g.menu_options]
    assert labels == ["Resume", "Save", "Load", "Title Screen"]
    g.teardown()


def test_pressing_p_during_play_opens_pause(tmp_path):
    g = Game(width=200, height=200, save_path=tmp_path / "save.json")
    g.setup((200, 200))
    g.handle_event(keydown(pygame.K_p))
    assert g.state == STATE_PAUSED
    g.teardown()


def test_resume_returns_to_playing(tmp_path):
    g = Game(width=200, height=200, save_path=tmp_path / "save.json")
    g.setup((200, 200))
    g._show_pause_menu()
    g.menu_index = 0  # Resume
    g.handle_event(keydown(pygame.K_RETURN))
    assert g.state == STATE_PLAYING
    g.teardown()


def test_escape_in_pause_menu_resumes(tmp_path):
    g = Game(width=200, height=200, save_path=tmp_path / "save.json")
    g.setup((200, 200))
    g._show_pause_menu()
    g.handle_event(keydown(pygame.K_ESCAPE))
    assert g.state == STATE_PLAYING
    g.teardown()


def test_save_action_writes_file_and_resumes(tmp_path):
    save_path = tmp_path / "save.json"
    g = Game(width=200, height=200, save_path=save_path)
    g.setup((200, 200))
    g._show_pause_menu()
    g.menu_index = 1  # Save
    g.handle_event(keydown(pygame.K_RETURN))
    assert save_path.is_file()
    assert g.state == STATE_PLAYING
    g.teardown()


def test_load_from_pause_restores_state(tmp_path):
    save_path = tmp_path / "save.json"
    g = Game(width=200, height=200, save_path=save_path)
    g.setup((200, 200))
    g.inventory.add("gold", 9)
    g.player.rect.topleft = (200, 100)
    g._show_pause_menu()
    g.menu_index = 1  # Save
    g.handle_event(keydown(pygame.K_RETURN))

    # Mutate, then load via menu.
    g.inventory.add("gold", 50)
    g.player.rect.topleft = (0, 0)
    g._show_pause_menu()
    g.menu_index = 2  # Load
    g.handle_event(keydown(pygame.K_RETURN))
    assert g.state == STATE_PLAYING
    assert g.inventory.count("gold") == 9
    assert g.player.rect.topleft == (200, 100)
    g.teardown()


def test_title_screen_load_does_nothing_when_no_save(tmp_path):
    g = Game(width=200, height=200, save_path=tmp_path / "missing.json")
    g.menu_index = 1  # Load Game
    g.handle_event(keydown(pygame.K_RETURN))
    # Should remain on title since no save exists.
    assert g.state == STATE_TITLE


def test_update_does_not_advance_player_when_paused(tmp_path):
    g = Game(width=200, height=200, save_path=tmp_path / "save.json")
    g.setup((200, 200))
    g.player.set_direction((1, 0))
    starting_x = g.player.rect.x
    g._show_pause_menu()
    g.update(1.0)
    assert g.player.rect.x == starting_x
    g.teardown()


def test_update_does_not_advance_player_on_title():
    g = Game(width=200, height=200)
    g.update(1.0)  # state is TITLE; should not crash and should not move anyone
    assert g.player is None
