"""
finish.py — Laurel P4 (#131): materials, glazing, three levels, the manifest.

    blender --background --python-exit-code 1 --python finish.py -- [--out DIR]

Builds Laurel from spec.yaml with build.py, applies spec.materials, sets glass
in every window and the entry door's sidelite, exports three Draco-compressed
levels as .glb, and writes the configurator manifest the page reads. Nothing
in export/ changes until every gate below has passed.

THE KIT DOES MOST OF IT (#153): materials, assignment, the closed-and-outward
gate, the lod2 contract, staged publishing, and the manifest's identity, sets
and views blocks are adu_kit's, shared with the barn cabin. What is Laurel's:
  * its glazing, placed from the openings build.py records,
  * which openings belong in lod1 -- the exterior walls' -- and
  * its dimensions block.

A scene is authored at 1 Blender unit = 1 foot; the export is in metres.
"""
import json
import shutil
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.append(str(HERE.parents[1]))          # buyer/3D, where adu_kit lives
from build import _wall_band, arrangement_ids, build, load_spec, option_nodes  # noqa: E402
from adu_kit import manifest as kit_manifest  # noqa: E402
from adu_kit.export import export_glb, glb_info, patch_base_color_factors  # noqa: E402
from adu_kit.manifest import face_slots  # noqa: E402
from adu_kit.finish import (  # noqa: E402
    assign, closure_problems, lod2_contract_nodes, make_materials, promote,
    report_lod2_contract, stage)
from adu_kit.kernel import box, collection  # noqa: E402
from adu_kit.schema.model_contract import (  # noqa: E402
    baseline_problems, display_problems, footprint_problems, glb_names,
    identity_problems)

# lod2 first: its node contract is checked before ANY export, so a rejected
# build leaves every file in export/ as it was.
LEVELS = ("lod2", "lod0", "lod1")
DRACO = "KHR_draco_mesh_compression"


def add_glazing(spec, geo, coll):
    """A pane in every window and in door 1's sidelite, in the sash's plane.

    Placed from the openings build.py records, at the glazing plane its sashes
    straddle. The pane is thinner than the members stand proud of that plane
    on each side, so no pane face is coplanar with a member's; and it is inset
    by half a frame, so its edges end inside the frame rather than on the
    rough opening's face.
    """
    win = spec["windows"]
    d = win["glass_thickness"]["ft"]
    inset = win["frame_to_glass"]["ft"] / 2
    made = []
    for o in geo["built"]:
        if o["id"].startswith("W-"):
            name, (b0, b1) = f"Glazing_{o['id']}", (o["a0"], o["a1"])
        elif "sidelite_x" in o["row"]:
            name, (b0, b1) = f"Glazing_{o['id']}_sidelite", o["row"]["sidelite_x"]
        else:
            continue                      # a door is a leaf, not glass
        lo, hi = _wall_band(geo["walls"], o["wall"], o["along"])
        plane = (lo + hi) / 2
        a0, a1 = b0 + inset, b1 - inset
        z0, z1 = o["z0"] + inset, o["z1"] - inset
        p0, p1 = plane - d / 2, plane + d / 2
        spec_box = ((a0, a1, p0, p1, z0, z1) if o["along"] == "x"
                    else (p0, p1, a0, a1, z0, z1))
        made.append(box(name, *spec_box, coll))
    return made


def exterior_ids(geo):
    """The openings in an exterior wall: the ones a street view shows."""
    return {o["id"] for o in geo["built"] if o["wall"] in geo["skin_of"]}


def opening_id(name):
    """`Sash_W-A1` -> `W-A1`; `Sash_D-1_sidelite` and `Leaf_D-1` -> `D-1`."""
    return name.split("_", 1)[1].removesuffix("_sidelite")


