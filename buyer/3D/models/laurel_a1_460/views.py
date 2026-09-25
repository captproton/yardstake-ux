"""
views.py — interior viewing modes for the Blender GUI (#129 review aid).

Run from Blender's Text Editor (Open -> views.py -> Run Script), or from the
Python Console:

    exec(open("/full/path/to/views.py").read())

That registers a sidebar panel: press N in the 3D viewport and pick the
"Laurel" tab. Every mode and preset below is a button there.

The functions stay callable by hand. VISIBILITY modes come from the spec:

    full()           everything, as built
    dollhouse()      roof off — look down into the rooms
    cutaway()        dollhouse, plus the front wall and its skin off
    interior_only()  partitions and slab alone

CAMERA presets move the view instead:

    living()    standing at the entry, looking back across the living room
    kitchen()   in the living room, looking at the kitchen end
    bath()      looking into the bath across its own partitions
    plan()      straight down, the whole footprint
    front()     outside the front elevation, whole building in frame

Nothing here changes geometry or materials — only visibility and the viewport
camera. None of that is exported, so none of it can reach a .glb.

WHY THE MODES LIVE IN THE SPEC. spec.export.display_modes is the one
definition of what each mode hides; this file reads it, and the manifest
#131 writes will read the same block. The barn cabin had the answer in two
places and documented what that cost.

WHY THE PRESETS MEASURE THE MODEL. A camera position typed here would be a
building dimension in code by another name, and would rot the first time a
partition moved. Each preset is derived from the geometry actually loaded —
the partitions' own bounding boxes and the model's — so moving a wall moves
the camera with it.

LAUREL HAS NO CEILING OBJECTS, and that is not an omission. Every wall and
partition runs to the underside of the one roof plane, which is what A-1.0
means by "CEILINGS FOLLOW ROOF LINE". So `dollhouse` hides the roof and there
is nothing else above head height to strip.
"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

TAB = "Laurel"


def _here():
    """The model directory, however this file was run.

    Pasting into the console defines no `__file__`, and an unsaved .blend has
    no filepath — in which case Path("").resolve() is wherever Blender was
    launched from, and reading a spec from there is worse than reading none.
    """
    if "__file__" in globals():
        return Path(__file__).resolve().parent
    if bpy.data.filepath:
        return Path(bpy.data.filepath).resolve().parent
    raise RuntimeError(
        "views.py needs to find spec.yaml and cannot: the .blend is unsaved "
        "and this script has no path. Save the .blend beside spec.yaml, or "
        "run views.py from a file rather than pasting it.")


HERE = _here()
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from build import load_spec  # noqa: E402

SPEC = load_spec(HERE / "spec.yaml")
_DM = SPEC["export"]["display_modes"]
_G = {k: tuple(v) for k, v in _DM["groups"].items()}

# A misspelt group fails here the way it will fail in the exporter, rather
# than as an opaque KeyError that leaves no panel at all.
_missing = sorted({g for m in _DM["modes"] for g in m["hide"] if g not in _G})
if _missing:
    raise RuntimeError(f"spec.export.display_modes references groups that do "
                       f"not exist: {_missing} (have {sorted(_G)})")


# ---------------------------------------------------------------------------
# visibility
# ---------------------------------------------------------------------------
# BUILT AND HELD BACK (spec.export.held_back): the siding exterior trim is in
# the file for #133 and in no export, and this blend shows the stucco finish,
# so no mode shows it.
_HELD = set((SPEC["export"].get("held_back") or {}).get("nodes") or ())


def _apply(mode_id):
    mode = next(m for m in _DM["modes"] if m["id"] == mode_id)
    prefixes = tuple(p for g in mode["hide"] for p in _G[g])
    by_name = set(mode.get("hide_objects") or ()) | _HELD
    for ob in bpy.data.objects:
        hide = ob.name in by_name or (bool(prefixes) and ob.name.startswith(prefixes))
        ob.hide_set(hide)
        ob.hide_viewport = hide
    return mode


# `full` hides nothing the spec's mode names -- but it still hides _HELD,
# as every mode does: "everything" in this blend is everything that ships.
def full():            return _apply("full")
def dollhouse():       return _apply("dollhouse")
def cutaway():         return _apply("cutaway")
def interior_only():   return _apply("interior_only")


# ---------------------------------------------------------------------------
# camera presets, derived from the geometry that is loaded
# ---------------------------------------------------------------------------
def _bbox(objs):
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for ob in objs:
        for corner in ob.bound_box:
            w = ob.matrix_world @ Vector(corner)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    return lo, hi


def _named(*names):
    return [bpy.data.objects[n] for n in names if n in bpy.data.objects]


def _walls():
    return [o for o in bpy.data.objects if o.name.startswith("Wall_")]


def _look(eye, target, lens=None, clip_start=None):
    """Point every 3D viewport at `target` from `eye`."""
    eye, target = Vector(eye), Vector(target)
    quat = (target - eye).normalized().to_track_quat("-Z", "Y")
    done = 0
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type != "VIEW_3D":
                continue
            r3d = area.spaces.active.region_3d
            r3d.view_perspective = "PERSP"
            r3d.view_rotation = quat
            r3d.view_location = target
            r3d.view_distance = (target - eye).length
            if lens:
                area.spaces.active.lens = lens
            if clip_start:
                area.spaces.active.clip_start = clip_start
            area.tag_redraw()
            done += 1
    return done


# Blender's default sensor is 36mm wide, so a lens of L mm sees a half-angle
# of atan(18/L). These are camera arithmetic, not building dimensions.
_SENSOR_HALF_MM = 18.0
_FIT_MARGIN = 1.25


def _viewport_aspect():
    """width / height of the first 3D viewport, or None if there is none.

    Blender's sensor fit is horizontal, so the VERTICAL half-angle is the
    horizontal one scaled by height/width. A camera distance computed without
    that is only ever a horizontal bound.
    """
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == "VIEW_3D":
                region = next((r for r in area.regions if r.type == "WINDOW"), None)
                if region and region.width and region.height:
                    return region.width / region.height
    return None


def _fit_distance(across, up, lens):
    """How far back a camera needs to frame `across` wide by `up` tall.

    plan() carried a fixed multiple of the footprint instead, and at lens 50
    that put the camera 24 ft up looking at a 17 ft field on a 24 ft
    building -- a frame filled entirely by slab. The distance has to come
    from the lens, or the two drift apart the first time either changes.

    IT ASKS THE VIEWPORT ITS SHAPE. The version before this fitted the
    DIAGONAL and the comment claimed that held "whatever shape the viewport
    is". Review pointed out that it does not: the diagonal is still only a
    horizontal bound, so a tall viewport can satisfy it across and clip the
    footprint's depth vertically. Both requirements are computed here, from
    the real region's aspect, and the larger wins. With no viewport to ask --
    background, or a render script -- it falls back to the diagonal, which is
    the old behaviour and is honest about being an approximation.
    """
    half = _SENSOR_HALF_MM / lens                  # tan of the horizontal half-angle
    aspect = _viewport_aspect()
    if aspect is None:
        return (math.hypot(across, up) / 2) / half * _FIT_MARGIN
    horizontal = (across / 2) / half
    vertical = (up / 2) / (half / aspect)
    return max(horizontal, vertical) * _FIT_MARGIN


def _eye_height():
    """Standing eye height, as a fraction of the rear plate — the lowest head
    room in the building. Derived, so a taller plate raises the camera."""
    return SPEC["levels"]["top_of_plate_rear"]["ft"] * 0.72


def living():
    """At the entry, looking back across the living room toward X 0."""
    dollhouse()
    lo, hi = _bbox(_walls())
    z = _eye_height()
    eye = ((lo.x + hi.x) / 2, hi.y - (hi.y - lo.y) * 0.1, z)
    target = (lo.x + (hi.x - lo.x) * 0.2, lo.y + (hi.y - lo.y) * 0.4, z * 0.8)
    return _look(eye, target, lens=18, clip_start=0.05)


def kitchen():
    """From the living room, looking at the kitchen and bath end (X max)."""
    dollhouse()
    lo, hi = _bbox(_walls())
    block = _bbox(_named("P_block_W", "P_block_S"))[0]
    z = _eye_height()
    eye = (lo.x + (hi.x - lo.x) * 0.15, hi.y - (hi.y - lo.y) * 0.25, z)
    target = (hi.x, block.y, z * 0.85)
    return _look(eye, target, lens=18, clip_start=0.05)


def bath():
    """Looking into the bath, over its own two partitions."""
    dollhouse()
    walls = _bbox(_walls())
    bw = _bbox(_named("P_bath_W"))
    bs = _bbox(_named("P_bath_S"))
    z = _eye_height()
    # the bath is the corner beyond both partitions: X above P_bath_S, Y below P_bath_W
    centre = ((bs[1].x + walls[1].x) / 2, (walls[0].y + bw[0].y) / 2, z * 0.6)
    eye = (bs[0].x - (walls[1].x - walls[0].x) * 0.12, bw[1].y, z)
    return _look(eye, centre, lens=16, clip_start=0.05)


def plan():
    """Straight down on the whole footprint, roof off."""
    dollhouse()
    lo, hi = _bbox(_walls())
    ctr = (lo + hi) / 2
    lens = 50
    up = _fit_distance(hi.x - lo.x, hi.y - lo.y, lens)
    # nudged off the axis so the up vector is not degenerate looking straight down
    return _look((ctr.x, ctr.y - (hi.y - lo.y) / 1000, up), (ctr.x, ctr.y, 0.0), lens=lens)


def front():
    """Outside the front elevation (+Y), whole building in frame."""
    full()
    objs = [o for o in bpy.data.objects if o.type == "MESH"]
    lo, hi = _bbox(objs)
    ctr = (lo + hi) / 2
    lens = 35
    back = _fit_distance(hi.x - lo.x, hi.z - lo.z, lens)
    return _look((ctr.x, hi.y + back, ctr.z + back / 4), ctr, lens=lens, clip_start=0.1)


# ---------------------------------------------------------------------------
# the sidebar panel
# ---------------------------------------------------------------------------
_MODES = [(m["id"], m["label"], m.get("desc", "")) for m in _DM["modes"]]

# ONE EXPLICIT TABLE, not `dict(globals())`. Dispatching from every global
# meant the panel would happily offer a button for any spec mode id, and any
# typo -- or any non-view helper that happened to share a name -- resolved at
# CLICK time rather than at registration. The barn cabin uses explicit
# VISIBILITY/ALL maps for this reason. Review asked for the same here.
VISIBILITY = {"full": full, "dollhouse": dollhouse,
              "cutaway": cutaway, "interior_only": interior_only}
PRESETS = {"living": living, "kitchen": kitchen, "bath": bath,
           "plan": plan, "front": front}
ALL = dict(VISIBILITY, **PRESETS)

# A mode the spec declares and this file cannot draw is a defect in one of
# them, and it is found here rather than when somebody presses the button.
_undrawable = sorted(m["id"] for m in _DM["modes"] if m["id"] not in VISIBILITY)
if _undrawable:
    raise RuntimeError(
        f"spec.export.display_modes declares modes this file has no function "
        f"for: {_undrawable} (have {sorted(VISIBILITY)})")

_PRESET_LABELS = [("living", "Living"), ("kitchen", "Kitchen"), ("bath", "Bath"),
                  ("plan", "Plan"), ("front", "Front")]


class LAUREL_OT_view(bpy.types.Operator):
    bl_idname = "laurel.view"
    bl_label = "Laurel view"
    bl_options = {"REGISTER", "UNDO"}
    action: bpy.props.StringProperty()

    def execute(self, context):
        fn = ALL.get(self.action)
        if fn is None:
            self.report({"ERROR"}, f"no such view: {self.action!r}")
            return {"CANCELLED"}
        fn()
        return {"FINISHED"}


class LAUREL_PT_views(bpy.types.Panel):
    bl_label = "Laurel — views"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = TAB

    def draw(self, context):
        col = self.layout.column(align=True)
        col.label(text="Show")
        for mid, label, desc in _MODES:
            col.operator("laurel.view", text=label).action = mid
        col.separator()
        col.label(text="Stand")
        for fid, label in _PRESET_LABELS:
            col.operator("laurel.view", text=label).action = fid


_CLASSES = (LAUREL_OT_view, LAUREL_PT_views)


def _drop(name):
    """Remove whatever class is registered under `name`, if any.

    IT MUST BE THE OLD CLASS, NOT THE NEW ONE. The first version called
    `unregister_class(cls)` on the class this very run had just defined --
    which Blender has never seen, so it raised and the raise was swallowed,
    leaving the previous run's class registered.

    WHAT THAT ACTUALLY COST, MEASURED: nothing visible. Blender 5.1.1's
    `register_class` replaces a bl_idname it already holds, reporting
    "has been registered before, unregistering previous", and three runs
    still leave exactly one panel and one operator registered. So this is not
    the leak it looks like, and saying otherwise here would be inventing a
    failure nobody saw.

    It is written this way regardless, for two reasons that survive the
    measurement: it does not lean on replace-on-conflict, which is Blender's
    behaviour to change and not ours to depend on; and it is what the barn
    cabin's views.py does, where the same idempotence was worked out first.
    Running this file twice is the documented workflow, not an edge case.
    """
    old = getattr(bpy.types, name, None)
    if old is not None:
        try:
            bpy.utils.unregister_class(old)
        except RuntimeError:
            pass


def register():
    for cls in _CLASSES:
        _drop(cls.__name__)
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_CLASSES):
        _drop(cls.__name__)


register()
print(f"views.py: panel registered — press N in the viewport, '{TAB}' tab")
