"""Generate `maps/fort_interior.tmx`, an 11x9 fort interior.

Layout:
    Walls around the perimeter, floor inside, a south doorway at (5, 8)
    that transitions back to the overworld at (27, 20).
    A loot chest sits in the center.

Edit and re-run:
    PYTHONPATH=. python scripts/make_fort_interior_map.py
"""
from __future__ import annotations

from typing import List

from scripts.make_overworld_map import (
    grid_to_csv,
    render_objects,
    TMX_TEMPLATE,
)
from src import config

WIDTH = 11
HEIGHT = 9
TILE = 32

# Tile gids (firstgid=1 in the .tmx)
GRASS, WATER, TREE, DIRT, STONE, SAND, WALL, FLOOR = range(1, 9)


def build_grid() -> List[List[int]]:
    g = [[FLOOR] * WIDTH for _ in range(HEIGHT)]
    for x in range(WIDTH):
        g[0][x] = WALL
        g[HEIGHT - 1][x] = WALL
    for y in range(HEIGHT):
        g[y][0] = WALL
        g[y][WIDTH - 1] = WALL
    g[HEIGHT - 1][5] = FLOOR  # south doorway
    return g


INTERACTABLES = [
    {"name": "fort_chest", "kind": "chest", "tx": 5, "ty": 4,
     "text": "An ancient sword!", "item": "sword:1"},
    {"name": "fort_greeter", "kind": "npc", "tx": 7, "ty": 5,
     "text": "Welcome to the fort.|This blade has waited many years for an heir."},
    {"name": "fort_exit", "kind": "transition", "tx": 5, "ty": 8,
     "target_map": "overworld.tmx", "target_tx": 27, "target_ty": 20},
]


def main() -> None:
    grid = build_grid()
    csv = grid_to_csv(grid)
    out = config.MAPS_DIR / "fort_interior.tmx"
    out.write_text(
        TMX_TEMPLATE.format(
            w=WIDTH, h=HEIGHT, t=TILE, csv=csv,
            objects=render_objects(INTERACTABLES),
            next_obj=len(INTERACTABLES) + 1,
        )
    )
    print(f"Wrote {out} ({WIDTH}x{HEIGHT}, {len(INTERACTABLES)} interactables)")


if __name__ == "__main__":
    main()
