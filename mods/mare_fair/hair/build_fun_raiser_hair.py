#!/usr/bin/env python3
"""Solid mane and tail for Fun Raiser, rebuilt in place on the rig in fun_raiser.glb.

Needs numpy. Run it from anywhere:

    python mods/mare_fair/hair/build_fun_raiser_hair.py

Modelled from the official portrait (marefair.org/mascots): a swept orange fringe, a
big high ponytail in a green band, a ringlet at the cheek, and a thick S-shaped tail
that ends in a curl, all with a pale streak. There is no standing side view, so the
profile is modelled from it, not traced. The pictures are not shipped.

Rig space: +Y up, -Z toward the face, -X her right.
Materials are 0 orange, 1 pale streak, 2 green.
"""

import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from build_fair_flyer_hair import linear, write  # noqa: E402
from build_matinee_hair import head_cap  # noqa: E402
from build_soiree_hair import check_closed, fall_out, helmet_fringe, loft, mane_weight, merge, radial, read_glb, tail_out, tail_weight  # noqa: E402

GLB = os.path.join(HERE, "fun_raiser.glb")
ORANGE, PALE, GREEN, GOLD = 0, 1, 2, 3
COLORS = {ORANGE: "F5A03C", PALE: "FFD7A6", GREEN: "2E9A62", GOLD: "E3C15A"}


def streaked(keys, widths, thicks, out, steps=10, sides=20, share=0.52):
    """A lock and its pale streak, which stands just proud of both faces."""
    widths, thicks = np.array(widths), np.array(thicks)
    return loft(keys, widths, thicks, out, steps=steps, sides=sides), loft(keys, widths * share, thicks * 1.12, out, steps=steps, sides=sides)


def mane():
    orange, pale, green = head_cap(), [], []
    orange.append(helmet_fringe())
    # The big high ponytail: up from the crown, over, and curling forward at the end.
    body, streak = streaked(
        [(0, 1.07, -0.13), (0, 1.125, -0.075), (0, 1.135, 0.005), (0, 1.065, 0.055), (0, 0.98, 0.05), (0, 0.925, -0.01), (0, 0.94, -0.045)],
        [0.055, 0.105, 0.13, 0.12, 0.092, 0.056, 0.003],
        [0.055, 0.08, 0.09, 0.08, 0.06, 0.036, 0.003],
        tail_out,
    )
    orange.append(body)
    pale.append(streak)
    green.append(loft([(0, 1.055, -0.145), (0, 1.09, -0.125), (0, 1.12, -0.105)], [0.04, 0.066, 0.05], [0.04, 0.056, 0.04], tail_out, steps=6, sides=16))
    # A ringlet at her right cheek, a shorter lock at her left.
    body, streak = streaked(
        [(-0.13, 1.02, -0.24), (-0.175, 0.95, -0.27), (-0.18, 0.865, -0.28), (-0.165, 0.80, -0.255), (-0.14, 0.795, -0.22), (-0.135, 0.835, -0.225)],
        [0.04, 0.066, 0.07, 0.056, 0.036, 0.003],
        [0.02, 0.03, 0.03, 0.026, 0.018, 0.003],
        fall_out(-1.0),
        steps=12,
        sides=16,
    )
    orange.append(body)
    pale.append(streak)
    keys = [(0.10, 1.05, -0.19), (0.16, 0.985, -0.18), (0.162, 0.90, -0.19), (0.148, 0.83, -0.235), (0.12, 0.80, -0.27)]
    orange.append(loft(keys, [0.04, 0.068, 0.07, 0.05, 0.003], [0.016, 0.028, 0.028, 0.02, 0.003], fall_out(1.0), steps=10))
    return {ORANGE: orange, PALE: pale, GREEN: green, GOLD: half_moons()}


def half_moons(radius=0.05, wire=0.0034):
    """Armless half-moon reading glasses, balanced on her snout below the eyes."""
    parts = []
    y, spread = 0.89, 0.075
    def seat(x, yy):
        # The lenses angle back along the sides of the snout.
        return np.array((x, yy, -0.425 + 0.45 * max(abs(x) - 0.04, 0.0)))

    for side in (-1.0, 1.0):
        center_x = side * spread
        rim = [seat(center_x + np.cos(a) * radius, y + np.sin(a) * radius) for a in np.linspace(np.pi, 2.0 * np.pi, 15)]
        top = [seat(center_x + x, y) for x in np.linspace(radius, -radius * 1.06, 7)[1:]]
        loop = rim + top
        middle = seat(center_x, y - radius * 0.4)
        parts.append(loft(loop, [wire] * len(loop), [wire] * len(loop), lambda p, c=middle: p - c, steps=2, sides=10))
    # The bridge rests over the top of the snout.
    inner = spread - radius
    bridge = [seat(-inner, y), (0.0, y + 0.016, -0.432), seat(inner, y)]
    parts.append(loft(bridge, [wire] * 3, [wire] * 3, lambda _p: (0.0, 1.0, 0.0), steps=8, sides=8))
    return parts


def tail():
    body, streak = streaked(
        [(0, 0.645, 0.165), (0, 0.71, 0.26), (0, 0.69, 0.38), (0, 0.57, 0.43), (0, 0.45, 0.38), (0, 0.36, 0.34), (0, 0.27, 0.37), (0, 0.225, 0.45), (0, 0.275, 0.52), (0, 0.345, 0.49), (0, 0.335, 0.44)],
        [0.025, 0.066, 0.10, 0.115, 0.105, 0.09, 0.075, 0.066, 0.052, 0.032, 0.003],
        [0.028, 0.052, 0.07, 0.078, 0.068, 0.056, 0.046, 0.04, 0.034, 0.022, 0.003],
        tail_out,
        steps=12,
    )
    return {ORANGE: [body], PALE: [streak]}


def main():
    rig, blob = read_glb(GLB)
    if len(rig["materials"]) < 3:
        raise SystemExit("expected orange, pale and green materials in the file")
    import json

    while len(rig["materials"]) < 4:
        rig["materials"].append(json.loads(json.dumps(rig["materials"][ORANGE])) | {"name": "FunRaiserHair%d" % len(rig["materials"])})
    for material, color in COLORS.items():
        rig["materials"][material]["pbrMetallicRoughness"]["baseColorFactor"] = linear(color)
    mane_groups, tail_groups = mane(), tail()
    for groups in (mane_groups, tail_groups):
        for locks in groups.values():
            check_closed(locks)
    meshes = [
        ("FunRaiserDevkitMane", {m: merge(l, mane_weight) for m, l in mane_groups.items()}),
        ("FunRaiserDevkitTail", {m: merge(l, tail_weight) for m, l in tail_groups.items()}),
    ]
    write(GLB, rig, blob, meshes)
    print("bytes", os.path.getsize(GLB))


if __name__ == "__main__":
    main()