def level_objects(lod, geo, colls, glazing):
    """What each level exports, as spec.export.levels describes it.

    The SIDING collection -- the siding skins and their trim -- goes in lod0
    and lod1, where a buyer can choose it (#133), and never in lod2, whose
    contract is the stucco skin alone."""
    keep = (list(colls["Shell"].objects) + list(colls["Roof"].objects)
            + list(colls["Site"].objects))
    if lod == "lod2":
        return keep
    # The siding and the condenser on its pad are OUTSIDE, so a street view
    # (lod1) carries them as lod0 does; lod2's contract carries neither.
    siding = list(colls["Siding"].objects) + list(colls["Equipment"].objects)
    if lod == "lod0":
        return (keep + siding + list(colls["Openings"].objects)
                + list(colls["Partitions"].objects) + list(colls["Trim"].objects)
                + list(colls["Fixtures"].objects) + list(colls["Furniture"].objects)
                + glazing)
    outside = exterior_ids(geo)
    return keep + siding + [o for o in colls["Openings"].objects
                            if opening_id(o.name) in outside] + glazing


def presence_block(groups, nodes, arrangements=frozenset()):
    """`presence`: spec.variants.presence as the page reads it, with each
    group's `controls` checked against the nodes the export carries, and
    problems.

    EVERY NODE A GROUP CONTROLS IS SHOWN BY EXACTLY ONE OF ITS OPTIONS. A
    group declares the name prefixes it controls; any exported node with one
    of them that no option shows would never appear, and one two options
    show would be half of two finishes at once. `controls` stays in the spec:
    the page needs only the options.

    A furniture option names an `arrangement` instead of a `show` list
    (#135), one of `arrangements`, the ids spec.fixtures.furniture declares;
    build.option_nodes resolves it to the Furn_<arrangement>_ nodes the
    export carries, and the manifest publishes the resolved list, which
    is all the page reads."""
    # READ, NOT OBEYED (rule 25): a malformed block is a named problem, and
    # nothing partial is published. Found by review: `presence: [1]`, or an
    # option that is a scalar, raised mid-export instead.
    if groups is None:
        return [], []
    if not isinstance(groups, list):
        return [], [f"variants.presence must be a list of groups, found {type(groups).__name__}"]
    shape = []
    for i, g in enumerate(groups):
        if not isinstance(g, dict):
            shape.append(f"variants.presence[{i}] must be an object, found {type(g).__name__}")
            continue
        for key in ("options", "controls"):
            if key in g and not isinstance(g[key], list):
                shape.append(f"variants.presence[{i}].{key} must be a list")
        for j, o in enumerate(g.get("options") if isinstance(g.get("options"), list) else []):
            if not isinstance(o, dict):
                shape.append(f"variants.presence[{i}].options[{j}] must be an object, "
                             f"found {type(o).__name__}")
            elif not (isinstance(o.get("show", []), list)
                      and all(isinstance(n, str) for n in o.get("show", []))):
                shape.append(f"variants.presence[{i}].options[{j}].show must be a list of names")
            elif "arrangement" in o and "show" in o:
                shape.append(f"variants.presence[{i}].options[{j}] names both `show` and "
                             f"`arrangement`; one says what it shows")
            elif not isinstance(o.get("arrangement"), (str, type(None))):
                shape.append(f"variants.presence[{i}].options[{j}].arrangement must be an "
                             f"arrangement id or null")
        if not all(isinstance(p, str) for p in g.get("controls") or []
                   if isinstance(g.get("controls"), list)):
            shape.append(f"variants.presence[{i}].controls must be a list of prefixes")
    if shape:
        return [], shape
    problems, out = [], []
    for g in groups:
        gid = g.get("id")
        opts = g.get("options") or []
        resolved = [option_nodes(o, nodes, arrangements) for o in opts]
        shown = [n for s in resolved for n in s]
        # AN ARRANGEMENT THE SPEC DOES NOT DECLARE, or one that resolves to
        # nothing, is misspelt or unbuilt, and would publish as a silently
        # empty room -- or, matched as a prefix, as two alternatives at once.
        # Only null means empty; "" is not null. Found by review.
        problems += [f"presence {gid}: option {o.get('id')} names arrangement "
                     f"{o['arrangement']!r}, which fixtures.furniture does not declare"
                     for o in opts if "arrangement" in o and o["arrangement"] is not None
                     and o["arrangement"] not in arrangements]
        problems += [f"presence {gid}: option {o.get('id')} names arrangement "
                     f"{o['arrangement']!r}, which no exported node is"
                     for o, s in zip(opts, resolved)
                     if o.get("arrangement") in arrangements and not s]
        owned = sorted(n for n in nodes if n.startswith(tuple(g.get("controls") or ())))
        problems += [f"presence {gid}: {n} is shown by no option" for n in owned if n not in shown]
        problems += [f"presence {gid}: {n} is shown by {shown.count(n)} options"
                     for n in sorted(set(shown)) if shown.count(n) > 1]
        problems += [f"presence {gid}: {n} is shown but not in the export"
                     for n in sorted(set(shown) - set(nodes))]
        if not g.get("controls"):
            problems.append(f"presence {gid}: declares no `controls`, so nothing "
                            f"checks that every node it swaps is owned")
        # THE PREFIXES ARE HELD TO THE EXPORT TOO, as views_block holds a
        # mode's: every shown name falls under one, and every one matches a
        # node. Otherwise a missing or misspelt prefix passed whenever the
        # `show` lists happened to name the nodes, and the ownership check
        # above covered nothing. Found by review.
        prefixes = tuple(g.get("controls") or ())
        problems += [f"presence {gid}: {n} is shown but no `controls` prefix covers it"
                     for n in sorted(set(shown)) if not n.startswith(prefixes)]
        problems += [f"presence {gid}: `controls` prefix {x!r} matches no exported node"
                     for x in prefixes if not any(n.startswith(x) for n in nodes)]
        block = {"id": gid, "label": g.get("label")}
        # `room` IS KEPT. It is what marks a group as furniture, and so what
        # makes the page require the "not included" disclosure: dropping it
        # would let a furnished room ship without one. Its type is the
        # contract's to check. Found by review.
        if "room" in g:
            block["room"] = g["room"]
        block["property"] = "visible"
        block["options"] = [{"id": o.get("id"), "label": o.get("label"),
                             "show": s,
                             "default": bool(o.get("default"))} for o, s in zip(opts, resolved)]
        out.append(block)
    return out, problems


