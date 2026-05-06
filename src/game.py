"""Top-level Game class with a fixed-timestep loop and pyscroll camera."""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple, Union

import pygame
import pyscroll

from src import config
from src.audio import Audio
from src.inventory import Inventory, parse_item_spec
from src.item import Item
from src.npc import NPC
from src.particle import spawn_pickup_burst
from src.player import Player
from src.save import DEFAULT_SAVE_PATH, load_game, save_game
from src.tilemap import Interactable, TileMap


MOVE_LEFT_KEYS = (pygame.K_LEFT, pygame.K_a)
MOVE_RIGHT_KEYS = (pygame.K_RIGHT, pygame.K_d)
MOVE_UP_KEYS = (pygame.K_UP, pygame.K_w)
MOVE_DOWN_KEYS = (pygame.K_DOWN, pygame.K_s)
INTERACT_KEYS = (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN)
MUTE_KEY = pygame.K_m
PAUSE_KEYS = (pygame.K_ESCAPE, pygame.K_p)
MENU_UP_KEYS = (pygame.K_UP, pygame.K_w)
MENU_DOWN_KEYS = (pygame.K_DOWN, pygame.K_s)
MENU_ACTIVATE_KEYS = (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e)
INTERACT_PADDING = 16

STATE_TITLE = "title"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"


def keys_to_direction(pressed) -> Tuple[int, int]:
    """Translate a pygame key-state mapping into a (dx, dy) direction in {-1, 0, 1}."""
    def any_pressed(keys):
        return any(pressed[k] for k in keys)

    dx = int(any_pressed(MOVE_RIGHT_KEYS)) - int(any_pressed(MOVE_LEFT_KEYS))
    dy = int(any_pressed(MOVE_DOWN_KEYS)) - int(any_pressed(MOVE_UP_KEYS))
    return (dx, dy)


