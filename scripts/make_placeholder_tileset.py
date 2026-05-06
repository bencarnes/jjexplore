"""Generate `assets/tileset.png`, a 4x2 placeholder tileset (32px tiles).

Tile layout (column, row) -> tile id:
    (0,0) id 0 grass        (1,0) id 1 water
    (2,0) id 2 tree         (3,0) id 3 dirt
    (0,1) id 4 stone        (1,1) id 5 sand
    (2,1) id 6 wall         (3,1) id 7 floor

Re-run any time to regenerate the asset:
    PYTHONPATH=. python scripts/make_placeholder_tileset.py
"""
from __future__ import annotations

import pygame

from src import config

TILE_SIZE = 32
COLUMNS = 4
ROWS = 2


def _draw_grass(s: pygame.Surface) -> None:
    s.fill((86, 150, 64))
    for x, y in ((6, 6), (14, 18), (22, 10), (10, 24), (24, 26)):
        pygame.draw.line(s, (60, 110, 44), (x, y), (x, y - 3), 1)


def _draw_water(s: pygame.Surface) -> None:
    s.fill((58, 110, 180))
    for y in (8, 18, 26):
        pygame.draw.line(s, (120, 170, 220), (4, y), (28, y), 1)


def _draw_tree(s: pygame.Surface) -> None:
    s.fill((86, 150, 64))
    pygame.draw.rect(s, (90, 60, 30), pygame.Rect(14, 20, 4, 8))
    pygame.draw.circle(s, (40, 90, 40), (16, 14), 9)
    pygame.draw.circle(s, (60, 120, 60), (13, 12), 4)


def _draw_dirt(s: pygame.Surface) -> None:
    s.fill((140, 100, 60))
    for x, y in ((8, 8), (20, 12), (12, 22), (24, 24)):
        pygame.draw.circle(s, (110, 78, 46), (x, y), 2)


def _draw_stone(s: pygame.Surface) -> None:
    s.fill((130, 130, 130))
    pygame.draw.rect(s, (90, 90, 90), s.get_rect(), 2)
    pygame.draw.line(s, (90, 90, 90), (0, 16), (32, 16), 1)
    pygame.draw.line(s, (90, 90, 90), (16, 0), (16, 16), 1)
    pygame.draw.line(s, (90, 90, 90), (10, 16), (10, 32), 1)


def _draw_sand(s: pygame.Surface) -> None:
    s.fill((220, 200, 140))
    for x, y in ((6, 6), (14, 18), (22, 10), (10, 24), (24, 26)):
        pygame.draw.circle(s, (200, 180, 110), (x, y), 1)


def _draw_wall(s: pygame.Surface) -> None:
    s.fill((110, 80, 60))
    pygame.draw.rect(s, (70, 50, 35), s.get_rect(), 2)
    for row_y in (0, 8, 16, 24):
        offset = 0 if (row_y // 8) % 2 == 0 else 8
        for x in range(offset, 32, 16):
            pygame.draw.rect(s, (70, 50, 35), pygame.Rect(x, row_y, 16, 8), 1)


def _draw_floor(s: pygame.Surface) -> None:
    s.fill((180, 160, 130))
    pygame.draw.rect(s, (140, 120, 100), s.get_rect(), 1)


PAINTERS = [
    _draw_grass, _draw_water, _draw_tree, _draw_dirt,
    _draw_stone, _draw_sand, _draw_wall, _draw_floor,
]


def build_tileset() -> pygame.Surface:
    sheet = pygame.Surface((COLUMNS * TILE_SIZE, ROWS * TILE_SIZE))
    for index, painter in enumerate(PAINTERS):
        col, row = index % COLUMNS, index // COLUMNS
        tile = pygame.Surface((TILE_SIZE, TILE_SIZE))
        painter(tile)
        sheet.blit(tile, (col * TILE_SIZE, row * TILE_SIZE))
    return sheet


def main() -> None:
    pygame.init()
    try:
        config.ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        out = config.ASSETS_DIR / "tileset.png"
        pygame.image.save(build_tileset(), str(out))
        print(f"Wrote {out} ({COLUMNS * TILE_SIZE}x{ROWS * TILE_SIZE})")
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
