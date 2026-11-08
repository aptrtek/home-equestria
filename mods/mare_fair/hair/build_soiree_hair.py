#!/usr/bin/env python3
"""Solid mane and tail for Soiree, rebuilt in place on the rig already in soiree.glb.

Needs numpy. Run it from anywhere:

    python mods/mare_fair/hair/build_soiree_hair.py [--preview DIR]

--preview also needs Pillow and writes side, front, rear and top renders.

The shapes follow the official art (marefair.org/mascots and the 2025 site clips): a
swept fringe over a cap, falls down both sides of the neck that curl forward at the
chest, and a short crescent tail. That art has no standing side view, so the profile
is modelled from it, not traced. The pictures are not shipped.

Every lock is a closed loft, so the hair has real thickness from any angle.
Rig space: +Y up, -Z toward the face, -X her right.
"""

import argparse
import json
import os
import struct

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
GLB = os.path.join(HERE, "soiree.glb")

# Skin joint order in the rig.
PELVIS, CHEST, NECK, HEAD = 1, 2, 3, 4

SCALP_CENTER = np.array((0.0, 0.98, -0.20))


def unit(v):
    length = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.maximum(length, 1e-9)


def spline(keys, steps):
    """Catmull-Rom through keys. Returns the points and each point's key position."""
    keys = np.asarray(keys, float)
    padded = np.vstack((keys[0], keys, keys[-1]))
    points, where = [], []
    for span in range(len(keys) - 1):
        p0, p1, p2, p3 = padded[span : span + 4]
        for s in range(steps + (span == len(keys) - 2)):
            t = s / steps
            points.append(
                0.5
                * (
                    2 * p1
                    + (p2 - p0) * t
                    + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                    + (3 * p1 - p0 - 3 * p2 + p3) * t * t * t
                )
            )
            where.append(span + t)
    return np.array(points), np.array(where)


def loft(keys, widths, thicks, out, steps=8, sides=16):
    """A closed lens-section lock. `out(point)` is the way the flat of the lock faces."""
    center, where = spline(keys, steps)
    index = np.arange(len(keys))
    width = np.interp(where, index, widths)
    thick = np.interp(where, index, thicks)
    tangent = unit(np.gradient(center, axis=0))
    normal = np.array([out(p) for p in center], float)
    normal = unit(normal - tangent * np.sum(normal * tangent, axis=1, keepdims=True))
    across = np.cross(tangent, normal)
    angle = np.arange(sides) * 2 * np.pi / sides
    rings = (
        center[:, None, :]
        + across[:, None, :] * (width[:, None] * np.cos(angle))[:, :, None]
        + normal[:, None, :] * (thick[:, None] * np.sin(angle))[:, :, None]
    )
    verts = np.vstack((rings.reshape(-1, 3), center[0], center[-1]))
    count = len(center)
    start, end = count * sides, count * sides + 1
    faces = []
    for i in range(count - 1):
        for s in range(sides):
            a, b = i * sides + s, i * sides + (s + 1) % sides
            c, d = a + sides, b + sides
            faces += [(a, c, b), (b, c, d)]
    for s in range(sides):
        faces.append((start, s, (s + 1) % sides))
        last = (count - 1) * sides
        faces.append((end, last + (s + 1) % sides, last + s))
    faces = np.array(faces)
    a, b, c = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
    if np.sum(np.einsum("ij,ij->i", a, np.cross(b, c))) < 0:
        faces = faces[:, ::-1]
    return verts, faces


def radial(point):
    return point - SCALP_CENTER


def fall_out(side):
    def out(point):
        blend = np.clip((point[1] - 0.82) / 0.15, 0.0, 1.0)
        return unit(radial(point)) * blend + np.array((side, 0.0, 0.0)) * (1.0 - blend)

    return out


def tail_out(_point):
    return (1.0, 0.0, 0.0)


