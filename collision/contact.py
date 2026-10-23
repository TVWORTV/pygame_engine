from pygame.math import Vector2


class Contact:
    def __init__(self, collider_a, collider_b, manifolds, is_trigger):
        self.collider_a = collider_a
        self.collider_b = collider_b
        self.manifolds = manifolds
        self.is_trigger = is_trigger
        self.normal_impulse = 0.0
        self.relative_velocity = Vector2()

    @property
    def deepest(self):
        return max(self.manifolds, key=lambda m: m.depth)

    @property
    def normal(self):
        return Vector2(self.deepest.normal)

    @property
    def depth(self):
        return self.deepest.depth

    @property
    def points(self):
        return [Vector2(p) for p in self.deepest.points]


class Collision:
    def __init__(self, collider, other, contact):
        self.collider = collider
        self.other = other
        self.contact = contact
        is_a = contact.collider_a is collider
        self.normal = -contact.normal if is_a else contact.normal
        self.relative_velocity = (
            -contact.relative_velocity if is_a else Vector2(contact.relative_velocity)
        )
        self.points = contact.points
        self.depth = contact.depth
        self.impulse = contact.normal_impulse

    @property
    def body(self):
        return self.collider.body

    @property
    def other_body(self):
        return self.other.body


class RaycastHit:
    def __init__(self, collider, point, normal, distance):
        self.collider = collider
        self.point = point
        self.normal = normal
        self.distance = distance
