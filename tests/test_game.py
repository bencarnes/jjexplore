import pygame

from src import config
from src.game import Game


def make_event(event_type, **attrs):
    return pygame.event.Event(event_type, attrs)


def test_game_initializes_with_default_dimensions():
    g = Game()
    assert g.width == config.WINDOW_WIDTH
    assert g.height == config.WINDOW_HEIGHT
    assert g.target_fps == config.TARGET_FPS
    assert g.title == config.WINDOW_TITLE


def test_game_initializes_with_custom_dimensions():
    g = Game(width=320, height=240, target_fps=30, title="custom")
    assert g.width == 320
    assert g.height == 240
    assert g.target_fps == 30
    assert g.title == "custom"


def test_game_starts_not_running():
    assert Game().running is False


def test_fixed_dt_matches_fps():
    g = Game(target_fps=60)
    assert g.fixed_dt == 1 / 60
    assert Game(target_fps=30).fixed_dt == 1 / 30


def test_quit_event_stops_running():
    g = Game()
    g.running = True
    g.handle_event(make_event(pygame.QUIT))
    assert g.running is False


def test_escape_key_stops_running():
    g = Game()
    g.running = True
    g.handle_event(make_event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert g.running is False


def test_unbound_key_is_a_noop():
    g = Game()
    g.running = True
    g.handle_event(make_event(pygame.KEYDOWN, key=pygame.K_q))
    assert g.running is True


def test_update_is_noop_for_now():
    g = Game()
    g.update(0.016)


def test_render_without_screen_is_safe():
    g = Game()
    g.render()


def test_game_default_map_path_points_at_overworld():
    g = Game()
    assert g.map_path == config.MAPS_DIR / "overworld.tmx"
