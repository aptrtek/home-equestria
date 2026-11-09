#!/usr/bin/env python3
"""Solid mane and tail for Fair Flyer, rebuilt in place on the rig already in fair_flyer.glb.

Needs numpy. Run it from anywhere:

    python mods/mare_fair/hair/build_fair_flyer_hair.py

Modelled from the official art (marefair.org/mascots and the 2025 site clips): a soft
swept blonde fringe, a blue headband, a small braid behind the ear, wavy locks down
the chest with a dusky underside, and a large scalloped tail. The art has no standing
side view, so the profile is modelled from it, not traced. The pictures are not shipped.

Rig space: +Y up, -Z toward the face, -X her right. The materials already in the file
are 0 pale blonde, 1 dusky, 2 band, 3 darker blonde (added here for the two-tone hair).
"""

import json
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from build_soiree_hair import check_closed, fall_out, helmet_fringe, loft, mane_weight, merge, radial, read_glb, tail_out, tail_weight, unit  # noqa: E402

GLB = os.path.join(HERE, "fair_flyer.glb")
BLONDE, DUSKY, BAND, DARK, HAT, UNDER, PETAL, SEED = 0, 1, 2, 3, 4, 5, 6, 7
COLORS = {BLONDE: "FAEDB4", DUSKY: "E8AC9C", DARK: "EFD690", HAT: "FFF9E6", UNDER: "E3A8DC", PETAL: "F6C431", SEED: "6B4423"}