# THE NODES EACH FOOTPRINT IS (#119), in lod2: the heated box is the four
# stud walls, face of stud to face of stud; the extent over the eaves is the
# roof. finish.py holds each footprint's extent to these, as published.
FOOTPRINT_WITNESSES = {
    "main_body": ["Wall_front", "Wall_rear", "Wall_x0", "Wall_x24"],
    "overall": ["Roof_shed"],
}


def dimensions(spec):
    """The SHOW DIMENSIONS overlay's numbers. Width runs along the front.

    Each footprint carries its EXTENT (#119): where it sits in the file, so
    the overlay places it instead of centring it on the model's box. Laurel
    needs that more than most: its 5'-0" front overhang against 1'-6" at the
    rear pulls the box's centre 0.53 m off the walls'. Derived from the same
    spec numbers as the sizes, in the build's frame -- X 0..W, Y 0..D from
    the rear -- and checked against the exported walls and roof."""
    env, ov = spec["envelope"], spec["roof"]["overhangs"]
    w, d = env["width"]["ft"], env["depth"]["ft"]
    ends, front, rear = ov["ends"]["ft"], ov["front"]["ft"], ov["rear"]["ft"]
    return {
        "units": "feet",
        "main_body": {"width": w, "depth": d,
                      "extent": kit_manifest.extent_m((0.0, w), (0.0, d)),
                      "note": "the heated box, face of stud to face of stud (A-1.0)"},
        "overall": {"width": w + 2 * ends,
                    "depth": d + front + rear,
                    "extent": kit_manifest.extent_m((-ends, w + ends), (-rear, d + front)),
                    "note": f"over the roof: {ov['ends']['raw']} at each end, "
                            f"{ov['front']['raw']} over the entry and "
                            f"{ov['rear']['raw']} at the rear"},
        # A shed has no ridge: its highest point is the top of the roof at
        # the front edge of the overhang, which A-2.0 dimensions.
        "height_to_ridge": spec["levels"]["roof_top_at_front_edge"]["ft"],
        "note": ("TWO FOOTPRINTS. `main_body` is the building; `overall` is "
                 f"what the roof covers, with the {ov['front']['raw']} overhang "
                 "over the entry. A setback check needs both, since many "
                 "jurisdictions measure to the wall and cap eave projection "
                 "separately."),
    }


