"""JSON save/load for jjexplore."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from src import config
from src.inventory import Inventory

DEFAULT_SAVE_PATH = config.PROJECT_ROOT / "saves" / "quick.json"
SAVE_VERSION = 1


def save_game(game, path: Optional[Path] = None) -> Path:
    """Write a save file capturing the current run state. Game must be running."""
    if game.tilemap is None or game.player is None:
        raise RuntimeError("Cannot save: no map loaded.")
    target = Path(path or DEFAULT_SAVE_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)

    # Set comprehensions: `{...}` builds a set. The `-` operator is set difference,
    # so this gives us names that were on the map originally but aren't anymore.
    original_items = {i.name for i in game.tilemap.interactables if i.kind == "item"}
    current_items = {i.name for i in game.interactables if i.kind == "item"}
    consumed_items = sorted(original_items - current_items)
    opened_chests = sorted(
        i.name for i in game.interactables
        if i.kind == "chest" and i.state.get("opened")
    )

    data = {
        "version": SAVE_VERSION,
        "map": game.map_path.name,
        "player": [game.player.rect.x, game.player.rect.y],
        "inventory": dict(game.inventory.items()),
        "consumed_items": consumed_items,
        "opened_chests": opened_chests,
    }
    target.write_text(json.dumps(data, indent=2))
    return target


def load_game(game, path: Optional[Path] = None) -> bool:
    """Load a save file into the running game. Returns False if no file exists."""
    source = Path(path or DEFAULT_SAVE_PATH)
    if not source.is_file():
        return False
    data = json.loads(source.read_text())

    map_path = config.MAPS_DIR / data["map"]
    game._load_map(map_path, (0, 0))  # any spawn tile; we override the pixel pos below

    px, py = data["player"]
    game.player.rect.topleft = (px, py)
    game.player.position.update(px, py)

    game.inventory = Inventory()
    for name, count in data.get("inventory", {}).items():
        game.inventory.add(name, count)

    opened = set(data.get("opened_chests", []))
    for it in game.interactables:
        if it.kind == "chest" and it.name in opened:
            it.state["opened"] = True

    consumed = list(data.get("consumed_items", []))
    for item_name in consumed:
        for it in list(game.interactables):
            if it.kind == "item" and it.name == item_name:
                game._despawn_item(it)
                break
    return True
