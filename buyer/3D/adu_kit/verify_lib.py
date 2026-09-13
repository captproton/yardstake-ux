"""
adu_kit/verify_lib.py — geometry helpers shared by a model's gates.

MOVED, NOT CHANGED (#126), from models/barn_cabin_524/verify_lib.py. Only
what knows no building moves: `inside_mesh`. Its known-answer cases name the
barn cabin's objects and coordinates, so they stay in that model's
verify_lib.py, which imports this.
"""
from mathutils import Vector


def inside_mesh(ob, p):
    """Is the world-space point `p` within `ob`'s surface?

    TWO TESTS, AND BOTH ARE NEEDED.

    The bounding box alone is useless against a merged mesh: one mesh that
    welds several separate objects together has a box covering all of them
    and the space between.

    But the nearest-surface test alone is ALSO wrong: closest_point_on_mesh
    gives a meaningless answer for a point far outside an open or lofted
    shell, so a point in one room can be reported as inside an object in
    another. (Both happened on the barn cabin; its verify_lib.py keeps the
    known-answer cases.)

    Inside implies inside the bounding box, so the box is a sound prefilter
    and the surface test then does the real work.
    """
    cs = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    if not (min(c.x for c in cs) <= p.x <= max(c.x for c in cs)
            and min(c.y for c in cs) <= p.y <= max(c.y for c in cs)
            and min(c.z for c in cs) <= p.z <= max(c.z for c in cs)):
        return False
    local = ob.matrix_world.inverted() @ p
    ok, loc, nor, _ = ob.closest_point_on_mesh(local)
    return bool(ok) and (local - loc).dot(nor) < 0