def linear(hex_color):
    """glTF base colours are linear."""
    channels = [int(hex_color[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels] + [1.0]


def mane():
    blonde, dusky, band, dark = [], [], [], []
    # The cap sits on the skull, its underside inside the head.
    heights = np.linspace(-0.995, 0.995, 15)
    rim = np.sqrt(1.0 - heights * heights)
    keys = [(0.0, 0.995 + 0.108 * h, -0.225) for h in heights]
    dark.append(loft(keys, 0.168 * rim, 0.15 * rim, lambda _p: (0.0, 0.0, 1.0), steps=3, sides=32))
    # A broad backing under the fringe, so no scalp shows between its locks.
    blonde.append(loft([(0.03, 1.1, -0.21), (0.0, 1.085, -0.30), (-0.02, 1.035, -0.365)], [0.12, 0.16, 0.13], [0.012, 0.018, 0.01], radial, sides=24))
    # A smooth pale crown covers the roots where the locks meet at the part.
    blonde.append(loft([(0.0, 0.995 + 0.128 * h, -0.235) for h in heights], 0.172 * rim, 0.15 * rim, lambda _p: (0.0, 0.0, 1.0), steps=3, sides=32))
    # One soft swept fringe, stopping above the eye.
    blonde.append(helmet_fringe())
    # Back of the head, tucking into the crest.
    for tip in [(0.13, 0.93, -0.13), (0.065, 0.895, -0.092), (0.0, 0.885, -0.085), (-0.065, 0.895, -0.092), (-0.13, 0.93, -0.13)]:
        tip = np.array(tip)
        start = np.array((tip[0] * 0.3, 1.08, -0.18))
        mid = (start + tip) / 2 + unit(radial((start + tip) / 2)) * 0.03
        dark.append(loft([start, mid, tip], [0.04, 0.08, 0.05], [0.015, 0.028, 0.012], radial))
    # Crest down the back of the neck, ending on the withers.
    dark.append(
        loft(
            [(0, 0.985, -0.085), (0, 0.89, -0.088), (0, 0.81, -0.115), (0, 0.765, -0.085), (0, 0.755, -0.04)],
            [0.11, 0.125, 0.112, 0.07, 0.004],
            [0.02, 0.03, 0.03, 0.02, 0.004],
            lambda _p: (0.0, 0.35, 1.0),
            steps=10,
            sides=20,
        )
    )
    # Wavy locks down each side of the neck to the chest.
    path = (
        (0.10, 1.05, -0.17),
        (0.155, 0.985, -0.14),
        (0.14, 0.89, -0.125),
        (0.108, 0.80, -0.145),
        (0.10, 0.735, -0.185),
        (0.10, 0.675, -0.17),
        (0.096, 0.625, -0.215),
        (0.092, 0.575, -0.195),
        (0.09, 0.54, -0.245),
    )
    widths = [0.05, 0.062, 0.064, 0.058, 0.064, 0.05, 0.05, 0.03, 0.003]
    thicks = [0.016, 0.024, 0.024, 0.022, 0.024, 0.02, 0.018, 0.012, 0.003]
    for side in (-1.0, 1.0):
        keys = [(side * x, y, z) for x, y, z in path]
        dark.append(loft(keys, widths, thicks, fall_out(side), steps=10))
        # The pale centre stands just proud of the darker edges on both faces.
        blonde.append(loft(keys, np.array(widths) * 0.6, np.array(thicks) * 1.12, fall_out(side), steps=10))
    # A soft blush at the tip of the lock on her right, as in the art.
    tip = ((0.104, 0.72, -0.17), (0.104, 0.67, -0.185), (0.104, 0.625, -0.225), (0.10, 0.585, -0.205), (0.097, 0.54, -0.255))
    dusky.append(loft([(-x, y, z) for x, y, z in tip], [0.02, 0.03, 0.036, 0.028, 0.003], [0.012, 0.018, 0.02, 0.016, 0.003], fall_out(-1.0), steps=10))
    # A small braid behind her left ear: a chain of beads along one lock.
    bead_keys, bead_w = [], []
    for i in range(17):
        t = i / 16.0
        bead_keys.append((0.175 + 0.02 * t, 1.085 - 0.125 * t, -0.20 + 0.05 * t))
        bead_w.append(0.009 + 0.008 * abs(np.cos(t * np.pi * 4.0)))
    bead_w = np.array(bead_w)
    blonde.append(loft(bead_keys, bead_w, bead_w * 0.85, lambda _p: (1.0, 0.0, 0.0), steps=3, sides=12))
    # The headband lies on the hair over the crown; the hat is a separate piece she can take off.
    angles = np.radians(np.linspace(-62.0, 62.0, 13))
    arch = [(0.188 * np.sin(a), 1.0 + 0.139 * np.cos(a), -0.235) for a in angles]
    band.append(loft(arch, [0.013] * 13, [0.006] * 13, lambda p: (p[0], p[1] - 0.995, 0.0), steps=3, sides=10))
    return {BLONDE: blonde, DUSKY: dusky, BAND: band, DARK: dark}


def write_accessory(path, groups, colors):
    """A plain static model for the wardrobe: rig-space vertices, one primitive per colour."""
    buffer, views, accessors, primitives, materials = bytearray(), [], [], [], []

    def add(array, kind, component, target, bounds=False):
        while len(buffer) % 4:
            buffer.append(0)
        raw = array.tobytes()
        views.append({"buffer": 0, "byteOffset": len(buffer), "byteLength": len(raw), "target": target})
        buffer.extend(raw)
        item = {"bufferView": len(views) - 1, "componentType": component, "count": len(array), "type": kind}
        if bounds:
            item["min"] = [float(x) for x in array.min(0)]
            item["max"] = [float(x) for x in array.max(0)]
        accessors.append(item)
        return len(accessors) - 1

    for material, locks in groups.items():
        check_closed(locks)
        verts, normals, _joints, _weights, faces = merge(locks, lambda _y: [(0, 1.0)])
        primitives.append(
            {
                "attributes": {"POSITION": add(verts, "VEC3", 5126, 34962, True), "NORMAL": add(normals, "VEC3", 5126, 34962)},
                "indices": add(faces.reshape(-1), "SCALAR", 5125, 34963),
                "material": len(materials),
            }
        )
        materials.append({"name": "Accessory%d" % len(materials), "doubleSided": True, "pbrMetallicRoughness": {"baseColorFactor": colors[material], "metallicFactor": 0.0, "roughnessFactor": 0.85}})
    gltf = {
        "asset": {"version": "2.0", "generator": "mods/mare_fair/hair/" + os.path.basename(sys.argv[0])},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": "Accessory", "mesh": 0}],
        "meshes": [{"name": "Accessory", "primitives": primitives}],
        "materials": materials,
        "accessors": accessors,
        "bufferViews": views,
        "buffers": [{"byteLength": len(buffer)}],
    }
    text = json.dumps(gltf, separators=(",", ":")).encode()
    text += b" " * (-len(text) % 4)
    buffer.extend(b"\0" * (-len(buffer) % 4))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, 28 + len(text) + len(buffer)))
        f.write(struct.pack("<II", len(text), 0x4E4F534A) + text)
        f.write(struct.pack("<II", len(buffer), 0x004E4942) + bytes(buffer))


