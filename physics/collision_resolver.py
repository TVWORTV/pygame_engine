import math

from pygame.math import Vector2


class _Row:
    __slots__ = (
        "contact", "sa", "sb", "rax", "ray", "rbx", "rby", "nx", "ny", "tx", "ty",
        "ima", "imb", "iia", "iib", "mass_n", "mass_t", "bias", "friction",
        "normal_acc", "tangent_acc", "px", "py",
    )


_STATIC = (0.0, 0.0, 0.0)


def _velocity_state(body):
    if body is None:
        return [0.0, 0.0, 0.0]
    return [body.velocity.x, body.velocity.y, math.radians(body.angular_velocity)]


class CollisionResolver:
    def __init__(
        self,
        iterations=10,
        correction_percent=0.8,
        slop=0.5,
        max_correction=10.0,
        restitution_threshold=60.0,
        warm_starting=True,
    ):
        self.iterations = iterations
        self.correction_percent = correction_percent
        self.slop = slop
        self.max_correction = max_correction
        self.restitution_threshold = restitution_threshold
        self.warm_starting = warm_starting
        self._cache = {}
        self._cache_dt = 0.0

    def resolve(self, contacts, dt):
        states = {}
        initial = {}
        rows = []
        jobs = []
        old_cache = self._cache
        scale = dt / self._cache_dt if self._cache_dt > 0.0 else 1.0
        new_cache = {}

        def state_of(body):
            if body is None:
                return [0.0, 0.0, 0.0]
            s = states.get(body)
            if s is None:
                s = _velocity_state(body)
                states[body] = s
                initial[body] = tuple(s)
            return s

        for contact in contacts:
            if contact.is_trigger:
                continue
            collider_a = contact.collider_a
            collider_b = contact.collider_b
            body_a = collider_a.body
            body_b = collider_b.body
            ima = 0.0 if body_a is None else body_a.inverse_mass
            imb = 0.0 if body_b is None else body_b.inverse_mass
            iia = 0.0 if body_a is None else body_a.inverse_inertia
            iib = 0.0 if body_b is None else body_b.inverse_inertia
            if ima + imb + iia + iib == 0.0:
                continue
            if (body_a is None or body_a.is_sleeping) and (body_b is None or body_b.is_sleeping):
                continue
            friction = math.sqrt(collider_a.material.friction * collider_b.material.friction)
            bounce = max(collider_a.material.bounciness, collider_b.material.bounciness)
            sa = state_of(body_a)
            sb = state_of(body_b)
            com_a = body_a.world_center_of_mass if body_a is not None else Vector2()
            com_b = body_b.world_center_of_mass if body_b is not None else Vector2()
            for index, manifold in enumerate(contact.manifolds):
                normal = manifold.normal
                nx = normal.x
                ny = normal.y
                tx = -ny
                ty = nx
                jobs.append((manifold, body_a, body_b, ima, imb))
                key = (collider_a.id, collider_b.id, index)
                previous = old_cache.get(key) if self.warm_starting else None
                saved = []
                for point in manifold.points:
                    row = _Row()
                    row.contact = contact
                    row.sa = sa
                    row.sb = sb
                    row.rax = point.x - com_a.x
                    row.ray = point.y - com_a.y
                    row.rbx = point.x - com_b.x
                    row.rby = point.y - com_b.y
                    row.nx = nx
                    row.ny = ny
                    row.tx = tx
                    row.ty = ty
                    row.ima = ima
                    row.imb = imb
                    row.iia = iia
                    row.iib = iib
                    cn_a = row.rax * ny - row.ray * nx
                    cn_b = row.rbx * ny - row.rby * nx
                    ct_a = row.rax * ty - row.ray * tx
                    ct_b = row.rbx * ty - row.rby * tx
                    kn = ima + imb + iia * cn_a * cn_a + iib * cn_b * cn_b
                    kt = ima + imb + iia * ct_a * ct_a + iib * ct_b * ct_b
                    if kn <= 0.0:
                        continue
                    row.mass_n = 1.0 / kn
                    row.mass_t = 1.0 / kt if kt > 0.0 else 0.0
                    dvx = (sb[0] + sb[2] * row.rby) - (sa[0] + sa[2] * row.ray)
                    dvy = (sb[1] - sb[2] * row.rbx) - (sa[1] - sa[2] * row.rax)
                    vn = dvx * nx + dvy * ny
                    row.bias = -bounce * vn if vn < -self.restitution_threshold else 0.0
                    row.friction = friction
                    row.normal_acc = 0.0
                    row.tangent_acc = 0.0
                    row.px = point.x
                    row.py = point.y
                    if previous:
                        best = None
                        best_d = 16.0
                        for ox, oy, on, ot in previous:
                            d = (ox - point.x) ** 2 + (oy - point.y) ** 2
                            if d < best_d:
                                best_d = d
                                best = (on, ot)
                        if best is not None:
                            row.normal_acc = best[0] * scale
                            row.tangent_acc = best[1] * scale
                            self._apply(row, row.normal_acc * nx + row.tangent_acc * tx,
                                        row.normal_acc * ny + row.tangent_acc * ty)
                    rows.append(row)
                    saved.append(row)
                if saved:
                    new_cache[key] = saved
        for _ in range(self.iterations):
            for row in rows:
                self._solve_row(row)
        self._cache = {
            key: [(r.px, r.py, r.normal_acc, r.tangent_acc) for r in saved]
            for key, saved in new_cache.items()
        }
        self._cache_dt = dt
        for row in rows:
            row.contact.normal_impulse += row.normal_acc
        for body, state in states.items():
            start = initial[body]
            if body.is_kinematic:
                continue
            changed = (
                abs(state[0] - start[0]) > 1e-9
                or abs(state[1] - start[1]) > 1e-9
                or abs(state[2] - start[2]) > 1e-9
            )
            if not changed:
                continue
            if body.is_sleeping:
                body.wake_up()
            body.velocity = Vector2(state[0], state[1])
            body.angular_velocity = math.degrees(state[2])
            body.enforce_constraints()
        for manifold, body_a, body_b, ima, imb in jobs:
            total = ima + imb
            if total <= 0.0:
                continue
            correction = min(
                max(manifold.depth - self.slop, 0.0) * self.correction_percent,
                self.max_correction,
            )
            if correction <= 0.0:
                continue
            delta = manifold.normal * (correction / total)
            self._move(body_a, -delta * ima)
            self._move(body_b, delta * imb)

    @staticmethod
    def _apply(row, px, py):
        sa = row.sa
        sb = row.sb
        if row.ima:
            sa[0] -= px * row.ima
            sa[1] -= py * row.ima
        if row.iia:
            sa[2] += (row.rax * py - row.ray * px) * row.iia
        if row.imb:
            sb[0] += px * row.imb
            sb[1] += py * row.imb
        if row.iib:
            sb[2] -= (row.rbx * py - row.rby * px) * row.iib

    def _solve_row(self, row):
        sa = row.sa
        sb = row.sb
        nx = row.nx
        ny = row.ny
        tx = row.tx
        ty = row.ty
        dvx = (sb[0] + sb[2] * row.rby) - (sa[0] + sa[2] * row.ray)
        dvy = (sb[1] - sb[2] * row.rbx) - (sa[1] - sa[2] * row.rax)
        limit = row.friction * row.normal_acc
        new_t = row.tangent_acc - (dvx * tx + dvy * ty) * row.mass_t
        if new_t > limit:
            new_t = limit
        elif new_t < -limit:
            new_t = -limit
        lam = new_t - row.tangent_acc
        row.tangent_acc = new_t
        if lam:
            self._apply(row, tx * lam, ty * lam)
            dvx = (sb[0] + sb[2] * row.rby) - (sa[0] + sa[2] * row.ray)
            dvy = (sb[1] - sb[2] * row.rbx) - (sa[1] - sa[2] * row.rax)
        new_n = row.normal_acc - ((dvx * nx + dvy * ny) - row.bias) * row.mass_n
        if new_n < 0.0:
            new_n = 0.0
        lam = new_n - row.normal_acc
        row.normal_acc = new_n
        if lam:
            self._apply(row, nx * lam, ny * lam)

    @staticmethod
    def _move(body, delta):
        if body is None or body.is_sleeping or body.is_kinematic:
            return
        bits = body._constraint_bits
        if bits & 1:
            delta.x = 0.0
        if bits & 2:
            delta.y = 0.0
        body.position = body.position + delta
