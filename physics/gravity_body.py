import math

from pygame.math import Vector2

from .constraints import Constraints
from .force_mode import ForceMode
from .gravity_mode import GravityMode


class GravityBody:
    def __init__(
        self,
        mass=1.0,
        drag=0.0,
        angular_drag=0.05,
        use_gravity=True,
        is_kinematic=False,
        gravity_mode=GravityMode.SIMPLE,
        gravity_direction=(0.0, 1.0),
        gravity_magnitude=None,
        gravity_scale=1.0,
        constraints=Constraints.NONE,
        position=(0.0, 0.0),
        rotation=0.0,
        target=None,
        colliders=None,
        use_auto_mass=False,
        world=None,
    ):
        from .physics_world import PhysicsWorld

        self.world = world if world is not None else PhysicsWorld.default()
        self.target = target
        self.colliders = []
        self._shape_cache = None
        self.use_auto_mass = use_auto_mass
        self._mass = 1.0
        self.mass = mass
        self.drag = drag
        self.angular_drag = angular_drag
        self.use_gravity = use_gravity
        self.is_kinematic = is_kinematic
        self.gravity_mode = gravity_mode
        self.gravity_direction = Vector2(gravity_direction)
        self.gravity_magnitude = gravity_magnitude
        self.gravity_scale = gravity_scale
        self.constraints = constraints
        self.max_linear_velocity = math.inf
        self.max_angular_velocity = math.inf
        self._center_of_mass = Vector2()
        self._inertia = None
        self.velocity = Vector2()
        self.angular_velocity = 0.0
        self._position = Vector2(position)
        self._rotation = float(rotation)
        if target is not None:
            self._pull_from_target()
        self._force = Vector2()
        self._acceleration = Vector2()
        self._torque = 0.0
        self._angular_acceleration = 0.0
        self._move_target = None
        self._rotate_target = None
        self._linear_from_move = False
        self._angular_from_move = False
        self._sleeping = False
        self.world.add_body(self)
        for collider in colliders or []:
            self.add_collider(collider)

    def add_collider(self, collider):
        if collider.body is self:
            return
        if collider.body is not None:
            collider.body.remove_collider(collider)
        collider.body = self
        self.colliders.append(collider)
        collider.invalidate()
        self.mark_shape_changed()

    def remove_collider(self, collider):
        if collider in self.colliders:
            self.colliders.remove(collider)
            collider.body = None
            collider.invalidate()
            self.mark_shape_changed()

    def mark_shape_changed(self):
        self._shape_cache = None

    def _shape_properties(self):
        if self._shape_cache is None:
            area = 0.0
            polar = 0.0
            mass_sum = 0.0
            for collider in self.colliders:
                if collider.is_trigger:
                    continue
                a, j = collider.area_and_polar_moment(self._center_of_mass)
                area += a
                polar += j
                mass_sum += collider.area * collider.density
            self._shape_cache = (area, polar, mass_sum)
        return self._shape_cache

    @property
    def mass(self):
        if self.use_auto_mass and self.colliders:
            mass_sum = self._shape_properties()[2]
            if mass_sum > 0.0:
                return mass_sum
        return self._mass

    @mass.setter
    def mass(self, value):
        self._mass = max(float(value), 1e-6)

    @property
    def inertia(self):
        if self._inertia is not None:
            return self._inertia
        area, polar, _ = self._shape_properties()
        if area > 0.0:
            return max(self.mass * polar / area, 1e-6)
        return self.mass

    @inertia.setter
    def inertia(self, value):
        self._inertia = max(float(value), 1e-6)

    def reset_inertia(self):
        self._inertia = None

    @property
    def center_of_mass(self):
        return Vector2(self._center_of_mass)

    @center_of_mass.setter
    def center_of_mass(self, value):
        self._center_of_mass = Vector2(value)
        self.mark_shape_changed()

    def reset_center_of_mass(self):
        self.center_of_mass = Vector2()

    @property
    def constraints(self):
        return Constraints(self._constraint_bits)

    @constraints.setter
    def constraints(self, value):
        self._constraint_bits = int(value)

    @property
    def inverse_mass(self):
        if self.is_kinematic:
            return 0.0
        if (self._constraint_bits & 3) == 3:
            return 0.0
        return 1.0 / self.mass

    @property
    def inverse_inertia(self):
        if self.is_kinematic or (self._constraint_bits & 4):
            return 0.0
        return 1.0 / self.inertia

    @property
    def position(self):
        return Vector2(self._position)

    @position.setter
    def position(self, value):
        self._position = Vector2(value)
        self._push_to_target()

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, value):
        self._rotation = float(value)
        self._push_to_target()

    @property
    def linear_damping(self):
        return self.drag

    @linear_damping.setter
    def linear_damping(self, value):
        self.drag = value

    @property
    def angular_damping(self):
        return self.angular_drag

    @angular_damping.setter
    def angular_damping(self, value):
        self.angular_drag = value

    @property
    def world_center_of_mass(self):
        return self._position + self._to_world(self._center_of_mass)

    @property
    def is_sleeping(self):
        return self._sleeping

    def sleep(self):
        self._sleeping = True
        self.velocity = Vector2()
        self.angular_velocity = 0.0

    def wake_up(self):
        self._sleeping = False

    def _to_world(self, vector):
        return Vector2(vector).rotate(-self._rotation)

    def _to_local(self, vector):
        return Vector2(vector).rotate(self._rotation)

    def _pull_from_target(self):
        if self.target is None:
            return
        self._position = Vector2(self.target.position)
        if hasattr(self.target, "rotation"):
            self._rotation = float(self.target.rotation)

    def _push_to_target(self):
        if self.target is None:
            return
        self.target.position = Vector2(self._position)
        if hasattr(self.target, "rotation"):
            self.target.rotation = self._rotation

    def add_force(self, force, mode=ForceMode.FORCE):
        if self.is_kinematic:
            return
        force = Vector2(force)
        self.wake_up()
        if mode is ForceMode.FORCE:
            self._force += force
        elif mode is ForceMode.ACCELERATION:
            self._acceleration += force
        elif mode is ForceMode.IMPULSE:
            self.velocity += force / self.mass
        elif mode is ForceMode.VELOCITY_CHANGE:
            self.velocity += force

    def add_relative_force(self, force, mode=ForceMode.FORCE):
        self.add_force(self._to_world(force), mode)

    def add_torque(self, torque, mode=ForceMode.FORCE):
        if self.is_kinematic:
            return
        self.wake_up()
        if mode is ForceMode.FORCE:
            self._torque += torque
        elif mode is ForceMode.ACCELERATION:
            self._angular_acceleration += torque
        elif mode is ForceMode.IMPULSE:
            self.angular_velocity += math.degrees(torque / self.inertia)
        elif mode is ForceMode.VELOCITY_CHANGE:
            self.angular_velocity += math.degrees(torque)

    def add_relative_torque(self, torque, mode=ForceMode.FORCE):
        self.add_torque(torque, mode)

    def add_force_at_position(self, force, position, mode=ForceMode.FORCE):
        if self.is_kinematic:
            return
        force = Vector2(force)
        lever = Vector2(position) - self.world_center_of_mass
        torque = -(lever.x * force.y - lever.y * force.x)
        self.add_force(force, mode)
        self.add_torque(torque, mode)

    def add_relative_force_at_position(self, force, local_position, mode=ForceMode.FORCE):
        self.add_force_at_position(
            self._to_world(force), self._position + self._to_world(local_position), mode
        )

    def add_explosion_force(self, force, origin, radius, upwards_modifier=0.0, mode=ForceMode.FORCE):
        if self.is_kinematic:
            return
        origin = Vector2(origin) + Vector2(0.0, upwards_modifier)
        offset = self.world_center_of_mass - origin
        distance = offset.length()
        if distance > radius or radius <= 0.0:
            return
        if distance == 0.0:
            direction = Vector2(0.0, -1.0)
        else:
            direction = offset / distance
        self.add_force(direction * force * (1.0 - distance / radius), mode)

    def move_position(self, position):
        self._move_target = Vector2(position)

    def move_rotation(self, rotation):
        self._rotate_target = float(rotation)

    def get_point_velocity(self, world_point):
        lever = Vector2(world_point) - self.world_center_of_mass
        omega = math.radians(self.angular_velocity)
        return self.velocity + Vector2(lever.y, -lever.x) * omega

    def get_relative_point_velocity(self, local_point):
        return self.get_point_velocity(self._position + self._to_world(local_point))

    def gravity_acceleration(self):
        if not self.use_gravity:
            return Vector2()
        if self.gravity_mode is GravityMode.SIMPLE:
            acceleration = Vector2(self.world.gravity)
        elif self.gravity_mode is GravityMode.DIRECTIONAL:
            if self.gravity_direction.length_squared() == 0.0:
                return Vector2()
            magnitude = (
                self.gravity_magnitude
                if self.gravity_magnitude is not None
                else self.world.gravity.length()
            )
            acceleration = self.gravity_direction.normalize() * magnitude
        else:
            acceleration = self.world.center_acceleration_at(
                self.world_center_of_mass, ignore=self.target
            )
        return acceleration * self.gravity_scale

    def fixed_update(self, dt):
        self.begin_step(dt)
        self.integrate(dt)
        self.end_step()

    def begin_step(self, step_dt):
        self._pull_from_target()
        if self._move_target is not None:
            if self.is_kinematic:
                if step_dt > 0.0:
                    self.velocity = (self._move_target - self._position) / step_dt
                self._linear_from_move = True
            else:
                self._position = self._apply_position_constraints(self._move_target)
            self._move_target = None
        if self._rotate_target is not None:
            if self.is_kinematic:
                if step_dt > 0.0:
                    self.angular_velocity = (self._rotate_target - self._rotation) / step_dt
                self._angular_from_move = True
            else:
                self._rotation = self._rotate_target
            self._rotate_target = None

    def integrate(self, dt):
        if self.is_kinematic:
            self._position += self.velocity * dt
            self._rotation += self.angular_velocity * dt
            return
        if self._sleeping:
            return
        acceleration = self._force / self.mass + self._acceleration + self.gravity_acceleration()
        self.velocity += acceleration * dt
        self.velocity *= max(0.0, 1.0 - self.drag * dt)
        speed = self.velocity.length()
        if speed > self.max_linear_velocity:
            self.velocity *= self.max_linear_velocity / speed
        angular_acceleration = math.degrees(self._torque / self.inertia + self._angular_acceleration)
        self.angular_velocity += angular_acceleration * dt
        self.angular_velocity *= max(0.0, 1.0 - self.angular_drag * dt)
        self.angular_velocity = max(
            -self.max_angular_velocity, min(self.max_angular_velocity, self.angular_velocity)
        )
        self.enforce_constraints()
        self._position += self.velocity * dt
        self._rotation += self.angular_velocity * dt

    def end_step(self):
        if self._linear_from_move:
            self.velocity = Vector2()
            self._linear_from_move = False
        if self._angular_from_move:
            self.angular_velocity = 0.0
            self._angular_from_move = False
        self._clear_accumulators()
        self._push_to_target()

    def enforce_constraints(self):
        bits = self._constraint_bits
        if not bits:
            return
        if bits & 1:
            self.velocity.x = 0.0
        if bits & 2:
            self.velocity.y = 0.0
        if bits & 4:
            self.angular_velocity = 0.0

    def _apply_position_constraints(self, new_position):
        result = Vector2(new_position)
        if self._constraint_bits & 1:
            result.x = self._position.x
        if self._constraint_bits & 2:
            result.y = self._position.y
        return result

    def _clear_accumulators(self):
        self._force = Vector2()
        self._acceleration = Vector2()
        self._torque = 0.0
        self._angular_acceleration = 0.0

    def destroy(self, destroy_colliders=True):
        for collider in list(self.colliders):
            if destroy_colliders:
                collider.destroy()
            else:
                self.remove_collider(collider)
        self.world.remove_body(self)
