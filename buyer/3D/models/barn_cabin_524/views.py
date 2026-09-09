"""
views.py — interior viewing modes for the Blender GUI.

Run from Blender's Text Editor (Open -> views.py -> Run Script), or from the
Python Console:

    exec(open("/full/path/to/views.py").read())
    dollhouse()

then one of these VISIBILITY modes:

    full()        everything visible, as exported
    dollhouse()   roof and ceilings off -- look down into the rooms
    cutaway()     dollhouse, plus the south wall and porch off
    walkthrough() dollhouse, plus near-clip pulled in for first-person walking
    interior_only()  just the interior surfaces, no shell at all

or one of these CAMERA presets, which move the view instead:

    kitchen()     standing in the living area, looking down the kitchen run
    bathroom()    beside the tub, looking back down the west wall
    front()       outside the south elevation, whole building in frame

Nothing here changes geometry or materials -- only visibility, the viewport
camera, and a scene camera named `View_preset`. None of that is exported, so
none of it can affect a `.glb`. `full()` restores visibility.

WHY THE PRESETS MEASURE THE MODEL INSTEAD OF CARRYING COORDINATES. Ground rule
1 says the spec owns every dimension and code owns none. A camera position
typed in here would be a building dimension in code by another name, and would
rot the first time a partition moved. So each preset derives its framing from
the geometry actually loaded: the bath from the `Floor_bath` footprint, the
kitchen from the casework and appliances outside that footprint, and `front()`
from the whole-model bounding box and the viewport's own focal length. Move a
wall and the presets follow it.

Why a script rather than outliner checkboxes: the roof is its own collection
and does toggle in one click, but the ceilings are not -- they live in `Finish`
alongside the floors, doors and trim, and a verify_tier1 gate asserts that. So
hiding "everything above head height" is a per-object job, which is exactly
what a script is for.

Visibility keys off the object-name prefixes declared in spec.yaml, the same
convention the display modes and the glTF export rely on. New prefixes must be
declared there or these modes silently stop covering them.
"""
import bpy
from mathutils import Vector

# Prefix groups. Kept as prefixes, not names, so new trim or ceiling objects
# are picked up without editing this file.
ROOF = ("Roof_",)
CEILING = ("Ceil_", "Porch_ceiling")
SOUTH = ("Wall_S", "Porch_", "Gable_S")
SHELL = ("Wall_", "Gable_", "Dormer_", "Eave_", "Roof_", "Porch_", "Glazing_")


def _matches(ob, prefixes):
    return any(ob.name.startswith(p) for p in prefixes)


def _show(hide=()):
    """Hide objects matching `hide`; show everything else.

    There was an unused `prefixes` parameter here, which read as a
    half-built "show only these" feature. There is no such feature: every
    mode is expressed as what to hide.
    """
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        ob.hide_set(_matches(ob, hide))
        ob.hide_render = _matches(ob, hide)


def _viewport(near=None, shading="MATERIAL"):
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type != "VIEW_3D":
                continue
            for sp in area.spaces:
                if sp.type != "VIEW_3D":
                    continue
                sp.shading.type = shading
                if near is not None:
                    sp.clip_start = near


def full():
    """Everything visible, exactly as exported."""
    _show()
    _viewport(near=0.1)
    print("[view] full")


def dollhouse():
    """Roof and ceilings off — the view a buyer spends most time in."""
    _show(hide=ROOF + CEILING)
    _viewport(near=0.1)
    print("[view] dollhouse — roof and ceilings hidden")


def cutaway():
    """Dollhouse with the south wall and porch removed, for a sectional look."""
    _show(hide=ROOF + CEILING + SOUTH)
    _viewport(near=0.1)
    print("[view] cutaway — roof, ceilings, south wall and porch hidden")


def walkthrough():
    """First-person, with everything visible and the near clip pulled in.

    Deliberately NOT the dollhouse hiding: standing inside a room, you want the
    ceiling above you. Hiding it is right for looking down into the model and
    wrong for walking through it -- the vaulted living ceiling is one of the
    better things in here and the loft reads as open sky without it.

    The near clip matters. The scene is authored at 1 unit = 1 foot, so the
    default 0.1 sits about an inch from the eye once the unit scale is applied
    and slices through door casings as you pass them. 0.01 is comfortable.

    Then press Shift+` in the viewport to walk: W/A/S/D, mouse to look,
    Q and E for down and up, Shift to move faster. Esc or right-click exits
    without keeping the move; left-click or Enter keeps it.
    """
    _show()
    _viewport(near=0.01)
    print("[view] walkthrough — now press Shift+` in the viewport, W/A/S/D to move")


