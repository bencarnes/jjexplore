"""Wrapper around a pytmx-loaded Tiled map."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple, Union

import pygame
import pytmx
from pytmx.util_pygame import load_pygame


INTERACT_LAYER_NAME = "interact"
INTERACT_KINDS = ("sign", "chest", "door", "npc", "item", "transition")


# @dataclass auto-generates __init__, __repr__, etc. from the annotations below.
# field(default_factory=dict) creates a *new* dict per instance — never use a plain
# `state: dict = {}` as a default; all instances would share the same dict.
@dataclass
class Interactable:
    name: str
    kind: str        # one of INTERACT_KINDS
    rect: pygame.Rect
    text: str = ""
    state: dict = field(default_factory=dict)
    properties: dict = field(default_factory=dict)


class TileMap:
    def __init__(self, path: Union[str, Path]) -> None:
        self.path = Path(path)
        self.tmx = load_pygame(str(self.path))
        self.blocked_rects: List[pygame.Rect] = self._compute_blocked_rects()
        self.interactables: List[Interactable] = self._compute_interactables()

    def _compute_blocked_rects(self) -> List[pygame.Rect]:
        rects: List[pygame.Rect] = []
        tw, th = self.tmx.tilewidth, self.tmx.tileheight
        for layer in self.tmx.layers:
            if not isinstance(layer, pytmx.TiledTileLayer):
                continue
            for x, y, gid in layer.iter_data():
                if gid == 0:
                    continue
                props = self.tmx.get_tile_properties_by_gid(gid) or {}
                if props.get("blocked"):
                    rects.append(pygame.Rect(x * tw, y * th, tw, th))
        return rects

    def _compute_interactables(self) -> List[Interactable]:
        result: List[Interactable] = []
        for layer in self.tmx.layers:
            if not isinstance(layer, pytmx.TiledObjectGroup):
                continue
            if layer.name != INTERACT_LAYER_NAME:
                continue
            for obj in layer:
                kind = (getattr(obj, "type", None) or obj.properties.get("kind") or "").lower()
                if kind not in INTERACT_KINDS:
                    continue
                rect = pygame.Rect(int(obj.x), int(obj.y), int(obj.width), int(obj.height))
                result.append(
                    Interactable(
                        name=obj.name or "",
                        kind=kind,
                        rect=rect,
                        text=obj.properties.get("text", ""),
                        properties=dict(obj.properties),
                    )
                )
        return result

    @property
    def width_tiles(self) -> int: return self.tmx.width
    @property
    def height_tiles(self) -> int: return self.tmx.height
    @property
    def tile_width(self) -> int: return self.tmx.tilewidth
    @property
    def tile_height(self) -> int: return self.tmx.tileheight
    @property
    def pixel_width(self) -> int: return self.width_tiles * self.tile_width
    @property
    def pixel_height(self) -> int: return self.height_tiles * self.tile_height

    def in_bounds(self, tx: int, ty: int) -> bool:
        return 0 <= tx < self.width_tiles and 0 <= ty < self.height_tiles

    def gid_at(self, tx: int, ty: int, layer_name: str = "ground") -> int:
        if not self.in_bounds(tx, ty):
            raise IndexError(f"tile ({tx}, {ty}) out of bounds")
        layer = self.tmx.get_layer_by_name(layer_name)
        return layer.data[ty][tx]

    def render(self, surface: pygame.Surface, offset: Tuple[int, int] = (0, 0)) -> None:
        ox, oy = offset
        tw, th = self.tile_width, self.tile_height
        for layer in self.tmx.visible_layers:
            if not isinstance(layer, pytmx.TiledTileLayer):
                continue
            for x, y, image in layer.tiles():
                if image is None:
                    continue
                surface.blit(image, (x * tw - ox, y * th - oy))
