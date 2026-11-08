#!/usr/bin/env python3
"""Solid mane and tail for Soiree, rebuilt in place on the rig already in soiree.glb.

Needs numpy. Run it from anywhere:

    python mods/mare_fair/hair/build_soiree_hair.py [--preview DIR]

--preview also needs Pillow and writes side, front, rear and top renders.

The shapes follow the official art (marefair.org/mascots and the 2025 site clips): a
rounded bob whose edge is the fringe, a comma curl at each jaw, two swept flicks at the
crown, and a short crescent tail. That art has no standing side view, so the profile
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


def helmet_fringe(side=1.0, drop=0.032):
    """One smooth fringe lying close on the forehead, sloping down toward one side.

    side 1 sweeps down to her right, -1 to her left. drop is how far the edge falls.
    """
    angles = np.radians(np.linspace(-62.0, 72.0, 9))
    arc = [(-side * 0.178 * np.sin(a), 1.052 - drop * np.sin(a), -0.215 - 0.168 * np.cos(a)) for a in angles]
    return loft(arc, [0.012, 0.05, 0.062, 0.066, 0.066, 0.064, 0.058, 0.04, 0.004], [0.005, 0.012, 0.016, 0.018, 0.018, 0.018, 0.016, 0.012, 0.003], radial, steps=8, sides=20)


def bob_shell(columns=144, rows=24):
    """One closed rounded bob. Its lower edge is the fringe: level across the forehead,
    overhanging it a little, rounding down at the corners by the eyes, and carrying on
    down the back of the head to a rounded hem at the nape."""
    top, center_z, radius_x, radius_z = 1.128, -0.225, 0.19, 0.188
    verts = []
    for row in range(rows):
        f = (row / rows) ** 1.25
        for column in range(columns):
            theta = column * 2.0 * np.pi / columns
            turned = abs(np.arctan2(np.sin(theta), np.cos(theta)))
            degrees = np.degrees(turned)
            # Level across the forehead, down to a crisp corner by each eye, then cut back up.
            down = np.clip((degrees - 38.0) / 24.0, 0.0, 1.0)
            down = down * down * (3.0 - 2.0 * down)
            back_up = np.clip((degrees - 62.0) / 14.0, 0.0, 1.0)
            dome_edge = 1.012 - 0.036 * down + 0.02 * back_up
            # One slit in the fringe on her right, as in the portrait.
            signed = np.degrees(np.arctan2(np.sin(theta), np.cos(theta)))
            dome_edge += 0.03 * np.exp(-(((signed + 25.0) / 3.0) ** 2))
            # Behind the ears the shell carries on down to one rounded hem.
            nape = np.clip((degrees - 102.0) / 48.0, 0.0, 1.0)
            nape = nape * nape * (3.0 - 2.0 * nape)
            hem = 0.825 + 0.05 * ((180.0 - degrees) / 80.0) ** 2
            edge = dome_edge + (hem - dome_edge) * nape
            y = edge + (top - edge) * f
            height = np.clip((y - dome_edge) / (top - dome_edge), 0.0, 1.0)
            shape = np.sqrt(max(1.0 - height * height, 0.0)) * (0.955 if row == 0 else 1.0)
            below = np.clip((1.0 - y) / 0.17, 0.0, 1.0)
            # The rounded edge of the hem tucks in toward the neck.
            tuck = np.clip((edge + 0.05 - y) / 0.05, 0.0, 1.0) * nape
            tuck_x, tuck_z = 1.0 - 0.1 * tuck * tuck, 1.0 - 0.08 * tuck * tuck
            # The lower back is squarer in plan, so the sides flow into it without a seam.
            power = 1.0 - 0.4 * nape * np.clip((1.05 - y) / 0.1, 0.0, 1.0)
            sine, cosine = np.sin(theta), np.cos(theta)
            sine = np.sign(sine) * abs(sine) ** power
            cosine = np.sign(cosine) * abs(cosine) ** power
            depth = radius_z if cosine >= 0.0 else 0.165
            # The corner of the fringe stands a little proud of the face.
            proud = 1.0 + 0.04 * np.exp(-(((degrees - 62.0) / 10.0) ** 2)) * (1.0 - f) ** 3
            x = radius_x * sine * shape * (1.0 - 0.06 * below * below) * tuck_x * proud
            z = center_z - depth * cosine * shape * (1.0 - 0.15 * below * below) * tuck_z * proud
            verts.append((x, y, z))
    apex, base = rows * columns, rows * columns + 1
    verts += [(0.0, top, center_z), (0.0, 0.99, center_z)]
    faces = []
    for row in range(rows - 1):
        for column in range(columns):
            a, b = row * columns + column, row * columns + (column + 1) % columns
            c, d = a + columns, b + columns
            faces += [(a, c, b), (b, c, d)]
    for column in range(columns):
        a, b = column, (column + 1) % columns
        faces.append((base, a, b))
        last = (rows - 1) * columns
        faces.append((apex, last + b, last + a))
    verts, faces = np.array(verts, float), np.array(faces)
    a, b, c = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
    if np.sum(np.einsum("ij,ij->i", a - verts.mean(0), np.cross(b - verts.mean(0), c - verts.mean(0)))) < 0:
        faces = faces[:, ::-1]
    return verts, faces


SIDE_CURL = ((0.12, 1.0, -0.15), (0.128, 0.94, -0.13), (0.13, 0.89, -0.142), (0.132, 0.858, -0.18), (0.136, 0.845, -0.235), (0.134, 0.86, -0.278), (0.13, 0.925, -0.272))


def mane_accents():
    """A periwinkle underside peeking below each curl, as in the portraits."""
    locks = []
    for side in (-1.0, 1.0):
        keys = [(side * (x - 0.012), y - 0.01, z) for x, y, z in SIDE_CURL[2:]]
        locks.append(loft(keys, [0.04, 0.04, 0.03, 0.016, 0.002], [0.012, 0.012, 0.01, 0.006, 0.002], fall_out(side), steps=10, sides=14))
    return locks


def mane():
    locks = []
    # The cap: a closed dome that sits on the skull, its underside inside the head.
    heights = np.linspace(-0.995, 0.995, 15)
    dome_keys = [(0.0, 0.995 + 0.128 * h, -0.225) for h in heights]
    rim = np.sqrt(1.0 - heights * heights)
    locks.append(loft(dome_keys, 0.172 * rim, 0.148 * rim, lambda _p: (0.0, 0.0, 1.0), steps=3, sides=32))
    locks.append(bob_shell())
    # A slim lock falls in front of each ear from under the bob.
    for side in (-1.0, 1.0):
        keys = [(side * x, y, z) for x, y, z in ((0.1, 1.1, -0.2), (0.176, 1.03, -0.235), (0.188, 0.97, -0.245), (0.178, 0.925, -0.262))]
        locks.append(loft(keys, [0.012, 0.02, 0.016, 0.002], [0.01, 0.014, 0.011, 0.002], fall_out(side), steps=8, sides=14))
    # Two flicks at the crown, as in the drawings.
    for keys, width in (
        (((0.03, 1.075, -0.095), (0.024, 1.122, -0.16), (0.008, 1.132, -0.235), (-0.034, 1.13, -0.31)), 0.03),
        (((-0.05, 1.07, -0.1), (-0.06, 1.112, -0.155), (-0.08, 1.119, -0.215), (-0.108, 1.107, -0.275)), 0.026),
    ):
        locks.append(loft(keys, [0.004, width, width * 0.6, 0.001], [0.003, 0.009, 0.007, 0.002], radial, steps=10, sides=12))
    for side in (-1.0, 1.0):
        # The thick rounded C of hair behind the ear, curling forward under the jaw.
        keys = [(side * x, y, z) for x, y, z in SIDE_CURL]
        locks.append(
            loft(
                keys,
                [0.05, 0.06, 0.058, 0.048, 0.034, 0.016, 0.001],
                [0.018, 0.018, 0.018, 0.02, 0.018, 0.011, 0.002],
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
    # A small periwinkle flick on the concave edge, as in the portrait.
    flick = loft(
        [(0, 0.60, 0.285), (0, 0.53, 0.30), (0, 0.46, 0.27)],
        [0.024, 0.036, 0.001],
        [0.02, 0.03, 0.002],
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
    mane_locks, tail_locks, accents = mane(), tail(), mane_accents()
    check_closed(mane_locks + tail_locks + accents)
    parts = [
        ("SoireeDevkitMane", merge(mane_locks, mane_weight)),
        ("SoireeDevkitTail", merge(tail_locks, tail_weight)),
    ]
    # Imported here because the shared multi-material writer imports this module.
    from build_fair_flyer_hair import linear
    from build_fair_flyer_hair import write as write_groups

    if len(rig["materials"]) == 1:
        rig["materials"].append(json.loads(json.dumps(rig["materials"][0])) | {"name": "SoireeHair1"})
    rig["materials"][1]["pbrMetallicRoughness"]["baseColorFactor"] = linear("8E9CE0")
    write_groups(
        GLB,
        rig,
        blob,
        [
            ("SoireeDevkitMane", {0: merge(mane_locks, mane_weight), 1: merge(accents, mane_weight)}),
            ("SoireeDevkitTail", {0: merge(tail_locks[:1], tail_weight), 1: merge(tail_locks[1:], tail_weight)}),
        ],
    )
    for name, (verts, _n, _j, _w, faces) in parts:
        print(name, "verts", len(verts), "tris", len(faces), "min", verts.min(0).round(3), "max", verts.max(0).round(3))
    print("bytes", os.path.getsize(GLB))
    if args.preview:
        preview(parts, args.preview)


if __name__ == "__main__":
    main()
