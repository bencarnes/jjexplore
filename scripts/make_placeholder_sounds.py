"""Generate placeholder SFX and music WAVs using only the Python stdlib.

Re-run any time:
    PYTHONPATH=. python scripts/make_placeholder_sounds.py
"""
from __future__ import annotations

import math
import struct
import wave
from pathlib import Path
from typing import Iterable, List, Tuple

from src import config

SAMPLE_RATE = 22050
AMPLITUDE = 0.3


def tone(freq: float, duration_s: float, fade: bool = True) -> List[int]:
    n = int(duration_s * SAMPLE_RATE)
    out: List[int] = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = max(0.0, 1.0 - (i / n)) if fade else 1.0
        out.append(int(AMPLITUDE * env * 32767 * math.sin(2 * math.pi * freq * t)))
    return out


def sequence(notes: Iterable[Tuple[float, float]], fade: bool = False) -> List[int]:
    out: List[int] = []
    for freq, dur in notes:
        out.extend(tone(freq, dur, fade=fade))
    return out


def sweep(start_freq: float, end_freq: float, duration_s: float) -> List[int]:
    n = int(duration_s * SAMPLE_RATE)
    out: List[int] = []
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = start_freq + (end_freq - start_freq) * (i / n)
        env = 1.0 - (i / n)
        out.append(int(AMPLITUDE * env * 32767 * math.sin(2 * math.pi * freq * t)))
    return out


def write_wav(path: Path, samples: List[int]) -> None:
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(b"".join(struct.pack("<h", s) for s in samples))


SFX = {
    "pickup":     sequence([(660, 0.08), (880, 0.16)]),
    "chest":      sequence([(523, 0.08), (659, 0.08), (784, 0.12), (1047, 0.30)]),
    "door":       tone(110, 0.20),
    "transition": sweep(880, 220, 0.40),
}

MUSIC = {
    # Simple cheerful loop for the overworld.
    "overworld": sequence([
        (523, 0.30), (659, 0.30), (784, 0.30), (659, 0.30),
        (523, 0.30), (659, 0.30), (784, 0.30), (1047, 0.60),
        (784, 0.30), (659, 0.30), (523, 0.60),
    ]),
    # Slower, darker loop for the fort interior.
    "fort_interior": sequence([
        (196, 0.50), (220, 0.50), (262, 0.50), (220, 0.50),
        (196, 0.50), (165, 0.80),
        (220, 0.50), (262, 0.50), (330, 0.80),
    ]),
}


def main() -> None:
    sounds_dir = config.ASSETS_DIR / "sounds"
    music_dir = config.ASSETS_DIR / "music"
    sounds_dir.mkdir(parents=True, exist_ok=True)
    music_dir.mkdir(parents=True, exist_ok=True)
    for name, samples in SFX.items():
        write_wav(sounds_dir / f"{name}.wav", samples)
    for name, samples in MUSIC.items():
        write_wav(music_dir / f"{name}.wav", samples)
    print(f"Wrote {len(SFX)} SFX to {sounds_dir}")
    print(f"Wrote {len(MUSIC)} music tracks to {music_dir}")


if __name__ == "__main__":
    main()
