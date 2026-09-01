from dataclasses import dataclass, field
from enum import Enum, IntFlag, auto

from tiles.tile import *


class NeighborCondition(Enum):
    ANY = auto()
    EMPTY = auto()
    THIS = auto()
    NOT_THIS = auto()
    SPECIFIC = auto()
    NOT_SPECIFIC = auto()


class RuleTransform(IntFlag):
    NONE = 0
    ROTATED = auto()
    FLIPPED_HORIZONTAL = auto()
    FLIPPED_VERTICALLY = auto()


def rotate_offset(dx, dy, angle):
    turns = (angle // 90) % 4
    for _ in range(turns):
        dx, dy = -dy, dx
    return dx, dy


def transform_offset(dx, dy, angle, flip_h, flip_v):
    if flip_h:
        dx = -dx
    if flip_v:
        dy = -dy
    return rotate_offset(dx, dy, angle)


@dataclass
class Neighbor:
    dx: int
    dy: int
    condition: NeighborCondition
    target: object = None


@dataclass
class Rule:
    priority: int
    result_tile_id: int
    neighbors: list[Neighbor] = field(default_factory=list)
    transform: RuleTransform = RuleTransform.NONE

    def try_match(self, tilemap, x, y, self_tile):
        for angle, flip_h, flip_v in self._variants():
            if self._matches_variant(tilemap, x, y, self_tile, angle, flip_h, flip_v):
                return angle, flip_h, flip_v
        return None

    def _variants(self):
        angles = (0, 90, 180, 270) if self.transform & RuleTransform.ROTATED else (0,)
        flips_h = (False, True) if self.transform & RuleTransform.FLIPPED_HORIZONTAL else (False,)
        flips_v = (False, True) if self.transform & RuleTransform.FLIPPED_VERTICALLY else (False,)

        for angle in angles:
            for flip_h in flips_h:
                for flip_v in flips_v:
                    yield angle, flip_h, flip_v

    def _matches_variant(self, tilemap, x, y, self_tile, angle, flip_h, flip_v):
        for neighbor in self.neighbors:
            ndx, ndy = transform_offset(neighbor.dx, neighbor.dy, angle, flip_h, flip_v)
            placed = tilemap.get_placed(x + ndx, y + ndy)
            if not self._check_neighbor(neighbor, placed, self_tile):
                return False
        return True

    def _check_neighbor(self, neighbor, placed, self_tile):
        condition = neighbor.condition

        if condition == NeighborCondition.ANY:
            return placed is not None
        if condition == NeighborCondition.EMPTY:
            return placed is None
        if condition == NeighborCondition.THIS:
            return placed is self_tile
        if condition == NeighborCondition.NOT_THIS:
            return placed is not self_tile
        if condition == NeighborCondition.SPECIFIC:
            return placed is neighbor.target
        if condition == NeighborCondition.NOT_SPECIFIC:
            return placed is not neighbor.target

        return False


@dataclass
class RuleTile:
    default_tile_id: int
    rules: list[Rule] = field(default_factory=list)

    def get_visual(self, tilemap, x, y):
        for rule in sorted(self.rules, key=lambda r: r.priority):
            match = rule.try_match(tilemap, x, y, self)
            if match is not None:
                angle, flip_h, flip_v = match
                return TileVisual(rule.result_tile_id, angle, flip_h, flip_v)
        return TileVisual(self.default_tile_id)