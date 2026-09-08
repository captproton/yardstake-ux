"""
verify_views.py — the camera presets in views.py have to be checkable.

Every defect in these presets was found BY LOOKING AT A RENDER, which is the
weakest kind of verification this project has and the one it keeps warning
itself off. Three of them were real and none announced itself:

  * `front()` cropped the foundation, because the distance was fitted to the
    horizontal field of view only and the render is 16:10;
  * `bathroom()` put the lens INSIDE the vanity cabinet, because the pocket
    door it stood in is centred in front of that cabinet;
  * `kitchen()` framed 22.5 ft of "kitchen" spanning three rooms, because
    Appl_body is one merged mesh holding the fridge, the range, the dishwasher
    and the stacked washer/dryer in the bedroom closet.

So each of those is now a gate.

    blender --background barn_cabin_524.blend --python verify_views.py
"""
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import views  # noqa: E402

FAILED = []

# Anything a standing person would collide with. A camera inside one of these
# is not a view of the room, it is a view of the inside of a cupboard.
SOLID = ("Cab_", "Appl_", "Fix_", "Part_", "Wall_", "Door_", "Found_")


def gate(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name:52s} {detail}")
    if not ok:
        FAILED.append(name)


def inside(p, box, pad=0.0):
    x0, x1, y0, y1, z0, z1 = box
    return (x0 - pad <= p.x <= x1 + pad and y0 - pad <= p.y <= y1 + pad
            and z0 - pad <= p.z <= z1 + pad)


def inside_mesh(ob, p):
    """Is `p` actually within this object's surface?

    NOT a bounding-box test. `Appl_body` is one merged mesh holding the fridge,
    the range, the dishwasher and the stacked washer/dryer, so its bbox is an
    8 x 21 ft slab covering most of the building; a bbox test reported the
    bathroom camera as being "inside the appliances" when the nearest appliance
    was in another room. Asking the nearest SURFACE which side we are on gets
    the right answer for a merged mesh, because the nearest surface is the one
    actually next to us.
    """
    local = ob.matrix_world.inverted() @ p
    ok, loc, nor, _ = ob.closest_point_on_mesh(local)
    return bool(ok) and (local - loc).dot(nor) < 0


def main():
    print("=" * 96)
    print("VIEW PRESETS — framing is asserted, not eyeballed")
    print("=" * 96)

    scene = bpy.context.scene
    model = views._bounds([o for o in bpy.data.objects if o.type == "MESH"])
    bath = views._bounds([bpy.data.objects[views.BATH_FLOOR]])
    main_floor = views._bounds([bpy.data.objects[views.MAIN_FLOOR]])

    solids = [o for o in bpy.data.objects
              if o.type == "MESH" and views._matches(o, SOLID)]

    for name, fn in views.PRESETS.items():
        fn()
        cam = bpy.data.objects.get("View_preset")
        gate(f"{name}: leaves a usable scene camera",
             cam is not None and scene.camera is cam,
             cam.name if cam else "no View_preset camera")
        eye = cam.location

        # A camera buried in geometry renders the inside of that geometry.
        # This is the bathroom-inside-the-vanity defect, as a gate.
        if name != "front":
            hits = [o.name for o in solids if inside_mesh(o, eye)]
            gate(f"{name}: eye is not inside any solid object", not hits,
                 f"eye {tuple(round(v, 2) for v in eye)}"
                 + (f" — INSIDE {', '.join(hits[:3])}" if hits else ""))

    # ---- kitchen ---------------------------------------------------------
    views.kitchen()
    eye = bpy.data.objects["View_preset"].location
    gate("kitchen: eye stands in the main living space",
         inside(eye, main_floor[:4] + (0.0, 8.0)),
         f"x {eye.x:.2f} y {eye.y:.2f}")
    gate("kitchen: eye is south of the bath, not in it",
         eye.y < bath[2],
         f"eye y {eye.y:.2f} < bath south face {bath[2]:.2f}")

    # ---- bathroom --------------------------------------------------------
    views.bathroom()
    eye = bpy.data.objects["View_preset"].location
    gate("bathroom: eye stands inside the bath footprint",
         inside(eye, bath[:4] + (0.0, 8.0)),
         f"x {eye.x:.2f} y {eye.y:.2f} against "
         f"x {bath[0]:.2f}..{bath[1]:.2f} y {bath[2]:.2f}..{bath[3]:.2f}")

    # ---- front -----------------------------------------------------------
    views.front()
    cam = bpy.data.objects["View_preset"]
    gate("front: eye stands outside the building, to the south",
         cam.location.y < model[2],
         f"eye y {cam.location.y:.1f} vs south face {model[2]:.1f}")

    # THE WHOLE BUILDING IS IN FRAME, proved by projecting every corner of the
    # model's bounding box into camera space. This is the gate that would have
    # caught the cropped foundation: world_to_camera_view returns 0..1 inside
    # the frame, and the footing was landing below 0.
    x0, x1, y0, y1, z0, z1 = model
    corners = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    uv = [world_to_camera_view(scene, cam, __import__("mathutils").Vector(c))
          for c in corners]
    worst_u = min(min(p.x for p in uv), 1 - max(p.x for p in uv))
    worst_v = min(min(p.y for p in uv), 1 - max(p.y for p in uv))
    gate("front: every corner of the model is inside the frame",
         worst_u > 0 and worst_v > 0,
         f"tightest margin {min(worst_u, worst_v) * 100:.1f}% of frame "
         f"({'horizontal' if worst_u < worst_v else 'vertical'})")
    gate("front: the model is not lost in the frame",
         min(worst_u, worst_v) < 0.25,
         "it fills enough of the frame to be worth looking at")

    print("=" * 96)
    print(f"RESULT: {'ALL PASS' if not FAILED else 'FAILED: ' + ', '.join(FAILED)}")
    print("=" * 96)
    if FAILED:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
