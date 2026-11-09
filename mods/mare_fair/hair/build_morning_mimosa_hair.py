#!/usr/bin/env python3
"""Solid mane and tail for Morning Mimosa, rebuilt in place on the rig in morning_mimosa.glb.

Needs numpy. Run it from anywhere:

    python mods/mare_fair/hair/build_morning_mimosa_hair.py

Modelled from the official art (marefair.org/mascots and the 2025 site clips): a messy
green fringe with a cowlick, a long side braid of leaf-shaped lobes tied with an orange,
and a braided tail made the same way. The art has no standing side view, so the profile
is modelled from it, not traced. The pictures are not shipped.

Rig space: +Y up, -Z toward the face, -X her right. Materials are 0 green, 1 orange.
"""

import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from build_fair_flyer_hair import linear, write, write_accessory  # noqa: E402
from build_matinee_hair import head_cap  # noqa: E402
from build_soiree_hair import check_closed, fall_out, helmet_fringe, loft, mane_weight, merge, radial, read_glb, spline, tail_out, tail_weight  # noqa: E402

GLB = os.path.join(HERE, "morning_mimosa.glb")
GREEN, ORANGE, FRAME = 0, 1, 2
COLORS = {GREEN: "2FBE58", ORANGE: "F09A28", FRAME: "3A3A46"}