def write_manifest(spec, out, lod0):
    """variants.json, validated before it is written; (path, problems)."""
    model_id = spec["meta"]["model_id"]
    mats, nodes = glb_names(lod0)
    idx = spec["meta"].get("index") or {}
    ident, problems = kit_manifest.identity_block(spec, lod0, idx.get("note"))
    sets, bad = kit_manifest.sets_block(spec.get("variants"), mats)
    problems += bad
    views, bad = kit_manifest.views_block(
        (spec.get("export") or {}).get("display_modes"), nodes)
    problems += bad
    variants = spec.get("variants")
    presence, bad = presence_block(variants.get("presence") if isinstance(variants, dict) else None,
                                   nodes, arrangement_ids(spec))
    problems += bad
    manifest = {
        "model": ident,
        "note": ("Runtime material swaps. Each option sets baseColorFactor on "
                 "the named materials, which the stucco and siding textures "
                 "carry as luminance only, so a colour holds on either finish. "
                 "The finish itself is a presence choice: it swaps the skin."),
        "sets": sets,
        "presence": presence,
    }
    # THE DISCLOSURE (#135): the furniture groups name a `room`, and the
    # contract then requires it. Copied as written; model_contract judges it.
    for key in ("disclosure", "disclosure_note"):
        if isinstance(variants, dict) and key in variants:
            manifest[key] = variants[key]
    if views is not None:
        manifest["views"] = views
        manifest["views_note"] = kit_manifest.VIEWS_NOTE
    manifest["dimensions"] = dimensions(spec)
    problems += footprint_problems(out / f"{model_id}_lod2.glb", manifest["dimensions"],
                                   FOOTPRINT_WITNESSES)
    problems += identity_problems(manifest["model"], "model")
    problems += display_problems(manifest)
    if model_id != ident.get("id"):
        problems.append(f"the manifest's id {ident.get('id')!r} is not {model_id!r}")
    if problems:
        return None, problems
    path = out / "variants.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    return path, []


