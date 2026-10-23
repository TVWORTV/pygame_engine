import math

import pygame
from pygame.math import Vector2

from .collision_world import CollisionWorld
from .detail import CapsuleDirection, DetailLevel
from .geometry import (
    CircleShape,
    circle_points,
    convex_hull,
    ensure_ccw,
    is_convex,
    is_circle,
    merge_convex,
    piece_area_and_polar_moment,
    piece_bounds,
    piece_contains,
    polygon_normals,
    signed_area,
    triangulate,
)
from .material import PhysicsMaterial

EVENT_NAMES = (
    "on_collision_enter",
    "on_collision_stay",
    "on_collision_exit",
    "on_trigger_enter",
    "on_trigger_stay",
    "on_trigger_exit",
)


class Collider:
    _counter = 0

    def __init__(
        self,
        offset=(0.0, 0.0),
        local_rotation=0.0,
        is_trigger=False,
        layer=0,
        tag="",
        material=None,
        density=1.0,
        enabled=True,
        body=None,
        target=None,
        position=(0.0, 0.0),
        rotation=0.0,
        world=None,
    ):
        Collider._counter += 1
        self.id = Collider._counter
        self._offset = Vector2(offset)
        self._local_rotation = float(local_rotation)
        self.is_trigger = is_trigger
        self.layer = layer
        self.tag = tag
        self.material = material if material is not None else PhysicsMaterial()
        self.density = density
        self.enabled = enabled
        self.body = None
        self.target = target
        self._position = Vector2(position)
        self._rotation = float(rotation)
        self._local_cache = None
        self._world_key = None
        self.world_pieces = []
        self.piece_bounds = []
        self.piece_normals = []
        self.aabb = (0.0, 0.0, 0.0, 0.0)
        for name in EVENT_NAMES:
            setattr(self, name, None)
        self.world = world if world is not None else CollisionWorld.default()
        self.world.add_collider(self)
        if body is not None:
            body.add_collider(self)

    def build_shape(self):
        return []

    def invalidate(self):
        self._local_cache = None
        self._world_key = None
        if self.body is not None:
            self.body.mark_shape_changed()

    @property
    def offset(self):
        return Vector2(self._offset)

    @offset.setter
    def offset(self, value):
        self._offset = Vector2(value)
        self.invalidate()

    @property
    def local_rotation(self):
        return self._local_rotation

    @local_rotation.setter
    def local_rotation(self, value):
        self._local_rotation = float(value)
        self.invalidate()

    @property
    def local_pieces(self):
        if self._local_cache is None:
            pieces = []
            for raw in self.build_shape():
                if is_circle(raw):
                    center = raw.center.rotate(-self._local_rotation) + self._offset
                    pieces.append(CircleShape(center, raw.radius))
                    continue
                points = [Vector2(p).rotate(-self._local_rotation) + self._offset for p in raw]
                if len(points) >= 3:
                    points = ensure_ccw(points)
                pieces.append(points)
            self._local_cache = pieces
        return self._local_cache

    @property
    def position(self):
        if self.body is not None:
            return self.body.position
        if self.target is not None:
            return Vector2(self.target.position)
        return Vector2(self._position)

    @position.setter
    def position(self, value):
        if self.body is not None:
            self.body.position = value
        elif self.target is not None:
            self.target.position = Vector2(value)
        else:
            self._position = Vector2(value)

    @property
    def rotation(self):
        if self.body is not None:
            return self.body.rotation
        if self.target is not None and hasattr(self.target, "rotation"):
            return float(self.target.rotation)
        return self._rotation

    @rotation.setter
    def rotation(self, value):
        if self.body is not None:
            self.body.rotation = value
        elif self.target is not None and hasattr(self.target, "rotation"):
            self.target.rotation = float(value)
        else:
            self._rotation = float(value)

    @property
    def has_shape(self):
        return len(self.local_pieces) > 0

    @property
    def is_dynamic(self):
        return self.body is not None and not getattr(self.body, "is_kinematic", False)

    @property
    def min_extent(self):
        boxes = [
            piece_bounds(p) for p in self.local_pieces if is_circle(p) or len(p) >= 3
        ]
        if not boxes:
            return 0.0
        min_x = min(b[0] for b in boxes)
        min_y = min(b[1] for b in boxes)
        max_x = max(b[2] for b in boxes)
        max_y = max(b[3] for b in boxes)
        return min(max_x - min_x, max_y - min_y)

    def area_and_polar_moment(self, origin=(0.0, 0.0)):
        origin = Vector2(origin)
        area = 0.0
        moment = 0.0
        for piece in self.local_pieces:
            if not is_circle(piece) and len(piece) < 3:
                continue
            a, j = piece_area_and_polar_moment(piece, origin)
            area += a
            moment += j
        return area, moment

    @property
    def area(self):
        return self.area_and_polar_moment()[0]

    def update_world(self):
        position = self.position
        rotation = self.rotation
        key = (position.x, position.y, rotation)
        if key == self._world_key:
            return
        self._world_key = key
        pieces = []
        bounds = []
        normals = []
        for local in self.local_pieces:
            if is_circle(local):
                center = position + (local.center.rotate(-rotation) if rotation else local.center)
                world_piece = CircleShape(center, local.radius)
                normals.append(None)
            else:
                if rotation == 0.0:
                    world_piece = [position + p for p in local]
                else:
                    world_piece = [position + p.rotate(-rotation) for p in local]
                normals.append(polygon_normals(world_piece))
            pieces.append(world_piece)
            bounds.append(piece_bounds(world_piece))
        self.world_pieces = pieces
        self.piece_bounds = bounds
        self.piece_normals = normals
        if bounds:
            self.aabb = (
                min(b[0] for b in bounds),
                min(b[1] for b in bounds),
                max(b[2] for b in bounds),
                max(b[3] for b in bounds),
            )
        else:
            self.aabb = (0.0, 0.0, 0.0, 0.0)

    def contains_point(self, point):
        self.update_world()
        point = Vector2(point)
        return any(piece_contains(point, piece) for piece in self.world_pieces)

    def velocity_at(self, point):
        if self.body is not None and hasattr(self.body, "get_point_velocity"):
            return Vector2(self.body.get_point_velocity(point))
        return Vector2()

    def draw(self, surface, color=(80, 220, 120), width=1, fill=False):
        self.update_world()
        for piece in self.world_pieces:
            if is_circle(piece):
                center = (piece.center.x, piece.center.y)
                if fill:
                    pygame.draw.circle(surface, color, center, piece.radius)
                pygame.draw.circle(surface, color if not fill else (20, 20, 30), center, piece.radius, width)
                marker = piece.center + Vector2(piece.radius, 0.0).rotate(-self.rotation)
                pygame.draw.line(surface, color if not fill else (20, 20, 30), center, (marker.x, marker.y), max(width, 1))
                continue
            points = [(p.x, p.y) for p in piece]
            if len(points) >= 3:
                if fill:
                    pygame.draw.polygon(surface, color, points)
                pygame.draw.polygon(surface, color if not fill else (20, 20, 30), points, width)
            elif len(points) == 2:
                pygame.draw.line(surface, color, points[0], points[1], max(width, 1))

    def destroy(self):
        if self.body is not None:
            self.body.remove_collider(self)
        self.world.remove_collider(self)


