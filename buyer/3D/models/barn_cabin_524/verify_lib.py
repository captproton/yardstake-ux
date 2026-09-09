"""
verify_lib.py — helpers shared by the verify_*.py gates.

THIS FILE EXISTS BECAUSE A DUPLICATE COST US A DEFECT TWICE. `inside_mesh`
lived byte-identically in verify_views.py and verify_furniture.py, and the
missing bounding-box prefilter was in both copies. It surfaced in one of them
— a sofa in the living room reported as inside a toilet eight feet away — and
had to be fixed in two places, because the code existed in two places.

Only genuinely shared, genuinely tested helpers belong here. It is NOT a
dumping ground: `gate()` and the per-file `FAILED` lists are also duplicated
five ways, and the world-bbox idiom seven ways, but those are three different
notions of containment that happen to look alike, and collapsing them without
deciding which is correct would hide a decision rather than make one.
"""
from mathutils import Vector


def inside_mesh(ob, p):
    """Is the world-space point `p` within `ob`'s surface?

    TWO TESTS, AND BOTH ARE NEEDED.

    The bounding box alone is useless against this model's merged meshes --
    `Appl_body` is one mesh holding the fridge, the range, the dishwasher and
    the bedroom-closet washer/dryer, so its box covers most of the building.

    But the nearest-surface test alone is ALSO wrong: closest_point_on_mesh
    gives a meaningless answer for a point far outside an open or lofted
    shell, which is how a sofa in the living room was once reported as being
    inside a toilet in the bathroom.

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


def inside_mesh_cases(objects):
    """Known-answer cases for `inside_mesh`, as (name, point, expected, why).

    A shared helper with one home needs a test with one home too. These are
    checked by a gate in verify_furniture.py, because that is where the
    original defect surfaced.

    NOTE the tub: it is a hollow shell, so a point in the water volume is in
    AIR, not in solid. That case is the one that catches an implementation
    which merely asks "is this near the mesh".
    """
    return [
        ("Cab_carcass", Vector((1.50, 22.70, 1.50)), True,
         "middle of the bath vanity carcass"),
        ("Cab_carcass", Vector((4.50, 26.00, 5.00)), False,
         "open floor in the bath, but inside the merged mesh's bbox"),
        ("Wall_W", Vector((0.20, 15.00, 4.00)), True,
         "inside the west wall"),
        ("Wall_W", Vector((5.00, 15.00, 4.00)), False,
         "well inside the room"),
        ("Fix_tub_basin", Vector((2.50, 28.00, 0.50)), False,
         "in the tub's hollow — air, not solid"),
        ("Fix_toilet_bowl", Vector((6.95, 13.30, 0.60)), False,
         "the living-room sofa's seat, 8 ft from the toilet — the original bug"),
    ]