def interior_only():
    """Interior surfaces alone — floors, ceilings, partitions, doors, trim."""
    _show(hide=SHELL)
    _viewport(near=0.01)
    print("[view] interior only — shell hidden")




# ---------------------------------------------------------------------------
# Camera presets
# ---------------------------------------------------------------------------
# Eye height is a HUMAN dimension, not a building one, so it lives here rather
# than in the spec -- 5'-6" is a standing eye. The scene is authored at
# 1 unit = 1 foot.
EYE_FT = 5.5

# Objects that define a room. Floor_bath is the bath footprint exactly, which
# is a better boundary than any wall bbox: it stops at the finished faces.
BATH_FLOOR = "Floor_bath"
MAIN_FLOOR = "Floor_main_S"
COUNTER = "Cab_top"


def _bounds(objects):
    """World-space (x0, x1, y0, y1, z0, z1) over a list of mesh objects."""
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    for ob in objects:
        for corner in ob.bound_box:
            w = ob.matrix_world @ Vector(corner)
            for i in range(3):
                lo[i] = min(lo[i], w[i])
                hi[i] = max(hi[i], w[i])
    if lo[0] == float("inf"):
        raise ValueError("no objects matched — is the right .blend open?")
    return lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]


def _place_camera(eye, target, lens, near):
    """A scene camera, so a preset can be rendered as well as looked through.

    `near` is the caller's, not a constant. It used to be hardcoded at 0.01
    here while `_look` applied the caller's value to the viewport, so a preset
    rendered through this camera did not match what the viewport showed --
    front() asks for 0.1 and was silently getting 0.01.
    """
    cam = bpy.data.objects.get("View_preset")
    if cam is None:
        cam = bpy.data.objects.new("View_preset", bpy.data.cameras.new("View_preset"))
        bpy.context.scene.collection.objects.link(cam)
    cam.data.lens = lens
    cam.data.clip_start = near
    cam.location = eye
    cam.rotation_euler = (target - eye).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    # Setting location/rotation does NOT refresh matrix_world. Rendering
    # happens to force it, so this was invisible until verify_views.py
    # projected the model into camera space and got the world Z back as a
    # depth -- an identity matrix, silently.
    bpy.context.view_layer.update()
    return cam


def _look(eye, target, lens=35.0, near=0.01):
    """Point every 3D viewport at `target` from `eye`, and set a scene camera."""
    eye, target = Vector(eye), Vector(target)
    _place_camera(eye, target, lens, near)
    offset = eye - target
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type != "VIEW_3D":
                continue
            for sp in area.spaces:
                if sp.type != "VIEW_3D":
                    continue
                sp.lens = lens
                sp.clip_start = near
                r3d = sp.region_3d
                r3d.view_perspective = "PERSP"
                r3d.view_location = target
                r3d.view_distance = offset.length
                r3d.view_rotation = offset.to_track_quat("Z", "Y")
            area.tag_redraw()
    return eye, target