class RectCollider(Collider):
    def __init__(self, size=(32.0, 32.0), **kwargs):
        super().__init__(**kwargs)
        self._size = Vector2(size)

    @property
    def size(self):
        return Vector2(self._size)

    @size.setter
    def size(self, value):
        self._size = Vector2(value)
        self.invalidate()

    def build_shape(self):
        hw = self._size.x * 0.5
        hh = self._size.y * 0.5
        return [[Vector2(-hw, -hh), Vector2(hw, -hh), Vector2(hw, hh), Vector2(-hw, hh)]]


class CircleCollider(Collider):
    def __init__(self, radius=16.0, detail=DetailLevel.MEDIUM, exact=False, **kwargs):
        super().__init__(**kwargs)
        self._radius = float(radius)
        self._detail = max(int(detail), 3)
        self._exact = exact

    @property
    def exact(self):
        return self._exact

    @exact.setter
    def exact(self, value):
        self._exact = bool(value)
        self.invalidate()

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value):
        self._radius = float(value)
        self.invalidate()

    @property
    def detail(self):
        return self._detail

    @detail.setter
    def detail(self, value):
        self._detail = max(int(value), 3)
        self.invalidate()

    def build_shape(self):
        if self._exact:
            return [CircleShape((0.0, 0.0), self._radius)]
        return [circle_points(self._radius, self._detail)]


