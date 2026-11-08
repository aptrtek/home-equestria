#!/usr/bin/env python3
"""Original mane and tail shells for the five Mare Fair mascots.

The game skins a mane to mHead/mNeck/mChest and a tail to mTail1..mTail6
(hybrid_hair_link.gd, hybrid_tail_motion.gd). These GLBs use that same rig,
copied from an existing hair file so the bind pose still meets the head and
the rump, but the surfaces are new. Shapes follow the public mascot art
(marefair.org portraits and the 2025 idle clips), not another pony's mesh.

Coordinates are the hair rig's glTF space: +Y up, -Z toward the face,
the head bone near (0, 0.77, -0.22), the tail hanging through +Z then down.
"""

import json
import math
import os
import struct

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DONOR = os.path.join(ROOT, "world", "characters", "background", "lily_valley_hair.glb")
OUT_DIR = os.path.join(ROOT, "mods", "mare_fair", "hair")

# Skin joint index. Matches the donor skin order.
HEAD, NECK, CHEST = 4, 3, 2
TAIL = [5, 6, 7, 8, 9, 10]

TAIL_BONES = [
    (0.0, 0.636, 0.166),
    (0.014, 0.684, 0.288),
    (0.037, 0.685, 0.400),
    (0.072, 0.603, 0.497),
    (0.076, 0.473, 0.501),
    (0.079, 0.341, 0.502),
]


