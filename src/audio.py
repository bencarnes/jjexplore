"""Audio wrapper around pygame.mixer. Gracefully no-ops when audio is unavailable."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import pygame

from src import config


class Audio:
    def __init__(
        self,
        sounds_dir: Optional[Path] = None,
        music_dir: Optional[Path] = None,
    ) -> None:
        self.sounds_dir = sounds_dir or (config.ASSETS_DIR / "sounds")
        self.music_dir = music_dir or (config.ASSETS_DIR / "music")
        self.enabled = False
        self.muted = False
        self.volume = 0.6
        self._sounds: Dict[str, pygame.mixer.Sound] = {}
        self._music_track: Optional[str] = None

    def init(self) -> None:
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.enabled = True
        except pygame.error:
            self.enabled = False

    def load_sounds(self) -> None:
        if not self.enabled or not self.sounds_dir.is_dir():
            return
        for path in sorted(self.sounds_dir.glob("*.wav")):
            try:
                self._sounds[path.stem] = pygame.mixer.Sound(str(path))
            except pygame.error:
                pass
        self._apply_volume()

    def play(self, name: str) -> None:
        if not self.enabled or self.muted:
            return
        sound = self._sounds.get(name)
        if sound is not None:
            sound.play()

    def play_music(self, name: str, loop: bool = True) -> None:
        if not self.enabled:
            return
        if self._music_track == name:
            return
        path = self.music_dir / f"{name}.wav"
        if not path.is_file():
            return
        try:
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(0.0 if self.muted else self.volume)
            pygame.mixer.music.play(-1 if loop else 0)
            self._music_track = name
        except pygame.error:
            pass

    def stop_music(self) -> None:
        if not self.enabled:
            return
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass
        self._music_track = None

    def toggle_mute(self) -> None:
        self.muted = not self.muted
        if not self.enabled:
            return
        try:
            pygame.mixer.music.set_volume(0.0 if self.muted else self.volume)
        except pygame.error:
            pass

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, volume))
        self._apply_volume()

    def _apply_volume(self) -> None:
        if not self.enabled:
            return
        for sound in self._sounds.values():
            sound.set_volume(self.volume)
        try:
            pygame.mixer.music.set_volume(0.0 if self.muted else self.volume)
        except pygame.error:
            pass