class CapsuleCollider(Collider):
    def __init__(self, size=(24.0, 48.0), direction=None, detail=DetailLevel.MEDIUM, **kwargs):
        super().__init__(**kwargs)
        self._size = Vector2(size)
        self._direction = direction
        self._detail = max(int(detail), 4)

    @property
    def size(self):
        return Vector2(self._size)

    @size.setter
    def size(self, value):
        self._size = Vector2(value)
        self.invalidate()

    @property
    def direction(self):
        if self._direction is not None:
            return self._direction
        if self._size.y >= self._size.x:
            return CapsuleDirection.VERTICAL
        return CapsuleDirection.HORIZONTAL

    @direction.setter
    def direction(self, value):
        self._direction = value
        self.invalidate()

    @property
    def detail(self):
        return self._detail

    @detail.setter
    def detail(self, value):
        self._detail = max(int(value), 4)
        self.invalidate()

    def build_shape(self):
        horizontal = self.direction == CapsuleDirection.HORIZONTAL
        width, length = (self._size.y, self._size.x) if horizontal else (self._size.x, self._size.y)
        radius = width * 0.5
        half = max(length * 0.5 - radius, 0.0)
        segments = max(self._detail // 2, 2)
        points = []
        for k in range(segments + 1):
            angle = math.pi * k / segments
            points.append(Vector2(radius * math.cos(angle), -half - radius * math.sin(angle)))
        for k in range(segments + 1):
            angle = math.pi + math.pi * k / segments
            points.append(Vector2(radius * math.cos(angle), half - radius * math.sin(angle)))
        if horizontal:
            points = [Vector2(p.y, p.x) for p in points]
        return [points]


class FreeCollider(Collider):
    def __init__(self, points, closed=True, **kwargs):
        super().__init__(**kwargs)
        self._points = [Vector2(p) for p in points]
        self._closed = closed

    @property
    def points(self):
        return [Vector2(p) for p in self._points]

    @points.setter
    def points(self, value):
        self._points = [Vector2(p) for p in value]
        self.invalidate()

    @property
    def closed(self):
        return self._closed

    @closed.setter
    def closed(self, value):
        self._closed = bool(value)
        self.invalidate()

    def _segments(self, loop):
        points = self._points
        count = len(points)
        last = count if loop else count - 1
        return [[Vector2(points[i]), Vector2(points[(i + 1) % count])] for i in range(max(last, 0))]

    def build_shape(self):
        points = self._points
        if len(points) < 2:
            return []
        if not self._closed or len(points) < 3:
            return self._segments(False)
        if abs(signed_area(points)) < 1e-9:
            return self._segments(False)
        oriented = ensure_ccw(points)
        if is_convex(oriented):
            return [[Vector2(p) for p in oriented]]
        triangles = triangulate(points)
        if triangles is None:
            hull = convex_hull(points)
            return [hull] if len(hull) >= 3 else self._segments(True)
        pieces = merge_convex(points, triangles)
        return [[Vector2(points[k]) for k in piece] for piece in pieces]