def kitchen():
    """Standing in the living area, looking down the kitchen run.

    FRAMED FROM THE ROOM, NOT FROM THE CASEWORK. The obvious implementation --
    bound the `Cab_` and `Appl_` objects and look at that -- does not work
    here, and the reason is worth keeping. build_adu merges each material group
    into ONE mesh, so `Appl_body` is a single object containing the fridge, the
    range, the dishwasher AND the stacked washer/dryer in the bedroom closet.
    Its bounding box is 22.5 ft long and spans three rooms. No per-object test
    can split it, because there is only one object. `Cab_carcass` is the same:
    it carries the bath vanity on the far side of a wall.

    This is the shared-mesh problem that made the first verify_geometry.py a
    tautology, met again in a different place.

    So the run is located by the ROOM instead: the west wall, from the south
    interior face up to the bath's south wall. Only the counter DEPTH is read
    off the casework, and a depth is the same in every room the run passes
    through, so a merged mesh cannot corrupt it.
    """
    fx0, _, fy0, _, _, _ = _bounds([bpy.data.objects[MAIN_FLOOR]])
    _, _, by0, _, _, _ = _bounds([bpy.data.objects[BATH_FLOOR]])
    cx0, cx1, _, _, _, cz1 = _bounds([bpy.data.objects[COUNTER]])
    depth = cx1 - cx0

    run_y0, run_y1 = fy0, by0            # south interior face to the bath wall
    eye = Vector((fx0 + depth * 4.6, run_y0 + (run_y1 - run_y0) * 0.06, EYE_FT))
    target = Vector((fx0 + depth * 0.5,
                     run_y0 + (run_y1 - run_y0) * 0.62,
                     cz1 * 1.25))
    _viewport(near=0.01)
    _look(eye, target, lens=28.0)
    print(f"[view] kitchen — {run_y1 - run_y0:.1f} ft of west wall, "
          f"counter {depth:.2f} ft deep")


def bathroom():
    """Beside the tub, looking back down the west wall at vanity and WC.

    Not "just inside the door", which is what this said while the code did
    something else. The reasoning for the actual position is below.
    """
    x0, x1, y0, y1, _, _ = _bounds([bpy.data.objects[BATH_FLOOR]])
    w, d = x1 - x0, y1 - y0
    # LOOK BACK FROM BESIDE THE TUB, SOUTH-WEST TOWARD THE VANITY.
    #
    # This room defeats the obvious framings, and the geometry says why. Every
    # fixture is on the WEST wall -- vanity, mirror, and the WC, whose tank is
    # against it too -- and Fix_tub_surround is a featureless box spanning the
    # full width of the NORTH end from 1'-8" to 6'-0". So:
    #   * looking north down the room photographs a blank panel;
    #   * standing in the doorway puts the lens inside the vanity, because the
    #     pocket door is centred in front of it;
    #   * aiming at the WC from standing height is a 37-degree downward shot
    #     of the floor tile.
    # The only clear floor is a strip on the east side, about 3 x 5 ft. Stand
    # at the north end of it, next to the tub, and look back down the west
    # wall: vanity and mirror ahead, WC in the near field, surround behind the
    # camera where its blankness costs nothing.
    eye = Vector((x0 + w * 0.92, y0 + d * 0.62, EYE_FT * 0.91))
    target = Vector((x0 + w * 0.20, y0 + d * 0.26, EYE_FT * 0.58))
    _viewport(near=0.01)
    _look(eye, target, lens=16.0)
    print(f"[view] bathroom — {x1 - x0:.1f} x {y1 - y0:.1f} ft, wide lens to fit it")


def front():
    """Outside the south elevation, far enough back for the whole building.

    The distance is COMPUTED, not chosen: it is what the viewport's own focal
    length needs in order to fit the model's bounding box, with a margin. Widen
    the lens or grow the roof and it backs off on its own.
    """
    full()
    shell = [o for o in bpy.data.objects if o.type == "MESH"]
    x0, x1, y0, y1, z0, z1 = _bounds(shell)
    lens, sensor = 50.0, 36.0
    # FIT BOTH AXES. Blender maps the sensor to the LONGER side of the frame,
    # so on a 16:10 render the vertical half-angle is smaller by the aspect
    # ratio. Fitting the horizontal alone cropped the foundation off a model
    # that is 25 ft wide and 21.7 ft tall.
    r = bpy.context.scene.render
    aspect = r.resolution_y / r.resolution_x
    tan_h = sensor / 2.0 / lens
    tan_v = tan_h * aspect
    dist = max((x1 - x0) / 2.0 / tan_h, (z1 - z0) / 2.0 / tan_v) * 1.12

    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    eye = Vector((cx, y0 - dist, cz))
    target = Vector((cx, (y0 + y1) / 2, cz))
    _look(eye, target, lens=lens, near=0.1)
    print(f"[view] front — {dist:.0f} ft out; model is "
          f"{x1 - x0:.1f} x {y1 - y0:.1f} x {z1 - z0:.1f} ft")


PRESETS = {"kitchen": kitchen, "bathroom": bathroom, "front": front}


if __name__ == "__main__":
    dollhouse()
