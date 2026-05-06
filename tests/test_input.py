"""Pure tests for the keyboard → direction helper."""
import os
from collections import defaultdict

import pygame
import pytest

from src.game import keys_to_direction

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")


def pressed(*keys):
    """Build a pygame.key.get_pressed-like mapping with the given keys 'pressed'."""
    state = defaultdict(int)
    for k in keys:
        state[k] = 1
    return state


def test_no_keys_means_no_direction():
    assert keys_to_direction(pressed()) == (0, 0)


@pytest.mark.parametrize(
    "key, expected",
    [
        (pygame.K_RIGHT, (1, 0)),
        (pygame.K_d, (1, 0)),
        (pygame.K_LEFT, (-1, 0)),
        (pygame.K_a, (-1, 0)),
        (pygame.K_DOWN, (0, 1)),
        (pygame.K_s, (0, 1)),
        (pygame.K_UP, (0, -1)),
        (pygame.K_w, (0, -1)),
    ],
)
def test_single_key_directions(key, expected):
    assert keys_to_direction(pressed(key)) == expected


def test_diagonal_combinations():
    assert keys_to_direction(pressed(pygame.K_RIGHT, pygame.K_DOWN)) == (1, 1)
    assert keys_to_direction(pressed(pygame.K_a, pygame.K_w)) == (-1, -1)
    assert keys_to_direction(pressed(pygame.K_d, pygame.K_UP)) == (1, -1)


def test_opposite_keys_cancel():
    assert keys_to_direction(pressed(pygame.K_LEFT, pygame.K_RIGHT)) == (0, 0)
    assert keys_to_direction(pressed(pygame.K_UP, pygame.K_DOWN)) == (0, 0)