def lathe(origin, axis, profile, sides=40):
    """A closed round shape: profile is (distance along axis, radius) from bottom to top."""
    axis = unit(np.array(axis, float))
    side = unit(np.cross(axis, (1.0, 0.0, 0.0)))
    keys = [origin + axis * s for s, _r in profile]
    radii = [r for _s, r in profile]
    return loft(keys, radii, radii, lambda _p: side, steps=2, sides=sides)


def sun_hat(ribbon):
    """Her wide sun hat, tipped up at the front, with a blue ribbon and a sunflower."""
    origin = np.array((0.0, 1.08, -0.21))
    axis = unit(np.array((0.08, 0.97, 0.22)))
    top = lathe(origin, axis, [(-0.014, 0.01), (-0.012, 0.30), (-0.004, 0.325), (0.004, 0.30), (0.01, 0.165), (0.07, 0.155), (0.105, 0.14), (0.125, 0.085), (0.13, 0.005)])
    under = lathe(origin, axis, [(-0.02, 0.01), (-0.019, 0.30), (-0.014, 0.312), (-0.012, 0.005)])
    ribbon.append(lathe(origin, axis, [(0.012, 0.15), (0.016, 0.168), (0.05, 0.164), (0.054, 0.14)]))
    # The sunflower sits on the ribbon, front and to her left.
    toward = np.array((0.6, 0.0, -0.8))
    toward = unit(toward - axis * np.dot(toward, axis))
    center = origin + axis * 0.034 + toward * 0.172
    across = unit(np.cross(toward, axis))
    petals = []
    for i in range(12):
        angle = i * 2.0 * np.pi / 12.0
        spoke = across * np.cos(angle) + axis * np.sin(angle)
        petals.append(loft([center + spoke * 0.015, center + spoke * 0.045, center + spoke * 0.07], [0.012, 0.018, 0.001], [0.004, 0.005, 0.001], lambda _p: toward, steps=5, sides=10))
    seeds = lathe(center - toward * 0.004, toward, [(0.0, 0.004), (0.002, 0.034), (0.012, 0.03), (0.018, 0.004)], sides=20)
    return {HAT: [top], UNDER: [under], PETAL: petals, SEED: [seeds]}


def tail():
    # A big wavy tail with scallops down its back edge and a flicked tip.
    keys = [(0, 0.645, 0.165), (0, 0.70, 0.25), (0, 0.665, 0.36), (0, 0.55, 0.42), (0, 0.46, 0.385), (0, 0.37, 0.43), (0, 0.28, 0.39), (0, 0.215, 0.42), (0, 0.195, 0.335)]
    widths = np.array([0.025, 0.06, 0.09, 0.10, 0.085, 0.09, 0.07, 0.05, 0.003])
    thicks = np.array([0.028, 0.05, 0.065, 0.07, 0.06, 0.06, 0.045, 0.03, 0.003])
    main = loft(keys, widths, thicks, tail_out, steps=10, sides=20)
    # The pale centre panel, proud of the darker edge on both sides of the tail.
    centre = loft(keys, widths * 0.62, thicks * 1.1, tail_out, steps=10, sides=20)
    side = loft(
        [(0.022, 0.64, 0.33), (0.03, 0.54, 0.455), (0.026, 0.45, 0.42), (0.02, 0.37, 0.47), (0.014, 0.31, 0.445)],
        [0.03, 0.06, 0.05, 0.05, 0.003],
        [0.022, 0.04, 0.035, 0.03, 0.003],
        tail_out,
        steps=10,
        sides=16,
    )
    return {BLONDE: [centre], DARK: [main, side]}


