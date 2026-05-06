"""Tests for the Audio wrapper and the placeholder sound assets."""
import os
import wave

import pygame
import pytest

from src import config
from src.audio import Audio
from src.game import Game

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

SOUNDS_DIR = config.ASSETS_DIR / "sounds"
MUSIC_DIR = config.ASSETS_DIR / "music"
EXPECTED_SFX = ["pickup", "chest", "door", "transition"]
EXPECTED_MUSIC = ["overworld", "fort_interior"]


# --- Asset presence + validity ---


@pytest.mark.parametrize("name", EXPECTED_SFX)
def test_sfx_wav_exists(name):
    assert (SOUNDS_DIR / f"{name}.wav").is_file()


@pytest.mark.parametrize("name", EXPECTED_MUSIC)
def test_music_wav_exists(name):
    assert (MUSIC_DIR / f"{name}.wav").is_file()


@pytest.mark.parametrize("name", EXPECTED_SFX)
def test_sfx_wav_is_a_valid_mono_wave(name):
    with wave.open(str(SOUNDS_DIR / f"{name}.wav"), "rb") as w:
        assert w.getnchannels() == 1
        assert w.getsampwidth() == 2
        assert w.getframerate() == 22050
        assert w.getnframes() > 0


# --- Audio class graceful degradation (no init called) ---


def test_audio_starts_disabled():
    assert Audio().enabled is False


def test_play_when_disabled_is_silent():
    a = Audio()
    a.play("pickup")
    a.play("does_not_exist")  # also fine


def test_play_music_when_disabled_is_silent():
    a = Audio()
    a.play_music("overworld")
    assert a._music_track is None


def test_toggle_mute_works_when_disabled():
    a = Audio()
    assert a.muted is False
    a.toggle_mute()
    assert a.muted is True
    a.toggle_mute()
    assert a.muted is False


def test_set_volume_clamps():
    a = Audio()
    a.set_volume(2.0)
    assert a.volume == 1.0
    a.set_volume(-3.0)
    assert a.volume == 0.0


# --- Audio class initialized (mixer with dummy driver) ---


@pytest.fixture
def initialized_audio():
    pygame.init()
    a = Audio()
    a.init()
    yield a
    if a.enabled:
        pygame.mixer.quit()
    pygame.quit()


def test_init_sets_enabled_when_mixer_available(initialized_audio):
    # With SDL_AUDIODRIVER=dummy, init should usually succeed.
    if not initialized_audio.enabled:
        pytest.skip("mixer unavailable in this environment")
    assert initialized_audio.enabled is True


def test_load_sounds_picks_up_all_wavs(initialized_audio):
    if not initialized_audio.enabled:
        pytest.skip("mixer unavailable")
    initialized_audio.load_sounds()
    for name in EXPECTED_SFX:
        assert name in initialized_audio._sounds


def test_play_after_load_does_not_raise(initialized_audio):
    if not initialized_audio.enabled:
        pytest.skip("mixer unavailable")
    initialized_audio.load_sounds()
    initialized_audio.play("pickup")
    initialized_audio.play("missing_sound")  # silent no-op


# --- Game integration ---


def test_game_has_audio_attribute():
    g = Game()
    assert isinstance(g.audio, Audio)


def test_game_setup_does_not_require_audio_init():
    """Setup is called without calling Game.run, so audio is uninitialized.
    Calls to audio.play(...) inside the game must remain safe."""
    pygame.init()
    pygame.display.set_mode((1, 1))
    g = Game(width=200, height=200)
    g.setup((200, 200))
    assert g.audio.enabled is False
    # Trigger audio-emitting paths via interaction:
    sign = next(i for i in g.interactables if i.kind == "sign")
    g.player.rect.center = sign.rect.center
    g.interact()  # would play sounds if enabled; must not crash
    g.teardown()
    pygame.quit()
