#!/usr/bin/env python3
"""Solid mane and tail for Matinee, rebuilt in place on the rig already in matinee.glb.

Needs numpy. Run it from anywhere:

    python mods/mare_fair/hair/build_matinee_hair.py

Modelled from the official art (marefair.org/mascots and the 2025 site clips): a bob
like her twin's, soft locks framing the cheeks, a high ponytail in a pink scrunchie, and
a tapered light-blue tail. The art has no standing side view, so the profile is
modelled from it, not traced. The pictures are not shipped.

Rig space: +Y up, -Z toward the face, -X her right. Materials are 0 blue, 1 purple,
2 pink (added here for the scrunchie).
"""

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from build_fair_flyer_hair import linear, write  # noqa: E402
from build_soiree_hair import bob_shell, check_closed, fall_out, loft, mane_weight, merge, radial, read_glb, tail_out, tail_weight, unit  # noqa: E402

GLB = os.path.join(HERE, "matinee.glb")
BLUE, PURPLE, PINK, MID = 0, 1, 2, 3
COLORS = {BLUE: "A9E0F2", PURPLE: "8F8FDC", PINK: "EE7FA8", MID: "9CBBEB"}


def head_cap():
    """The crown, the back of the head, and a short crest that closes the nape."""
    locks = []
    heights = np.linspace(-0.995, 0.995, 15)
    rim = np.sqrt(1.0 - heights * heights)
    locks.append(loft([(0.0, 0.995 + 0.128 * h, -0.235) for h in heights], 0.172 * rim, 0.15 * rim, lambda _p: (0.0, 0.0, 1.0), steps=3, sides=32))
    for tip in [(0.13, 0.93, -0.13), (0.065, 0.895, -0.092), (0.0, 0.885, -0.085), (-0.065, 0.895, -0.092), (-0.13, 0.93, -0.13)]:
        tip = np.array(tip)
        start = np.array((tip[0] * 0.3, 1.08, -0.18))
        mid = (start + tip) / 2 + unit(radial((start + tip) / 2)) * 0.03
        locks.append(loft([start, mid, tip], [0.04, 0.08, 0.05], [0.015, 0.028, 0.012], radial))
    locks.append(loft([(0, 0.985, -0.085), (0, 0.90, -0.09), (0, 0.85, -0.105)], [0.12, 0.135, 0.02], [0.02, 0.03, 0.006], lambda _p: (0.0, 0.35, 1.0), steps=10, sides=20))
    return locks


def mane():
    blue, pink = head_cap(), []
    # The same rounded bob as her twin, mirrored so the fringe's slit is on her left.
    verts, faces = bob_shell()
    blue.append((verts * np.array((-1.0, 1.0, 1.0)), faces[:, ::-1]))
    # Soft full locks framing the cheeks, curving in at the jaw.
    for side in (-1.0, 1.0):
        keys = [(side * x, y, z) for x, y, z in ((0.10, 1.05, -0.19), (0.16, 0.985, -0.18), (0.162, 0.90, -0.19), (0.148, 0.83, -0.235), (0.12, 0.80, -0.27))]
        blue.append(loft(keys, [0.05, 0.085, 0.09, 0.066, 0.003], [0.018, 0.034, 0.034, 0.024, 0.003], fall_out(side), steps=10))
    # The high ponytail.
    pony = [(0, 1.03, -0.07), (0, 1.055, 0.015), (0, 1.0, 0.095), (0, 0.915, 0.115), (0, 0.85, 0.09), (0, 0.80, 0.135)]
    blue.append(loft(pony, [0.03, 0.07, 0.085, 0.08, 0.06, 0.003], [0.03, 0.05, 0.06, 0.05, 0.035, 0.003], tail_out, steps=10, sides=20))
    # The scrunchie, a short fat band at the root of the ponytail.
    pink.append(loft([(0, 1.01, -0.09), (0, 1.03, -0.065), (0, 1.045, -0.04)], [0.03, 0.05, 0.032], [0.03, 0.05, 0.032], tail_out, steps=6, sides=16))
    return {BLUE: blue, PINK: pink}


def tail():
    keys = [(0, 0.645, 0.165), (0, 0.68, 0.25), (0, 0.63, 0.34), (0, 0.53, 0.385), (0, 0.42, 0.375), (0, 0.32, 0.40), (0, 0.24, 0.365)]
    widths = [0.025, 0.05, 0.07, 0.07, 0.06, 0.045, 0.003]
    thicks = [0.026, 0.04, 0.05, 0.05, 0.04, 0.028, 0.003]
    return {BLUE: [loft(keys, widths, thicks, tail_out, steps=10, sides=20)]}


def main():
    rig, blob = read_glb(GLB)
    if len(rig["materials"]) < 2:
        raise SystemExit("expected blue and purple materials in the file")
    while len(rig["materials"]) < 4:
        rig["materials"].append(json.loads(json.dumps(rig["materials"][BLUE])) | {"name": "MatineeHair%d" % len(rig["materials"])})
    for material, color in COLORS.items():
        rig["materials"][material]["pbrMetallicRoughness"]["baseColorFactor"] = linear(color)
    mane_groups, tail_groups = mane(), tail()
    for groups in (mane_groups, tail_groups):
        for locks in groups.values():
            check_closed(locks)
    meshes = [
        ("MatineeDevkitMane", {m: merge(l, mane_weight) for m, l in mane_groups.items()}),
        ("MatineeDevkitTail", {m: merge(l, tail_weight) for m, l in tail_groups.items()}),
    ]
    write(GLB, rig, blob, meshes)
    print("bytes", os.path.getsize(GLB))


if __name__ == "__main__":
    main()