def mane():
    locks = []
    # The cap: a closed dome that sits on the skull, its underside inside the head.
    heights = np.linspace(-0.995, 0.995, 15)
    dome_keys = [(0.0, 0.995 + 0.108 * h, -0.225) for h in heights]
    rim = np.sqrt(1.0 - heights * heights)
    locks.append(loft(dome_keys, 0.168 * rim, 0.15 * rim, lambda _p: (0.0, 0.0, 1.0), steps=3, sides=32))
    # The fringe sweeps from a part on her left across the forehead to her right,
    # its overlapping ends stopping just above the eye.
    part = np.array((0.05, 1.085, -0.21))
    for tip in [(0.085, 1.035, -0.355), (0.05, 1.025, -0.378), (-0.03, 1.015, -0.39), (-0.11, 1.0, -0.365), (-0.168, 0.975, -0.30)]:
        tip = np.array(tip)
        mid = (part + tip) / 2 + unit(radial((part + tip) / 2)) * 0.025
        near = tip + np.array((0.04, 0.02, 0.012))
        locks.append(loft([part, mid, near, tip], [0.04, 0.09, 0.08, 0.03], [0.016, 0.03, 0.022, 0.008], radial))
    # Back of the head: overlapping locks that tuck into the crest.
    for tip in [(0.13, 0.93, -0.13), (0.065, 0.895, -0.092), (0.0, 0.885, -0.085), (-0.065, 0.895, -0.092), (-0.13, 0.93, -0.13)]:
        tip = np.array(tip)
        start = np.array((tip[0] * 0.3, 1.08, -0.18))
        mid = (start + tip) / 2 + unit(radial((start + tip) / 2)) * 0.03
        locks.append(loft([start, mid, tip], [0.04, 0.08, 0.05], [0.015, 0.028, 0.012], radial))
    # The crest closes the back of the neck between the falls and ends on the withers.
    locks.append(
        loft(
            [(0, 0.985, -0.085), (0, 0.89, -0.088), (0, 0.81, -0.115), (0, 0.765, -0.085), (0, 0.755, -0.04)],
            [0.11, 0.125, 0.112, 0.07, 0.004],
            [0.02, 0.03, 0.03, 0.02, 0.004],
            lambda _p: (0.0, 0.35, 1.0),
            steps=10,
            sides=20,
        )
    )
    # Two flicks at the crown, as in the drawings.
    for x, reach in ((0.015, 0.0), (-0.035, -0.03)):
        locks.append(
            loft(
                [(x, 1.085, -0.16), (x * 1.5, 1.11, -0.09 + reach), (x * 2.0, 1.105, -0.015 + reach)],
                [0.03, 0.03, 0.001],
                [0.012, 0.012, 0.002],
                radial,
                steps=6,
                sides=12,
            )
        )
    # The falls: over the head, down the neck, forward and up in a curl at the chest.
    for side in (-1.0, 1.0):
        keys = [(side * x, y, z) for x, y, z in (
            (0.10, 1.05, -0.17),
            (0.155, 0.985, -0.14),
            (0.14, 0.89, -0.115),
            (0.105, 0.79, -0.12),
            (0.095, 0.70, -0.16),
            (0.092, 0.65, -0.205),
            (0.088, 0.645, -0.25),
            (0.08, 0.675, -0.265),
        )]
        locks.append(
            loft(
                keys,
                [0.03, 0.05, 0.052, 0.046, 0.04, 0.034, 0.02, 0.002],
                [0.016, 0.024, 0.024, 0.022, 0.02, 0.016, 0.01, 0.003],
                fall_out(side),
                steps=10,
            )
        )
    return locks


def tail():
    # A crescent: out from the dock, round the back, the point coming forward at the stifle.
    main = loft(
        [(0, 0.645, 0.165), (0, 0.675, 0.245), (0, 0.635, 0.335), (0, 0.545, 0.39), (0, 0.45, 0.385), (0, 0.385, 0.325), (0, 0.365, 0.255)],
        [0.022, 0.05, 0.072, 0.082, 0.066, 0.034, 0.002],
        [0.022, 0.034, 0.042, 0.044, 0.034, 0.016, 0.003],
        tail_out,
        steps=10,
        sides=20,
    )
    # A small inner flick on the concave edge, as in the portrait.
    flick = loft(
        [(0, 0.60, 0.30), (0, 0.53, 0.325), (0, 0.475, 0.30)],
        [0.018, 0.024, 0.001],
        [0.018, 0.022, 0.002],
        tail_out,
        steps=8,
        sides=12,
    )
    return [main, flick]


