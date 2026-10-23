from enum import Enum, auto

from pygame.math import Vector2


class Falloff(Enum):
    CONSTANT = auto()
    LINEAR = auto()
    INVERSE_SQUARE = auto()


class GravityCenter:
    def __init__(
        self,
        position=(0.0, 0.0),
        strength=1000.0,
        radius=500.0,
        falloff=Falloff.INVERSE_SQUARE,
        core_radius=25.0,
        enabled=True,
        target=None,
        world=None,
    ):
        from .physics_world import PhysicsWorld

        self._position = Vector2(position)
        self.strength = strength
        self.radius = radius
        self.falloff = falloff
        self.core_radius = max(core_radius, 1e-6)
        self.enabled = enabled
        self.target = target
        self.world = world if world is not None else PhysicsWorld.default()
        self.world.add_center(self)

    @property
    def position(self):
        if self.target is not None:
            return Vector2(self.target.position)
        return Vector2(self._position)

    @position.setter
    def position(self, value):
        self._position = Vector2(value)
        if self.target is not None:
            self.target.position = Vector2(value)

    def magnitude_at_distance(self, distance):
        if distance > self.radius:
            return 0.0
        if self.falloff is Falloff.CONSTANT:
            return self.strength
        if self.falloff is Falloff.LINEAR:
            return self.strength * (1.0 - distance / self.radius)
        reference = max(distance, self.core_radius)
        return self.strength * (self.core_radius / reference) ** 2

    def get_acceleration_at(self, point):
        if not self.enabled:
            return Vector2()
        offset = self.position - Vector2(point)
        distance = offset.length()
        if distance == 0.0:
            return Vector2()
        magnitude = self.magnitude_at_distance(distance)
        if magnitude == 0.0:
            return Vector2()
        return offset * (magnitude / distance)

    def destroy(self):
        self.world.remove_center(self)