def vadd(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vmul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def vdot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vcross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def vlen(a):
    return math.sqrt(vdot(a, a))


def vnorm(a):
    length = vlen(a)
    if length < 1e-8:
        return (0.0, 1.0, 0.0)
    return vmul(a, 1.0 / length)


def lerp(a, b, t):
    return a + (b - a) * t


def vlerp(a, b, t):
    return (
        lerp(a[0], b[0], t),
        lerp(a[1], b[1], t),
        lerp(a[2], b[2], t),
    )


def clamp(t, lo=0.0, hi=1.0):
    return lo if t < lo else hi if t > hi else t


def srgb(hex_color):
    """glTF baseColorFactor is linear."""
    hex_color = hex_color.lstrip("#")
    channels = []
    for i in range(0, 6, 2):
        value = int(hex_color[i : i + 2], 16) / 255.0
        if value <= 0.04045:
            channels.append(value / 12.92)
        else:
            channels.append(((value + 0.055) / 1.055) ** 2.4)
    return channels + [1.0]


def catmull(points, steps):
    if len(points) < 2:
        return list(points)
    padded = [points[0]] + list(points) + [points[-1]]
    out = []
    spans = len(padded) - 3
    for i in range(spans):
        p0, p1, p2, p3 = padded[i : i + 4]
        count = steps if i < spans - 1 else steps + 1
        for s in range(count):
            t = s / steps
            t2 = t * t
            t3 = t2 * t
            out.append(
                (
                    0.5
                    * (
                        2 * p1[0]
                        + (-p0[0] + p2[0]) * t
                        + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                        + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
                    ),
                    0.5
                    * (
                        2 * p1[1]
                        + (-p0[1] + p2[1]) * t
                        + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                        + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
                    ),
                    0.5
                    * (
                        2 * p1[2]
                        + (-p0[2] + p2[2]) * t
                        + (2 * p0[2] - 5 * p1[2] + 4 * p2[2] - p3[2]) * t2
                        + (-p0[2] + 3 * p1[2] - 3 * p2[2] + p3[2]) * t3
                    ),
                )
            )
    return out


def frames(points, up=(0.0, 1.0, 0.0)):
    tangents = []
    for i, point in enumerate(points):
        if i == 0:
            direction = vsub(points[1], point)
        elif i == len(points) - 1:
            direction = vsub(point, points[i - 1])
        else:
            direction = vsub(points[i + 1], points[i - 1])
        tangents.append(vnorm(direction))
    out = []
    for tangent in tangents:
        side = vcross(tangent, up)
        if vlen(side) < 1e-4:
            helper = (1.0, 0.0, 0.0) if abs(tangent[0]) < 0.9 else (0.0, 0.0, 1.0)
            side = vcross(tangent, helper)
        side = vnorm(side)
        raised = vnorm(vcross(side, tangent))
        out.append((raised, side, tangent))
    return out


def tail_centerline(extra=0.16, samples=7):
    points = list(TAIL_BONES)
    direction = vnorm(vsub(TAIL_BONES[-1], TAIL_BONES[-2]))
    for i in range(1, samples + 1):
        points.append(vadd(TAIL_BONES[-1], vmul(direction, extra * i / samples)))
    return points


def mane_weights(point):
    height = point[1]
    if height > 0.84:
        return [(HEAD, 1.0)]
    if height > 0.70:
        blend = (0.84 - height) / 0.14
        return [(HEAD, 1.0 - blend), (NECK, blend)]
    blend = clamp((0.70 - height) / 0.16)
    return [(NECK, 1.0 - blend), (CHEST, blend)]


def tail_weights(point):
    best = []
    for index, origin in enumerate(TAIL_BONES):
        best.append((vlen(vsub(point, origin)), index))
    best.sort()
    first = best[0][1]
    second = best[1][1]
    d0 = best[0][0] + 1e-4
    d1 = best[1][0] + 1e-4
    w0 = 1.0 / d0
    w1 = 1.0 / d1
    # The hanging tip, past the last bone, stays on that bone.
    if point[1] < TAIL_BONES[-1][1] - 0.02:
        return [(TAIL[5], 1.0)]
    total = w0 + w1
    return [(TAIL[first], w0 / total), (TAIL[second], w1 / total)]


class Shell:
    def __init__(self):
        self.parts = []

    def add_tube(self, points, radius, material, weight_fn, sides=16, up=(0.0, 1.0, 0.0), cap=True):
        if len(points) < 2:
            return
        radii = radius if isinstance(radius, list) else [radius] * len(points)
        if len(radii) != len(points):
            raise ValueError("radius list must match the path")
        basis = frames(points, up)
        rings = []
        normals = []
        for point, (raised, side, _tangent), rad in zip(points, basis, radii):
            rx, ry = rad if isinstance(rad, tuple) else (rad, rad)
            ring = []
            norms = []
            for s in range(sides):
                angle = s / sides * math.tau
                offset = vadd(vmul(raised, math.cos(angle) * rx), vmul(side, math.sin(angle) * ry))
                ring.append(vadd(point, offset))
                norms.append(vnorm(vadd(vmul(raised, math.cos(angle) / max(rx, 1e-4)), vmul(side, math.sin(angle) / max(ry, 1e-4)))))
            rings.append(ring)
            normals.append(norms)
        verts = []
        norms = []
        weights = []
        for ring, norms_ring, point in zip(rings, normals, points):
            influence = _pack(weight_fn(point))
            for vert, normal in zip(ring, norms_ring):
                verts.append(vert)
                norms.append(normal)
                weights.append(influence)
        indices = []
        for i in range(len(points) - 1):
            for s in range(sides):
                a = i * sides + s
                b = i * sides + (s + 1) % sides
                c = (i + 1) * sides + s
                d = (i + 1) * sides + (s + 1) % sides
                indices.extend((a, b, c, b, d, c))
        if cap:
            self._caps(verts, norms, weights, indices, rings, points, sides)
        self.parts.append({"verts": verts, "norms": norms, "weights": weights, "indices": indices, "material": material})

    def _caps(self, verts, norms, weights, indices, rings, points, sides):
        for end, ring, point, sign in (
            (0, rings[0], points[0], -1.0),
            (len(points) - 1, rings[-1], points[-1], 1.0),
        ):
            direction = vnorm(vsub(points[min(end + 1, len(points) - 1)], points[max(end - 1, 0)]))
            if end == 0:
                direction = vmul(direction, -1.0)
            center = len(verts)
            verts.append(point)
            norms.append(direction if sign > 0 or end == 0 else direction)
            weights.append(weights[end * sides])
            base = end * sides
            for s in range(sides):
                a = base + s
                b = base + (s + 1) % sides
                if end == 0:
                    indices.extend((center, a, b))
                else:
                    indices.extend((center, b, a))

    def add_ellipsoid(self, center, radii, material, weight_fn, stacks=10, slices=14, keep=None):
        verts = []
        norms = []
        weights = []
        grid = []
        for iy in range(stacks + 1):
            row = []
            v = iy / stacks
            theta = v * math.pi
            for ix in range(slices):
                u = ix / slices
                phi = u * math.tau
                normal = (
                    math.sin(theta) * math.cos(phi),
                    math.cos(theta),
                    math.sin(theta) * math.sin(phi),
                )
                point = (
                    center[0] + radii[0] * normal[0],
                    center[1] + radii[1] * normal[1],
                    center[2] + radii[2] * normal[2],
                )
                if keep is not None and not keep(point, normal):
                    row.append(None)
                    continue
                row.append(len(verts))
                verts.append(point)
                norms.append(vnorm((normal[0] / radii[0], normal[1] / radii[1], normal[2] / radii[2])))
                weights.append(_pack(weight_fn(point)))
            grid.append(row)
        indices = []
        for iy in range(stacks):
            for ix in range(slices):
                a = grid[iy][ix]
                b = grid[iy][(ix + 1) % slices]
                c = grid[iy + 1][ix]
                d = grid[iy + 1][(ix + 1) % slices]
                if None in (a, b, c, d):
                    continue
                indices.extend((a, b, c, b, d, c))
        if indices:
            self.parts.append({"verts": verts, "norms": norms, "weights": weights, "indices": indices, "material": material})

    def add_disc(self, center, axis, radius, thickness, material, weight_fn, wedge=0.7, sides=16):
        axis = vnorm(axis)
        helper = (0.0, 1.0, 0.0) if abs(axis[1]) < 0.85 else (1.0, 0.0, 0.0)
        side = vnorm(vcross(axis, helper))
        raised = vnorm(vcross(side, axis))
        path = [vadd(center, vmul(axis, -thickness)), vadd(center, vmul(axis, thickness))]
        # A notched disc: skip a wedge so it reads as a citrus slice.
        angles = []
        count = sides
        for s in range(count):
            angle = wedge / 2 + (math.tau - wedge) * s / (count - 1)
            angles.append(angle)
        rings = []
        for point in path:
            ring = [point]
            for angle in angles:
                ring.append(
                    vadd(
                        point,
                        vadd(vmul(raised, math.cos(angle) * radius), vmul(side, math.sin(angle) * radius)),
                    )
                )
            rings.append(ring)
        verts = []
        norms = []
        weights = []
        for ring in rings:
            for vert in ring:
                verts.append(vert)
                norms.append(axis)
                weights.append(_pack(weight_fn(vert)))
        span = len(rings[0])
        indices = []
        for s in range(1, span - 1):
            indices.extend((0, s, s + 1))
            indices.extend((span, span + s + 1, span + s))
        for s in range(1, span):
            a = s
            b = s + 1 if s + 1 < span else 1
            c = span + s
            d = span + (s + 1 if s + 1 < span else 1)
            indices.extend((a, b, c, b, d, c))
        # The two cut faces of the wedge.
        indices.extend((0, span - 1, span + span - 1, 0, span + span - 1, span))
        indices.extend((0, span + 1, 1, 0, span, span + 1))
        self.parts.append({"verts": verts, "norms": norms, "weights": weights, "indices": indices, "material": material})


def _pack(pairs):
    joints = [0, 0, 0, 0]
    weights = [0.0, 0.0, 0.0, 0.0]
    total = sum(weight for _, weight in pairs) or 1.0
    for i, (joint, weight) in enumerate(pairs[:4]):
        joints[i] = joint
        weights[i] = weight / total
    return joints, weights


def arc(points, steps=6):
    return catmull(points, steps)


def radius_ramp(count, start, mid, end):
    out = []
    for i in range(count):
        t = i / max(count - 1, 1)
        if t < 0.5:
            out.append(lerp(start, mid, t / 0.5))
        else:
            out.append(lerp(mid, end, (t - 0.5) / 0.5))
    return out


# --- styles -----------------------------------------------------------------

def crown(mane, material=0):
    # Fills the scalp between the ears. The face (far -Z) and the ear line stay clear.
    mane.add_ellipsoid(
        (0.0, 1.02, -0.20),
        (0.15, 0.08, 0.155),
        material,
        mane_weights,
        stacks=8,
        slices=16,
        keep=lambda point, normal: normal[1] > 0.05 and point[2] > -0.34,
    )


def soiree(shells):
    mane, tail = shells
    crown(mane)
    # Short cyan cap: bangs over the forehead, a side sweep to her right, a short nape.
    bangs = arc(
        [
            (0.13, 0.99, -0.30),
            (0.04, 1.02, -0.36),
            (-0.08, 1.01, -0.37),
            (-0.15, 0.97, -0.32),
        ]
    )
    mane.add_tube(bangs, 0.045, 0, mane_weights, up=(0.0, 0.0, -1.0))
    ridge = arc(
        [
            (0.0, 1.01, -0.34),
            (-0.02, 1.06, -0.24),
            (-0.01, 1.02, -0.14),
            (0.0, 0.94, -0.08),
        ]
    )
    mane.add_tube(ridge, 0.055, 0, mane_weights)
    sweep = arc(
        [
            (-0.02, 1.05, -0.26),
            (-0.12, 1.00, -0.24),
            (-0.16, 0.90, -0.28),
            (-0.14, 0.82, -0.30),
        ]
    )
    mane.add_tube(sweep, radius_ramp(len(sweep), 0.04, 0.055, 0.03), 0, mane_weights)
    other = arc(
        [
            (0.04, 1.04, -0.22),
            (0.12, 0.98, -0.22),
            (0.13, 0.90, -0.20),
        ]
    )
    mane.add_tube(other, 0.04, 0, mane_weights)
    nape = arc([(-0.08, 0.94, -0.10), (0.0, 0.92, -0.07), (0.08, 0.94, -0.10)])
    mane.add_tube(nape, 0.04, 0, mane_weights)
    line = catmull(tail_centerline(0.10, 5), 4)
    # A gentle hook at the end, the way her tail turns in.
    hook = arc(
        [
            line[-4],
            line[-1],
            vadd(line[-1], (-0.05, -0.06, 0.02)),
            vadd(line[-1], (-0.02, -0.10, -0.02)),
        ],
        3,
    )
    path = line[:-1] + hook
    tail.add_tube(path, radius_ramp(len(path), 0.028, 0.048, 0.018), 0, tail_weights)


def matinee(shells):
    mane, tail = shells
    crown(mane)
    bangs = arc(
        [
            (0.15, 1.00, -0.30),
            (0.02, 1.04, -0.38),
            (-0.10, 1.03, -0.38),
            (-0.16, 0.98, -0.32),
        ]
    )
    mane.add_tube(bangs, 0.05, 0, mane_weights, up=(0.0, 0.0, -1.0))
    puff = arc(
        [
            (0.02, 1.02, -0.32),
            (-0.04, 1.10, -0.22),
            (-0.06, 1.06, -0.12),
            (0.0, 0.96, -0.08),
        ]
    )
    mane.add_tube(puff, 0.07, 0, mane_weights)
    sweep = arc(
        [
            (-0.04, 1.08, -0.24),
            (-0.15, 1.02, -0.22),
            (-0.18, 0.90, -0.26),
            (-0.15, 0.80, -0.28),
        ]
    )
    mane.add_tube(sweep, radius_ramp(len(sweep), 0.045, 0.06, 0.035), 0, mane_weights)
    streak = arc(
        [
            (-0.06, 1.08, -0.20),
            (-0.14, 0.98, -0.20),
            (-0.16, 0.88, -0.24),
        ]
    )
    mane.add_tube(streak, 0.022, 1, mane_weights)
    other = arc([(0.06, 1.05, -0.20), (0.14, 0.98, -0.18), (0.14, 0.88, -0.16)])
    mane.add_tube(other, 0.042, 0, mane_weights)
    line = catmull(tail_centerline(0.12, 6), 4)
    split = int(len(line) * 0.62)
    tail.add_tube(line[: split + 1], radius_ramp(split + 1, 0.03, 0.05, 0.04), 0, tail_weights)
    tail.add_tube(line[split:], radius_ramp(len(line) - split, 0.04, 0.045, 0.02), 1, tail_weights)


def fair_flyer(shells):
    mane, tail = shells
    crown(mane)
    bangs = arc(
        [
            (0.14, 0.98, -0.32),
            (0.04, 1.01, -0.40),
            (-0.08, 1.00, -0.40),
            (-0.15, 0.96, -0.34),
        ],
        5,
    )
    mane.add_tube(bangs, (0.028, 0.055), 0, mane_weights, up=(0.0, 1.0, 0.0))
    band = arc(
        [
            (0.12, 1.02, -0.30),
            (0.0, 1.045, -0.36),
            (-0.12, 1.02, -0.30),
        ],
        4,
    )
    mane.add_tube(band, 0.012, 2, mane_weights)
    lock = arc(
        [
            (0.0, 1.04, -0.30),
            (-0.08, 1.02, -0.20),
            (-0.16, 0.88, -0.16),
            (-0.18, 0.72, -0.12),
            (-0.14, 0.58, -0.14),
            (-0.08, 0.50, -0.18),
            (-0.14, 0.46, -0.12),
        ],
        5,
    )
    split = int(len(lock) * 0.78)
    mane.add_tube(lock[: split + 1], radius_ramp(split + 1, 0.05, 0.065, 0.05), 0, mane_weights)
    mane.add_tube(lock[split:], radius_ramp(len(lock) - split, 0.05, 0.04, 0.025), 1, mane_weights)
    curl = arc(
        [
            (-0.10, 1.00, -0.18),
            (-0.16, 0.98, -0.14),
            (-0.12, 0.94, -0.12),
            (-0.16, 0.96, -0.18),
        ],
        3,
    )
    mane.add_tube(curl, 0.028, 0, mane_weights)
    line = []
    base = tail_centerline(0.02, 2)
    for i, point in enumerate(catmull(base, 5)):
        t = i / 28.0
        wave = math.sin(t * math.tau * 1.6) * 0.045
        line.append(vadd(point, (wave, 0.0, 0.0)))
    # Continue into the big end curl.
    tip = line[-1]
    curl_pts = [tip]
    for step in range(1, 16):
        angle = -math.pi * 0.15 + step / 15 * math.pi * 1.15
        curl_pts.append(
            (
                tip[0] + math.cos(angle) * 0.09,
                tip[1] + math.sin(angle) * 0.09 - 0.02,
                tip[2] + 0.01 * step / 15,
            )
        )
    path = line + curl_pts[1:]
    tail.add_tube(path, radius_ramp(len(path), 0.04, 0.085, 0.03), 0, tail_weights, sides=14)


def morning_mimosa(shells):
    mane, tail = shells
    crown(mane)
    bangs = arc(
        [
            (0.12, 0.98, -0.30),
            (0.0, 1.02, -0.38),
            (-0.12, 1.00, -0.36),
        ]
    )
    mane.add_tube(bangs, 0.048, 0, mane_weights, up=(0.0, 0.0, -1.0))
    ridge = arc(
        [
            (0.0, 1.01, -0.32),
            (0.02, 1.08, -0.22),
            (0.0, 1.02, -0.12),
            (-0.02, 0.94, -0.08),
        ]
    )
    mane.add_tube(ridge, 0.06, 0, mane_weights)
    cowlick = arc(
        [
            (0.02, 1.04, -0.22),
            (0.05, 1.12, -0.26),
            (0.08, 1.18, -0.30),
        ],
        4,
    )
    mane.add_tube(cowlick, radius_ramp(len(cowlick), 0.035, 0.028, 0.012), 0, mane_weights)
    left = arc(
        [
            (-0.04, 1.04, -0.24),
            (-0.14, 0.96, -0.26),
            (-0.16, 0.84, -0.28),
            (-0.12, 0.74, -0.24),
        ]
    )
    mane.add_tube(left, radius_ramp(len(left), 0.04, 0.05, 0.03), 0, mane_weights)
    right = arc([(0.06, 1.02, -0.22), (0.14, 0.94, -0.20), (0.13, 0.84, -0.18)])
    mane.add_tube(right, 0.04, 0, mane_weights)
    # Orange slice tucked by the ear. Part of the hair, so it rides the head.
    mane.add_disc((-0.15, 0.96, -0.30), (-0.2, 0.15, 1.0), 0.055, 0.01, 1, mane_weights)
    line = catmull(tail_centerline(0.08, 4), 5)
    frames_line = frames(line)
    for phase in (0.0, math.tau / 3.0, 2.0 * math.tau / 3.0):
        strand = []
        for i, (point, (raised, side, _tangent)) in enumerate(zip(line, frames_line)):
            t = i / max(len(line) - 1, 1)
            angle = phase + t * math.tau * 3.2
            orbit = 0.02 * (1.0 - 0.35 * t)
            strand.append(vadd(point, vadd(vmul(raised, math.cos(angle) * orbit), vmul(side, math.sin(angle) * orbit))))
        tail.add_tube(strand, radius_ramp(len(strand), 0.02, 0.024, 0.014), 0, tail_weights, sides=8)
    tail.add_ellipsoid(TAIL_BONES[1], (0.028, 0.028, 0.028), 1, tail_weights, stacks=6, slices=8)


def fun_raiser(shells):
    mane, tail = shells
    crown(mane)
    band = arc(
        [
            (0.11, 1.01, -0.30),
            (0.0, 1.04, -0.36),
            (-0.11, 1.01, -0.30),
        ],
        4,
    )
    mane.add_tube(band, 0.013, 2, mane_weights)
    swept = arc(
        [
            (0.0, 1.00, -0.34),
            (0.0, 1.08, -0.22),
            (0.02, 1.10, -0.08),
            (0.02, 1.02, 0.00),
        ]
    )
    mane.add_tube(swept, 0.04, 0, mane_weights)
    loop = []
    center = (0.0, 1.14, 0.02)
    for step in range(28):
        angle = step / 27 * math.tau * 0.92 - 0.2
        loop.append(
            (
                center[0] + math.sin(angle) * 0.035,
                center[1] + math.cos(angle) * 0.10,
                center[2] + math.sin(angle) * 0.09,
            )
        )
    mane.add_tube(loop, 0.055, 0, lambda _p: [(HEAD, 1.0)], sides=12)
    streak = []
    for step, point in enumerate(loop):
        streak.append(vadd(point, (0.03, 0.0, 0.0)))
    mane.add_tube(streak, 0.02, 1, lambda _p: [(HEAD, 1.0)], sides=8)
    tendril = []
    for step in range(18):
        t = step / 17
        angle = t * math.tau * 1.15
        tendril.append(
            (
                -0.12 - math.cos(angle) * 0.045,
                0.98 - t * 0.22,
                -0.26 + math.sin(angle) * 0.03,
            )
        )
    mane.add_tube(tendril, radius_ramp(len(tendril), 0.028, 0.024, 0.014), 0, mane_weights)
    line = catmull(tail_centerline(0.0, 1), 4)
    tip = line[-1]
    curl = list(line)
    for step in range(1, 22):
        angle = -math.pi * 0.5 + step / 21 * math.tau * 0.85
        curl.append(
            (
                tip[0] + math.cos(angle) * 0.13,
                tip[1] + (math.sin(angle) + 1.0) * 0.05,
                tip[2] + math.sin(angle) * 0.05,
            )
        )
    tail.add_tube(curl, radius_ramp(len(curl), 0.045, 0.09, 0.035), 0, tail_weights, sides=14)
    pale = [vadd(point, (0.035, 0.0, 0.0)) for point in curl]
    tail.add_tube(pale, 0.022, 1, tail_weights, sides=8)


STYLES = {
    "fair_flyer": (
        "FairFlyer",
        fair_flyer,
        {
            0: "F4E2A4",
            1: "C4846C",
            2: "3E86C8",
        },
    ),
    "soiree": ("Soiree", soiree, {0: "8FD8EA"}),
    "matinee": ("Matinee", matinee, {0: "A9E0F2", 1: "7B62B0"}),
    "morning_mimosa": ("MorningMimosa", morning_mimosa, {0: "2FBE58", 1: "F09A28"}),
    "fun_raiser": ("FunRaiser", fun_raiser, {0: "F5A03C", 1: "FFD7A6", 2: "2E9A62"}),
}


def load_donor():
    data = open(DONOR, "rb").read()
    length, kind = struct.unpack_from("<II", data, 12)
    js = json.loads(data[20 : 20 + length])
    blob = data[20 + length + 8 :]
    return js, blob


def copy_ibm(js, blob):
    skin = js["skins"][0]
    accessor = js["accessors"][skin["inverseBindMatrices"]]
    view = js["bufferViews"][accessor["bufferView"]]
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    count = accessor["count"] * 16 * 4
    return blob[start : start + count]


def build_one(prefix, populate, colors):
    mane = Shell()
    tail = Shell()
    populate((mane, tail))
    return pack(prefix, mane, tail, colors)


def pack(prefix, mane, tail, colors):
    donor, blob = load_donor()
    nodes = json.loads(json.dumps(donor["nodes"][:12]))
    nodes[0]["name"] = prefix + "HairRig"
    nodes[0]["children"] = [1, 12, 13]
    nodes.append({"name": prefix + "DevkitMane", "mesh": 0, "skin": 0})
    nodes.append({"name": prefix + "DevkitTail", "mesh": 1, "skin": 0})
    materials = []
    for index in sorted(colors):
        materials.append(
            {
                "name": "%sHair%d" % (prefix, index),
                "doubleSided": True,
                "pbrMetallicRoughness": {
                    "baseColorFactor": srgb(colors[index]),
                    "metallicFactor": 0.0,
                    "roughnessFactor": 0.85,
                },
            }
        )
    buffer = bytearray()
    views = []
    accessors = []
    meshes = []

    def align():
        while len(buffer) % 4:
            buffer.append(0)

    def add_bytes(raw, target):
        align()
        offset = len(buffer)
        buffer.extend(raw)
        views.append({"buffer": 0, "byteOffset": offset, "byteLength": len(raw), "target": target})
        return len(views) - 1

    def add_vec3(values):
        raw = b"".join(struct.pack("<fff", *value) for value in values)
        view = add_bytes(raw, 34962)
        mins = [min(v[i] for v in values) for i in range(3)]
        maxs = [max(v[i] for v in values) for i in range(3)]
        accessors.append(
            {
                "bufferView": view,
                "componentType": 5126,
                "count": len(values),
                "type": "VEC3",
                "min": mins,
                "max": maxs,
            }
        )
        return len(accessors) - 1

    def add_vec2(count):
        raw = b"\x00" * (count * 8)
        view = add_bytes(raw, 34962)
        accessors.append({"bufferView": view, "componentType": 5126, "count": count, "type": "VEC2"})
        return len(accessors) - 1

    def add_joints(values):
        raw = b"".join(struct.pack("<HHHH", *value) for value in values)
        view = add_bytes(raw, 34962)
        accessors.append({"bufferView": view, "componentType": 5123, "count": len(values), "type": "VEC4"})
        return len(accessors) - 1

    def add_weights(values):
        raw = b"".join(struct.pack("<ffff", *value) for value in values)
        view = add_bytes(raw, 34962)
        accessors.append({"bufferView": view, "componentType": 5126, "count": len(values), "type": "VEC4"})
        return len(accessors) - 1

    def add_indices(values):
        raw = b"".join(struct.pack("<I", value) for value in values)
        view = add_bytes(raw, 34963)
        accessors.append({"bufferView": view, "componentType": 5125, "count": len(values), "type": "SCALAR"})
        return len(accessors) - 1

    def mesh_of(shell, name):
        primitives = []
        grouped = {}
        for part in shell.parts:
            grouped.setdefault(part["material"], []).append(part)
        for material, parts in grouped.items():
            verts = []
            norms = []
            joints = []
            weights = []
            indices = []
            for part in parts:
                base = len(verts)
                verts.extend(part["verts"])
                norms.extend(part["norms"])
                for joint, weight in part["weights"]:
                    joints.append(joint)
                    weights.append(weight)
                indices.extend(index + base for index in part["indices"])
            primitives.append(
                {
                    "attributes": {
                        "POSITION": add_vec3(verts),
                        "NORMAL": add_vec3(norms),
                        "TEXCOORD_0": add_vec2(len(verts)),
                        "JOINTS_0": add_joints(joints),
                        "WEIGHTS_0": add_weights(weights),
                    },
                    "indices": add_indices(indices),
                    "material": material,
                }
            )
        meshes.append({"name": name, "primitives": primitives})

    mesh_of(mane, prefix + "DevkitMane")
    mesh_of(tail, prefix + "DevkitTail")
    align()
    ibm = copy_ibm(donor, blob)
    ibm_view = add_bytes(ibm, None)
    views[-1].pop("target", None)
    accessors.append(
        {
            "bufferView": ibm_view,
            "componentType": 5126,
            "count": 11,
            "type": "MAT4",
        }
    )
    skin = {
        "inverseBindMatrices": len(accessors) - 1,
        "joints": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        "skeleton": 0,
        "name": prefix + "Hair",
    }
    gltf = {
        "asset": {"version": "2.0", "generator": "tools/mare_fair/build_hair.py"},
        "scene": 0,
        "scenes": [{"nodes": [0], "name": prefix}],
        "nodes": nodes,
        "meshes": meshes,
        "skins": [skin],
        "materials": materials,
        "accessors": accessors,
        "bufferViews": views,
        "buffers": [{"byteLength": len(buffer)}],
    }
    text = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    while len(text) % 4:
        text += b" "
    out = bytearray()
    out += struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(text) + 8 + len(buffer))
    out += struct.pack("<II", len(text), 0x4E4F534A)
    out += text
    out += struct.pack("<II", len(buffer), 0x004E4942)
    out += buffer
    # Fix the total length now that we know it.
    struct.pack_into("<I", out, 8, len(out))
    return bytes(out)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for pony_id, (prefix, populate, colors) in STYLES.items():
        data = build_one(prefix, populate, colors)
        path = os.path.join(OUT_DIR, pony_id + ".glb")
        open(path, "wb").write(data)
        print(pony_id, len(data))


if __name__ == "__main__":
    main()
