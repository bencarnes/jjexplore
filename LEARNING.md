# Learning Python with jjexplore

This codebase is small enough to read end-to-end in an afternoon, structured for change, and protected by tests. The fastest way to learn Python here is to *change something and see what happens*. Run `pytest` after every change.

## Quick tour of the codebase

| File | What it does |
| ---- | ------------ |
| `main.py` | Entry point. Constructs `Game()` and calls `run()`. |
| `src/config.py` | Window size, FPS, asset paths. Constants only. |
| `src/game.py` | The `Game` class — state machine, main loop, menus, dispatch. |
| `src/player.py` | Player sprite. Movement, collision, walk animation. |
| `src/npc.py` | NPC sprite. Stationary; talks via dialog. |
| `src/item.py` | Pickup sprite drawn in the world. |
| `src/inventory.py` | Player inventory (dict wrapped in a class). |
| `src/tilemap.py` | Loads `.tmx` maps via pytmx and parses interactables. |
| `src/particle.py` | Short-lived sparkle sprites for pickup bursts. |
| `src/audio.py` | Wraps `pygame.mixer` with safe fallbacks. |
| `src/save.py` | JSON save/load. |
| `scripts/` | Asset and map generators (run on demand). |
| `tests/` | Pytest tests, organized by module. |

## Suggested first changes

Pick one, run `pytest`, then run `python main.py`.

1. **Make the player faster.** Change `Player.SPEED` in `src/player.py`. What test verifies this still works? (Hint: `tests/test_player_movement.py`.)
2. **Add a new item.** Open `scripts/make_overworld_map.py`, add an entry to `INTERACTABLES` with `"kind": "item"` and a tile location on grass, then re-run the script. Walk over and pick it up.
3. **Add a new NPC with multi-page dialog.** Same file, kind `"npc"`, separate pages with `|`.
4. **Make a new tile type "lava" that's blocked.** Edit `assets/tileset.tsx` to mark a tile id `blocked=true`, regenerate the tileset image with a new painter in `scripts/make_placeholder_tileset.py`, and use the new gid in your map.
5. **Make the chest loot something else.** Edit the `forest_chest` `item` property in the generator, regenerate, and check the inventory panel.
6. **Tweak the walk-cycle animation.** Adjust `Player.STEP_DISTANCE` to make the animation faster/slower, or modify `_make_frame()` to draw something different.

## Python concepts you'll see (and where)

These are everyday Python features. When you see one and aren't sure how it works, the linked file is a small, real example.

- **Classes & inheritance** — every sprite class subclasses `pygame.sprite.Sprite`. See `src/player.py`.
- **`@dataclass`** — `Interactable` in `src/tilemap.py` uses `@dataclass` to skip `__init__` boilerplate.
- **`@property`** — `Game.current_message` is a property over a list (`src/game.py`).
- **Type hints** — every public function has them (`def add(self, item: str, count: int = 1) -> None:`).
- **Dunder methods** — `Inventory` defines `__contains__` and `__len__` so `"gold" in inv` and `len(inv)` work.
- **List/dict/set comprehensions** — see `_compute_blocked_rects` in `src/tilemap.py`, save state computation in `src/save.py`.
- **f-strings** — `f"Picked up {label}."` (`src/game.py`).
- **`pathlib.Path`** — file paths everywhere (`src/config.py`, `src/save.py`).
- **`json` module** — `src/save.py` for save files.
- **Generators** — pytmx exposes `layer.iter_data()` which yields tuples; we consume in a `for` loop.
- **`try` / `except`** — `src/audio.py` swallows `pygame.error` so the game runs without sound hardware.
- **Default factories** — `field(default_factory=dict)` in `Interactable` (mutable defaults pitfall — see comments).
- **Tuple unpacking** — `for x, y, gid in layer.iter_data():`.
- **`*args` / unpacking** — `(*self.color, alpha)` in `src/particle.py` extends an RGB tuple with an alpha channel.

## Workflow

1. Edit code or a generator script.
2. If you edited a script, re-run it (`PYTHONPATH=. python scripts/<name>.py`).
3. Run tests: `pytest`.
4. Run the game: `python main.py`.

If a test fails, read the assertion message — it usually tells you the expected vs. actual values.

## Where to read next

- **`src/game.py`** is the longest file but the most rewarding. Skim `Game.__init__`, then trace `run()` → `update()` → `render()`.
- **`src/player.py`** is a nice complete unit: input → physics → animation → render.
- **`src/save.py`** is short and shows how to serialize state to JSON.
