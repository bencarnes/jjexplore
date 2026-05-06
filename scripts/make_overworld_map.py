"""Generate `maps/overworld.tmx`, a 32x24 overworld with four regions.

Layout:
    - Top-left:    forest      (trees scattered on grass)
    - Top-right:   lake        (water with sand beach border)
    - Bottom-left: canyons     (vertical stone walls with corridor gaps)
    - Bottom-right: forts      (two walled rectangular buildings)
    - Center:      grass crossroads (player spawn at tile (16, 12))

Edit and re-run:
    PYTHONPATH=. python scripts/make_overworld_map.py
"""
from __future__ import annotations

import random
from typing import List

from src import config

WIDTH = 32
HEIGHT = 24
TILE = 32

# Tile gids (firstgid=1 in the .tmx)
GRASS, WATER, TREE, DIRT, STONE, SAND, WALL, FLOOR = range(1, 9)


def build_grid() -> List[List[int]]:
    g = [[GRASS] * WIDTH for _ in range(HEIGHT)]
    rng = random.Random(42)

    # Forest: top-left, scatter trees in cols 1..13, rows 1..10
    placed = 0
    while placed < 50:
        x = rng.randint(1, 13)
        y = rng.randint(1, 10)
        if g[y][x] == GRASS:
            g[y][x] = TREE
            placed += 1

    # Lake: top-right oval centered (24, 6) with sand border
    for y in range(HEIGHT):
        for x in range(WIDTH):
            dx = (x - 24) / 4.0
            dy = (y - 6) / 3.0
            d = dx * dx + dy * dy
            if d < 1.0:
                g[y][x] = WATER
            elif d < 1.7:
                if g[y][x] == GRASS:
                    g[y][x] = SAND

    # Canyons: bottom-left, two vertical stone walls with gaps
    for y in range(13, 23):
        if y not in (15, 16, 17):
            g[y][4] = STONE
        if y not in (19, 20):
            g[y][9] = STONE

    # Fort 1: rows 14..18, cols 18..23
    for y in range(14, 19):
        for x in range(18, 24):
            if y in (14, 18) or x in (18, 23):
                g[y][x] = WALL
            else:
                g[y][x] = FLOOR
    g[18][20] = FLOOR  # south doorway

    # Fort 2: rows 19..22, cols 25..29
    for y in range(19, 23):
        for x in range(25, 30):
            if y in (19, 22) or x in (25, 29):
                g[y][x] = WALL
            else:
                g[y][x] = FLOOR
    g[19][27] = FLOOR  # north doorway

    return g


def grid_to_csv(g: List[List[int]]) -> str:
    return "\n" + ",\n".join(",".join(str(v) for v in row) for row in g) + "\n"


# Interactable objects placed on the "interact" object layer.
# Optional fields: text (display message; '|' separates NPC dialog pages),
# item ("name:count" or just "name", added to inventory on pickup/open).
INTERACTABLES = [
    {"name": "welcome_sign", "kind": "sign",  "tx": 15, "ty": 11, "text": "Welcome to jjexplore! Press E to read signs."},
    {"name": "forest_sign",  "kind": "sign",  "tx":  6, "ty": 11, "text": "Forest of Whispers - watch out for trees."},
    {"name": "forts_sign",   "kind": "sign",  "tx": 20, "ty": 11, "text": "Forts ahead. Try to find the doorways."},
    {"name": "forest_chest", "kind": "chest", "tx": 12, "ty":  4, "text": "You found 5 gold pieces.", "item": "gold:5"},
    {"name": "fort1_door",   "kind": "door",  "tx": 20, "ty": 18, "text": "The door is locked."},
    {"name": "guide",        "kind": "npc",   "tx": 17, "ty": 12, "text": "Hi there! Welcome to the overworld.|Try exploring the forest to the west.|There's a chest hidden somewhere in the trees."},
    {"name": "fisher",       "kind": "npc",   "tx": 21, "ty":  4, "text": "The lake is too cold for swimming today.|But the fishing is great!"},
    {"name": "lonely_apple", "kind": "item",  "tx":  5, "ty": 16, "item": "apple"},
    {"name": "shore_potion", "kind": "item",  "tx": 28, "ty":  5, "item": "potion"},
    {"name": "fort2_entrance", "kind": "transition", "tx": 27, "ty": 19,
     "target_map": "fort_interior.tmx", "target_tx": 5, "target_ty": 7},
]


RESERVED_KEYS = {"name", "kind", "tx", "ty"}


def render_property(name: str, value) -> str:
    if isinstance(value, bool):
        return f'<property name="{name}" type="bool" value="{str(value).lower()}"/>'
    if isinstance(value, int):
        return f'<property name="{name}" type="int" value="{value}"/>'
    if isinstance(value, float):
        return f'<property name="{name}" type="float" value="{value}"/>'
    return f'<property name="{name}" value="{value}"/>'


def render_objects(interactables) -> str:
    lines = ['<objectgroup id="2" name="interact">']
    for obj_id, entry in enumerate(interactables, start=1):
        lines.append(
            f'  <object id="{obj_id}" name="{entry["name"]}" type="{entry["kind"]}" '
            f'x="{entry["tx"] * TILE}" y="{entry["ty"] * TILE}" '
            f'width="{TILE}" height="{TILE}">'
        )
        lines.append("   <properties>")
        for key, value in entry.items():
            if key in RESERVED_KEYS:
                continue
            lines.append(f"    {render_property(key, value)}")
        lines.append("   </properties>")
        lines.append("  </object>")
    lines.append(" </objectgroup>")
    return "\n ".join(lines)


TMX_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.2" orientation="orthogonal" renderorder="right-down" width="{w}" height="{h}" tilewidth="{t}" tileheight="{t}" infinite="0" nextlayerid="3" nextobjectid="{next_obj}">
 <tileset firstgid="1" source="../assets/tileset.tsx"/>
 <layer id="1" name="ground" width="{w}" height="{h}">
  <data encoding="csv">{csv}</data>
 </layer>
 {objects}
</map>
"""


def main() -> None:
    grid = build_grid()
    csv = grid_to_csv(grid)
    out = config.MAPS_DIR / "overworld.tmx"
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
