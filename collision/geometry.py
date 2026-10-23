import math

from pygame.math import Vector2

EPSILON = 1e-9


def cross(a, b):
    return a.x * b.y - a.y * b.x


def signed_area(points):
    total = 0.0
    count = len(points)
    for i in range(count):
        a = points[i]
        b = points[(i + 1) % count]
        total += a.x * b.y - b.x * a.y
    return total * 0.5


def ensure_ccw(points):
    if signed_area(points) < 0.0:
        return list(reversed(points))
    return list(points)


def is_convex(points, tolerance=1e-7):
    count = len(points)
    if count < 3:
        return True
    for i in range(count):
        a = points[i]
        b = points[(i + 1) % count]
        c = points[(i + 2) % count]
        if cross(b - a, c - b) < -tolerance:
            return False
    return True


def convex_hull(points):
    unique = sorted(set((p.x, p.y) for p in points))
    if len(unique) <= 2:
        return [Vector2(p) for p in unique]

    def turn(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in unique:
        while len(lower) >= 2 and turn(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(unique):
        while len(upper) >= 2 and turn(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return [Vector2(p) for p in lower[:-1] + upper[:-1]]


def circle_points(radius, count, center=(0.0, 0.0)):
    center = Vector2(center)
    return [
        center + Vector2(math.cos(math.tau * k / count), math.sin(math.tau * k / count)) * radius
        for k in range(count)
    ]


def polygon_bounds(points):
    min_x = min(p.x for p in points)
    min_y = min(p.y for p in points)
    max_x = max(p.x for p in points)
    max_y = max(p.y for p in points)
    return (min_x, min_y, max_x, max_y)


def bounds_overlap(a, b):
    return not (a[0] > b[2] or b[0] > a[2] or a[1] > b[3] or b[1] > a[3])


def polygon_area_and_polar_moment(points):
    count = len(points)
    if count < 3:
        return 0.0, 0.0
    area = 0.0
    moment = 0.0
    for i in range(count):
        a = points[i]
        b = points[(i + 1) % count]
        c = a.x * b.y - b.x * a.y
        area += c
        moment += c * (a.dot(a) + a.dot(b) + b.dot(b))
    return area * 0.5, moment / 12.0


def point_in_convex(point, polygon):
    count = len(polygon)
    if count < 3:
        return False
    for i in range(count):
        a = polygon[i]
        edge = polygon[(i + 1) % count] - a
        if cross(edge, point - a) < 0.0:
            return False
    return True


def _strictly_inside(p, a, b, c):
    return (
        cross(b - a, p - a) > EPSILON
        and cross(c - b, p - b) > EPSILON
        and cross(a - c, p - c) > EPSILON
    )


def triangulate(points):
    count = len(points)
    if count < 3:
        return None
    indices = list(range(count))
    if signed_area(points) < 0.0:
        indices.reverse()
    triangles = []
    while len(indices) > 3:
        size = len(indices)
        found = False
        for i in range(size):
            ip = indices[(i - 1) % size]
            ic = indices[i]
            inx = indices[(i + 1) % size]
            a, b, c = points[ip], points[ic], points[inx]
            if cross(b - a, c - b) <= EPSILON:
                continue
            blocked = False
            for j in indices:
                if j in (ip, ic, inx):
                    continue
                if _strictly_inside(points[j], a, b, c):
                    blocked = True
                    break
            if blocked:
                continue
            triangles.append((ip, ic, inx))
            indices.pop(i)
            found = True
            break
        if found:
            continue
        removed = False
        for i in range(size):
            a = points[indices[(i - 1) % size]]
            b = points[indices[i]]
            c = points[indices[(i + 1) % size]]
            if abs(cross(b - a, c - b)) <= EPSILON:
                indices.pop(i)
                removed = True
                break
        if not removed:
            return None
    if len(indices) == 3:
        a, b, c = (points[k] for k in indices)
        if abs(cross(b - a, c - b)) > EPSILON:
            triangles.append(tuple(indices))
    return triangles


def _try_merge(points, first, second):
    first_count = len(first)
    second_count = len(second)
    for ia in range(first_count):
        u = first[ia]
        v = first[(ia + 1) % first_count]
        for ib in range(second_count):
            if second[ib] == v and second[(ib + 1) % second_count] == u:
                path = [first[(ia + 1 + k) % first_count] for k in range(first_count)]
                interior = [second[(ib + 2 + k) % second_count] for k in range(second_count - 2)]
                candidate = path + interior
                if is_convex([points[k] for k in candidate]):
                    return candidate
                return None
    return None


def merge_convex(points, triangles):
    pieces = [list(t) for t in triangles]
    changed = True
    while changed:
        changed = False
        for i in range(len(pieces)):
            for j in range(i + 1, len(pieces)):
                candidate = _try_merge(points, pieces[i], pieces[j])
                if candidate is not None:
                    pieces[i] = candidate
                    pieces.pop(j)
                    changed = True
                    break
            if changed:
                break
    return pieces


def polygon_normals(polygon):
    normals = []
    count = len(polygon)
    for i in range(count):
        edge = polygon[(i + 1) % count] - polygon[i]
        length = edge.length()
        if length < EPSILON:
            normals.append(Vector2())
        else:
            normals.append(Vector2(edge.y, -edge.x) / length)
    return normals


class CircleShape:
    __slots__ = ("center", "radius")

    def __init__(self, center, radius):
        self.center = Vector2(center)
        self.radius = float(radius)


def is_circle(piece):
    return type(piece) is CircleShape


def piece_bounds(piece):
    if type(piece) is CircleShape:
        c = piece.center
        r = piece.radius
        return (c.x - r, c.y - r, c.x + r, c.y + r)
    return polygon_bounds(piece)


def piece_contains(point, piece):
    if type(piece) is CircleShape:
        return (point - piece.center).length_squared() <= piece.radius * piece.radius
    return point_in_convex(point, piece)


def piece_area_and_polar_moment(piece, origin=(0.0, 0.0)):
    origin = Vector2(origin)
    if type(piece) is CircleShape:
        area = math.pi * piece.radius * piece.radius
        offset = piece.center - origin
        return area, 0.5 * area * piece.radius * piece.radius + area * offset.length_squared()
    return polygon_area_and_polar_moment([p - origin for p in piece])


class Manifold:
    __slots__ = ("normal", "depth", "points")

    def __init__(self, normal, depth, points):
        self.normal = normal
        self.depth = depth
        self.points = points


def _max_separation(poly_a, normals_a, poly_b):
    best = -math.inf
    best_index = -1
    for i in range(len(normals_a)):
        normal = normals_a[i]
        nx = normal.x
        ny = normal.y
        if nx == 0.0 and ny == 0.0:
            continue
        origin = poly_a[i]
        ox = origin.x
        oy = origin.y
        separation = math.inf
        for p in poly_b:
            d = (p.x - ox) * nx + (p.y - oy) * ny
            if d < separation:
                separation = d
        if separation > 0.0:
            return separation, i
        if separation > best:
            best = separation
            best_index = i
    return best, best_index


def _clip(p0, p1, normal, offset):
    d0 = normal.dot(p0) - offset
    d1 = normal.dot(p1) - offset
    out = []
    if d0 <= 0.0:
        out.append(p0)
    if d1 <= 0.0:
        out.append(p1)
    if d0 * d1 < 0.0:
        out.append(p0 + (p1 - p0) * (d0 / (d0 - d1)))
    return out


def _contact_points(ref, ref_index, ref_normal, inc, inc_normals):
    v1 = ref[ref_index]
    v2 = ref[(ref_index + 1) % len(ref)]
    tangent = v2 - v1
    length = tangent.length()
    if length < EPSILON:
        tangent = Vector2(ref_normal.y, -ref_normal.x)
    else:
        tangent = tangent / length
    incident_index = 0
    lowest = math.inf
    for i, normal in enumerate(inc_normals):
        d = normal.dot(ref_normal)
        if d < lowest:
            lowest = d
            incident_index = i
    w1 = inc[incident_index]
    w2 = inc[(incident_index + 1) % len(inc)]
    deepest = min(inc, key=lambda p: (p - v1).dot(ref_normal))
    clipped = _clip(w1, w2, -tangent, -tangent.dot(v1))
    if len(clipped) < 2:
        return [deepest]
    clipped = _clip(clipped[0], clipped[1], tangent, tangent.dot(v2))
    if len(clipped) < 2:
        return [deepest]
    result = [p for p in clipped if (p - v1).dot(ref_normal) <= 1e-6]
    if not result:
        return [deepest]
    return result


def collide_convex(poly_a, poly_b, want_points=True, normals_a=None, normals_b=None):
    if normals_a is None:
        normals_a = polygon_normals(poly_a)
    if normals_b is None:
        normals_b = polygon_normals(poly_b)
    separation_a, index_a = _max_separation(poly_a, normals_a, poly_b)
    if index_a < 0 or separation_a > 0.0:
        return None
    separation_b, index_b = _max_separation(poly_b, normals_b, poly_a)
    if index_b < 0 or separation_b > 0.0:
        return None
    if separation_b > separation_a + 0.01:
        ref, ref_index = poly_b, index_b
        inc, inc_normals = poly_a, normals_a
        ref_normal = normals_b[index_b]
        normal = -ref_normal
        depth = -separation_b
    else:
        ref, ref_index = poly_a, index_a
        inc, inc_normals = poly_b, normals_b
        ref_normal = normals_a[index_a]
        normal = Vector2(ref_normal)
        depth = -separation_a
    points = []
    if want_points:
        points = _contact_points(ref, ref_index, ref_normal, inc, inc_normals)
    return Manifold(normal, depth, points)


def collide_circles(a, b):
    offset = b.center - a.center
    distance = offset.length()
    total = a.radius + b.radius
    if distance > total:
        return None
    if distance < EPSILON:
        normal = Vector2(0.0, -1.0)
    else:
        normal = offset / distance
    depth = total - distance
    point = a.center + normal * (a.radius - depth * 0.5)
    return Manifold(normal, depth, [point])


def collide_polygon_circle(poly, normals, center, radius):
    best = -math.inf
    best_index = -1
    for i, normal in enumerate(normals):
        if normal.x == 0.0 and normal.y == 0.0:
            continue
        separation = (center - poly[i]).dot(normal)
        if separation > radius:
            return None
        if separation > best:
            best = separation
            best_index = i
    if best_index < 0:
        return None
    v1 = poly[best_index]
    v2 = poly[(best_index + 1) % len(poly)]
    if best >= 0.0:
        edge = v2 - v1
        u1 = (center - v1).dot(edge)
        u2 = (center - v2).dot(-edge)
        corner = None
        if u1 <= 0.0:
            corner = v1
        elif u2 <= 0.0:
            corner = v2
        if corner is not None:
            offset = center - corner
            distance = offset.length()
            if distance > radius:
                return None
            normal = offset / distance if distance > EPSILON else Vector2(normals[best_index])
            return Manifold(normal, radius - distance, [Vector2(corner)])
    normal = Vector2(normals[best_index])
    return Manifold(normal, radius - best, [center - normal * best])


def collide_pieces(a, b, want_points=True, normals_a=None, normals_b=None):
    a_circle = type(a) is CircleShape
    b_circle = type(b) is CircleShape
    if a_circle and b_circle:
        return collide_circles(a, b)
    if b_circle:
        if normals_a is None:
            normals_a = polygon_normals(a)
        return collide_polygon_circle(a, normals_a, b.center, b.radius)
    if a_circle:
        if normals_b is None:
            normals_b = polygon_normals(b)
        manifold = collide_polygon_circle(b, normals_b, a.center, a.radius)
        if manifold is not None:
            manifold.normal = -manifold.normal
        return manifold
    return collide_convex(a, b, want_points, normals_a, normals_b)


def _ray_segment(origin, direction, p0, p1, max_distance):
    s = p1 - p0
    denominator = cross(direction, s)
    if abs(denominator) < EPSILON:
        return None
    delta = p0 - origin
    t = cross(delta, s) / denominator
    u = cross(delta, direction) / denominator
    if t < 0.0 or t > max_distance or u < 0.0 or u > 1.0:
        return None
    length = s.length()
    if length < EPSILON:
        return None
    normal = Vector2(s.y, -s.x) / length
    if normal.dot(direction) > 0.0:
        normal = -normal
    return t, normal, origin + direction * t


def _raycast_circle(origin, direction, circle, max_distance):
    offset = origin - circle.center
    b = offset.dot(direction)
    c = offset.dot(offset) - circle.radius * circle.radius
    if c <= 0.0:
        return 0.0, -direction, Vector2(origin)
    if b > 0.0:
        return None
    discriminant = b * b - c
    if discriminant < 0.0:
        return None
    t = -b - math.sqrt(discriminant)
    if t > max_distance:
        return None
    point = origin + direction * t
    return t, (point - circle.center) / circle.radius, point


def raycast_piece(origin, direction, piece, max_distance):
    if type(piece) is CircleShape:
        return _raycast_circle(origin, direction, piece, max_distance)
    count = len(piece)
    if count < 2:
        return None
    if count == 2:
        return _ray_segment(origin, direction, piece[0], piece[1], max_distance)
    t_enter = -math.inf
    t_exit = math.inf
    hit_normal = None
    for i in range(count):
        a = piece[i]
        edge = piece[(i + 1) % count] - a
        length = edge.length()
        if length < EPSILON:
            continue
        normal = Vector2(edge.y, -edge.x) / length
        denominator = direction.dot(normal)
        numerator = (a - origin).dot(normal)
        if abs(denominator) < 1e-12:
            if numerator < 0.0:
                return None
            continue
        t = numerator / denominator
        if denominator < 0.0:
            if t > t_enter:
                t_enter = t
                hit_normal = normal
        else:
            t_exit = min(t_exit, t)
    if t_enter > t_exit or t_exit < 0.0:
        return None
    if t_enter < 0.0:
        return 0.0, -direction, Vector2(origin)
    if t_enter > max_distance or hit_normal is None:
        return None
    return t_enter, hit_normal, origin + direction * t_enter