def braid(keys, lobes, width, thick, out):
    """A chain of overlapping leaf-shaped lobes along a path."""
    points, _ = spline(keys, 12)
    index = np.linspace(0, len(points) - 1, lobes + 1).astype(int)
    locks = []
    for i in range(lobes):
        fade = 1.0 - 0.3 * i / max(lobes - 1, 1)
        start, end = points[index[i]], points[index[i + 1]]
        # Each lobe reaches a little into the next so the chain has no gaps.
        end = end + (end - start) * 0.25
        middle = points[(index[i] + index[i + 1]) // 2]
        # A leaf: a smooth curved outline, widest below the stem, narrowing to a clean point.
        t = np.linspace(0.0, 1.0, 11)
        keys = [(1 - s) ** 2 * start + 2 * s * (1 - s) * middle + s**2 * end for s in t]
        shape = np.maximum(np.sin(np.pi * t**0.75) ** 0.8, 0.03)
        locks.append(loft(keys, width * fade * shape, thick * fade * shape, out, steps=3, sides=18))
    return locks


def orange(center, radius, squash=1.0):
    """A small round orange, or with squash below 1 a slice facing sideways."""
    heights = np.linspace(-0.995, 0.995, 11)
    rim = np.sqrt(1.0 - heights * heights)
    keys = [(center[0], center[1] + radius * h, center[2]) for h in heights]
    return loft(keys, radius * rim * squash, radius * rim, lambda _p: (0.0, 0.0, 1.0), steps=2, sides=16)


def mane():
    green = head_cap()
    green.append(helmet_fringe(drop=0.02))
    # A few short tufts along the edge keep her messy.
    for x, z in ((0.09, -0.368), (0.0, -0.405), (-0.09, -0.392)):
        green.append(loft([(x, 1.04, z + 0.012), (x - 0.006, 1.005, z), (x - 0.018, 0.98, z - 0.004)], [0.016, 0.018, 0.001], [0.008, 0.008, 0.001], radial, steps=10, sides=14))
    # The cowlick.
    green.append(loft([(0.0, 1.10, -0.17), (0.012, 1.17, -0.15), (0.03, 1.215, -0.20)], [0.03, 0.022, 0.001], [0.016, 0.012, 0.002], lambda _p: (1.0, 0.0, 0.0), steps=8, sides=12))
    green.append(loft([(-0.03, 1.10, -0.14), (-0.05, 1.16, -0.09), (-0.075, 1.185, -0.12)], [0.024, 0.018, 0.001], [0.013, 0.01, 0.002], lambda _p: (1.0, 0.0, 0.0), steps=8, sides=12))
    # A short lock on her right, to the jaw.
    keys = [(-0.10, 1.05, -0.19), (-0.16, 0.985, -0.18), (-0.162, 0.90, -0.19), (-0.148, 0.83, -0.235), (-0.12, 0.80, -0.27)]
    green.append(loft(keys, [0.04, 0.068, 0.07, 0.05, 0.003], [0.016, 0.028, 0.028, 0.02, 0.003], fall_out(-1.0), steps=10))
    # The long braid over her left side, ending on the shoulder.
    path = [(0.13, 1.03, -0.16), (0.165, 0.94, -0.15), (0.14, 0.84, -0.15), (0.115, 0.74, -0.18), (0.118, 0.65, -0.215), (0.13, 0.56, -0.20), (0.135, 0.50, -0.21)]
    green += braid(path, 5, 0.095, 0.036, fall_out(1.0))
    # The tie and a small leafy tuft below it.
    green.append(loft([(0.135, 0.50, -0.21), (0.137, 0.46, -0.235), (0.14, 0.43, -0.20)], [0.028, 0.034, 0.002], [0.02, 0.018, 0.002], fall_out(1.0), steps=8, sides=14))
    # The orange slice tucked by her left ear, as in the no-glasses art.
    return {GREEN: green, ORANGE: [orange((0.145, 0.492, -0.215), 0.03), orange((0.182, 1.05, -0.205), 0.04, squash=0.22)]}


def glasses(spiral=True, radius=0.074, wire=0.0056):
    """Round glasses close to the face. With spiral, a fine line marks each lens."""
    parts = []
    z = -0.405
    for side in (-1.0, 1.0):
        center = np.array((side * 0.095, 0.905, z))
        out = lambda p, c=center: p - c  # noqa: E731
        ring = [center + np.array((np.cos(a), np.sin(a), 0.0)) * radius for a in np.linspace(0.0, 2.0 * np.pi + 0.3, 27)]
        parts.append(loft(ring, [wire] * 27, [wire] * 27, out, steps=2, sides=10))
        if spiral:
            turns = np.linspace(0.0, 1.0, 34)
            coil = [center + np.array((np.cos(side * t * 4.4 * np.pi), np.sin(side * t * 4.4 * np.pi), 0.0)) * (0.012 + (radius - 0.02) * t) for t in turns]
            parts.append(loft(coil, [0.0022] * 34, [0.0022] * 34, lambda _p: (0.0, 0.0, 1.0), steps=2, sides=8))
        arm = [(side * (0.095 + radius), 0.915, z), (side * 0.18, 0.935, -0.30), (side * 0.175, 0.96, -0.20)]
        parts.append(loft(arm, [wire, wire, 0.002], [wire, wire, 0.002], radial, steps=6, sides=8))
    gap = 0.095 - radius
    bridge = [(-gap, 0.925, z - 0.004), (0.0, 0.94, z - 0.02), (gap, 0.925, z - 0.004)]
    parts.append(loft(bridge, [wire] * 3, [wire] * 3, lambda _p: (0.0, 1.0, 0.0), steps=6, sides=8))
    return parts


def tail():
    path = [(0, 0.645, 0.165), (0, 0.705, 0.26), (0, 0.68, 0.365), (0, 0.585, 0.425), (0, 0.465, 0.425), (0, 0.345, 0.425), (0, 0.255, 0.41)]
    green = braid(path, 6, 0.112, 0.042, tail_out)
    green.append(loft([(0, 0.25, 0.41), (0, 0.205, 0.445), (0, 0.175, 0.385)], [0.03, 0.04, 0.002], [0.024, 0.02, 0.002], tail_out, steps=8, sides=14))
    return {GREEN: green, ORANGE: [orange((0.024, 0.245, 0.41), 0.032)]}


def main():
    rig, blob = read_glb(GLB)
    if len(rig["materials"]) < 2:
        raise SystemExit("expected green and orange materials in the file")
    import json

    while len(rig["materials"]) < 3:
        rig["materials"].append(json.loads(json.dumps(rig["materials"][GREEN])) | {"name": "MorningMimosaHair%d" % len(rig["materials"])})
    for material, color in COLORS.items():
        rig["materials"][material]["pbrMetallicRoughness"]["baseColorFactor"] = linear(color)
    mane_groups, tail_groups = mane(), tail()
    for groups in (mane_groups, tail_groups):
        for locks in groups.values():
            check_closed(locks)
    meshes = [
        ("MorningMimosaDevkitMane", {m: merge(l, mane_weight) for m, l in mane_groups.items()}),
        ("MorningMimosaDevkitTail", {m: merge(l, tail_weight) for m, l in tail_groups.items()}),
    ]
    write(GLB, rig, blob, meshes)
    write_accessory(os.path.join(HERE, "..", "accessories", "spiral_glasses.glb"), {FRAME: glasses()}, {FRAME: linear(COLORS[FRAME])})
    print("bytes", os.path.getsize(GLB))


if __name__ == "__main__":
    main()
