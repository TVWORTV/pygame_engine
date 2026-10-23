import math

from pygame.math import Vector2

from .contact import Collision, Contact, RaycastHit
from .geometry import (
    CircleShape,
    bounds_overlap,
    collide_pieces,
    piece_bounds,
    piece_contains,
    raycast_piece,
)

ALL_LAYERS = 0xFFFFFFFF


class CollisionWorld:
    _default = None

    def __init__(self):
        self.colliders = []
        self._ignored_layers = set()
        self._active_pairs = {}
        self._frame_pairs = {}

    @classmethod
    def default(cls):
        if cls._default is None:
            cls._default = cls()
        return cls._default

    @classmethod
    def reset_default(cls):
        cls._default = None

    def add_collider(self, collider):
        if collider not in self.colliders:
            self.colliders.append(collider)

    def remove_collider(self, collider):
        if collider in self.colliders:
            self.colliders.remove(collider)
        for store in (self._active_pairs, self._frame_pairs):
            for key in [k for k in store if collider.id in k]:
                contact = store.pop(key)
                if store is self._active_pairs:
                    self._fire_exit(contact)

    def set_layer_collision(self, layer_a, layer_b, enabled):
        key = (min(layer_a, layer_b), max(layer_a, layer_b))
        if enabled:
            self._ignored_layers.discard(key)
        else:
            self._ignored_layers.add(key)

    def layers_collide(self, layer_a, layer_b):
        return (min(layer_a, layer_b), max(layer_a, layer_b)) not in self._ignored_layers

    def _candidate_pairs(self, active):
        ordered = sorted(active, key=lambda c: c.aabb[0])
        for i, a in enumerate(ordered):
            for j in range(i + 1, len(ordered)):
                b = ordered[j]
                if b.aabb[0] > a.aabb[2]:
                    break
                if not bounds_overlap(a.aabb, b.aabb):
                    continue
                if a.id < b.id:
                    yield a, b
                else:
                    yield b, a

    def _test_pair(self, a, b):
        if a.body is not None and a.body is b.body:
            return None
        if not self.layers_collide(a.layer, b.layer):
            return None
        trigger = a.is_trigger or b.is_trigger
        if trigger:
            if a.body is None and b.body is None:
                return None
        elif not (a.is_dynamic or b.is_dynamic):
            return None
        manifolds = []
        for i, piece_a in enumerate(a.world_pieces):
            bounds_a = a.piece_bounds[i]
            for j, piece_b in enumerate(b.world_pieces):
                if not bounds_overlap(bounds_a, b.piece_bounds[j]):
                    continue
                manifold = collide_pieces(
                    piece_a,
                    piece_b,
                    not trigger,
                    a.piece_normals[i],
                    b.piece_normals[j],
                )
                if manifold is not None:
                    manifolds.append(manifold)
                    if trigger:
                        break
            if trigger and manifolds:
                break
        if not manifolds:
            return None
        contact = Contact(a, b, manifolds, trigger)
        if not trigger:
            deepest = contact.deepest
            if deepest.points:
                point = deepest.points[0]
                contact.relative_velocity = b.velocity_at(point) - a.velocity_at(point)
        return contact

    def detect(self):
        active = [c for c in self.colliders if c.enabled and c.has_shape]
        for collider in active:
            collider.update_world()
        contacts = []
        for a, b in self._candidate_pairs(active):
            contact = self._test_pair(a, b)
            if contact is not None:
                contacts.append(contact)
                self._frame_pairs[(a.id, b.id)] = contact
        return contacts

    def step(self, resolver=None):
        contacts = self.detect()
        if resolver is not None:
            resolver(contacts)
        self.dispatch_events()
        return contacts

    def dispatch_events(self):
        current = self._frame_pairs
        previous = self._active_pairs
        self._frame_pairs = {}
        self._active_pairs = current
        for key, contact in list(current.items()):
            old = previous.get(key)
            if old is None:
                self._fire_enter(contact)
            elif old.is_trigger != contact.is_trigger:
                self._fire_exit(old)
                self._fire_enter(contact)
            else:
                self._fire_stay(contact)
        for key, old in list(previous.items()):
            if key not in current:
                self._fire_exit(old)

    @staticmethod
    def _call(collider, name, argument):
        callback = getattr(collider, name, None)
        if callable(callback):
            callback(argument)
        target = collider.target
        if target is not None:
            handler = getattr(target, name, None)
            if callable(handler):
                handler(argument)

    def _fire(self, contact, phase):
        a = contact.collider_a
        b = contact.collider_b
        if contact.is_trigger:
            name = "on_trigger_" + phase
            self._call(a, name, b)
            self._call(b, name, a)
        else:
            name = "on_collision_" + phase
            self._call(a, name, Collision(a, b, contact))
            self._call(b, name, Collision(b, a, contact))

    def _fire_enter(self, contact):
        self._fire(contact, "enter")

    def _fire_stay(self, contact):
        self._fire(contact, "stay")

    def _fire_exit(self, contact):
        self._fire(contact, "exit")

    def _query_candidates(self, layer_mask, include_triggers):
        result = []
        for collider in self.colliders:
            if not collider.enabled or not collider.has_shape:
                continue
            if not (layer_mask >> collider.layer) & 1:
                continue
            if collider.is_trigger and not include_triggers:
                continue
            collider.update_world()
            result.append(collider)
        return result

    def overlap_point(self, point, layer_mask=ALL_LAYERS, include_triggers=True):
        point = Vector2(point)
        return [
            c
            for c in self._query_candidates(layer_mask, include_triggers)
            if c.aabb[0] <= point.x <= c.aabb[2]
            and c.aabb[1] <= point.y <= c.aabb[3]
            and any(piece_contains(point, piece) for piece in c.world_pieces)
        ]

    def overlap_circle(self, center, radius, layer_mask=ALL_LAYERS, include_triggers=True):
        shape = CircleShape(center, radius)
        bounds = piece_bounds(shape)
        found = []
        for collider in self._query_candidates(layer_mask, include_triggers):
            if not bounds_overlap(bounds, collider.aabb):
                continue
            for piece, box in zip(collider.world_pieces, collider.piece_bounds):
                if bounds_overlap(bounds, box) and collide_pieces(shape, piece, False):
                    found.append(collider)
                    break
        return found

    def raycast_all(self, origin, direction, max_distance=math.inf, layer_mask=ALL_LAYERS, include_triggers=False):
        origin = Vector2(origin)
        direction = Vector2(direction)
        if direction.length_squared() == 0.0:
            return []
        direction = direction.normalize()
        hits = []
        for collider in self._query_candidates(layer_mask, include_triggers):
            best = None
            for piece in collider.world_pieces:
                result = raycast_piece(origin, direction, piece, max_distance)
                if result is not None and (best is None or result[0] < best[0]):
                    best = result
            if best is not None:
                hits.append(RaycastHit(collider, best[2], best[1], best[0]))
        hits.sort(key=lambda h: h.distance)
        return hits

    def raycast(self, origin, direction, max_distance=math.inf, layer_mask=ALL_LAYERS, include_triggers=False):
        hits = self.raycast_all(origin, direction, max_distance, layer_mask, include_triggers)
        return hits[0] if hits else None

    def debug_draw(self, surface, color=(80, 220, 120), trigger_color=(240, 200, 60), width=1):
        for collider in self.colliders:
            if collider.enabled and collider.has_shape:
                collider.draw(surface, trigger_color if collider.is_trigger else color, width)
