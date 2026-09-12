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
import copy
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import views  # noqa: E402
from verify_lib import inside_mesh  # noqa: E402
from build_adu import load_spec  # noqa: E402

FAILED = []

# Anything a standing person would collide with. A camera inside one of these
# is not a view of the room, it is a view of the inside of a cupboard.
SOLID = ("Cab_", "Appl_", "Fix_", "Part_", "Wall_", "Door_", "Found_")


def _drop(st, key, opt=None):
    """A copy of presence set `st` with one key removed.

    `opt` names an option index to remove the key from instead of the set
    itself. Used only to manufacture the malformed manifests the schema gate
    requires views._bad_set() to reject.
    """
    st = copy.deepcopy(st)
    target = st if opt is None else st["options"][opt]
    target.pop(key, None)
    return st


def gate(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name:52s} {detail}")
    if not ok:
        FAILED.append(name)


def inside(p, box, pad=0.0):
    x0, x1, y0, y1, z0, z1 = box
    return (x0 - pad <= p.x <= x1 + pad and y0 - pad <= p.y <= y1 + pad
            and z0 - pad <= p.z <= z1 + pad)


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
    uv = [world_to_camera_view(scene, cam, Vector(c)) for c in corners]
    worst_u = min(min(p.x for p in uv), 1 - max(p.x for p in uv))
    worst_v = min(min(p.y for p in uv), 1 - max(p.y for p in uv))
    gate("front: every corner of the model is inside the frame",
         worst_u > 0 and worst_v > 0,
         f"tightest margin {min(worst_u, worst_v) * 100:.1f}% of frame "
         f"({'horizontal' if worst_u < worst_v else 'vertical'})")
    gate("front: the model is not lost in the frame",
         min(worst_u, worst_v) < 0.25,
         "it fills enough of the frame to be worth looking at")

    # ---- the sidebar panel -----------------------------------------------
    gate("panel: the operator and panel are registered",
         hasattr(bpy.types, "ADU_OT_view") and hasattr(bpy.types, "ADU_PT_views"),
         "adu.view + Barn Cabin 524 panel")

    # A button that names a view which does not exist is a dead button, and
    # the panel builds its buttons straight from these dicts.
    missing = [k for k, v in views.ALL.items() if not callable(v)]
    unlabelled = [k for k in views.ALL if k not in views.LABELS]
    gate("panel: every button maps to a callable view",
         not missing and not unlabelled,
         f"{len(views.ALL)} views"
         + (f" — NOT CALLABLE {missing}" if missing else "")
         + (f" — NO LABEL {unlabelled}" if unlabelled else ""))

    gate("panel: camera presets and visibility modes do not collide",
         set(views.PRESETS).isdisjoint(views.VISIBILITY),
         f"{len(views.PRESETS)} camera + {len(views.VISIBILITY)} visibility")

    # END TO END: the button must actually move the camera, not merely exist.
    # Start from a DIFFERENT camera preset. The first version of this gate
    # used full(), which only changes visibility -- the camera never moved, so
    # "before == after" and the gate failed on correct behaviour.
    views.kitchen()
    before = tuple(bpy.data.objects["View_preset"].location)
    bpy.ops.adu.view(view="front")
    after = tuple(bpy.data.objects["View_preset"].location)
    gate("panel: pressing a button actually moves the camera",
         before != after and after[1] < model[2],
         f"camera now at y {after[1]:.1f}, south of the building at {model[2]:.1f}")

    # Running the file twice is normal with exec(open(...)); a plain
    # register_class would raise the second time and half-install the panel.
    try:
        views.register()
        views.register()
        again = True
    except Exception as exc:                                  # noqa: BLE001
        again = False
        print(f"        re-register raised: {exc}")
    gate("panel: re-running the file re-registers cleanly", again,
         "register() called twice without error")

    # ---- the visibility modes must not fight the arrangements -------------
    # This is the defect that prompted the gate: _show() blanket-unhid every
    # mesh it was not told to hide, so pressing Full put the office desk
    # through the bed -- exactly the state the manifest warns runtimes about,
    # reproduced by a button in our own panel.
    sets = views._presence()
    gate("presence sets reach views.py", bool(sets),
         f"{len(sets)} sets from {views.MANIFEST}"
         if sets else "no manifest — run finish_adu.py first")

    if sets:
        # A malformed manifest must be REJECTED, not survived. The failure
        # mode is a KeyError or StopIteration raised out of the panel's
        # draw(), which leaves the sidebar blank with no clue why -- so this
        # gate breaks the real manifest one key at a time and requires
        # _bad_set() to catch each. The list is every key the code indexes
        # unconditionally; anything added to that list here must be added to
        # the validator, and vice versa.
        good = copy.deepcopy(sets[0])
        broken = {}
        for key in ("id", "label", "options"):
            broken[f"set has no {key!r}"] = _drop(good, key)
        for key in ("id", "label", "show", "default"):
            broken[f"option has no {key!r}"] = _drop(good, key, opt=0)
        broken["set has no options"] = {**good, "options": []}
        broken["set is not an object"] = ["not", "a", "dict"]
        broken["no option is default"] = {
            **good, "options": [{**o, "default": False} for o in good["options"]]}
        broken["two options are default"] = {
            **good, "options": [{**o, "default": True} for o in good["options"]]}
        # Append a non-default copy of the first option, so this manifest is
        # malformed ONLY in the id. Duplicating the option outright also
        # duplicates its `default`, and the gate would then pass on the
        # exactly-one-default rule while the duplicate-id rule did nothing.
        broken["duplicate option ids"] = {
            **good, "options": [*good["options"],
                                {**good["options"][0], "default": False}]}
        survived = [why for why, bad in broken.items()
                    if views._bad_set(bad) is None]
        gate("a malformed presence set is rejected, not survived",
             not survived and views._bad_set(good) is None,
             f"{len(broken)} malformations, all caught"
             if not survived else f"SURVIVED {survived}")

    if sets:
        controlled = views._controlled()
        for mode in ("full", "dollhouse", "cutaway", "walkthrough",
                     "interior_only"):
            views.VISIBILITY[mode]()
            visible = {n for n in controlled
                       if (o := bpy.data.objects.get(n)) and not o.hide_get()}
            # MATCH ON THE EXACT SET, not on containment. The first version
            # asked which options were a SUBSET of what is visible, and had to
            # skip empty options because the empty set is a subset of
            # everything. That made "Unfurnished" untestable and, worse, made
            # the gate FAIL on correct behaviour the moment anyone chose it --
            # no option would match and the count would be zero.
            per_set = []
            for st in sets:
                owned = {n for o in st["options"] for n in o["show"]}
                shown = owned & visible
                on = [o["id"] for o in st["options"]
                      if set(o["show"]) == shown]
                per_set.append((st["id"], on, sorted(shown)))
            bad = [f"{sid}:{on or 'no option matches ' + str(shown)}"
                   for sid, on, shown in per_set if len(on) != 1]
            gate(f"{mode}(): exactly one arrangement visible per set", not bad,
                 ", ".join(f"{sid}={on[0] if len(on) == 1 else '?'}"
                           for sid, on, _ in per_set)
                 + (f" — WRONG {bad}" if bad else ""))

        # Switching must actually switch, through the operator the panel uses.
        # SEARCH FOR A USABLE SET rather than assuming sets[0] has one. The
        # first version indexed [0] and called next() with no default, so a
        # manifest reordered to put a single-arrangement set first would raise
        # StopIteration and abort the whole run -- a crash where a readable
        # gate failure belongs.
        cand = [(st, o) for st in sets for o in st["options"]
                if not o["default"] and o["show"]]
        gate("some set offers a non-default arrangement to switch to",
             bool(cand), f"{len(cand)} across {len(sets)} sets")
    if sets and cand:
        st, alt = cand[0]
        bpy.ops.adu.layout(set_id=st["id"], option_id=alt["id"])
        now = {n for n in views._controlled()
               if (o := bpy.data.objects.get(n)) and not o.hide_get()}
        gate("choosing an arrangement shows it and hides the others",
             set(alt["show"]) <= now
             and not any(n in now for o in st["options"] if o["id"] != alt["id"]
                         for n in o["show"]),
             f"{st['id']} -> {alt['id']}")

        # And a visibility mode must not undo that choice.
        views.full()
        after = {n for n in views._controlled()
                 if (o := bpy.data.objects.get(n)) and not o.hide_get()}
        gate("a visibility mode preserves the chosen arrangement",
             set(alt["show"]) <= after,
             f"{alt['id']} still visible after full()")

        # The empty option is the one the first gate could not see. Choose it
        # explicitly and require the set to go dark.
        empty = next((o for o in st["options"] if not o["show"]), None)
        if empty is not None:
            views.layout(st["id"], empty["id"])
            dark = {n for o in st["options"] for n in o["show"]
                    if (ob := bpy.data.objects.get(n)) and not ob.hide_get()}
            gate("an empty arrangement hides everything its set controls",
                 not dark, f"{st['id']} -> {empty['id']}"
                 + (f" — STILL VISIBLE {sorted(dark)[:3]}" if dark else ""))

        views.layout(st["id"], next(o["id"] for o in st["options"] if o["default"]))

    # ---- the manifest's visibility modes, and views.py, must agree --------
    # THE PAGE AND THE BLENDER TOOL ARE TWO CONSUMERS OF ONE RULE. views.py
    # has known how to strip a roof since Tier 1, and the configurator could
    # not ask for the same thing because the rule lived in this module and
    # never reached the runtime. It is spec.export.display_modes now, resolved
    # into the manifest as node NAMES.
    #
    # Which creates the obvious hazard: two consumers, one of which could
    # quietly stop matching the other. So drive views.py and compare what it
    # ACTUALLY HID against what the manifest promises the page will hide --
    # the objects, not the prefixes.
    # UNTRUSTED, like views._manifest() already treats it. A missing,
    # truncated or hand-edited file must produce a FAILING GATE, not a
    # traceback out of read_text() before any gate has run.
    views.full()
    man, man_err = {}, None
    try:
        man = json.loads((HERE / "export" / "variants.json").read_text())
        if not isinstance(man, dict):
            man, man_err = {}, "manifest is not an object"
    except (OSError, ValueError) as e:
        man_err = f"{type(e).__name__}: {e}"
    modes = [m for m in (man.get("views") or [])
             if isinstance(m, dict) and isinstance(m.get("id"), str)
             and isinstance(m.get("hide"), list)]
    gate("the manifest carries visibility modes at all", bool(modes),
         f"{len(modes)} modes: {[m['id'] for m in modes]}" if modes else
         (f"unreadable — {man_err}" if man_err else
          "no `views` block — the page cannot offer SHOW INTERIOR"))

    known = {o.name for o in bpy.data.objects if o.type == "MESH"}
    bad_modes = []
    for m in modes:
        # THROUGH THE ALLOW-LIST. `getattr(views, id)` would let a manifest
        # id reach ANY callable in that module -- `register`, or a camera
        # preset like `front` -- and the gate could then report agreement
        # about something that never changed visibility at all.
        fn = views.VISIBILITY.get(m["id"])
        if not callable(fn):
            bad_modes.append(f"{m['id']} is not one of views.VISIBILITY "
                             f"({sorted(views.VISIBILITY)})")
            continue
        fn()
        hidden = {o.name for o in bpy.data.objects
                  if o.type == "MESH" and o.hide_get()}
        # ONLY WHAT THIS SCENE CAN ANSWER FOR. The manifest is resolved
        # against the EXPORT, and the export has glazing -- finish_adu.py adds
        # it, so barn_cabin_524.blend does not have it. Comparing the two sets
        # raw reports eleven Glazing_ nodes as "views.py leaves them shown"
        # when views.py is looking at a scene where they do not exist. That is
        # #86's mistake exactly: a gate pointed at a file holding none of the
        # objects it trips on. Every name is guaranteed to be a real EXPORT
        # node by finish_adu, which resolves them from the exported set.
        promised = set(m["hide"]) & known
        # a presence set hides furniture independently of the mode, so judge
        # only what this mode itself claims to control
        extra = promised - hidden
        missed = {n for n in hidden - promised if not n.startswith("Furn_")}
        if extra:
            bad_modes.append(f"{m['id']}: the manifest says hide "
                             f"{sorted(extra)[:3]}, views.py leaves them shown")
        if missed:
            bad_modes.append(f"{m['id']}: views.py hides {sorted(missed)[:3]}, "
                             f"the manifest never names them")
    views.full()
    gate("every mode hides in the page exactly what it hides in Blender",
         not bad_modes, "; ".join(bad_modes[:2]) or
         f"{len(modes)} modes agree, object for object")

    # A name that resolves to nothing hides nothing and looks like it worked.
    # Glazing is the known-absent set here, so it is named rather than
    # silently tolerated: anything ELSE unknown is a real ghost.
    # THE EXEMPTION IS A LIST, NOT A PREFIX. Deferring anything beginning
    # `Glazing_` also defers `Glazing_W-KITCHEN_typo`, so a stale name would
    # be waved through by both this gate and the agreement check above. The
    # builder states the set -- it adds the glazing, so it knows which names
    # exist only after export -- rather than the verifier reconstructing it
    # from a spec whose openings are nested per wall.
    expect_glaz = set(man.get("views_export_only") or [])
    named = {n for m in modes for n in m["hide"]}
    ghosts = sorted(n for n in named - known if n not in expect_glaz)
    skipped = sorted(n for n in named - known if n in expect_glaz)
    gate("every node the manifest names exists, or the builder vouched for it",
         not ghosts,
         f"{len(ghosts)} unknown: {ghosts[:3]}" if ghosts else
         f"{len(named)} names across {len(modes)} modes; {len(skipped)} "
         f"deferred, each one named in views_export_only by the builder")

    # ---- and the numbers a SHOW DIMENSIONS overlay would draw -------------
    # Against the MODEL, not against the spec arithmetic that wrote them. The
    # overlay's job is to describe this building, so the building is the
    # authority -- rule 36, applied to a number leaving the repo.
    # EVERY FOOTPRINT IT PUBLISHES, not just the one that was easy. Checking
    # `overall` alone let a bad formula in either buyer-facing number ship
    # green -- and `with_porch` is the one a dimension overlay actually draws.
    # Each has a witness in the geometry:
    def span(prefixes):
        vs = [o.matrix_world @ v.co for o in bpy.data.objects
              if o.type == "MESH" and o.name.startswith(prefixes)
              for v in o.data.vertices]
        return (max(v.x for v in vs) - min(v.x for v in vs),
                max(v.y for v in vs) - min(v.y for v in vs),
                max(v.z for v in vs)) if vs else None

    dims = man.get("dimensions") or {}
    witness = {"main_body": ("Wall_",),                 # the heated box
               "with_porch": ("Wall_", "Gable_"),       # walls plus porch gable
               "overall": ("Roof_",)}                   # eave and rake
    bad_dim = []
    for key, pref in witness.items():
        d, got = dims.get(key), span(pref)
        if not d:
            bad_dim.append(f"{key} missing from the manifest")
            continue
        if abs(d["width"] - got[0]) > 0.02:
            bad_dim.append(f"{key} width {d['width']} vs {got[0]:.2f} built")
        if abs(d["depth"] - got[1]) > 0.02:
            bad_dim.append(f"{key} depth {d['depth']} vs {got[1]:.2f} built")
    ridge = dims.get("height_to_ridge")
    got_r = span(("Roof_",))
    if ridge is None:
        bad_dim.append("height_to_ridge missing from the manifest")
    elif abs(ridge - got_r[2]) > 0.02:
        bad_dim.append(f"ridge {ridge} vs {got_r[2]:.2f} built")
    gate("every dimension the manifest publishes matches the model",
         bool(dims) and not bad_dim, "; ".join(bad_dim[:3]) or
         (f"{len(witness)} footprints and the ridge, each against its own "
          f"geometry" if dims else "no `dimensions` block"))

    print("=" * 96)
    print(f"RESULT: {'ALL PASS' if not FAILED else 'FAILED: ' + ', '.join(FAILED)}")
    print("=" * 96)
    if FAILED:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