class Game:
    PLAYER_SPAWN_TILE: Tuple[int, int] = (16, 12)

    FADE_SPEED = 600.0  # alpha per second

    def __init__(
        self,
        width: int = config.WINDOW_WIDTH,
        height: int = config.WINDOW_HEIGHT,
        target_fps: int = config.TARGET_FPS,
        title: str = config.WINDOW_TITLE,
        map_path: Union[str, Path] = config.MAPS_DIR / "overworld.tmx",
        save_path: Optional[Path] = None,
        fade_duration_s: float = 0.4,
    ) -> None:
        self.width = width
        self.height = height
        self.target_fps = target_fps
        self.title = title
        self.map_path = Path(map_path)
        self.running = False
        self.screen: Optional[pygame.Surface] = None
        self.clock: Optional[pygame.time.Clock] = None
        self.tilemap: Optional[TileMap] = None
        self.player: Optional[Player] = None
        self.map_layer: Optional[pyscroll.BufferedRenderer] = None
        self.group: Optional[pyscroll.PyscrollGroup] = None
        self.interactables: list = []
        self.npcs: list = []
        self.item_sprites: dict = {}
        self.inventory: Inventory = Inventory()
        self.dialog_pages: list = []
        self.viewport_size: Tuple[int, int] = (width, height)
        self.audio: Audio = Audio()
        self.save_path: Path = Path(save_path) if save_path else DEFAULT_SAVE_PATH
        self.state: str = STATE_TITLE
        self.menu_options: list = []
        self.menu_index: int = 0
        self._fonts: dict = {}
        self.fade_duration_s: float = fade_duration_s
        self.fade_alpha: float = 0.0
        self.fade_direction: int = 0  # +1 fading out, -1 fading in, 0 idle
        self.pending_transition: Optional[Tuple[str, Tuple[int, int]]] = None
        self._show_title_menu()

    # @property lets callers read `game.current_message` like an attribute,
    # while we compute the value from `dialog_pages` on the fly.
    @property
    def current_message(self) -> Optional[str]:
        return self.dialog_pages[0] if self.dialog_pages else None

    @property
    def fixed_dt(self) -> float:
        return 1.0 / self.target_fps

    def spawn_pixel(self) -> Tuple[int, int]:
        assert self.tilemap is not None, "setup() must run before spawn_pixel()"
        tx, ty = self.PLAYER_SPAWN_TILE
        return (
            tx * self.tilemap.tile_width + self.tilemap.tile_width // 2,
            ty * self.tilemap.tile_height + self.tilemap.tile_height // 2,
        )

    def setup(self, viewport_size: Tuple[int, int]) -> None:
        """Build tilemap, pyscroll renderer, sprite group, and player.

        Also marks the state as PLAYING so direct test usage of `setup()` skips the title.
        """
        self.viewport_size = viewport_size
        self._load_map(self.map_path, self.PLAYER_SPAWN_TILE)
        self.state = STATE_PLAYING

    # --- Menu / state actions ---

    def _show_title_menu(self) -> None:
        self.state = STATE_TITLE
        self.menu_options = [
            ("New Game", self._action_new_game),
            ("Load Game", self._action_load),
            ("Quit", self._action_quit),
        ]
        self.menu_index = 0

    def _show_pause_menu(self) -> None:
        self.state = STATE_PAUSED
        self.menu_options = [
            ("Resume", self._action_resume),
            ("Save", self._action_save),
            ("Load", self._action_load),
            ("Title Screen", self._show_title_menu),
        ]
        self.menu_index = 0

    def _action_new_game(self) -> None:
        if self.tilemap is None:
            self.setup(self.viewport_size)
        else:
            self.inventory = Inventory()
            self._load_map(config.MAPS_DIR / "overworld.tmx", self.PLAYER_SPAWN_TILE)
        self.state = STATE_PLAYING

    def _action_resume(self) -> None:
        self.state = STATE_PLAYING

    def _action_save(self) -> None:
        if self.tilemap is not None:
            save_game(self, self.save_path)
        self.state = STATE_PLAYING

    def _action_load(self) -> None:
        if not self.save_path.is_file():
            return  # nothing to load
        if self.tilemap is None:
            self.setup(self.viewport_size)
        if load_game(self, self.save_path):
            self.state = STATE_PLAYING

    def _action_quit(self) -> None:
        self.running = False

    def activate_selected_menu(self) -> None:
        if not self.menu_options:
            return
        _, action = self.menu_options[self.menu_index]
        action()

    def _load_map(self, map_path: Union[str, Path], spawn_tile: Tuple[int, int]) -> None:
        """Load a map, recreate sprite group and player at `spawn_tile`. Inventory persists."""
        self.map_path = Path(map_path)
        self.tilemap = TileMap(self.map_path)
        self.dialog_pages = []

        map_data = pyscroll.data.TiledMapData(self.tilemap.tmx)
        self.map_layer = pyscroll.BufferedRenderer(map_data, self.viewport_size, clamp_camera=True)
        self.group = pyscroll.PyscrollGroup(map_layer=self.map_layer)

        tx, ty = spawn_tile
        cx = tx * self.tilemap.tile_width + self.tilemap.tile_width // 2
        cy = ty * self.tilemap.tile_height + self.tilemap.tile_height // 2
        self.player = Player(position=(cx - Player.SIZE // 2, cy - Player.SIZE // 2))
        self.player.blockers = list(self.tilemap.blocked_rects)
        self.group.add(self.player)

        self.interactables = list(self.tilemap.interactables)
        self.npcs = []
        self.item_sprites = {}
        for item in self.interactables:
            if item.kind == "npc":
                npc = NPC(position=item.rect.topleft, name=item.name)
                self.npcs.append(npc)
                self.group.add(npc)
                self.player.blockers.append(npc.rect)
            elif item.kind == "item":
                ix = item.rect.centerx - Item.SIZE // 2
                iy = item.rect.centery - Item.SIZE // 2
                sprite = Item(position=(ix, iy), name=item.name)
                self.item_sprites[item.name] = sprite
                self.group.add(sprite)
        self.group.center(self.player.rect.center)
        self.audio.play_music(self.map_path.stem)

    def transition_to(self, target_map_filename: str, target_tile: Tuple[int, int]) -> None:
        """Switch to a new map at the given spawn tile. Inventory carries over."""
        target_path = config.MAPS_DIR / target_map_filename
        self._load_map(target_path, target_tile)

    def _check_transitions(self) -> None:
        if self.player is None or not self.interactables:
            return
        if self.pending_transition is not None or self.fade_direction != 0:
            return
        for it in self.interactables:
            if it.kind != "transition":
                continue
            if not self.player.rect.colliderect(it.rect):
                continue
            target_map = it.properties.get("target_map")
            if not target_map:
                continue
            tx = int(it.properties.get("target_tx", 0))
            ty = int(it.properties.get("target_ty", 0))
            self.audio.play("transition")
            if self.fade_duration_s <= 0:
                self.transition_to(str(target_map), (tx, ty))
            else:
                self.pending_transition = (str(target_map), (tx, ty))
                self.fade_alpha = 0.0
                self.fade_direction = 1
            return

    def teardown(self) -> None:
        self.audio.stop_music()
        self.tilemap = None
        self.player = None
        self.group = None
        self.map_layer = None
        self.interactables = []
        self.npcs = []
        self.item_sprites = {}
        self.inventory = Inventory()
        self.dialog_pages = []
        self._fonts = {}

    def find_nearest_interactable(self) -> Optional[Interactable]:
        if self.player is None or not self.interactables:
            return None
        reach = self.player.rect.inflate(INTERACT_PADDING * 2, INTERACT_PADDING * 2)
        candidates = [i for i in self.interactables if reach.colliderect(i.rect)]
        if not candidates:
            return None
        center = pygame.Vector2(self.player.rect.center)
        return min(candidates, key=lambda i: center.distance_squared_to(pygame.Vector2(i.rect.center)))

    def interact(self) -> None:
        if self.dialog_pages:
            self.dialog_pages.pop(0)
            return
        item = self.find_nearest_interactable()
        if item is None:
            return
        self.dialog_pages = self._dialog_for(item)

    def _dialog_for(self, item: Interactable) -> list:
        if item.kind == "sign":
            return [item.text or "(blank sign)"]
        if item.kind == "chest":
            if item.state.get("opened"):
                return ["The chest is empty."]
            item.state["opened"] = True
            self._collect_item(item)
            self.audio.play("chest")
            self._spawn_pickup_burst(item.rect.center)
            return [item.text or "You found something!"]
        if item.kind == "door":
            self.audio.play("door")
            return [item.text or "The door is locked."]
        if item.kind == "npc":
            text = item.text or "..."
            pages = [p.strip() for p in text.split("|") if p.strip()]
            return pages or ["..."]
        if item.kind == "item":
            pickup_pos = item.rect.center
            name, count = self._collect_item(item)
            self._despawn_item(item)
            self.audio.play("pickup")
            self._spawn_pickup_burst(pickup_pos)
            label = f"{count} {name}" if count > 1 else name
            return [item.text or f"Picked up {label}."]
        return []

    def _collect_item(self, interactable: Interactable):
        spec = interactable.properties.get("item", "")
        name, count = parse_item_spec(spec)
        if name and count > 0:
            self.inventory.add(name, count)
        return (name, count)

    def _spawn_pickup_burst(self, position: Tuple[int, int]) -> None:
        if self.group is None:
            return
        spawn_pickup_burst(self.group, position)

    def _despawn_item(self, interactable: Interactable) -> None:
        sprite = self.item_sprites.pop(interactable.name, None)
        if sprite is not None:
            sprite.kill()
        if interactable in self.interactables:
            self.interactables.remove(interactable)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
            return
        if event.type != pygame.KEYDOWN:
            return
        if self.state == STATE_TITLE:
            self._handle_menu_input(event.key, on_back=self._action_quit)
        elif self.state == STATE_PAUSED:
            self._handle_menu_input(event.key, on_back=self._action_resume)
        else:  # STATE_PLAYING
            if event.key in PAUSE_KEYS:
                self._show_pause_menu()
            elif event.key == MUTE_KEY:
                self.audio.toggle_mute()
            elif event.key in INTERACT_KEYS:
                self.interact()

    def _handle_menu_input(self, key: int, on_back) -> None:
        if not self.menu_options:
            return
        if key in MENU_UP_KEYS:
            self.menu_index = (self.menu_index - 1) % len(self.menu_options)
        elif key in MENU_DOWN_KEYS:
            self.menu_index = (self.menu_index + 1) % len(self.menu_options)
        elif key in MENU_ACTIVATE_KEYS:
            self.activate_selected_menu()
        elif key == pygame.K_ESCAPE:
            on_back()

    def clamp_player_to_map(self) -> None:
        if self.player is None or self.tilemap is None:
            return
        max_x = self.tilemap.pixel_width - self.player.rect.width
        max_y = self.tilemap.pixel_height - self.player.rect.height
        self.player.rect.x = max(0, min(self.player.rect.x, max_x))
        self.player.rect.y = max(0, min(self.player.rect.y, max_y))
        self.player.position.update(self.player.rect.x, self.player.rect.y)

    def update(self, dt: float) -> None:
        self._update_fade(dt)
        if self.state != STATE_PLAYING:
            if self.group is not None and self.player is not None:
                self.group.center(self.player.rect.center)
            return
        # Freeze player during fade-out so they don't keep moving past the trigger.
        if self.fade_direction > 0:
            if self.player is not None:
                self.player.set_direction((0, 0))
            if self.group is not None:
                self.group.update(dt)
            if self.group is not None and self.player is not None:
                self.group.center(self.player.rect.center)
            return
        if self.player is not None:
            if self.current_message is not None:
                self.player.set_direction((0, 0))
            else:
                self.player.set_direction(keys_to_direction(pygame.key.get_pressed()))
        if self.group is not None:
            self.group.update(dt)
        self.clamp_player_to_map()
        self._check_transitions()
        if self.group is not None and self.player is not None:
            self.group.center(self.player.rect.center)

    def _update_fade(self, dt: float) -> None:
        if self.fade_direction == 0:
            return
        self.fade_alpha += self.fade_direction * self.FADE_SPEED * dt
        if self.fade_direction > 0 and self.fade_alpha >= 255:
            self.fade_alpha = 255
            if self.pending_transition is not None:
                target_map, target_tile = self.pending_transition
                self.pending_transition = None
                self.transition_to(target_map, target_tile)
            self.fade_direction = -1
        elif self.fade_direction < 0 and self.fade_alpha <= 0:
            self.fade_alpha = 0
            self.fade_direction = 0

    def render(self) -> None:
        if self.screen is None:
            return
        if self.state == STATE_TITLE:
            self._render_title()
        else:
            self.screen.fill((20, 24, 28))
            if self.group is not None:
                self.group.draw(self.screen)
            self._draw_inventory()
            self._draw_message()
            if self.state == STATE_PAUSED:
                self._render_pause_overlay()
            self._draw_fade()
        pygame.display.flip()

    def _draw_fade(self) -> None:
        if self.screen is None or self.fade_alpha <= 0:
            return
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(self.fade_alpha)))
        self.screen.blit(overlay, (0, 0))

    def _font(self, size: int) -> pygame.font.Font:
        if size not in self._fonts:
            self._fonts[size] = pygame.font.Font(None, size)
        return self._fonts[size]

    def _render_title(self) -> None:
        if self.screen is None:
            return
        self.screen.fill((18, 26, 40))
        title_surf = self._font(72).render("jjexplore", True, (255, 255, 255))
        sub_surf = self._font(22).render(
            "Up/Down to choose, Enter to confirm", True, (180, 180, 200)
        )
        self.screen.blit(title_surf, title_surf.get_rect(center=(self.width // 2, self.height // 4)))
        self.screen.blit(sub_surf, sub_surf.get_rect(center=(self.width // 2, self.height // 4 + 56)))
        self._draw_menu(start_y=self.height // 2)

    def _render_pause_overlay(self) -> None:
        if self.screen is None:
            return
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))
        title = self._font(40).render("Paused", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center=(self.width // 2, self.height // 3)))
        self._draw_menu(start_y=self.height // 2)

    def _draw_menu(self, start_y: int) -> None:
        if self.screen is None or not self.menu_options:
            return
        font = self._font(32)
        y = start_y
        for i, (label, _action) in enumerate(self.menu_options):
            color = (255, 230, 100) if i == self.menu_index else (220, 220, 220)
            prefix = "> " if i == self.menu_index else "  "
            surf = font.render(f"{prefix}{label}", True, color)
            self.screen.blit(surf, surf.get_rect(center=(self.width // 2, y)))
            y += surf.get_height() + 6

    def _draw_inventory(self) -> None:
        if self.screen is None or len(self.inventory) == 0:
            return
        font = self._font(22)
        lines = [f"{name}: {count}" for name, count in self.inventory.items()]
        surfs = [font.render(line, True, (255, 255, 255)) for line in lines]
        box = pygame.Rect(0, 0, max(s.get_width() for s in surfs) + 16,
                          sum(s.get_height() for s in surfs) + 12)
        box.topright = (self.width - 8, 8)
        backdrop = pygame.Surface(box.size, pygame.SRCALPHA)
        backdrop.fill((0, 0, 0, 160))
        self.screen.blit(backdrop, box.topleft)
        pygame.draw.rect(self.screen, (255, 255, 255), box, 1)
        y = box.y + 6
        for surf in surfs:
            self.screen.blit(surf, (box.x + 8, y))
            y += surf.get_height()

    def _draw_message(self) -> None:
        if self.current_message is None or self.screen is None:
            return
        text_surf = self._font(24).render(self.current_message, True, (255, 255, 255))
        box = pygame.Rect(0, 0, text_surf.get_width() + 24, text_surf.get_height() + 16)
        box.midbottom = (self.width // 2, self.height - 16)
        backdrop = pygame.Surface(box.size, pygame.SRCALPHA)
        backdrop.fill((0, 0, 0, 200))
        self.screen.blit(backdrop, box.topleft)
        pygame.draw.rect(self.screen, (255, 255, 255), box, 1)
        self.screen.blit(text_surf, (box.x + 12, box.y + 8))

    def run(self) -> None:
        pygame.init()
        self.audio.init()
        self.audio.load_sounds()
        try:
            self.screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption(self.title)
            self.clock = pygame.time.Clock()
            self.setup((self.width, self.height))
            self.running = True
            accumulator = 0.0
            while self.running:
                frame_ms = self.clock.tick(self.target_fps)
                accumulator += frame_ms / 1000.0
                for event in pygame.event.get():
                    self.handle_event(event)
                while accumulator >= self.fixed_dt:
                    self.update(self.fixed_dt)
                    accumulator -= self.fixed_dt
                self.render()
        finally:
            self.teardown()
            pygame.quit()
            self.screen = None
            self.clock = None