def save_viewable_blend(spec, dest):
    """lod0 with its materials, as a .blend to open and look at. build.py's
    .blend is grey: the materials are made here. Gitignored."""
    geo, colls = build(spec, cut_openings=True)
    mats = make_materials(spec, HERE / "textures", textured=True)
    add_glazing(spec, geo, collection("Glazing"))
    assign(spec, mats, face_slots(spec["materials"])[0])
    # Each presence group as the page opens it: its default option, or its
    # FIRST when none is marked -- the contract allows that, and the page
    # and views.py both fall back to the first. Found by review: with no
    # default this hid every option, and the blend showed no finish at all.
    # Here the stucco skin shows and the siding with its trim is hidden.
    names = [ob.name for ob in bpy.data.objects]
    for g in (spec.get("variants") or {}).get("presence") or []:
        opts = g["options"]
        chosen = next((o for o in opts if o.get("default")), opts[0] if opts else None)
        for o in opts:
            if o is chosen:
                continue
            for name in option_nodes(o, names, arrangement_ids(spec)):
                ob = bpy.data.objects.get(name)
                if ob is not None:
                    ob.hide_set(True)
                    ob.hide_viewport = ob.hide_render = True
    bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    return dest


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    final_out = (Path(argv[argv.index("--out") + 1]) if "--out" in argv
                 else HERE / "export")
    spec = load_spec(HERE / "spec.yaml")
    model_id = spec["meta"]["model_id"]
    out = stage(final_out)

    slots, bad = face_slots(spec["materials"])
    if bad:
        print("\nNOTHING EXPORTED: " + "; ".join(bad))
        shutil.rmtree(out, ignore_errors=True)
        raise SystemExit(1)

    want2 = lod2_contract_nodes(spec)
    if not want2:
        report_lod2_contract(want2, None)
        print("\nNOTHING EXPORTED: the lod2 contract is the precondition.")
        shutil.rmtree(out, ignore_errors=True)
        raise SystemExit(1)

    results, closure, unmatched = {}, [], {}
    untextured = set(spec["texturing"].get("untextured_levels") or [])
    for lod in LEVELS:
        geo, colls = build(spec, cut_openings=(lod != "lod2"))
        textured = lod not in untextured
        mats = make_materials(spec, HERE / "textures", textured=textured)
        glazing = ([] if lod == "lod2"
                   else add_glazing(spec, geo, collection("Glazing")))
        unmatched[lod] = assign(spec, mats, slots)
        keep = level_objects(lod, geo, colls, glazing)
        if lod == "lod2" and not report_lod2_contract(
                want2, sorted(o.name for o in keep)):
            print("\nNOTHING WRITTEN: lod2 is built first so a broken contract "
                  "costs no artefacts.")
            shutil.rmtree(out, ignore_errors=True)
            raise SystemExit(1)
        closure += closure_problems(keep, lod)
        path = out / f"{model_id}_{lod}.glb"
        export_glb(path, keep)
        if textured:
            # Blender writes a neutral map with no factor; the colour is put
            # back on the material, as the barn cabin's is (adu_kit.export).
            patch_base_color_factors(path, spec["materials"]["library"])
        results[lod] = glb_info(path)
        results[lod]["objects"] = len(keep)

    vpath, vproblems = write_manifest(spec, out, out / f"{model_id}_lod0.glb")
    base_bad = baseline_problems(out / f"{model_id}_lod2.glb",
                                 spec["export"].get("lod2_baseline"))
    budget = {k: v for k, v in spec["export"]["budget_kb"].items()
              if k.startswith("lod")}

    print("\n" + "=" * 76)
    print(f"{model_id} P4 EXPORT REPORT")
    print("=" * 76)
    for lod in ("lod0", "lod1", "lod2"):
        i = results[lod]
        bb = " x ".join(f"{v:.2f}" for v in i["bbox"])
        print(f"{lod}  {i['objects']:3d} objects  {i['meshes']:3d} meshes  "
              f"{i['materials']:2d} mats  {i['size_kb']:7.1f} KB / {budget[lod]} KB  "
              f"bbox {bb} m  {'draco' if DRACO in i['extensions'] else 'NO DRACO'}")
    for p_ in closure + vproblems + base_bad:
        print(f"  PROBLEM: {p_}")
    stray = sorted({n for names in unmatched.values() for n in names})

    gates = [
        ("every exported mesh is closed and wound outwards", not closure),
        ("every mesh matched a material", not stray),
        ("Draco on every level", all(DRACO in r["extensions"] for r in results.values())),
        ("every level within its size budget",
         all(results[k]["size_kb"] <= v for k, v in budget.items())),
        ("lod2 sits on its baseline: origin, axes, units and floor", not base_bad),
        ("the manifest meets the page's contract, the entry sits at its front, "
         "and every finish and furniture node is shown by exactly one option",
         vpath is not None),
    ]
    print("-" * 76)
    if stray:
        print(f"  unmatched: {stray}")
    for label, ok in gates:
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    print("=" * 76)
    if not all(ok for _, ok in gates):
        shutil.rmtree(out, ignore_errors=True)
        print(f"\nNOTHING PUBLISHED: {final_out} still holds the last set that "
              f"passed. The staged files have been discarded.")
        raise SystemExit(1)

    # The unsuffixed .glb is a copy of lod0, for anyone who wants one file.
    (out / f"{model_id}.glb").write_bytes((out / f"{model_id}_lod0.glb").read_bytes())
    removed = promote(out, final_out)
    print(f"\npublished {len(list(final_out.iterdir()))} files to {final_out}"
          + (f"; removed from another generation: {removed}" if removed else ""))
    blend = save_viewable_blend(spec, HERE / f"{model_id}_finished.blend")
    print(f"viewable: {blend}  (lod0 with its materials)")


if __name__ == "__main__":
    main()
