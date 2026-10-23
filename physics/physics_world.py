import math

from pygame.math import Vector2

from collision import CollisionWorld

from .collision_resolver import CollisionResolver


class PhysicsWorld:
    _default = None

    def __init__(
        self,
        gravity=(0.0, 980.0),
        fixed_timestep=1.0 / 60.0,
        max_steps_per_frame=8,
        collision_world=None,
        resolver=None,
    ):
        self.gravity = Vector2(gravity)
        self.fixed_timestep = fixed_timestep
        self.max_steps_per_frame = max_steps_per_frame
        self.time_scale = 1.0
        self.bodies = []
        self.centers = []
        self.collision_world = collision_world if collision_world is not None else CollisionWorld()
        self.resolver = resolver if resolver is not None else CollisionResolver()
        self.continuous = True
        self.max_substeps = 16
        self.min_substep_distance = 2.0
        self._accumulator = 0.0

    @classmethod
    def default(cls):
        if cls._default is None:
            cls._default = cls(collision_world=CollisionWorld.default())
        return cls._default

    @classmethod
    def reset_default(cls):
        cls._default = None
        CollisionWorld.reset_default()

    def add_body(self, body):
        if body not in self.bodies:
            self.bodies.append(body)

    def remove_body(self, body):
        if body in self.bodies:
            self.bodies.remove(body)

    def add_center(self, center):
        if center not in self.centers:
            self.centers.append(center)

    def remove_center(self, center):
        if center in self.centers:
            self.centers.remove(center)

    def center_acceleration_at(self, point, ignore=None):
        total = Vector2()
        for center in self.centers:
            if ignore is not None and center.target is ignore:
                continue
            total += center.get_acceleration_at(point)
        return total

    def step(self, dt):
        self._accumulator += dt * self.time_scale
        steps = 0
        while self._accumulator >= self.fixed_timestep and steps < self.max_steps_per_frame:
            self.fixed_step(self.fixed_timestep)
            self._accumulator -= self.fixed_timestep
            steps += 1
        if steps == self.max_steps_per_frame:
            self._accumulator = 0.0

    def _substeps_for(self, bodies, dt):
        if not self.continuous:
            return 1
        thinnest = math.inf
        for collider in self.collision_world.colliders:
            if collider.enabled and not collider.is_trigger:
                extent = collider.min_extent
                if 0.0 < extent < thinnest:
                    thinnest = extent
        if thinnest == math.inf:
            thinnest = self.min_substep_distance * 2.0
        threshold = max(thinnest * 0.5, self.min_substep_distance)
        fastest = 0.0
        for body in bodies:
            if body.colliders:
                fastest = max(fastest, body.velocity.length() * dt)
        return max(1, min(self.max_substeps, math.ceil(fastest / threshold)))

    def fixed_step(self, dt):
        bodies = list(self.bodies)
        collision_world = self.collision_world
        for body in bodies:
            body.begin_step(dt)
        detecting = bool(collision_world.colliders)
        substeps = self._substeps_for(bodies, dt) if detecting else 1
        sub_dt = dt / substeps
        for _ in range(substeps):
            for body in bodies:
                body.integrate(sub_dt)
            if detecting:
                contacts = collision_world.detect()
                self.resolver.resolve(contacts, sub_dt)
        for body in bodies:
            body.end_step()
        if detecting or collision_world._active_pairs:
            collision_world.dispatch_events()