def mane_weight(y):
    """Head above the jaw, then neck, then chest, blended so the fall bends smoothly."""
    if y > 0.84:
        return [(HEAD, 1.0)]
    if y > 0.70:
        blend = (0.84 - y) / 0.14
        return [(HEAD, 1.0 - blend), (NECK, blend)]
    blend = min(1.0, (0.70 - y) / 0.16)
    return [(NECK, 1.0 - blend), (CHEST, blend)]


def tail_weight(_y):
    # On the pelvis, as before: the rest tail chain reaches far past this crescent.
    return [(PELVIS, 1.0)]


def merge(locks, weight):
    verts, normals, faces, base = [], [], [], 0
    for v, f in locks:
        face_normal = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
        n = np.zeros_like(v)
        for corner in range(3):
            np.add.at(n, f[:, corner], face_normal)
        verts.append(v)
        normals.append(unit(n))
        faces.append(f + base)
        base += len(v)
    verts = np.vstack(verts)
    joints = np.zeros((len(verts), 4), np.uint16)
    weights = np.zeros((len(verts), 4), np.float32)
    for i, y in enumerate(verts[:, 1]):
        for slot, (joint, amount) in enumerate(weight(float(y))):
            joints[i, slot] = joint
            weights[i, slot] = amount
    return verts.astype(np.float32), np.vstack(normals).astype(np.float32), joints, weights, np.vstack(faces).astype(np.uint32)


def read_glb(path):
    data = open(path, "rb").read()
    length = struct.unpack_from("<I", data, 12)[0]
    return json.loads(data[20 : 20 + length]), data[20 + length + 8 :]


def write(path, rig, blob, parts):
    skin = rig["skins"][0]
    accessor = rig["accessors"][skin["inverseBindMatrices"]]
    view = rig["bufferViews"][accessor["bufferView"]]
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    ibm = blob[start : start + accessor["count"] * 64]
    buffer, views, accessors = bytearray(), [], []

    def add(array, kind, component, target, bounds=False):
        while len(buffer) % 4:
            buffer.append(0)
        raw = array.tobytes()
        entry = {"buffer": 0, "byteOffset": len(buffer), "byteLength": len(raw)}
        if target:
            entry["target"] = target
        buffer.extend(raw)
        views.append(entry)
        item = {"bufferView": len(views) - 1, "componentType": component, "count": len(array), "type": kind}
        if bounds:
            item["min"] = [float(x) for x in array.min(0)]
            item["max"] = [float(x) for x in array.max(0)]
        accessors.append(item)
        return len(accessors) - 1

    meshes = []
    for name, (verts, normals, joints, weights, faces) in parts:
        attributes = {
            "POSITION": add(verts, "VEC3", 5126, 34962, True),
            "NORMAL": add(normals, "VEC3", 5126, 34962),
            "TEXCOORD_0": add(np.zeros((len(verts), 2), np.float32), "VEC2", 5126, 34962),
            "JOINTS_0": add(joints, "VEC4", 5123, 34962),
            "WEIGHTS_0": add(weights, "VEC4", 5126, 34962),
        }
        indices = add(faces.reshape(-1), "SCALAR", 5125, 34963)
        meshes.append({"name": name, "primitives": [{"attributes": attributes, "indices": indices, "material": 0}]})
    skin["inverseBindMatrices"] = add(np.frombuffer(ibm, np.float32).reshape(-1, 16), "MAT4", 5126, None)
    rig["asset"]["generator"] = "mods/mare_fair/hair/build_soiree_hair.py"
    rig.update(meshes=meshes, accessors=accessors, bufferViews=views, buffers=[{"byteLength": len(buffer)}])
    text = json.dumps(rig, separators=(",", ":")).encode()
    text += b" " * (-len(text) % 4)
    buffer.extend(b"\0" * (-len(buffer) % 4))
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, 28 + len(text) + len(buffer)))
        f.write(struct.pack("<II", len(text), 0x4E4F534A) + text)
        f.write(struct.pack("<II", len(buffer), 0x004E4942) + bytes(buffer))


