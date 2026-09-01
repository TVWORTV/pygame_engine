from dataclasses import dataclass


@dataclass
class TileVisual:
    sprite_id: int
    rotation: int = 0
    flip_h: bool = False
    flip_v: bool = False


@dataclass
class Tile:
    tile_id: int

    def get_visual(self, tilemap, x, y):
        return TileVisual(self.tile_id)