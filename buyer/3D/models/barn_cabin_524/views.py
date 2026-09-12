"""
views.py — interior viewing modes for the Blender GUI.

Run from Blender's Text Editor (Open -> views.py -> Run Script), or from the
Python Console:

    exec(open("/full/path/to/views.py").read())

That registers a **sidebar panel**: press N in the 3D viewport and pick the
"ADU" tab. Every mode below is a button there, which is the intended way to
move between them -- the console is for scripting, not for clicking.

The functions stay callable by hand:

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
import json
from pathlib import Path

import bpy
from mathutils import Vector

# Prefix groups. Kept as prefixes, not names, so new trim or ceiling objects
# are picked up without editing this file.
# WHAT EACH MODE HIDES NOW LIVES IN THE SPEC, because the configurator page
# needs the same answer and was not getting it: this module knew how to strip
# a roof and a web runtime had no way to ask. spec.export.display_modes is the
# one definition; finish_adu.py resolves it into the manifest as node NAMES,
# and these four tuples are the same lists read back for use in Blender.
def _display_modes():
    """spec.export.display_modes — groups AND the modes composed from them.

    TWO THINGS HERE THAT REVIEW CAUGHT, both worth the comment.

    The import path first. This file is documented to run as
    `exec(open(".../views.py").read())` from Blender's console, and that does
    NOT put this directory on sys.path -- nor does it define `__file__`. A
    bare `from build_adu import load_spec` worked only when Blender happened
    to be launched from the model directory. The directory is resolved from
    the open .blend when `__file__` is absent, and put on the path first.

    And the MODES, not just the groups. The first version of this read only
    `groups` and left `dollhouse` composing `ROOF + CEILING` in code -- so a
    spec that recomposed a mode would have finish_adu emitting the new
    manifest while Blender applied the old one, and the "one definition"
    this was written to create would have been two again. The agreement gate
    would have caught it, but only after the fact.
    """
    import sys
    here = None
    if "__file__" in globals():
        here = Path(__file__).resolve().parent
    elif bpy.data.filepath:
        here = Path(bpy.data.filepath).resolve().parent
    else:
        # UNSAVED .blend, RUN FROM THE TEXT EDITOR. `__file__` is absent and
        # bpy.data.filepath is "" -- and Path("").resolve() is the current
        # working directory, which is wherever Blender happened to be
        # launched from. Reading a spec from there would be worse than
        # reading none: the panel would register against another building's
        # modes. Fall back to the only honest answer, which is to say so.
        raise RuntimeError(
            "views.py needs to find spec.yaml and cannot: the .blend is "
            "unsaved and this script has no path. Save the .blend beside "
            "spec.yaml, or run views.py from a file rather than pasting it.")
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    from build_adu import load_spec
    return load_spec(here / "spec.yaml")["export"]["display_modes"]


_DM = _display_modes()
_G = {k: tuple(val) for k, val in _DM["groups"].items()}
# each mode's prefixes, composed in the spec rather than here
# A MISSPELT GROUP FAILS THE SAME WAY IT DOES IN THE EXPORTER. This used to
# be a bare `_G[g]`, so the identical spec typo that gives finish_adu a
# readable PROBLEM gave the Blender panel an opaque KeyError at import and no
# panel at all. Two consumers of one spec should fail alike.
_missing = sorted({g for m in _DM["modes"] for g in m["hide"] if g not in _G})
if _missing:
    raise RuntimeError(
        f"spec.export.display_modes references groups that do not exist: "
        f"{_missing} (have {sorted(_G)})")
HIDES = {m["id"]: tuple(x for g in m["hide"] for x in _G[g])
         for m in _DM["modes"]}
ROOF = _G["roof"]
CEILING = _G["ceiling"]
SOUTH = _G["south"]
SHELL = _G["shell"]



# ---------------------------------------------------------------------------
# Furniture arrangements
# ---------------------------------------------------------------------------
# TWO BEDROOM ARRANGEMENTS SHARE THE FLOOR and are alternatives -- a bed and a
# home office. lod0 ships both, because a runtime can only toggle what is in
# the file, and `presence` in the configurator manifest says which is visible.
#
# _show() used to blanket-unhide every mesh it was not told to hide, which
# undid that and put the desk through the bed the moment anyone pressed Full.
# So the visibility modes now honour the manifest.
#
# WHY THE MANIFEST AND NOT THE SPEC. The browser reads variants.json; reading
# the same file here makes this panel a reference implementation of the same
# contract, so Blender and the browser cannot quietly disagree. It also means a
# malformed manifest shows up in the viewport before it shows up in front of a
# homeowner.
MANIFEST = "export/variants.json"

_layout = {}          # set id -> chosen option id, for this session


_warned = set()
_cache = {}      # path -> (mtime, parsed manifest)


def _warn_once(key, message):
    if key not in _warned:
        _warned.add(key)
        print(f"[view] {message}")


def _manifest():
    """The exported manifest, or None if there is not one yet.

    views.py has to keep working on a .blend alone: a fresh build_adu.py run
    has no export. A missing manifest degrades to the old behaviour rather
    than raising, and says so ONCE -- _show() calls this on every mode change,
    so a per-call message would bury the console in a loop the user cannot
    see the start of.
    """
    blend = bpy.data.filepath
    if not blend:
        _warn_once("unsaved", "unsaved .blend; furniture arrangements not applied")
        return None
    path = Path(blend).parent / MANIFEST
    try:
        mtime = path.stat().st_mtime
    except OSError:
        _warn_once("missing", f"no {MANIFEST}; run finish_adu.py to get "
                              f"furniture arrangements")
        return None

    # CACHED BY MTIME. _presence() is called from the panel's draw(), which
    # Blender runs on every redraw, and from _show() on every mode change.
    # Re-reading and re-parsing the file that often is real disk I/O inside
    # the UI loop. Keyed on mtime so a fresh finish_adu.py run is picked up
    # without restarting Blender.
    hit = _cache.get(str(path))
    if hit is not None and hit[0] == mtime:
        return hit[1]
    try:
        man = json.loads(path.read_text())
    except (OSError, ValueError) as exc:              # noqa: BLE001
        _warn_once("unreadable",
                   f"{MANIFEST} unreadable ({exc}); arrangements not applied")
        return None
    _cache[str(path)] = (mtime, man)
    return man


def _bad_set(st):
    """Why this presence set cannot be trusted, or None if it can.

    The schema is not a guess at what a manifest ought to contain. It is the
    list of keys this project INDEXES UNCONDITIONALLY, read off the consumers:
    _apply_layouts() and _controlled() below, the panel's draw(), and
    verify_views.py. A key nothing indexes is not checked; a key something
    indexes is, because the alternative is a KeyError out of draw(), and a
    draw() that raises leaves the sidebar blank with no clue why.

    `default` carries an invariant as well as a type. Three call sites do
    `next(o for o in options if o["default"])` with a bare next(): zero
    defaults raises StopIteration mid-redraw, two defaults silently take
    whichever came first. Requiring exactly one is what makes those three
    lines safe, so it is checked here rather than defended at each of them.

    Ids must be unique for the same reason. `_layout` is keyed by set id and
    option lookup is a first-match next(), so a duplicate id would apply one
    arrangement while layout() printed the other -- a wrong answer reported as
    a right one, which is a failure mode this file has already shipped once.
    """
    if not isinstance(st, dict):
        return "not an object"
    for key in ("id", "label"):
        if not isinstance(st.get(key), str):
            return f"set {key!r} missing or not a string"
    opts = st.get("options")
    if not isinstance(opts, list) or not opts:
        return "'options' missing, not a list, or empty"
    for o in opts:
        if not isinstance(o, dict):
            return "option is not an object"
        for key in ("id", "label"):
            if not isinstance(o.get(key), str):
                return f"option {key!r} missing or not a string"
        if not isinstance(o.get("show"), list) or not all(
                isinstance(n, str) for n in o["show"]):
            return f"option {o['id']!r}: 'show' is not a list of strings"
        if not isinstance(o.get("default"), bool):
            return f"option {o['id']!r}: 'default' missing or not a boolean"
    n_default = sum(o["default"] for o in opts)
    if n_default != 1:
        return f"{n_default} options marked default, need exactly 1"
    ids = [o["id"] for o in opts]
    if len(set(ids)) != len(ids):
        return f"duplicate option ids in {ids}"
    return None


def _presence():
    """The presence sets, or [] if the manifest cannot be trusted.

    VALIDATED, NOT ASSUMED -- and validated against what the code actually
    indexes, which is what _bad_set() enumerates. `variants.json` can be valid
    JSON and still be the wrong shape: a top-level array, a set with no
    `options`, an option with no `label`, a set with no default. Left
    unchecked those raise AttributeError, KeyError or StopIteration out of
    _show() and out of the panel's draw(), and a draw() that raises leaves the
    sidebar broken with no clue why.

    All or nothing on purpose: a half-applied presence block is worse than
    none, because it puts the desk back through the bed.
    """
    man = _manifest()
    if man is None:
        return []
    if not isinstance(man, dict) or not isinstance(man.get("presence", []), list):
        _warn_once("schema", f"{MANIFEST} is not the expected shape; "
                             f"arrangements not applied")
        return []
    sets = man.get("presence", [])
    for st in sets:
        why = _bad_set(st)
        if why is not None:
            name = st.get("id", "?") if isinstance(st, dict) else repr(st)
            _warn_once("schema", f"{MANIFEST} presence block is malformed "
                                 f"(set {name}: {why}); arrangements not applied")
            return []
    ids = [st["id"] for st in sets]
    if len(set(ids)) != len(ids):
        _warn_once("schema", f"{MANIFEST} has duplicate presence set ids "
                             f"({ids}); arrangements not applied")
        return []
    return sets


def _controlled():
    """Every object name any presence option can show."""
    return {n for st in _presence() for o in st["options"] for n in o["show"]}


def _apply_layouts():
    """Show one option per presence set; hide everything else it controls."""
    sets = _presence()
    if not sets:
        return
    shown = set()
    for st in sets:
        want = _layout.get(st["id"])
        opt = next((o for o in st["options"] if o["id"] == want), None)
        if opt is None:
            opt = next(o for o in st["options"] if o["default"])
            _layout[st["id"]] = opt["id"]
        shown |= set(opt["show"])
    for name in _controlled():
        ob = bpy.data.objects.get(name)
        if ob is not None:
            ob.hide_set(name not in shown)
            ob.hide_render = name not in shown


def layout(set_id, option_id):
    """Choose one furniture arrangement, exactly as the runtime would.

    BOTH ids are validated. An unknown option used to be accepted here and
    then silently replaced by the default inside _apply_layouts(), while this
    function cheerfully printed the option that had NOT been applied -- a
    wrong answer reported as a right one.
    """
    st = next((x for x in _presence() if x["id"] == set_id), None)
    if st is None:
        have = [x["id"] for x in _presence()]
        raise ValueError(f"no such layout set: {set_id!r} (have {have})")
    if option_id not in [o["id"] for o in st["options"]]:
        have = [o["id"] for o in st["options"]]
        raise ValueError(
            f"no such option in {set_id!r}: {option_id!r} (have {have})")
    _layout[set_id] = option_id
    _apply_layouts()
    print(f"[view] layout {set_id} -> {option_id}")

def _matches(ob, prefixes):
    return any(ob.name.startswith(p) for p in prefixes)


def _show(hide=()):
    """Hide objects matching `hide`; show everything else.

    There was an unused `prefixes` parameter here, which read as a
    half-built "show only these" feature. There is no such feature: every
    mode is expressed as what to hide.

    Objects a presence set controls are left alone here and settled by
    _apply_layouts(), because "show everything not hidden" is the wrong rule
    for a set of alternatives -- it showed the bed AND the desk.
    """
    controlled = _controlled()
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        if ob.name in controlled:
            continue          # a presence set owns this one; see _apply_layouts
        ob.hide_set(_matches(ob, hide))
        ob.hide_render = _matches(ob, hide)
    _apply_layouts()


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
    _show(hide=HIDES["dollhouse"])
    _viewport(near=0.1)
    print("[view] dollhouse — roof and ceilings hidden")


def cutaway():
    """Dollhouse with the south wall and porch removed, for a sectional look."""
    _show(hide=HIDES["cutaway"])
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
    _show(hide=HIDES["interior_only"])
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


# ---------------------------------------------------------------------------
# Sidebar panel
# ---------------------------------------------------------------------------
# Everything above is callable from the Python Console, which is fine for
# scripting and poor for looking. Switching view meant retyping a name or
# hunting through console history, so the modes are buttons: N in the 3D
# viewport, "Views" tab.
VISIBILITY = {
    "full": full,
    "dollhouse": dollhouse,
    "cutaway": cutaway,
    "walkthrough": walkthrough,
    "interior_only": interior_only,
}

# One lookup for both kinds, so the panel and the operator cannot disagree
# about what exists. A gate in verify_views.py asserts every entry is callable.
ALL = dict(PRESETS, **VISIBILITY)

LABELS = {
    "kitchen": "Kitchen",
    "bathroom": "Bathroom",
    "front": "Front elevation",
    "full": "Full",
    "dollhouse": "Dollhouse",
    "cutaway": "Cutaway",
    "walkthrough": "Walkthrough",
    "interior_only": "Interior only",
}


class ADU_OT_view(bpy.types.Operator):
    """Jump to one of the Barn Cabin 524 views"""

    bl_idname = "adu.view"
    bl_label = "ADU view"
    bl_options = {"REGISTER", "UNDO"}

    view: bpy.props.StringProperty(name="View", default="full")

    def execute(self, context):
        fn = ALL.get(self.view)
        if fn is None:
            self.report({"ERROR"}, f"no such view: {self.view!r}")
            return {"CANCELLED"}
        fn()
        return {"FINISHED"}


class ADU_OT_layout(bpy.types.Operator):
    """Choose a furniture arrangement, as the configurator would"""

    bl_idname = "adu.layout"
    bl_label = "ADU layout"
    bl_options = {"REGISTER", "UNDO"}

    set_id: bpy.props.StringProperty(name="Set")
    option_id: bpy.props.StringProperty(name="Option")

    def execute(self, context):
        try:
            layout(self.set_id, self.option_id)
        except ValueError as exc:                      # noqa: BLE001
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        return {"FINISHED"}


class ADU_PT_views(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    # NOT "Views": Blender ships a built-in "View" tab in this same sidebar,
    # and the two sit next to each other in the tab strip. "ADU" cannot be
    # confused with anything Blender provides.
    bl_category = "ADU"
    bl_label = "Barn Cabin 524"

    def draw(self, context):
        lay = self.layout

        lay.label(text="Camera", icon="CAMERA_DATA")
        col = lay.column(align=True)
        for key in PRESETS:
            col.operator("adu.view", text=LABELS[key]).view = key

        lay.separator()
        lay.label(text="Visibility", icon="HIDE_OFF")
        col = lay.column(align=True)
        for key in VISIBILITY:
            col.operator("adu.view", text=LABELS[key]).view = key

        sets = _presence()
        if sets:
            lay.separator()
            lay.label(text="Furniture", icon="OUTLINER_OB_GROUP_INSTANCE")
            for st in sets:
                box = lay.box()
                box.label(text=st["label"])
                col = box.column(align=True)
                for o in st["options"]:
                    cur = _layout.get(st["id"])
                    if cur is None:
                        cur = next(x["id"] for x in st["options"] if x["default"])
                    op = col.operator("adu.layout", text=o["label"],
                                      depress=(o["id"] == cur))
                    op.set_id = st["id"]
                    op.option_id = o["id"]
        else:
            lay.separator()
            lay.label(text="No variants.json — run finish_adu.py", icon="INFO")

        lay.separator()
        lay.label(text="Numpad 0 looks through the preset", icon="INFO")


_CLASSES = (ADU_OT_view, ADU_OT_layout, ADU_PT_views)


def register():
    """Idempotent on purpose.

    This file is normally run with `exec(open(...).read())`, which people do
    more than once in a session. A plain register_class would raise
    "already registered" the second time and leave the panel half-installed,
    so anything already there is removed first.
    """
    for cls in _CLASSES:
        old = getattr(bpy.types, cls.__name__, None)
        if old is not None:
            try:
                bpy.utils.unregister_class(old)
            except RuntimeError:
                pass
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_CLASSES):
        old = getattr(bpy.types, cls.__name__, None)
        if old is not None:
            try:
                bpy.utils.unregister_class(old)
            except RuntimeError:
                pass


register()


if __name__ == "__main__":
    dollhouse()