def check_closed(locks):
    for v, f in locks:
        edges = np.sort(np.vstack((f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]])), axis=1)
        _, counts = np.unique(edges, axis=0, return_counts=True)
        if not np.all(counts == 2):
            raise SystemExit("a lock is not closed")


def preview(parts, directory):
    from PIL import Image

    os.makedirs(directory, exist_ok=True)
    views = {
        "side": ((0, 0, 1), (0, 1, 0), (-1, 0, 0)),
        "other_side": ((0, 0, -1), (0, 1, 0), (1, 0, 0)),
        "front": ((1, 0, 0), (0, 1, 0), (0, 0, -1)),
        "rear": ((-1, 0, 0), (0, 1, 0), (0, 0, 1)),
    }
    verts = np.vstack([p[1][0] for p in parts])
    faces, base = [], 0
    for _, (v, _n, _j, _w, f) in parts:
        faces.append(f.astype(np.int64) + base)
        base += len(v)
    faces = np.vstack(faces)
    size, scale = 760, 720.0
    light = unit(np.array((-0.4, 0.6, -0.7)))
    for name, (right, up, toward) in views.items():
        right, up, toward = np.array(right, float), np.array(up, float), np.array(toward, float)
        px = np.stack(
            (size / 2 + (verts @ right - 0.0) * scale * 0.82, size - 30 - (verts @ up - 0.3) * scale * 0.82, verts @ toward), axis=1
        )
        depth = np.full((size, size), -1e9)
        image = np.full((size, size, 3), 235, np.uint8)
        for tri in faces:
            a, b, c = px[tri]
            area = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            if abs(area) < 1e-6:
                continue
            x0, x1 = int(max(min(a[0], b[0], c[0]), 0)), int(min(max(a[0], b[0], c[0]) + 1, size - 1))
            y0, y1 = int(max(min(a[1], b[1], c[1]), 0)), int(min(max(a[1], b[1], c[1]) + 1, size - 1))
            if x1 < x0 or y1 < y0:
                continue
            xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
            w0 = ((b[0] - xs) * (c[1] - ys) - (b[1] - ys) * (c[0] - xs)) / area
            w1 = ((c[0] - xs) * (a[1] - ys) - (c[1] - ys) * (a[0] - xs)) / area
            w2 = 1 - w0 - w1
            mask = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
            z = w0 * a[2] + w1 * b[2] + w2 * c[2]
            hit = mask & (z > depth[ys, xs])
            if hit.any():
                n = unit(np.cross(verts[tri[1]] - verts[tri[0]], verts[tri[2]] - verts[tri[0]]))
                tone = 0.62 + 0.38 * abs(float(n @ light))
                depth[ys[hit], xs[hit]] = z[hit]
                image[ys[hit], xs[hit]] = (np.array((143, 216, 234)) * tone).astype(np.uint8)
        Image.fromarray(image).save(os.path.join(directory, "soiree_%s.png" % name))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview")
    args = parser.parse_args()
    rig, blob = read_glb(GLB)
    mane_locks, tail_locks = mane(), tail()
    check_closed(mane_locks + tail_locks)
    parts = [
        ("SoireeDevkitMane", merge(mane_locks, mane_weight)),
        ("SoireeDevkitTail", merge(tail_locks, tail_weight)),
    ]
    write(GLB, rig, blob, parts)
    for name, (verts, _n, _j, _w, faces) in parts:
        print(name, "verts", len(verts), "tris", len(faces), "min", verts.min(0).round(3), "max", verts.max(0).round(3))
    print("bytes", os.path.getsize(GLB))
    if args.preview:
        preview(parts, args.preview)


if __name__ == "__main__":
    main()
