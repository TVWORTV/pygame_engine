from dataclasses import dataclass, field
from enum import Enum, auto


class NeighborCondition(Enum):
    ANY = auto()
    EMPTY = auto()
    THIS = auto()
    NOT_THIS = auto()
    SPECIFIC = auto()
    NOT_SPECIFIC = auto()


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

    def matches(self, tilemap, x, y, self_tile):
        for neighbor in self.neighbors:
            placed = tilemap.get_placed(x + neighbor.dx, y + neighbor.dy)
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

    def get_sprite_id(self, tilemap, x, y):
        for rule in sorted(self.rules, key=lambda r: r.priority):
            if rule.matches(tilemap, x, y, self):
                return rule.result_tile_id
        return self.default_tile_id