def write(path, rig, blob, meshes_in):
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
    for name, groups in meshes_in:
        primitives = []
        for material, (verts, normals, joints, weights, faces) in groups.items():
            attributes = {
                "POSITION": add(verts, "VEC3", 5126, 34962, True),
                "NORMAL": add(normals, "VEC3", 5126, 34962),
                "TEXCOORD_0": add(np.zeros((len(verts), 2), np.float32), "VEC2", 5126, 34962),
                "JOINTS_0": add(joints, "VEC4", 5123, 34962),
                "WEIGHTS_0": add(weights, "VEC4", 5126, 34962),
            }
            primitives.append({"attributes": attributes, "indices": add(faces.reshape(-1), "SCALAR", 5125, 34963), "material": material})
        meshes.append({"name": name, "primitives": primitives})
    skin["inverseBindMatrices"] = add(np.frombuffer(ibm, np.float32).reshape(-1, 16), "MAT4", 5126, None)
    rig["asset"]["generator"] = "mods/mare_fair/hair/" + os.path.basename(sys.argv[0])
    rig.update(meshes=meshes, accessors=accessors, bufferViews=views, buffers=[{"byteLength": len(buffer)}])
    text = json.dumps(rig, separators=(",", ":")).encode()
    text += b" " * (-len(text) % 4)
    buffer.extend(b"\0" * (-len(buffer) % 4))
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, 28 + len(text) + len(buffer)))
        f.write(struct.pack("<II", len(text), 0x4E4F534A) + text)
        f.write(struct.pack("<II", len(buffer), 0x004E4942) + bytes(buffer))


def main():
    rig, blob = read_glb(GLB)
    if len(rig["materials"]) < 3:
        raise SystemExit("expected blonde, dusky and band materials in the file")
    while len(rig["materials"]) < 8:
        rig["materials"].append(json.loads(json.dumps(rig["materials"][BLONDE])) | {"name": "FairFlyerHair%d" % len(rig["materials"])})
    for material, color in COLORS.items():
        rig["materials"][material]["pbrMetallicRoughness"]["baseColorFactor"] = linear(color)
    mane_groups, tail_groups = mane(), tail()
    for groups in (mane_groups, tail_groups):
        for locks in groups.values():
            check_closed(locks)
    meshes = [
        ("FairFlyerDevkitMane", {m: merge(l, mane_weight) for m, l in mane_groups.items()}),
        ("FairFlyerDevkitTail", {m: merge(l, tail_weight) for m, l in tail_groups.items()}),
    ]
    write(GLB, rig, blob, meshes)
    ribbon = []
    hat = sun_hat(ribbon)
    hat[BAND] = ribbon
    colors = {m: linear(c) for m, c in COLORS.items()}
    colors[BAND] = rig["materials"][BAND]["pbrMetallicRoughness"]["baseColorFactor"]
    write_accessory(os.path.join(HERE, "..", "accessories", "sun_hat.glb"), hat, colors)
    for name, groups in meshes:
        for material, (verts, _n, _j, _w, faces) in groups.items():
            print(name, "material", material, "verts", len(verts), "tris", len(faces), verts.min(0).round(3), verts.max(0).round(3))
    print("bytes", os.path.getsize(GLB))


if __name__ == "__main__":
    main()
